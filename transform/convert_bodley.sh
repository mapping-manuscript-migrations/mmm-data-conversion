#!/bin/bash

set -eo pipefail

# run the SPARQL construct query
printf '\nConstructing Bodley manuscripts\n\n'
curl -f --data-urlencode "query=$(cat /app/construct_bod_manuscripts.sparql)" $INPUT_BODLEY_SPARQL_ENDPOINT -v > $OUTPUT/_bodley_manuscripts.ttl
printf '\nConstructing Bodley people\n\n'
curl -f --data-urlencode "query=$(cat /app/construct_bod_people.sparql)" $INPUT_BODLEY_SPARQL_ENDPOINT -v > $OUTPUT/_bodley_people.ttl
printf '\nConstructing Bodley places\n\n'
curl -f --data-urlencode "query=$(cat /app/construct_bod_places.sparql)" $INPUT_BODLEY_SPARQL_ENDPOINT -v > $OUTPUT/_bodley_places.ttl

cat $OUTPUT/_bodley_manuscripts.ttl $OUTPUT/_bodley_people.ttl $OUTPUT/_bodley_places.ttl > $OUTPUT/_bodley_combined.ttl

printf '\nLinking Bodley places\n\n'

python linker.py bodley_places $OUTPUT/_bodley_combined.ttl $OUTPUT/_bodley_linked.ttl --logfile $OUTPUT/logs/bodley_linking.log

rapper -i turtle $OUTPUT/_bodley_linked.ttl -o turtle > $OUTPUT/bodley_cidoc.ttl

exec "$@"
