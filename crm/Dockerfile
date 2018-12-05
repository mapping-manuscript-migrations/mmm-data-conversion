FROM secoresearch/fuseki

USER root

RUN apk add --no-cache curl

USER 9008

ENV PATH "$PATH:/jena-fuseki/bin"
ENV ASSEMBLER "/fuseki-base/configuration/assembler.ttl"
ENV INPUT_SDBM_SPARQL_ENDPOINT "http://input-sdbm:3030/ds/sparql"
ENV INPUT_BODLEY_SPARQL_ENDPOINT "http://input-bodley:3030/ds/sparql"
ENV INPUT_BIBALE_SPARQL_ENDPOINT "http://input-bibale:3030/ds/sparql"

RUN mkdir -p $FUSEKI_BASE/databases/tdb \
    $FUSEKI_BASE/databases/lucene \
    $FUSEKI_BASE/databases/spatiallucene

COPY fuseki-config-crm.ttl $FUSEKI_BASE/config.ttl
COPY crm/assembler.ttl $FUSEKI_BASE/configuration/assembler.ttl
COPY crm/mmm-schema.ttl $FUSEKI_HOME/mmm-schema.ttl
COPY crm/construct_sdbm_manuscripts.sparql $FUSEKI_HOME/construct_sdbm_manuscripts.sparql
COPY crm/construct_sdbm_people.sparql $FUSEKI_HOME/construct_sdbm_people.sparql
COPY crm/construct_sdbm_places.sparql $FUSEKI_HOME/construct_sdbm_places.sparql
COPY crm/construct_sdbm_sources.sparql $FUSEKI_HOME/construct_sdbm_sources.sparql
COPY crm/construct_bod_manuscripts.sparql $FUSEKI_HOME/construct_bod_manuscripts.sparql
COPY crm/construct_bod_people.sparql $FUSEKI_HOME/construct_bod_people.sparql
COPY crm/construct_bod_places.sparql $FUSEKI_HOME/construct_bod_places.sparql
COPY crm/construct_bibale_actors.sparql $FUSEKI_HOME/construct_bibale_actors.sparql
COPY crm/construct_bibale_manuscripts.sparql $FUSEKI_HOME/construct_bibale_manuscripts.sparql
COPY crm/construct_bibale_places.sparql $FUSEKI_HOME/construct_bibale_places.sparql

COPY --chown=9008 crm/convert.sh crm/convert_sdbm.sh crm/convert_bodley.sh crm/convert_bibale.sh tdbloader tdbindexer s-delete $FUSEKI_HOME/
RUN chmod +x $FUSEKI_HOME/convert.sh $FUSEKI_HOME/convert_sdbm.sh $FUSEKI_HOME/convert_bodley.sh $FUSEKI_HOME/convert_bibale.sh $FUSEKI_HOME/tdbloader $FUSEKI_HOME/tdbindexer $FUSEKI_HOME/s-delete

EXPOSE 3030

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["java", "-cp", "*:/javalibs/*", "org.apache.jena.fuseki.cmd.FusekiCmd"]
