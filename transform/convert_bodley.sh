#!/bin/bash

set -eo pipefail

rm -f $OUTPUT/_bodley*
rm -f $OUTPUT/mmm_bodley.ttl

printf '\nConverting Phillipps numbers\n\n'
python phillipps_csv.py /data/bibale_phillipps.csv /output/_bibale_phillipps.ttl bodley_

# run the SPARQL construct query
printf '\nConstructing Bodley manuscripts\n\n'
curl -f --data-urlencode "query=$(cat /app/construct_bod_manuscripts.sparql)" $INPUT_BODLEY_SPARQL_ENDPOINT -v > $OUTPUT/_bodley_manuscripts.ttl
printf '\nConstructing Bodley works\n\n'
curl -f --data-urlencode "query=$(cat /app/construct_bod_works.sparql)" $INPUT_BODLEY_SPARQL_ENDPOINT -v > $OUTPUT/_bodley_works.ttl
printf '\nConstructing Bodley expressions\n\n'
curl -f --data-urlencode "query=$(cat /app/construct_bod_expressions.sparql)" $INPUT_BODLEY_SPARQL_ENDPOINT -v > $OUTPUT/_bodley_expressions.ttl
printf '\nConstructing Bodley people\n\n'
curl -f --data-urlencode "query=$(cat /app/construct_bod_people.sparql)" $INPUT_BODLEY_SPARQL_ENDPOINT -v > $OUTPUT/_bodley_people.ttl
printf '\nConstructing Bodley places\n\n'
curl -f --data-urlencode "query=$(cat /app/construct_bod_places.sparql)" $INPUT_BODLEY_SPARQL_ENDPOINT -v > $OUTPUT/_bodley_places.ttl
printf '\nConstructing Bodley observations\n\n'
curl -f --data-urlencode "query=$(cat /app/construct_bod_observations.sparql)" $INPUT_BODLEY_SPARQL_ENDPOINT -v > $OUTPUT/_bodley_observations.ttl

cat $OUTPUT/_bodley_manuscripts.ttl $OUTPUT/_bodley_works.ttl $OUTPUT/_bodley_expressions.ttl $OUTPUT/_bodley_people.ttl $OUTPUT/_bodley_places.ttl $OUTPUT/_bodley_observations.ttl > $OUTPUT/_bodley_combined.ttl

printf '\nLinking Bodley places\n\n'

python linker.py bodley_places $OUTPUT/_bodley_combined.ttl $OUTPUT/_bodley_linked.ttl --logfile $OUTPUT/logs/bodley_linking.log

exec "$@"
