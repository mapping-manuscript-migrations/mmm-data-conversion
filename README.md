# Mapping Manuscript Migrations data conversion pipeline

Currently the pipeline includes the following steps:

1. Create a directory called `data` with a subdirectory for each of the source databases and download the input RDF data as follows: (manual)
    * Schoenberg Database of Manuscripts (sdbm): https://sdbm.library.upenn.edu/downloads (you have to be logged in)
    * Medieval Manuscripts in Oxford Libraries (bodley): https://github.com/oerc-music/BodleianMedievalMSS-RDF
    * Bibale Database (bibale): http://bibale.irht.cnrs.fr/export/rdf/get
    * CSV of manual manuscript links to `data/additional/manuscript_links.csv`

2. Set up input databases (automated)
    * Load `data/sdbm/input.ttl` to `http://localhost:3051/ds/sparql`
    * Load `data/bodley/input.ttl` to `http://localhost:3052/ds/sparql`
    * Load `data/bibale/input.ttl` to `http://localhost:3053/ds/sparql`

3. Convert input datasets to unified data model using SPARQL CONSTRUCTs (automated)
    * Link Bibale places to GeoNames (You'll need GeoNames API key(s) for this)

4. Load the final result into `http://localhost:3050/ds/sparql`

## Build, convert, and run

`./rebuild.sh`


## Deploy new output files without data conversion

`./deploy.sh`


## Rebuild after updating CONSTRUCT queries

Avoid rebuilding the input Fuseki.

Build the images:

`docker-compose build`

Convert again and run:

`./convert_again.sh`

Convert only from a single input dataset:

`./convert_again.sh bibale`
or
`./convert_again.sh bodley`
or
`./convert_again.sh sdbm`


## Rebuild after updating input data

`./rebuild.sh`


## Validating the output

`./validate.sh`


## Logs

`docker-compose logs -f`


## Running tests

`cd transform/src`

`GEONAMES_KEY=<APIKEY> nosetests --with-doctest`

Replace `<APIKEY>` with your GeoNames APIKEY.
