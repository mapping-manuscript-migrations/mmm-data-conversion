#!/bin/bash
set -eo pipefail

docker-compose build crm

docker-compose rm -vsf crm  # Force stop and remove crm volume
docker-compose run --rm crm ./deploy.sh
docker-compose up -d crm
