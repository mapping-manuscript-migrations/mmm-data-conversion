#!/bin/bash

set -eo pipefail

rm -f /output/_bibale*
rm -f /output/mmm_bibale.ttl
rm -f /output/mmm_places.ttl

printf '\nConverting Phillipps numbers\n\n'
grep "bibale" /data/phillipps_numbers.csv > /output/bibale_phillipps.csv
python phillipps_csv.py /output/bibale_phillipps.csv /output/_bibale_phillipps.ttl bibale_

# run the SPARQL construct query
printf '\nConstructing Bibale manuscripts\n\n'
curl -f --data-urlencode "query=$(cat /app/construct_bibale_manuscripts.sparql)" $INPUT_BIBALE_SPARQL_ENDPOINT -v > /output/_bibale_manuscripts.ttl
printf '\nConstructing Bibale works\n\n'
curl -f --data-urlencode "query=$(cat /app/construct_bibale_works.sparql)" $INPUT_BIBALE_SPARQL_ENDPOINT -v > /output/_bibale_works.ttl
printf '\nConstructing Bibale places\n\n'
curl -f --data-urlencode "query=$(cat /app/construct_bibale_places.sparql)" $INPUT_BIBALE_SPARQL_ENDPOINT -v > /output/_bibale_places.ttl
printf '\nConstructing Bibale actors\n\n'
curl -f --data-urlencode "query=$(cat /app/construct_bibale_actors.sparql)" $INPUT_BIBALE_SPARQL_ENDPOINT -v > /output/_bibale_actors.ttl
printf '\nConstructing Bibale collections\n\n'
curl -f --data-urlencode "query=$(cat /app/construct_bibale_collections.sparql)" $INPUT_BIBALE_SPARQL_ENDPOINT -v > /output/_bibale_collections.ttl
printf '\nConstructing Bibale transactions\n\n'
curl -f --data-urlencode "query=$(cat /app/construct_bibale_transactions.sparql)" $INPUT_BIBALE_SPARQL_ENDPOINT -v > /output/_bibale_transactions.ttl
printf '\nConstructing Bibale owner observations\n\n'
curl -f --data-urlencode "query=$(cat /app/construct_bibale_provenance.sparql)" $INPUT_BIBALE_SPARQL_ENDPOINT -v > /output/_bibale_provenance.ttl

cat /output/_bibale_phillipps.ttl /output/_bibale_manuscripts.ttl /output/_bibale_works.ttl /output/_bibale_places.ttl /output/_bibale_actors.ttl /output/_bibale_collections.ttl /output/_bibale_transactions.ttl /output/_bibale_provenance.ttl > /output/_bibale_combined.ttl

printf '\nLinking Bibale places\n\n'
python linker_places.py bibale_places /output/_bibale_combined.ttl /output/_bibale_linked.ttl --logfile /output/logs/bibale_linking.log

chmod a+r $OUTPUT/*

exec "$@"
