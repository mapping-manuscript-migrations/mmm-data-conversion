# Schoenberg Database of Manuscripts docker

Convert SDBM RDF data into a new data model using SPARQL CONSTRUCT.
Before running the scripts, download the RDF Dataset (.ttl) file from https://sdbm.library.upenn.edu/downloads (you have to be logged in)
into `data` directory, and rename it as `input.ttl`.

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
