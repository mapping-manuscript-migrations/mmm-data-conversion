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

COPY SPARQL/*.sparql /app/

COPY src/* /app/

#COPY convert.sh /app/convert.sh
#COPY convert_bibale.sh /app/convert_bibale.sh
#COPY convert_bodley.sh /app/convert_bodley.sh
#COPY convert_sdbm.sh /app/convert_sdbm.sh
#COPY prune.sh /app/prune.sh

RUN chmod +x /app/convert.sh /app/convert_sdbm.sh /app/convert_bodley.sh /app/convert_bibale.sh

CMD ["./convert.sh"]
