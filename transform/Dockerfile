FROM python:3.6.5-stretch

RUN echo deb http://http.debian.net/debian stretch-backports main >> /etc/apt/sources.list

RUN apt-get update && apt-get -t stretch-backports install -y git curl raptor2-utils

WORKDIR /app

COPY requirements.txt /app/

RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY . /app/

ENV INPUT_SDBM_SPARQL_ENDPOINT "http://input-sdbm:3030/ds/sparql"
ENV INPUT_BODLEY_SPARQL_ENDPOINT "http://input-bodley:3030/ds/sparql"
ENV INPUT_BIBALE_SPARQL_ENDPOINT "http://input-bibale:3030/ds/sparql"
ENV OUTPUT "/output"

#COPY mmm-schema.ttl /app/mmm-schema.ttl
COPY SPARQL/construct_sdbm_manuscripts.sparql /app/construct_sdbm_manuscripts.sparql
COPY SPARQL/construct_sdbm_works.sparql /app/construct_sdbm_works.sparql
COPY SPARQL/construct_sdbm_manuscripts_transactions.sparql /app/construct_sdbm_manuscripts_transactions.sparql
COPY SPARQL/construct_sdbm_people.sparql /app/construct_sdbm_people.sparql
COPY SPARQL/construct_sdbm_places.sparql /app/construct_sdbm_places.sparql
COPY SPARQL/construct_sdbm_sources.sparql /app/construct_sdbm_sources.sparql
COPY SPARQL/construct_bod_manuscripts.sparql /app/construct_bod_manuscripts.sparql
COPY SPARQL/construct_bod_people.sparql /app/construct_bod_people.sparql
COPY SPARQL/construct_bod_places.sparql /app/construct_bod_places.sparql
COPY SPARQL/construct_bibale_actors.sparql /app/construct_bibale_actors.sparql
COPY SPARQL/construct_bibale_manuscripts.sparql /app/construct_bibale_manuscripts.sparql
COPY SPARQL/construct_bibale_places.sparql /app/construct_bibale_places.sparql
COPY SPARQL/construct_bibale_works.sparql /app/construct_bibale_works.sparql

COPY src/link_bibale_places.py /app/link_bibale_places.py
COPY src/geonames.py /app/geonames.py

#COPY convert.sh /app/convert.sh
#COPY convert_bibale.sh /app/convert_bibale.sh
#COPY convert_bodley.sh /app/convert_bodley.sh
#COPY convert_sdbm.sh /app/convert_sdbm.sh
#COPY prune.sh /app/prune.sh

RUN chmod +x /app/convert.sh /app/convert_sdbm.sh /app/convert_bodley.sh /app/convert_bibale.sh

CMD ["./convert.sh"]