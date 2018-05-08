#!/bin/bash

# run the SPARQL construct query
curl -f --data-urlencode "query=$(cat $FUSEKI_HOME/construct_cidoc_crm.sparql)" $INPUT_SPARQL_ENDPOINT -v > /tmp/cidoc.ttl

# load the result to a new Fuseki
$FUSEKI_HOME/tdbloader --graph=http://ldf.fi/mmm-sdbm-cidoc-crm/ /tmp/cidoc.ttl \
  && $FUSEKI_HOME/tdbloader --graph=http://ldf.fi/mmm-sdbm-cidoc-crm/ /tmp/mmm-schema.ttl \
  && rm /tmp/*

exec "$@"
