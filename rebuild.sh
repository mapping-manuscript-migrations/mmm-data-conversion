#!/bin/bash
docker-compose down -v \
  && docker-compose run --rm input ./load_data.sh \
  && docker-compose up -d input \
  && sleep 5 \
  && docker-compose run --rm crm ./convert.sh \
  && docker-compose up -d crm
