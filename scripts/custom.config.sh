
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
