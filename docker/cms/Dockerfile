# use osgeo gdal ubuntu small 3.7 image.
# pre-installed with GDAL 3.7.0 and Python 3.10.6
FROM ghcr.io/osgeo/gdal:ubuntu-small-3.7.0

# install dependencies
RUN apt-get update && apt-get install -y \
    cron \
    libgeos-dev \
    imagemagick \
    libmagic1 \
    libcairo2-dev \
    libffi-dev \
    python3-pip --fix-missing

# set python env
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install docker-compose wait
ADD https://github.com/ufoscout/docker-compose-wait/releases/download/2.12.0/wait /wait
RUN chmod +x /wait

# Download cms
ENV APP_HOME=/home/app/web
RUN mkdir -p $APP_HOME

# install requirements
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt && pip install gunicorn

# setup working dir
WORKDIR $APP_HOME

# copy code to $APP_HOME
COPY . .

# Copy entrypoint script
COPY docker/cms/docker-entrypoint.sh ./
RUN chmod +x docker-entrypoint.sh

# add satellite.cron to crontab
COPY ./satellite.cron /etc/cron.d/satellite.cron

RUN chmod 0644 /etc/cron.d/satellite.cron && crontab /etc/cron.d/satellite.cron

# create tmp dir for handling large django uploads
RUN mkdir -p tmp

# Port used by this container to serve HTTP.
EXPOSE 8000

ENTRYPOINT ["./docker-entrypoint.sh"]