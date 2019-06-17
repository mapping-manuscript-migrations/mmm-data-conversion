#!/bin/bash

set -eo pipefail

rm -f /output/_sdbm*
rm -f /output/mmm_sdbm.ttl

# run the SPARQL construct query

printf '\nConstructing SDBM manuscripts transactions\n\n'
curl -f --data-urlencode "query=$(cat /app/construct_sdbm_manuscripts_transactions.sparql)" $INPUT_SDBM_SPARQL_ENDPOINT -v > /output/_sdbm_manuscripts_transactions.ttl
printf '\nConstructing SDBM manuscripts\n\n'
curl -f --data-urlencode "query=$(cat /app/construct_sdbm_manuscripts.sparql)" $INPUT_SDBM_SPARQL_ENDPOINT -v > /output/_sdbm_manuscripts.ttl
printf '\nConstructing SDBM works\n\n'
curl -f --data-urlencode "query=$(cat /app/construct_sdbm_works.sparql)" $INPUT_SDBM_SPARQL_ENDPOINT -v > /output/_sdbm_works.ttl
printf '\nConstructing SDBM actors\n\n'
curl -f --data-urlencode "query=$(cat /app/construct_sdbm_people.sparql)" $INPUT_SDBM_SPARQL_ENDPOINT -v > /output/_sdbm_people.ttl
printf '\nConstructing SDBM places\n\n'
curl -f --data-urlencode "query=$(cat /app/construct_sdbm_places.sparql)" $INPUT_SDBM_SPARQL_ENDPOINT -v > /output/_sdbm_places.ttl
printf '\nConstructing SDBM sources\n\n'
curl -f --data-urlencode "query=$(cat /app/construct_sdbm_sources.sparql)" $INPUT_SDBM_SPARQL_ENDPOINT -v > /output/_sdbm_sources.ttl
printf '\nConstructing SDBM languages\n\n'
curl -f --data-urlencode "query=$(cat /app/construct_sdbm_languages.sparql)" $INPUT_SDBM_SPARQL_ENDPOINT -v > /output/_sdbm_languages.ttl

# Take only relevant parts of the data for place linking, and combine with the rest later

cat /output/_sdbm_manuscripts_transactions.ttl /output/_sdbm_manuscripts.ttl /output/_sdbm_people.ttl /output/_sdbm_places.ttl /output/_sdbm_sources.ttl /output/_sdbm_languages.ttl > /output/_sdbm_combined.ttl

printf '\nLinking SDBM places\n\n'
python linker.py sdbm_places /output/_sdbm_combined.ttl /output/_sdbm_linked_places.ttl --logfile /output/logs/sdbm_linking.log

cat /output/_sdbm_works.ttl /output/_sdbm_linked_places.ttl > /output/_sdbm_linked.ttl

chmod a+r $OUTPUT/*

exec "$@"
