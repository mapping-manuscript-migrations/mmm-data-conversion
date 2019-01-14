#!/bin/bash

set -eo pipefail

# run the SPARQL construct query
printf '\nConstructing Bibale manuscripts\n\n'
curl -f --data-urlencode "query=$(cat $FUSEKI_HOME/construct_bibale_manuscripts.sparql)" $INPUT_BIBALE_SPARQL_ENDPOINT -v > /tmp/bibale_manuscripts.ttl
printf '\nConstructing Bibale works\n\n'
curl -f --data-urlencode "query=$(cat $FUSEKI_HOME/construct_bibale_works.sparql)" $INPUT_BIBALE_SPARQL_ENDPOINT -v > /tmp/bibale_works.ttl
printf '\nConstructing Bibale places\n\n'
curl -f --data-urlencode "query=$(cat $FUSEKI_HOME/construct_bibale_places.sparql)" $INPUT_BIBALE_SPARQL_ENDPOINT -v > /tmp/bibale_places.ttl
printf '\nConstructing Bibale actors\n\n'
curl -f --data-urlencode "query=$(cat $FUSEKI_HOME/construct_bibale_actors.sparql)" $INPUT_BIBALE_SPARQL_ENDPOINT -v > /tmp/bibale_actors.ttl

cat /tmp/bibale_manuscripts.ttl /tmp/bibale_works.ttl /tmp/bibale_places.ttl /tmp/bibale_actors.ttl > /tmp/bibale_cidoc_v1.ttl

printf '\nLinking Bibale places\n\n'
python link_bibale_places.py /tmp/bibale_cidoc_v1.ttl /tmp/bibale_cidoc.ttl

exec "$@"
