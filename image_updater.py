#!/usr/bin/python

import argparse
import json
import os
import pathlib
import re
import requests
import sys

REQUIRED_CONFIG_PARAMETERS = [
    "offline_token",
    "access_token_url",
    "rhel_major_versions_to_track",
    "img_list_url"
]


class ImageUpdater:
    def __init__(self, config_file):
        self.config = self.read_config_file(config_file)
        self.state = self.read_state_file()

    def read_config_file(self, config_file):
        with open(config_file) as f:
            config = json.load(f)

        for config_parameter in REQUIRED_CONFIG_PARAMETERS:
            if not config_parameter in config:
                print(f"Parmeter '{config_parameter}' not found in config, exiting.")
                sys.exit(1)

        return config

    def read_state_file(self):
        state_file = self.config["state_file"]

        # on the first run there is no state file yet so we return an empty dict
        if not os.path.exists(state_file):
            return {}

        with open(state_file) as f:
            return json.load(f)

    def write_state_file(self):
        statefile = self.config["state_file"]
        statefile_parent_directory = pathlib.Path(statefile).parent
        self.create_directory_if_not_exitsts(statefile_parent_directory)

        with open(statefile, "w") as outfile:
            json.dump(self.state, outfile)

    def create_directory_if_not_exitsts(self, directoy_to_create):
        if not os.path.exists(directoy_to_create):
            print(f"will create directory {directoy_to_create} ..")
            os.mkdir(directoy_to_create)

    def get_access_token(self):
        access_token_url = self.config["access_token_url"]
        offline_token = self.config["offline_token"]

        data = {
            "grant_type": "refresh_token",
            "client_id": "rhsm-api",
            "refresh_token": offline_token
        }

        response = requests.post(access_token_url, data=data)
        response_json = response.json()
        if "access_token" in response_json:
            self.access_token = response_json["access_token"]
            return response_json["access_token"]

        print(f'There was an error fetching an access_token:\n{response_json}')
        return None

    def build_img_list_url(self, rhel_major_version, architecture, limit, offset=0):
        base_url = self.config["img_list_url"]
        return f"{base_url}/rhel-{rhel_major_version}-for-{architecture}-baseos-isos?limit={limit}&offset={offset}"

    def get_latest_qcow_image_url(self, rhel_major_version, architecture):
        url = self.build_img_list_url(rhel_major_version, architecture, 100)
        print(f"will fetch available image data from {url} ..")

        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }

        response = requests.get(url, headers=headers)
        response_json = response.json()

        # print(response_json)

        latest_img = None
        max = -1

        pattern = f"rhel-{rhel_major_version}.(\d+)-{architecture}-kvm.qcow2"
        for img in response_json["body"]:
            imggrp = re.match(pattern, img["filename"])
            if not imggrp:
                continue

            if max < int(imggrp.group(1)):
                max = int(imggrp.group(1))
                latest_img = img

        return latest_img

    def download_image(self, img):
        # make sure download destination directory exists
        self.create_directory_if_not_exitsts(self.config["download_destination"])

        url = img["downloadHref"]
        filename = img["filename"]
        filepath = os.path.join(self.config["download_destination"], filename)

        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }

        try:
            with requests.get(url, stream=True, headers=headers) as response:
                response.raise_for_status()
                print(f"image size reported is {response.headers.get('content-length', 0)}, starting download (this will take a while) ..")
                with open(filepath, 'wb') as file:
                    for chunk in response.iter_content(chunk_size=8192):
                        file.write(chunk)
        except Exception as e:
            print(f"error downloading image - {e} ..")
            return False

        print("download complete ..")

        return True

    def update_state_for_image(self, img_state_identifier, img):
        if not img_state_identifier in self.state:
            self.state[img_state_identifier] = {}

        self.state[img_state_identifier]["checksum"] = img["checksum"]

        self.write_state_file()

    def are_checksums_equal(self, img_state_identifier, latest_img):
        if not img_state_identifier in self.state:
            return False

        existing_checksum = self.state[img_state_identifier]["checksum"]
        if existing_checksum != latest_img["checksum"]:
            return False

        return True

    def update_check(self):
        access_token = image_updater.get_access_token()
        if not access_token:
            print("error in fetchin access token, exiting.")
            sys.exit(1)

        for rhel_major_version in self.config["rhel_major_versions_to_track"]:
            for arch in rhel_major_version["architectures"]:
                latest_img = self.get_latest_qcow_image_url(rhel_major_version["rhel_major"], arch)
                print(f"latest img extracted from API {latest_img}")

                img_state_identifier = f'{rhel_major_version["rhel_major"]}-{arch}'
                if self.are_checksums_equal(img_state_identifier, latest_img):
                    print("checksums are equal, no need to download image ..")
                    continue

                if self.download_image(latest_img):
                    self.update_state_for_image(img_state_identifier, latest_img)

    def upload_image_to_glance(self):
        pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", help="Location of config file in JSON format", nargs='?', default='/etc/image_updater_config.json')
    args = parser.parse_args()
    config_file = args.config

    image_updater = ImageUpdater(config_file)
    image_updater.update_check()
