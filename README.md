# Schoenberg Database of Manuscripts docker

Container includes SDBM Fuseki configuration, and all data.


## Build

`docker build -t mmm-sdbm-fuseki .`

## Run

`docker run -d -p 3030:3030 --name mmm-sdbm mmm-sdbm-fuseki`

Get the Fuseki control panel password with `docker logs mmm-sdbm`

## Upgrade

```
docker build -t mmm-sdbm-fuseki .
docker stop mmm-sdbm
docker rm mmm-sdbm
docker run -d -p 3030:3030 --name mmm-sdbm mmm-sdbm-fuseki
```
