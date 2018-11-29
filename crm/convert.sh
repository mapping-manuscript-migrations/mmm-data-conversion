#!/bin/bash

set -eo pipefail

./convert_sdbm.sh
./convert_bodley.sh
./convert_bibale.sh

echo "Loading conversion results to Fuseki"

$FUSEKI_HOME/tdbloader --graph=http://ldf.fi/mmm-sdbm/ /tmp/sdbm_cidoc.ttl \
  && $FUSEKI_HOME/tdbloader --graph=http://ldf.fi/mmm-bodley/ /tmp/bodley_cidoc.ttl \
  && $FUSEKI_HOME/tdbloader --graph=http://ldf.fi/mmm-bibale/ /tmp/bibale_cidoc.ttl \
  && $FUSEKI_HOME/tdbloader --graph=http://ldf.fi/schema/mmm/ $FUSEKI_HOME/mmm-schema.ttl \
  && rm /tmp/*

exec "$@"
