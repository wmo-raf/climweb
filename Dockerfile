FROM python:3.9-slim-buster

USER root

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       binutils \
       libproj-dev \
       gdal-bin \
       postgresql-client \
       build-essential \
        libpq-dev \
        libmariadbclient-dev \
        libjpeg62-turbo-dev \
        zlib1g-dev \
        libwebp-dev \
       netcat \
    && rm -rf /var/lib/apt/lists/*

# create directory for the app user
RUN mkdir -p /home/app

# create the app user
RUN useradd app

# Set up a working directory
# create the appropriate directories
ENV HOME=/home/app
ENV APP_HOME=/home/app/web
RUN mkdir $APP_HOME


# change to the app user
# USER app
WORKDIR $APP_HOME

# Install Python dependencies
COPY requirements.txt .
# RUN pip install --upgrade pip 
# USER root

RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . $APP_HOME

# copy entrypoint.sh
COPY entrypoint.sh .

# # Port used by this container to serve HTTP.
EXPOSE 8000
# switch back to non-root user to run Gunicorn
# USER app
ENTRYPOINT ["/home/app/web/entrypoint.sh"]

