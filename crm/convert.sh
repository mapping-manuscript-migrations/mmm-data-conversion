#!/bin/bash

# run the SPARQL construct query
echo 'query=' | cat - $FUSEKI_HOME/construct_cidoc_crm.sparql | curl -d @- $INPUT_SPARQL_ENDPOINT -v > /tmp/cidoc.ttl

# load the result to a new Fuseki
$FUSEKI_HOME/tdbloader --graph=http://ldf.fi/mmm-sdbm-cidoc-crm/ /tmp/cidoc.ttl \
    && rm /tmp/*

exec "$@"
