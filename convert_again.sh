#!/bin/bash
docker-compose down \
  && docker volume rm mmm-data-conversion_mmm-crm \
  && docker-compose build crm \
  && docker-compose up -d input-sdbm \
  && docker-compose up -d input-bibale \
  && docker-compose up -d input-bodley \
  && sleep 5 \
  && docker-compose run --rm crm ./convert.sh \
  && docker-compose up -d crm
