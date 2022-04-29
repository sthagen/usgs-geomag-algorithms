# these base images are not available in public usgs registry yet
# inline for now

ARG FROM_IMAGE=public.ecr.aws/lts/ubuntu:22.04

FROM $FROM_IMAGE as ubuntu-22

# Allow builds within DOI network
COPY DOIRootCA2.crt /usr/share/ca-certificates/extra/DOIRootCA2.crt

# Update current system packages and certificates
RUN export DEBIAN_FRONTEND=noninteractive \
    && apt update \
    && apt upgrade -y \
    && apt install -y \
      ca-certificates \
      language-pack-en \
    && apt clean \
    && update-ca-certificates

# this is redundant with above, but avoids additional layer
ENV DEBIAN_FRONTEND=noninteractive \
    LANG='en_US.UTF-8' \
    LC_ALL='en_US.UTF-8' \
    LC_CTYPE=en_US.UTF-8 \
    SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt \
    TZ=Etc/UTC

# Create a USGS user to run application inside container
RUN useradd \
      -c 'Docker image user' \
      -m \
      -r \
      -s /sbin/nologin \
      -U \
      usgs-user \
    && mkdir /app

USER usgs-user
WORKDIR /app

################################################################################

# base python image
FROM ubuntu-22 as python
ARG PYTHON_VERSION=3.10

LABEL maintainer='HazDev <gs-haz_dev_team_group@usgs.gov>' \
  version='1.0.0'

# configure python ssl intercept variables
ENV PIP_CERT="${SSL_CERT_FILE}" \
  REQUESTS_CA_BUNDLE="${SSL_CERT_FILE}"

USER root

RUN apt update \
    && apt upgrade -y \
    && apt install -y \
      curl \
      python${PYTHON_VERSION} \
      python${PYTHON_VERSION}-distutils \
    && apt clean \
    # make this version the default "python" command
    && update-alternatives \
    --install /usr/bin/python python /usr/bin/python${PYTHON_VERSION} 1 \
    # get-pip reduces resulting image size to ~250MB (100MB compressed).
    && curl -LO https://github.com/pypa/get-pip/raw/22.0.3/public/get-pip.py \
    && python get-pip.py \
    && rm get-pip.py \
    && pip install -U \
      pip \
      poetry \
    && pip cache purge

RUN echo "$PYTHON_VERSION"

USER usgs-user


# python build image
FROM python as python-build
ARG PYTHON_VERSION=3.10

USER root

RUN apt update \
    && apt upgrade -y \
    && apt install -y \
      build-essential \
      git \
      libcurl4-openssl-dev \
      libssl-dev \
      python${PYTHON_VERSION}-dev \
    && apt clean


# build obspy
FROM python-build as obspy-build

# obspy
RUN pip wheel obspy --wheel-dir /wheels
# pycurl (not required for obspy, but the main other hard-to-install package)
RUN export PYCURL_SSL_LIBRARY=openssl \
  && pip wheel pycurl --wheel-dir /wheels


# install wheels from obspy-build
FROM python as obspy

# install to system python
USER root

COPY --from=obspy-build /wheels/obspy* /wheels/pycurl* /wheels/

RUN pip install --find-links file:///wheels obspy pycurl \
  && python -c "import obspy" \
  && pip cache purge

USER usgs-user


################################################################################
FROM obspy as build
# start actual geomag_algorithms image
# ARG FROM_IMAGE=usgs/python:3.10-obspy

# build wheel
# FROM ${FROM_IMAGE} as build

USER root
WORKDIR /app

# install dependencies in separate layer
# this is a temporary container and they change less often than other files
COPY poetry.lock pyproject.toml /app/
RUN poetry install --no-root

COPY . /app/
RUN poetry build


# install and configure entrypoint
FROM python
# FROM ${FROM_IMAGE}

ARG GIT_BRANCH_NAME=none
ARG GIT_COMMIT_SHA=none
ARG WEBSERVICE="false"

# set environment variables
ENV GIT_BRANCH_NAME=${GIT_BRANCH_NAME} \
    GIT_COMMIT_SHA=${GIT_COMMIT_SHA} \
    WEBSERVICE=${WEBSERVICE}

COPY --from=build /app/dist/*.whl /app/docker-entrypoint.sh /app/

# install as root
USER root
RUN apt update \
    && apt upgrade -y \
    && pip install /app/*.whl \
    && pip cache purge
USER usgs-user

# entrypoint needs double quotes
ENTRYPOINT [ "/app/docker-entrypoint.sh" ]
EXPOSE 8000
