# Running the Metadata Webservice Locally

## Run mysql in a container (for local development)

```
docker run --rm --name mysql-db -e MYSQL_ROOT_PASSWORD=password -p 3306:3306 mysql:5.7
```

This exposes port 3306 so python can connect locally. When running the webservice in a container, container links should be used so the container can access the database container.

## Set up schema in database

> This is only needed the first time the database is created. Volume mounts can make this more persistent.

```
export DATABASE_URL=mysql://root:password@localhost/geomag_operations
```

### Create mysql database
```
docker exec -it mysql-db mysql -uroot -ppassword
```
> Inside mysql container:
```
CREATE DATABASE geomag_operations;
exit
```

```
pipenv alembic upgrade head
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
export DATABASE_URL=mysql://root:password@localhost/geomag_operations
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
