#!/bin/bash

set -eo pipefail

rm -f output/_bibale*
rm -f output/bibale_cidoc.ttl

printf '\nConverting Phillipps numbers\n\n'
python bibale_phillipps_csv.py /data/bibale_phillipps.csv output/_bibale_phillipps.ttl

# run the SPARQL construct query
printf '\nConstructing Bibale manuscripts\n\n'
curl -f --data-urlencode "query=$(cat /app/construct_bibale_manuscripts.sparql)" $INPUT_BIBALE_SPARQL_ENDPOINT -v > output/_bibale_manuscripts.ttl
printf '\nConstructing Bibale works\n\n'
curl -f --data-urlencode "query=$(cat /app/construct_bibale_works.sparql)" $INPUT_BIBALE_SPARQL_ENDPOINT -v > output/_bibale_works.ttl
printf '\nConstructing Bibale places\n\n'
curl -f --data-urlencode "query=$(cat /app/construct_bibale_places.sparql)" $INPUT_BIBALE_SPARQL_ENDPOINT -v > output/_bibale_places.ttl
printf '\nConstructing Bibale actors\n\n'
curl -f --data-urlencode "query=$(cat /app/construct_bibale_actors.sparql)" $INPUT_BIBALE_SPARQL_ENDPOINT -v > output/_bibale_actors.ttl
printf '\nConstructing Bibale collections\n\n'
curl -f --data-urlencode "query=$(cat /app/construct_bibale_collections.sparql)" $INPUT_BIBALE_SPARQL_ENDPOINT -v > output/_bibale_collections.ttl

cat output/_bibale_phillipps.ttl output/_bibale_manuscripts.ttl output/_bibale_works.ttl output/_bibale_places.ttl output/_bibale_actors.ttl output/_bibale_collections.ttl > output/_bibale_combined.ttl

printf '\nLinking Bibale places\n\n'
python linker.py bibale_places output/_bibale_combined.ttl output/_bibale_linked.ttl --logfile output/logs/bibale_linking.log

rapper -i turtle output/_bibale_linked.ttl -o turtle > output/bibale_cidoc.ttl

exec "$@"
