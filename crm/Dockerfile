FROM secoresearch/fuseki:spatial-legacy

USER root

RUN apk add --no-cache curl

USER 9008

ENV PATH "$PATH:/jena-fuseki/bin"
ENV ASSEMBLER "/fuseki-base/configuration/assembler.ttl"
ENV INPUT_SDBM_SPARQL_ENDPOINT "http://input-sdbm:3030/ds/sparql"
ENV INPUT_BODLEY_SPARQL_ENDPOINT "http://input-bodley:3030/ds/sparql"
ENV INPUT_BIBALE_SPARQL_ENDPOINT "http://input-bibale:3030/ds/sparql"
ENV OUTPUT "/output"

RUN mkdir -p $FUSEKI_BASE/databases/tdb \
    $FUSEKI_BASE/databases/lucene \
    $FUSEKI_BASE/databases/spatiallucene

COPY fuseki-config-crm.ttl $FUSEKI_BASE/config.ttl
COPY crm/assembler.ttl $FUSEKI_BASE/configuration/assembler.ttl
COPY crm/schema/* $FUSEKI_HOME/

COPY --chown=9008 tdbloader tdbindexer crm/deploy.sh crm/prune.sh $FUSEKI_HOME/
RUN chmod +x $FUSEKI_HOME/tdbloader $FUSEKI_HOME/tdbindexer $FUSEKI_HOME/deploy.sh $FUSEKI_HOME/prune.sh
