#!/bin/bash
set -eo pipefail

case "$1" in
  "bibale")
    docker-compose up -d crm
    sleep 5
    docker-compose exec crm ./prune.sh "http://ldf.fi/mmm-bibale/"
    docker-compose down
  ;;
  "bodley")
    docker-compose up -d crm
    sleep 5
    docker-compose exec crm ./prune.sh "http://ldf.fi/mmm-bodley/"
    docker-compose down
  ;;
  "sdbm")
    docker-compose up -d crm
    sleep 5
    docker-compose exec crm ./prune.sh "http://ldf.fi/mmm-sdbm/" # TODO: sdbm-graafi on liian iso poistettavaksi s-deletellä
    docker-compose down
  ;;
  *)
    docker-compose down
    docker volume rm mmm-data-conversion_mmm-crm
  ;;
esac

docker-compose build crm
docker-compose up -d input-bibale
docker-compose up -d input-bodley
docker-compose up -d input-sdbm
sleep 5
docker-compose run --rm transform ./convert.sh $1
docker-compose run --rm crm ./deploy.sh
docker-compose up -d
