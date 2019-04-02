#!/bin/bash
set -eo pipefail

docker-compose build crm

docker-compose stop crm
docker-compose run --rm crm ./deploy.sh
docker-compose up -d crm
