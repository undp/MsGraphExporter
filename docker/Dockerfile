ARG BASE_CONTAINER=python:3.7-alpine

FROM $BASE_CONTAINER as base

# get all required dependencies on the multi-stage builder
FROM base as builder

# install `curl`
RUN set -xe && apk add --update --no-cache \
    curl

# NOTE:REFACTOR
#   As of 2019-08-26 `export` command of `poetry` is
#   available in the pre-release version only. Change to
#   appropriate release when available.
#
# install `poetry` pre-release version
RUN curl -sOSL https://raw.githubusercontent.com/sdispater/poetry/master/get-poetry.py
RUN python get-poetry.py --preview

# prepare all bin dependencies to install `cryptography` with `pip`
RUN set -xe && apk add --update --no-cache \
    gcc \
    musl-dev \
    python3-dev \
    libffi-dev \
    openssl-dev

#  get project dependencies
COPY poetry.lock /poetry.lock
COPY pyproject.toml /pyproject.toml

# export requirements.txt from poetry.lock & pyproject.toml
RUN $HOME/.poetry/bin/poetry export -f requirements.txt > requirements.txt

RUN mkdir /install

WORKDIR /install

# install all requirements
RUN pip install --upgrade pip
RUN pip install --install-option="--prefix=/install" -r /requirements.txt

# on base image
FROM base

ARG NON_PRIV_USER=celery
ARG NON_PRIV_GROUP=celery

LABEL maintainer="Oleksiy Kuzmenko <oleksiy.kuzmenko@undp.org>"

USER root

# copy required dependencies from multi-stage builder
COPY --from=builder /install /usr/local

# install `supervisord` binaries
RUN set -xe && apk add --update --no-cache \
    supervisor

# create a dedicated non-privilaged user/group
RUN set -xe && addgroup -S $NON_PRIV_GROUP && \
    adduser -S $NON_PRIV_USER -G $NON_PRIV_GROUP

# create folders for app code & instance-specific config
RUN set -xe && mkdir -p /app/instance

# make app root a default work directory
WORKDIR /app

# copy default configs
COPY docker/supervisord.conf supervisord.conf
COPY docker/docker-entrypoint.sh docker-entrypoint.sh
COPY docker/app_config.yaml instance/app_config.yaml

# copy app code
COPY ms_graph_exporter/ ms_graph_exporter/

# set permissions to read-only ownership by non-privilaged user/group
RUN set -xe && chown -R $NON_PRIV_USER:$NON_PRIV_GROUP /app
RUN set -xe && chmod -R ug+rx /app && chmod o-rwx /app

# switch to non-privilaged user
USER $NON_PRIV_USER:$NON_PRIV_GROUP

# Celery application
ENV CELERY_APP="ms_graph_exporter.celery.app"

# Celery beat config
ENV CELERY_BEAT_LOG_LEVEL="WARN"

# Celery brocker config
ENV CELERY_BROKER_URL="redis://redis:6379?db=0"

# Celery worker config
ENV CELERY_WORKER_CONCURRENCY="10"
ENV CELERY_WORKER_LOG_LEVEL="WARN"
ENV CELERY_WORKER_POOL="gevent"
ENV CELERY_WORKER_USER=$NON_PRIV_USER

# App config
ENV GRAPH_APP_CONFIG="instance/app_config.yaml"
ENV GRAPH_CLIENT_ID=""
ENV GRAPH_CLIENT_SECRET=""
ENV GRAPH_ENV="production"
ENV GRAPH_REDIS_URL=$CELERY_BROKER_URL
ENV GRAPH_TENANT=""

VOLUME /app/instance

# Entrypoint scrip
ENTRYPOINT ["/app/docker-entrypoint.sh"]

# Entrypoint execution command
# Starts Celery Beat and Worker servicing all app queues
CMD ["msgraphexporter", "--beat", "--map", "--fetch", "--store"]
