#!/bin/bash

set -eo pipefail

# run the SPARQL construct query
printf '\nConstructing SDBM manuscripts transactions\n\n'
curl -f --data-urlencode "query=$(cat /app/construct_sdbm_manuscripts_transactions.sparql)" $INPUT_SDBM_SPARQL_ENDPOINT -v > $OUTPUT/sdbm_manuscripts_transactions.ttl
printf '\nConstructing SDBM manuscripts\n\n'
curl -f --data-urlencode "query=$(cat /app/construct_sdbm_manuscripts.sparql)" $INPUT_SDBM_SPARQL_ENDPOINT -v > $OUTPUT/sdbm_manuscripts.ttl
printf '\nConstructing SDBM works\n\n'
curl -f --data-urlencode "query=$(cat /app/construct_sdbm_works.sparql)" $INPUT_SDBM_SPARQL_ENDPOINT -v > $OUTPUT/sdbm_works.ttl
printf '\nConstructing SDBM actors\n\n'
curl -f --data-urlencode "query=$(cat /app/construct_sdbm_people.sparql)" $INPUT_SDBM_SPARQL_ENDPOINT -v > $OUTPUT/sdbm_people.ttl
printf '\nConstructing SDBM places\n\n'
curl -f --data-urlencode "query=$(cat /app/construct_sdbm_places.sparql)" $INPUT_SDBM_SPARQL_ENDPOINT -v > $OUTPUT/sdbm_places.ttl
printf '\nConstructing SDBM sources\n\n'
curl -f --data-urlencode "query=$(cat /app/construct_sdbm_sources.sparql)" $INPUT_SDBM_SPARQL_ENDPOINT -v > $OUTPUT/sdbm_sources.ttl

cat $OUTPUT/sdbm_manuscripts_transactions.ttl $OUTPUT/sdbm_manuscripts.ttl $OUTPUT/sdbm_works.ttl $OUTPUT/sdbm_people.ttl $OUTPUT/sdbm_places.ttl $OUTPUT/sdbm_sources.ttl > $OUTPUT/sdbm_cidoc.ttl

exec "$@"
