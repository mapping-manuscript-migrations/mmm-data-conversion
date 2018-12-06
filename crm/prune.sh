#!/bin/bash
set -eo pipefail

$FUSEKI_HOME/bin/s-delete "http://localhost:3030/ds/data" $1
