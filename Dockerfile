ARG FROM_IMAGE=usgs/centos:7


################################################################################
# base python image

FROM ${FROM_IMAGE} as python
ARG PYTHON_VERSION=38

LABEL maintainer="Jeremy Fee <jmfee@usgs.gov>"

# put rh-python38 at start of path
ENV PATH="/opt/rh/rh-python38/root/usr/bin:/opt/rh/rh-python38/root/usr/local/bin:${PATH}"
# configure ssl intercept
ENV PIP_CERT="${SSL_CERT_FILE}"
ENV REQUESTS_CA_BUNDLE="${SSL_CERT_FILE}"

RUN yum install -y \
    centos-release-scl \
    glibc-langpack-en \
    which \
    && yum install -y rh-python${PYTHON_VERSION} \
    && python -m pip install -U \
    pip \
    poetry \
    wheel \
    && yum clean all


################################################################################
# python builder image

FROM python as obspy
ARG PYTHON_VERSION=38

# build with compilers in separate stage
RUN yum groupinstall -y "Development Tools"
RUN yum install -y rh-python${PYTHON_VERSION}-python-devel
ENV LD_LIBRARY_PATH="/opt/rh/rh-python${PYTHON_VERSION}/root/usr/lib64"
ENV PKG_CONFIG_PATH="/opt/rh/rh-python${PYTHON_VERSION}/root/usr/lib64/pkgconfig"

# obspy
RUN python -m pip wheel obspy --wheel-dir /wheels
# pycurl
RUN yum install -y libcurl-devel openssl-devel
RUN export PYCURL_SSL_LIBRARY=nss \
    && python -m pip wheel pycurl --wheel-dir /wheels


################################################################################
# geomag-algorithms image

FROM python

ARG GIT_BRANCH_NAME=none
ARG GIT_COMMIT_SHA=none
ARG WEBSERVICE="false"

# set environment variables
ENV GIT_BRANCH_NAME=${GIT_BRANCH_NAME} \
    GIT_COMMIT_SHA=${GIT_COMMIT_SHA} \
    WEBSERVICE=${WEBSERVICE}

# install obspy and pycurl using wheels
COPY --from=obspy /wheels /wheels
RUN python -m pip install --find-links file:///wheels obspy pycurl

# install packages when dependencies change
COPY pyproject.toml poetry.lock /geomag-algorithms/
RUN cd /geomag-algorithms \
    # install into system python
    && poetry config virtualenvs.create false \
    # only install dependencies, not project
    && poetry install --no-root

# install rest of library as editable
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
