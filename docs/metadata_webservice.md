# Running the Metadata Webservice Locally

## Run postgres in a container (for local development)

```
docker run --rm -it -p 5432:5432 -e POSTGRES_PASSWORD=postgres postgres:10
```

This exposes port 5432 so python can connect locally. When running the webservice in a container, container links should be used so the container can access the database container.

## Set up schema in database

> This is only needed the first time the database is created. Volume mounts can make this more persistent.

```
export DATABASE_URL="postgresql://postgres@localhost/postgres?password=postgres"
pipenv run python .\create_db.py
```

### Add some testing data (depends on DATABASE_URL environment set above).

```
pipenv run python .\test_metadata.py
```

## Set up OpenID application in code.usgs.gov.

- Under your account, go to settings
- Applications -> Add New Application:

  Callback URLs for local development:

  ```
  http://127.0.0.1:8000/ws/secure/authorize
  http://127.0.0.1:4200/ws/secure/authorize
  ```

  Confidential: `Yes`

  Scopes: `openid`, `profile`, `email`

## Start webservice

- Export variables used for authentication:

```
export DATABASE_URL="postgresql://postgres@localhost/postgres?password=postgres"
export OPENID_CLIENT_ID={Application ID}
export OPENID_CLIENT_SECRET={Secret}
export OPENID_METADATA_URL=https://code.usgs.gov/.well-known/openid-configuration
export SECRET_KEY=changeme
export SECRET_SALT=salt
```

- Run app

```
pipenv run uvicorn geomagio.api:app
```
