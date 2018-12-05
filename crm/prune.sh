#!/bin/bash
set -eo pipefail

case "$1" in
  "bibale")
    $FUSEKI_HOME/bin/s-delete "http://localhost:3030/ds/data" "http://ldf.fi/mmm-bibale/"
  ;;
  "bodley")
    $FUSEKI_HOME/bin/s-delete "http://localhost:3030/ds/data" "http://ldf.fi/mmm-bodley/"
  ;;
  "sdbm")
    $FUSEKI_HOME/bin/s-delete "http://localhost:3030/ds/data" "http://ldf.fi/mmm-sdbm/"
  ;;
esac