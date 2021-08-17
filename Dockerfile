ARG FROM_IMAGE=usgs/python:3.8-obspy


FROM ${FROM_IMAGE}

ARG GIT_BRANCH_NAME=none
ARG GIT_COMMIT_SHA=none
ARG WEBSERVICE="false"

# set environment variables
ENV GIT_BRANCH_NAME=${GIT_BRANCH_NAME} \
    GIT_COMMIT_SHA=${GIT_COMMIT_SHA} \
    WEBSERVICE=${WEBSERVICE}

# install to system python
USER root

# install packages when dependencies change
COPY pyproject.toml poetry.lock /geomag-algorithms/
RUN cd /geomag-algorithms \
    # install into system python
    && poetry config virtualenvs.create false \
    # only install dependencies, not project
    && poetry install --no-root

# install rest of library separate from dependencies
COPY . /geomag-algorithms
RUN cd /geomag-algorithms \
    # now install project to install scripts
    && poetry install \
    # add data directory owned by usgs-user
    && mkdir -p /data \
    && chown -R usgs-user:usgs-user /data
# configure python path, so project can be volume mounted
ENV PYTHONPATH="/geomag-algorithms"

# run as usgs-user
USER usgs-user
WORKDIR /data
# entrypoint needs double quotes
ENTRYPOINT [ "/geomag-algorithms/docker-entrypoint.sh" ]
EXPOSE 8000
