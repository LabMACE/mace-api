# MACE API
The backend API for the MACE lab

### Seed the database with some data

Assuming the credentials for the database are `postgres:psql@localhost:5433/postgres` and the database is empty, run the following command to seed the database with some data:

`poetry run python seed_db.py postgresql+asyncpg://postgres:psql@localhost:5433/postgres`

### Run the server
Build the docker image:

`docker build -t mace-api .`

Run a PostGIS server, then run the docker image:
```
docker run \
    -e DB_HOST=<postgis hostname>
    -e DB_PORT=<postgis port>
    -e DB_USER=<postgis user>
    -e DB_PASSWORD=<postgis password>
    -e DB_NAME=<postgis dbname>
    -e DB_PREFIX=postgresql+asyncpg
    docker.io/library/mace-api:latest
```

The [macemap-ui repository](https://github.com/LabMACE/macemap-ui) has a development docker-compose.yaml file to load the API, BFF, PostGIS and UI all together, assuming all repositories are cloned locally.