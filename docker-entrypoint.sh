#! /bin/bash

# Environment variable to determine whether to start webservice
export WEBSERVICE=${WEBSERVICE:-false}

# add geomagio to notebook path
export PYTHONPATH=/geomag-algorithms


if [ "${WEBSERVICE}" = "false" ]; then
  # run arguments as command, or bash prompt if no arguments
  exec "${@:-/bin/bash}"
else
  # run gunicorn server for web service
  exec pipenv run gunicorn \
      --access-logfile - \
      --bind 0.0.0.0:8000 \
      --threads 2 \
      --workers 2 \
      --worker-class uvicorn.workers.UvicornWorker \
      --worker-tmp-dir /dev/shm \
      geomagio.api:app
fi
