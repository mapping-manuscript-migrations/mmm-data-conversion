# Mapping Manuscript Migrations data conversion pipeline

Currently the pipeline includes the following steps:

1. Create a directory called `data` and download input RDF data into it (manual)
  * Schoenberg Database of Manuscripts: https://sdbm.library.upenn.edu/downloads (you have to be logged in)
  * Bodley: [TODO]
  * Bibale: [TODO]

2. Set up input databases (automated)
  * Load `data/sdbm/input.ttl` to `http://localhost:3051/ds/sparql`
  * Load `data/bodley/input.ttl` to `http://localhost:3052/ds/sparql`
  * Load `data/bibale/input.ttl` to `http://localhost:3053/ds/sparql`

3. Convert to unified data model using SPARQL CONSTRUCT (automated)
  * The final result is loaded into `http://localhost:3050/ds/sparql`

## Build, convert, and run

Build the images:

`docker-compose build`

Convert and run:

`./rebuild.sh`

Or manually:

```bash
# Stop the services and volumes if running:
docker-compose down -v
# Load input data from ./data
docker-compose run --rm input ./load_data.sh
# Start the input Fuseki
docker-compose up -d input
# Convert to CRM
docker-compose run --rm crm ./convert.sh
# Start Fuseki with converted data
docker-compose up -d crm
```

## Rebuild after updating CONSTRUCT queries

Avoid rebuilding the input Fuseki.

Convert again and run:

`./convert_again.sh`

Or manually:

```bash
# Stop the services
docker-compose down
# Remove the old CRM volume
docker volume rm mmmsdbmdata_mmm-crm
# Build the CRM container again (with updated SPARQL CONSTRUCT)
docker-compose build crm
# Start the input Fuseki
docker-compose up -d input
# Convert to CRM
docker-compose run --rm crm ./convert.sh
# Start the CRM Fuseki with converted data
docker-compose up -d crm
```

## Rebuild after updating input data

```bash
./rebuild.sh
```


## Logs

`docker-compose logs -f`
