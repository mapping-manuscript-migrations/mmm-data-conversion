#!/bin/bash

set -eo pipefail

# run the SPARQL construct query
printf '\nConstructing Bodley manuscripts\n\n'
curl -f --data-urlencode "query=$(cat /app/construct_bod_manuscripts.sparql)" $INPUT_BODLEY_SPARQL_ENDPOINT -v > $OUTPUT/bodley_manuscripts.ttl
printf '\nConstructing Bodley people\n\n'
curl -f --data-urlencode "query=$(cat /app/construct_bod_people.sparql)" $INPUT_BODLEY_SPARQL_ENDPOINT -v > $OUTPUT/bodley_people.ttl
printf '\nConstructing Bodley places\n\n'
curl -f --data-urlencode "query=$(cat /app/construct_bod_places.sparql)" $INPUT_BODLEY_SPARQL_ENDPOINT -v > $OUTPUT/bodley_places.ttl

cat $OUTPUT/bodley_manuscripts.ttl $OUTPUT/bodley_people.ttl $OUTPUT/bodley_places.ttl > $OUTPUT/bodley_cidoc.ttl

exec "$@"
