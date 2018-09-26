#!/bin/bash
docker-compose down -v \
  && docker-compose run --rm input-sdbm ./load_data.sh \
  && docker-compose run --rm input-bibale ./load_data.sh \
  && docker-compose run --rm input-bodley ./load_data.sh \
  && docker-compose up -d input-sdbm \
  && docker-compose up -d input-bibale \
  && docker-compose up -d input-bodley \
  && sleep 5 \
  && docker-compose run --rm crm ./convert.sh \
  && docker-compose up -d crm
