# syntax = docker/dockerfile:1.5

# use osgeo gdal ubuntu small 3.7 image.
# pre-installed with GDAL 3.7.0 and Python 3.10.6
FROM ghcr.io/osgeo/gdal:ubuntu-small-3.7.0 as base

ARG UID
ENV UID=${UID:-9999}
ARG GID
ENV GID=${GID:-9999}

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Create or rename group to climweb_docker_group with desired GID
RUN if getent group $GID > /dev/null; then \
        existing_group=$(getent group $GID | cut -d: -f1); \
        if [ "$existing_group" != "climweb_docker_group" ]; then \
            groupmod -n climweb_docker_group "$existing_group"; \
        fi; \
    else \
        groupadd -g $GID climweb_docker_group; \
    fi

RUN useradd --shell /bin/bash -u $UID -g $GID -o -c "" -m climweb_docker_user -l || exit 0

ENV DOCKER_USER=climweb_docker_user

ENV POSTGRES_VERSION=15

# Install dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    build-essential \
    lsb-release \
    ca-certificates \
    gnupg2 \
    curl \
    cron \
    tini \
    libpq-dev \
    libgeos-dev \
    imagemagick \
    libmagic1 \
    libcairo2-dev \
    libpangocairo-1.0-0 \
    libffi-dev \
    python3-pip \
    python3-dev \
    python3-venv \
    inotify-tools \
    poppler-utils \
    git \
    gosu \
    && echo "deb http://apt.postgresql.org/pub/repos/apt/ $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list \
    && curl --silent https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add - \
    && apt-get update \
    && apt-get install --no-install-recommends -y \
    postgresql-client-$POSTGRES_VERSION \
    && apt-get autoclean \
    && apt-get clean \
    && apt-get autoremove \
    && rm -rf /var/lib/apt/lists/*

ENV DOCKER_COMPOSE_WAIT_VERSION=2.12.1

# Install docker-compose wait
ADD https://github.com/ufoscout/docker-compose-wait/releases/download/$DOCKER_COMPOSE_WAIT_VERSION/wait /wait
RUN chmod +x /wait

# Create directories and set correct permissions
RUN mkdir -p /climweb/web /climweb/plugins && chown -R $UID:$GID /climweb

USER $UID:$GID

COPY ./climweb/requirements/base.txt /climweb/requirements/
RUN python3 -m venv /climweb/venv

ENV PIP_CACHE_DIR=/tmp/climweb_pip_cache
# hadolint ignore=SC1091,DL3042
RUN --mount=type=cache,mode=777,target=$PIP_CACHE_DIR,uid=$UID,gid=$GID . /climweb/venv/bin/activate && \
     pip3 install  -r /climweb/requirements/base.txt

COPY --chown=$UID:$GID ./climweb /climweb/web

# Create static and media directories
RUN mkdir -p /climweb/web/src/climweb/static \
    && mkdir -p /climweb/web/src/climweb/media \
    && mkdir -p /climweb/web/src/climweb/backup \
    && chown -R $UID:$GID /climweb/web/src/climweb

# Create a tmp directory for the django to use
RUN mkdir -p /climweb/tmp && chown -R $UID:$GID /climweb/tmp

WORKDIR /climweb/web

# Ensure that Python outputs everything that's printed inside
# the application rather than buffering it.
ENV PYTHONUNBUFFERED 1

COPY --chown=$UID:$GID ./deploy/plugins/*.sh /climweb/plugins/

# Create a directory for raster data to be auto-ingested
ENV GEOMANAGER_AUTO_INGEST_RASTER_DATA_DIR=/climweb/geomanager/data
RUN mkdir -p $GEOMANAGER_AUTO_INGEST_RASTER_DATA_DIR && chown -R $UID:$GID $GEOMANAGER_AUTO_INGEST_RASTER_DATA_DIR

# install climweb as a package
RUN chmod a+x /climweb/web/docker/docker-entrypoint.sh && \
    /climweb/venv/bin/pip install --no-cache-dir -e /climweb/web/

ENTRYPOINT ["/usr/bin/tini", "--", "/bin/bash", "/climweb/web/docker/docker-entrypoint.sh"]

# Add the venv to the path. This ensures that the venv is always activated when the container starts.
ENV PATH="/climweb/venv/bin:$PATH"

ENV DJANGO_SETTINGS_MODULE='climweb.config.settings.production'

CMD ["gunicorn"]

FROM base as dev

USER $UID:$GID

# Override env variables and initial cmd to start up in dev mode.
ENV DJANGO_SETTINGS_MODULE='climweb.config.settings.dev'
CMD ["django-dev-no-attach"]