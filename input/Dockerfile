FROM secoresearch/fuseki

ENV PATH "$PATH:/jena-fuseki/bin"
ENV ASSEMBLER "$FUSEKI_BASE/configuration/assembler.ttl"

RUN mkdir -p $FUSEKI_BASE/databases/tdb \
    $FUSEKI_BASE/databases/lucene \
    $FUSEKI_BASE/databases/spatiallucene

COPY fuseki-config.ttl $FUSEKI_BASE/config.ttl
COPY input/assembler.ttl $FUSEKI_BASE/configuration/assembler.ttl

COPY --chown=9008 tdbloader input/load_data.sh $FUSEKI_HOME/
RUN chmod +x $FUSEKI_HOME/tdbloader $FUSEKI_HOME/load_data.sh

EXPOSE 3030
USER 9008

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["java", "-cp", "*:/javalibs/*", "org.apache.jena.fuseki.cmd.FusekiCmd"]
