FROM secoresearch/fuseki

USER root

RUN apk add --no-cache curl

USER 9008

ENV PATH "$PATH:/jena-fuseki/bin"
ENV ASSEMBLER "/fuseki-base/configuration/assembler.ttl"
ENV INPUT_SPARQL_ENDPOINT "http://input-sdbm:3030/ds/sparql"

RUN mkdir -p $FUSEKI_BASE/databases/tdb \
    $FUSEKI_BASE/databases/lucene \
    $FUSEKI_BASE/databases/spatiallucene

COPY fuseki-config.ttl $FUSEKI_BASE/config.ttl
COPY crm/assembler.ttl $FUSEKI_BASE/configuration/assembler.ttl
COPY crm/mmm-schema.ttl $FUSEKI_HOME/mmm-schema.ttl
COPY crm/construct_cidoc_crm.sparql $FUSEKI_HOME/construct_cidoc_crm.sparql
COPY crm/construct_people.sparql $FUSEKI_HOME/construct_people.sparql
COPY crm/construct_places.sparql $FUSEKI_HOME/construct_places.sparql
COPY crm/construct_sources.sparql $FUSEKI_HOME/construct_sources.sparql

COPY --chown=9008 crm/convert.sh tdbloader $FUSEKI_HOME/
RUN chmod +x $FUSEKI_HOME/convert.sh $FUSEKI_HOME/tdbloader

EXPOSE 3030

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["java", "-cp", "*:/javalibs/*", "org.apache.jena.fuseki.cmd.FusekiCmd"]
