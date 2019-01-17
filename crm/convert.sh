#!/bin/bash
set -eo pipefail

case "$1" in
  "bibale")
    ./convert_bibale.sh
    $FUSEKI_HOME/tdbloader --graph=http://ldf.fi/mmm-bibale/ /tmp/bibale_cidoc.ttl
  ;;
  "bodley")
    ./convert_bodley.sh
    $FUSEKI_HOME/tdbloader --graph=http://ldf.fi/mmm-bodley/ /tmp/bodley_cidoc.ttl
  ;;
  "sdbm")
    ./convert_sdbm.sh
    $FUSEKI_HOME/tdbloader --graph=http://ldf.fi/mmm-sdbm/ /tmp/sdbm_cidoc.ttl
  ;;
  *)
    ./convert_bibale.sh
    ./convert_bodley.sh
    ./convert_sdbm.sh
    $FUSEKI_HOME/tdbloader --graph=http://ldf.fi/mmm-bibale/ /tmp/bibale_cidoc.ttl
    $FUSEKI_HOME/tdbloader --graph=http://ldf.fi/mmm-bodley/ /tmp/bodley_cidoc.ttl
    $FUSEKI_HOME/tdbloader --graph=http://ldf.fi/mmm-sdbm/ /tmp/sdbm_cidoc.ttl
  ;;
esac

$FUSEKI_HOME/tdbloader --graph=http://ldf.fi/schema/mmm/ $FUSEKI_HOME/mmm-schema.ttl
$FUSEKI_HOME/tdbindexer
rm /tmp/*
