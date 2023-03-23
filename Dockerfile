FROM python:3.9-slim-buster
ENV PYTHONUNBUFFERED 1

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       binutils \
       libproj-dev \
       gdal-bin \
       postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Set up a working directory
RUN mkdir /app
WORKDIR /app

COPY ./capeditor-0.1.1.tar.gz .

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the application code
COPY . /app/

# Set environment variables
ENV DJANGO_SETTINGS_MODULE=nmhs_cms.settings.dev

# Collect static files
RUN python manage.py collectstatic --noinput

# Expose port 8000
EXPOSE 8000

# Start the application
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "nmhs_cms.wsgi"]
