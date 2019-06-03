#!/bin/bash

set -eo pipefail

rm -f /output/_bodley*
rm -f /output/mmm_bodley.ttl

printf '\nConverting Phillipps numbers\n\n'
python phillipps_csv.py /data/bodley_phillipps.csv /output/_bodley_phillipps.ttl bodley_

# run the SPARQL construct query
printf '\nConstructing Bodley manuscripts\n\n'
curl -f --data-urlencode "query=$(cat /app/construct_bod_manuscripts.sparql)" $INPUT_BODLEY_SPARQL_ENDPOINT -v > /output/_bodley_manuscripts.ttl
printf '\nConstructing Bodley works\n\n'
curl -f --data-urlencode "query=$(cat /app/construct_bod_works.sparql)" $INPUT_BODLEY_SPARQL_ENDPOINT -v > /output/_bodley_works.ttl
printf '\nConstructing Bodley expressions\n\n'
curl -f --data-urlencode "query=$(cat /app/construct_bod_expressions.sparql)" $INPUT_BODLEY_SPARQL_ENDPOINT -v > /output/_bodley_expressions.ttl
printf '\nConstructing Bodley people\n\n'
curl -f --data-urlencode "query=$(cat /app/construct_bod_people.sparql)" $INPUT_BODLEY_SPARQL_ENDPOINT -v > /output/_bodley_people.ttl
printf '\nConstructing Bodley places\n\n'
curl -f --data-urlencode "query=$(cat /app/construct_bod_places.sparql)" $INPUT_BODLEY_SPARQL_ENDPOINT -v > /output/_bodley_places.ttl
printf '\nConstructing Bodley observations\n\n'
curl -f --data-urlencode "query=$(cat /app/construct_bod_observations.sparql)" $INPUT_BODLEY_SPARQL_ENDPOINT -v > /output/_bodley_observations.ttl
printf '\nConstructing Bodley languages\n\n'
curl -f --data-urlencode "query=$(cat /app/construct_bod_languages.sparql)" $INPUT_BODLEY_SPARQL_ENDPOINT -v > /output/_bodley_languages.ttl
printf '\nConstructing Bodley collections\n\n'
curl -f --data-urlencode "query=$(cat /app/construct_bod_collections.sparql)" $INPUT_BODLEY_SPARQL_ENDPOINT -v > /output/_bodley_collections.ttl

cat /output/_bodley_phillipps.ttl /output/_bodley_manuscripts.ttl /output/_bodley_works.ttl /output/_bodley_expressions.ttl /output/_bodley_people.ttl /output/_bodley_places.ttl /output/_bodley_observations.ttl /output/_bodley_languages.ttl /output/_bodley_collections.ttl > /output/_bodley_combined.ttl

printf '\nLinking Bodley places\n\n'

python linker.py bodley_places /output/_bodley_combined.ttl /output/_bodley_linked.ttl --logfile /output/logs/bodley_linking.log

exec "$@"
