# Schoenberg Database of Manuscripts docker

Container includes SDBM Fuseki configuration, and all data.

## Docker configuration

For squash to work, you might need to enable docker experimental features explicitly. Edit or create /etc/docker/daemon.json and add following:
`{
    "experimental": true
}`
and restart the docker service.

Alternatievely you could manually run the dockerd daemon with the --experimental flag.

Docker in the Pouta instance is currently not configured for --squash.

## Build

`docker build --squash -t mmm-sdbm-fuseki .`

## Run

`docker run -d -p 3030:3030 --name mmm-sdbm mmm-sdbm-fuseki`

Get the Fuseki control panel password with `docker logs mmm-sdbm`

## Upgrade

```
docker build --squash -t mmm-sdbm-fuseki .
docker stop mmm-sdbm
docker rm mmm-sdbm
docker run -d -p 3030:3030 --name mmm-sdbm mmm-sdbm-fuseki
```
