#!/bin/bash
set -eo pipefail

docker-compose build crm

docker-compose rm -vsf crm
docker volume rm mmm-data-conversion_mmm-crm

docker-compose run --rm crm ./deploy.sh
docker-compose up -d crm
