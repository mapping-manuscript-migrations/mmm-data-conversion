# Mapping Manuscript Migrations data conversion pipeline

Currently the pipeline includes the following steps:

1. Create a directory called `data` with a subdirectory for each of the source databases and download the input RDF data as follows: (manual)
    * Schoenberg Database of Manuscripts (sdbm): https://sdbm.library.upenn.edu/downloads (you have to be logged in)
    * Medieval Manuscripts in Oxford Libraries (bodley): https://github.com/mapping-manuscript-migrations/bodleian-RDF
        * To combine files into `input.ttl`:

          `for f in *.rdf; do (rapper $f -i rdfxml -o turtle) > $f.ttl; done; `

          `cat *.ttl| rapper - "https://medieval.bodleian.ox.ac.uk/catalog/" -i turtle -o turtle > input.ttl`

    * Bibale Database (bibale): http://bibale.irht.cnrs.fr/exports/mmm/
    * CSV of Bibale shelfmark city locations to `data/additional/bibale_locations.csv`
    * CSV of manual manuscript links to `data/additional/manuscript_links.csv`
    * CSV of Bibale/Bodley Phillipps numbers to `data/additional/phillipps_numbers.csv`
    * CSVs of actor Recon runs to `data/additional/recon_actors_{LETTER}_{DATE}.csv`
    ** where {LETTER} corresponds to actor name starting letter
    ** and {DATE} corresponds to date in format YYYY-MM-DD 
    ** (e.g., `recon_actors_A_2019-05-22.csv`)
    * CSVs of work Recon runs to `data/additional/recon_works_{LETTERS}_{DATE}.csv`
    ** similarly, e.g., `recon_works_J-P_2019_06_10.csv`

2. Set up input databases (automated)
    * Load `data/sdbm/input.ttl` to `http://localhost:3051/ds/sparql`
    * Load `data/bodley/input.ttl` to `http://localhost:3052/ds/sparql`
    * Load `data/bibale/input.ttl` to `http://localhost:3053/ds/sparql`

3. Convert input datasets to unified data model using SPARQL CONSTRUCTs (automated)
    * Link Bibale places to GeoNames (You'll need GeoNames API key(s) for this)
    ** You can add GeoNames API keys to `.env` in format 
    ** `GEONAMES_KEY=<key>`
    ** `GEONAMES_KEY2=<key 2>`
    ** `GEONAMES_KEY3=<key 3>`
    ** ...
    ** Keys are throttled when the API temporal query limit is exhausted  

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

## Rebuild after updating input data

`./rebuild.sh`


## Validating the output

`./validate.sh`


## Logs

`docker-compose logs -f`


## Running tests

`cd transform/src`

`GEONAMES_KEY=<APIKEY> nosetests -v --with-doctest`

Replace `<APIKEY>` with your GeoNames APIKEY.
