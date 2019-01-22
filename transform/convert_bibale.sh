#!/bin/bash

set -eo pipefail

# run the SPARQL construct query
printf '\nConstructing Bibale manuscripts\n\n'
curl -f --data-urlencode "query=$(cat /app/construct_bibale_manuscripts.sparql)" $INPUT_BIBALE_SPARQL_ENDPOINT -v > $OUTPUT/bibale_manuscripts.ttl
printf '\nConstructing Bibale works\n\n'
curl -f --data-urlencode "query=$(cat /app/construct_bibale_works.sparql)" $INPUT_BIBALE_SPARQL_ENDPOINT -v > $OUTPUT/bibale_works.ttl
printf '\nConstructing Bibale places\n\n'
curl -f --data-urlencode "query=$(cat /app/construct_bibale_places.sparql)" $INPUT_BIBALE_SPARQL_ENDPOINT -v > $OUTPUT/bibale_places.ttl
printf '\nConstructing Bibale actors\n\n'
curl -f --data-urlencode "query=$(cat /app/construct_bibale_actors.sparql)" $INPUT_BIBALE_SPARQL_ENDPOINT -v > $OUTPUT/bibale_actors.ttl

cat $OUTPUT/bibale_manuscripts.ttl $OUTPUT/bibale_works.ttl $OUTPUT/bibale_places.ttl $OUTPUT/bibale_actors.ttl > $OUTPUT/_temp_bibale_cidoc.ttl

printf '\nLinking Bibale places\n\n'
python link_bibale_places.py $OUTPUT/_temp_bibale_cidoc.ttl $OUTPUT/bibale_cidoc.ttl --logfile $OUTPUT/logs/bibale_linking.log

exec "$@"
