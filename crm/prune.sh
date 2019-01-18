#!/bin/bash
set -eo pipefail

query="ASK WHERE { GRAPH <$1> { ?s ?p ?o } }"
res=`curl -f --data-urlencode "query=${query}" http://localhost:3030/ds/sparql `

# If the graph exists, remove it
if [[ $res == *"\"boolean\" : true"* ]]
then
    $FUSEKI_HOME/bin/s-delete "http://localhost:3030/ds/data" $1
fi
