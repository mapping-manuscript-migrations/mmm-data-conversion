# Schoenberg Database of Manuscripts docker

Convert SDBM RDF data from https://drive.google.com/drive/folders/0B4mAIaZomRI4UTZRN2F3WS02bGs into a new data model using SPARQL CONSTRUCT.

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

## Logs

`docker-compose logs -f`
