#!/bin/bash
set -eo pipefail

case "$1" in
  "bibale")
    docker-compose up -d crm
    sleep 5
    docker-compose exec crm ./prune.sh $1
    docker-compose down
  ;;
  "bodley")
    docker-compose up -d crm
    sleep 5
    docker-compose exec crm ./prune.sh $1
    docker-compose down
  ;;
  "sdbm")
    docker-compose up -d crm
    sleep 5
    docker-compose exec crm ./prune.sh $1
    docker-compose down
  ;;
  *)
    docker-compose down
    docker volume rm mmm-data-conversion_mmm-crm
  ;;
esac

docker-compose build crm
docker-compose up -d input-sdbm
docker-compose up -d input-bibale
docker-compose up -d input-bodley
sleep 5
docker-compose run --rm crm ./convert.sh $1
docker-compose up -d