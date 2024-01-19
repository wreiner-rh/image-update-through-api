# image_updater

## How to obtain `offline_token`

The article explaining on how to obtain the `offline_token` can be found [here](https://access.redhat.com/articles/3626371).

With this `offline_token` it is possible to obtain an access_token up to 30 days after creating the `offline_token`. Those 30 days will be pushed forward, everytime a new access_token is obtained, so this script should be run at least once every 30 days.
