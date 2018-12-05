#!/bin/bash
set -eo pipefail

command -v s-delete >/dev/null 2>&1 || { echo >&2 "s-delete is not available, aborting"; exit 1; }

case "$1" in
  "bibale")
    s-delete "http://localhost:3050/ds/data" "http://ldf.fi/mmm-bibale/"
    docker-compose down
  ;;
  "bodley")
    s-delete "http://localhost:3050/ds/data" "http://ldf.fi/mmm-bodley/"
    docker-compose down
  ;;
  "sdbm")
    s-delete "http://localhost:3050/ds/data" "http://ldf.fi/mmm-sdbm/"
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
