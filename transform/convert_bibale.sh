#!/bin/bash

set -eo pipefail

# run the SPARQL construct query
printf '\nConstructing Bibale manuscripts\n\n'
curl -f --data-urlencode "query=$(cat /app/construct_bibale_manuscripts.sparql)" $INPUT_BIBALE_SPARQL_ENDPOINT -v > $OUTPUT/_bibale_manuscripts.ttl
printf '\nConstructing Bibale works\n\n'
curl -f --data-urlencode "query=$(cat /app/construct_bibale_works.sparql)" $INPUT_BIBALE_SPARQL_ENDPOINT -v > $OUTPUT/_bibale_works.ttl
printf '\nConstructing Bibale places\n\n'
curl -f --data-urlencode "query=$(cat /app/construct_bibale_places.sparql)" $INPUT_BIBALE_SPARQL_ENDPOINT -v > $OUTPUT/_bibale_places.ttl
printf '\nConstructing Bibale actors\n\n'
curl -f --data-urlencode "query=$(cat /app/construct_bibale_actors.sparql)" $INPUT_BIBALE_SPARQL_ENDPOINT -v > $OUTPUT/_bibale_actors.ttl

cat $OUTPUT/_bibale_manuscripts.ttl $OUTPUT/_bibale_works.ttl $OUTPUT/_bibale_places.ttl $OUTPUT/_bibale_actors.ttl > $OUTPUT/_bibale_combined.ttl

printf '\nLinking Bibale places\n\n'
python linker.py bibale_places $OUTPUT/_bibale_combined.ttl $OUTPUT/_bibale_linked.ttl --logfile $OUTPUT/logs/bibale_linking.log

rapper -i turtle $OUTPUT/_bibale_linked.ttl -o turtle > $OUTPUT/bibale_cidoc.ttl

exec "$@"
