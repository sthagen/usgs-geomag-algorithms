#!/bin/bash

function get_ehp_server_ini {
  local key=$1; shift;

  grep "${key}" "${EHP_SERVER_INI}" \
    | tail -n 1 \
    | cut -d '=' -f 2 \
    | tr -d ' ' \
  ;
}

export SITE_URL="${SITE_URL_PREFIX}geomag${SITE_URL_SUFFIX}";
export BASE_HREF=${BASE_HREF:-ws};
export SERVICE_MAP=(
  "/${BASE_HREF}:web"
);
# Algorithms Environment Variables
export DATA_HOST=${DATA_HOST:-cwbpub.cr.usgs.gov};
export DATA_PORT=${DATA_PORT:-2060};
export DATA_TYPE=${DATA_TYPE:-edge};

# Web Service Environment Variables

export DATABASE_URL=${DATABASE_URL:-""}
if [ -f "${EHP_SERVER_INI}" ]; then
  # when ehp server ini exists, read connection information
  DB_HOST=$(get_ehp_server_ini 'restricted_database=');
  DB_NAME=geomag_operations
  DB_USER=$(get_ehp_server_ini 'mysql_web_absolutes_user=');
  DB_PASS=$(get_ehp_server_ini 'mysql_web_absolutes_password=');
  export DATABASE_URL="mysql://${DB_USER}:${DB_PASS}@${DB_HOST}/${DB_NAME}";
fi

export OPENID_CLIENT_ID=${OPENID_CLIENT_ID:-""}
export OPENID_CLIENT_SECRET=${OPENID_CLIENT_SECRET:-""}
export OPENID_METADATA_URL=${OPENID_METADATA_URL:-""}
export SECRET_KEY=${SECRET_KEY:-""}
export SECRET_SALT=${SECRET_SALT:-""}
export ADMIN_GROUP=${ADMIN_GROUP:-""}
export REVIEWER_GROUP=${REVIEWER_GROUP:-""}

if [[ $TARGET_HOSTNAME == *"mage"* ]]; then
  export DATA_HOST=${TARGET_HOSTNAME}
fi
