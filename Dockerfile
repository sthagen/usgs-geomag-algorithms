ARG FROM_IMAGE=usgs/obspy:3.8

FROM ${FROM_IMAGE}
LABEL maintainer="Jeremy Fee <jmfee@usgs.gov>"

ARG GIT_BRANCH_NAME=none
ARG GIT_COMMIT_SHA=none
ARG WEBSERVICE="false"

# set environment variables
ENV GIT_BRANCH_NAME=${GIT_BRANCH_NAME} \
    GIT_COMMIT_SHA=${GIT_COMMIT_SHA} \
    WEBSERVICE=${WEBSERVICE}


# install packages into system python, when Pipfile changes
COPY Pipfile Pipfile.lock /geomag-algorithms/
RUN cd /geomag-algorithms \
    && pipenv install --dev --pre --system

# install rest of library as editable
COPY . /geomag-algorithms
RUN cd /geomag-algorithms \
    && pip install -e . \
    # add data directory owned by usgs-user
    && mkdir -p /data \
    && chown -R usgs-user:usgs-user /data

USER usgs-user
WORKDIR /data


# entrypoint needs double quotes
ENTRYPOINT [ "/geomag-algorithms/docker-entrypoint.sh" ]
EXPOSE 8000
