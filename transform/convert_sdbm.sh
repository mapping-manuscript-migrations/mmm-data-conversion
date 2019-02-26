#!/bin/bash

set -eo pipefail

rm -f $OUTPUT/_sdbm*
rm -f $OUTPUT/sdbm_cidoc.ttl

# run the SPARQL construct query

printf '\nConstructing SDBM manuscripts transactions\n\n'
curl -f --data-urlencode "query=$(cat /app/construct_sdbm_manuscripts_transactions.sparql)" $INPUT_SDBM_SPARQL_ENDPOINT -v > $OUTPUT/_sdbm_manuscripts_transactions.ttl
printf '\nConstructing SDBM manuscripts\n\n'
curl -f --data-urlencode "query=$(cat /app/construct_sdbm_manuscripts.sparql)" $INPUT_SDBM_SPARQL_ENDPOINT -v > $OUTPUT/_sdbm_manuscripts.ttl
printf '\nConstructing SDBM works\n\n'
curl -f --data-urlencode "query=$(cat /app/construct_sdbm_works.sparql)" $INPUT_SDBM_SPARQL_ENDPOINT -v > $OUTPUT/_sdbm_works.ttl
printf '\nConstructing SDBM actors\n\n'
curl -f --data-urlencode "query=$(cat /app/construct_sdbm_people.sparql)" $INPUT_SDBM_SPARQL_ENDPOINT -v > $OUTPUT/_sdbm_people.ttl
printf '\nConstructing SDBM places\n\n'
curl -f --data-urlencode "query=$(cat /app/construct_sdbm_places.sparql)" $INPUT_SDBM_SPARQL_ENDPOINT -v > $OUTPUT/_sdbm_places.ttl
printf '\nConstructing SDBM sources\n\n'
curl -f --data-urlencode "query=$(cat /app/construct_sdbm_sources.sparql)" $INPUT_SDBM_SPARQL_ENDPOINT -v > $OUTPUT/_sdbm_sources.ttl

# Take only relevant parts of the data for place linking, and combine with the rest later

cat $OUTPUT/_sdbm_manuscripts_transactions.ttl $OUTPUT/_sdbm_manuscripts.ttl $OUTPUT/_sdbm_people.ttl $OUTPUT/_sdbm_places.ttl $OUTPUT/_sdbm_sources.ttl > $OUTPUT/_sdbm_combined.ttl

printf '\nLinking SDBM places\n\n'
python linker.py sdbm_places $OUTPUT/_sdbm_combined.ttl $OUTPUT/_sdbm_linked.ttl --logfile $OUTPUT/logs/sdbm_linking.log

cat $OUTPUT/_sdbm_works.ttl $OUTPUT/_sdbm_linked.ttl  | rapper - "http://ldf.fi/mmm/" -i turtle -o turtle > $OUTPUT/sdbm_cidoc.ttl

exec "$@"
