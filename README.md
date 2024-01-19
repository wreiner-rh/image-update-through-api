# image_updater

This script checks the Red Hat access API for new versions of RHEL qcow2 images and downloads those images.

## Configuation

Configuration is done through a configuration file in JSON format.

An example config, `config.json-example`, can be found distributed with this repository.

### Necessary Config Parameters

The following config parameters are necessary to use this script:

| Parameter                    | Usage                                                                |
|------------------------------|----------------------------------------------------------------------|
| offline_token                | Offline token to obtain access token (see section below)             |
| access_token_url             | URL to obtain the access token                                       |
| img_list_url                 | URL to fetch image lists                                             |
| download_destination         | Destination on where to download images to                           |
| state_file                   | State file holding information on downloaded images                  |
| rhel_major_versions_to_track | List of RHEL major version and architectures the script should track |

### How to obtain `offline_token`

The article explaining on how to obtain the `offline_token` can be found [here](https://access.redhat.com/articles/3626371).

With this `offline_token` it is possible to obtain an access_token up to 30 days after creating the `offline_token`. Those 30 days will be pushed forward, everytime a new access_token is obtained, so this script should be run at least once every 30 days.
