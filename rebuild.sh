#!/bin/bash
set -eo pipefail

docker-compose down -v
docker-compose run --rm input-bibale ./load_data.sh
docker-compose run --rm input-bodley ./load_data.sh
docker-compose run --rm input-sdbm ./load_data.sh
docker-compose up -d input-bibale
docker-compose up -d input-bodley
docker-compose up -d input-sdbm
sleep 5
docker-compose run --rm crm ./convert.sh
docker-compose up -d crm
