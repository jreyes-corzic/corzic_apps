#!/bin/bash
#Build the docker image for the sufs manager app and push the newest version to the server/registry
#For each update the sufs-manager.yaml file needs to be updated with the latest version number
#test locally by creating environment and running
#python3 main.py from app directory with modules modified for local use

docker buildx build --push --platform linux/amd64 --tag registry.corzicsys.com/sufs-manager-web-app:v2-5 .
cat sufs-manager.yaml | curl https://iolite.corzicsys.com/api/apps/sufs-manager -i -X PUT -H "Content-Type: text/yaml" -H "X-API-Key: XXn7tsQHbEqy4hHPQ2otg6OZA7FgbM" --data-binary @-
