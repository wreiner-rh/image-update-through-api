#!/usr/bin/python
import re
import requests
import sys

OFFLINE_TOKEN = "...."
ACCESS_TOKEN_URL = "https://sso.redhat.com/auth/realms/redhat-external/protocol/openid-connect/token"
IMG_LIST_URL = "https://api.access.redhat.com/management/v1/images/cset"
DOWNLOAD_DESTINATION = "/tmp/latest_images"

def build_img_list_url(base_url, rhel_major_version, architecture, limit, offset=0):
    return f"{base_url}/rhel-{rhel_major_version}-for-{architecture}-baseos-isos?limit={limit}&offset={offset}"

def get_access_token(access_token_url, offline_token):
    data = {
        "grant_type": "refresh_token",
        "client_id": "rhsm-api",
        "refresh_token": offline_token
    }

    response = requests.post(access_token_url, data=data)
    response_json = response.json()
    if "access_token" in response_json:
        return response_json["access_token"]

    print(f'There was an error fetching an access_token:\n{response_json}')
    return  None

def get_latest_qcow_image_url(access_token, img_list_url, rhel_major_version, architecture):
    url = build_img_list_url(img_list_url, rhel_major_version, architecture, 100)
    print(f"will fetch available image data from {url} ..")

    headers = {
        "Authorization": f"Bearer {access_token}"
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

def download_image(img, destination):
    pass

def upload_image_to_glance():
    pass

if __name__ == "__main__":
    access_token = get_access_token(ACCESS_TOKEN_URL, OFFLINE_TOKEN)
    if not access_token:
        print("error in fetchin access token, exiting.")
        sys.exit(1)

    # print(access_token)
    supported_major_versions = [8, 9]
    for major_version in supported_major_versions:
        img = get_latest_qcow_image_url(access_token, IMG_LIST_URL, major_version, "x86_64")

        print(f'\nImage for major {major_version}:\n{img["filename"]}')
        print(f'Image download url for major {major_version}:\n{img["downloadHref"]}')
        print(f'Image checksum\n{img["checksum"]}\n')

        download_image(img, DOWNLOAD_DESTINATION)
