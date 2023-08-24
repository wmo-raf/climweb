#!/bin/bash

# migrate
python manage.py migrate --noinput

# collect static
python manage.py collectstatic --noinput

#ensure environment-variables are available for cronjob
printenv | grep -v "no_proxy" >>/etc/environment

# ensure cron is running
service cron start
service cron status

# submit satellite imagery download task
python manage.py submit_sat_imagery_download

exec "$@"
