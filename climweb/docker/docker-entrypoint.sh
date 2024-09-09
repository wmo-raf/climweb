#!/bin/bash
# Bash strict mode: http://redsymbol.net/articles/unofficial-bash-strict-mode/
set -euo pipefail

# ======================================================
# ENVIRONMENT VARIABLES USED DIRECTLY BY THIS ENTRYPOINT
# ======================================================

MIGRATE_ON_STARTUP=${MIGRATE_ON_STARTUP:-true}
COLLECT_STATICFILES_ON_STARTUP=${COLLECT_STATICFILES_ON_STARTUP:-true}
WATCH_GEOMANAGER_DATA_DIR=${WATCH_GEOMANAGER_DATA_DIR:-true}
GEOMANAGER_AUTO_INGEST_RASTER_DATA_DIR=${GEOMANAGER_AUTO_INGEST_RASTER_DATA_DIR:-/climweb/geomanager/data}

CLIMWEB_LOG_LEVEL=${CLIMWEB_LOG_LEVEL:-INFO}
GUNICORN_NUM_OF_WORKERS=${GUNICORN_NUM_OF_WORKERS:-}

CLIMWEB_CELERY_BEAT_DEBUG_LEVEL=${CLIMWEB_CELERY_BEAT_DEBUG_LEVEL:-INFO}

show_help() {
    echo """
The available ClimWeb related commands and services are shown below:

ADMIN COMMANDS:
manage          : Manage ClimWeb and its database
shell           : Start a Django Python shell
install-plugin  : Installs a plugin (append --help for more info).
list-plugins    : Lists currently installed plugins.
help            : Show this message

SERVICE COMMANDS:
gunicorn            : Start ClimWeb using a prod ready gunicorn server:
                         * Waits for the postgres database to be available first.
                         * Automatically migrates the database on startup.
                         * Binds to 0.0.0.0
gunicorn-wsgi       : Same as gunicorn but runs a wsgi server
celery-worker       : Start the celery worker queue which runs async tasks
celery-beat         : Start the celery beat service used to schedule periodic jobs
"""
}

show_startup_banner() {
  # Use https://manytools.org/hacker-tools/ascii-banner/ and the font ANSI Shadow / Wide / Wide to generate
cat <<EOF
=========================================================================================
 ██████╗██╗     ██╗███╗   ███╗██╗    ██╗███████╗██████╗
██╔════╝██║     ██║████╗ ████║██║    ██║██╔════╝██╔══██╗
██║     ██║     ██║██╔████╔██║██║ █╗ ██║█████╗  ██████╔╝
██║     ██║     ██║██║╚██╔╝██║██║███╗██║██╔══╝  ██╔══██╗
╚██████╗███████╗██║██║ ╚═╝ ██║╚███╔███╔╝███████╗██████╔╝
 ╚═════╝╚══════╝╚═╝╚═╝     ╚═╝ ╚══╝╚══╝ ╚══════╝╚═════╝

Version $CLIMWEB_APP_VERSION

=========================================================================================
EOF
}

run_setup_commands_if_configured() {
    startup_plugin_setup

        # migrate database
    if [ "$MIGRATE_ON_STARTUP" = "true" ]; then
        echo "python /climweb/web/src/climweb/manage.py migrate"
        /climweb/web/src/climweb/manage.py migrate --noinput
    fi

        # collect staticfiles
    if [ "$COLLECT_STATICFILES_ON_STARTUP" = "true" ]; then
        echo "python /climweb/web/src/climweb/manage.py collectstatic --clear --noinput"
        /climweb/web/src/climweb/manage.py collectstatic --clear --noinput
    fi

    # ensure cron is running
    service cron start

    # submit satellite imagery download task
    /climweb/web/src/climweb/manage.py submit_sat_imagery_download

    # initialize geomanager
    /climweb/web/src/climweb/manage.py initialize_geomanager

    # reset cms upgrade status
    /climweb/web/src/climweb/manage.py reset_cms_upgrade_status

    # start background tasks, with 15 minutes duration.
    # Cron Job will triggered after 15 minutes
    # https://django-background-tasks.readthedocs.io/en/latest/#running-tasks
    /climweb/web/src/climweb/manage.py process_tasks --duration 900 &

    # migrate database
    if [ "$WATCH_GEOMANAGER_DATA_DIR" = "true" ]; then
      echo "GeoManager Listening for new files in $GEOMANAGER_AUTO_INGEST_RASTER_DATA_DIR"
      # start command to watch for new files in the geomanager auto-ingest data dir
      while file=$(inotifywait -e create --format "%w%f" -r "$GEOMANAGER_AUTO_INGEST_RASTER_DATA_DIR"); do
        EXT=${file##*.}
        if [ "$EXT" = "tif" ] || [ "$EXT" = "nc" ]; then
          echo "New Geomanager ingestion file detected: $file"
          /climweb/web/src/climweb/manage.py ingest_geomanager_raster created "$file" --overwrite --clip
        fi
      done &
    fi
}

start_celery_worker() {
    startup_plugin_setup

    EXTRA_CELERY_ARGS=()

    if [[ -n "$GUNICORN_NUM_OF_WORKERS" ]]; then
        EXTRA_CELERY_ARGS+=(--concurrency "$GUNICORN_NUM_OF_WORKERS")
    fi
    exec celery -A climweb worker "${EXTRA_CELERY_ARGS[@]}" -l INFO "$@"
}

run_server() {
    run_setup_commands_if_configured

    if [[ "$1" = "wsgi" ]]; then
        STARTUP_ARGS=(climweb.config.wsgi:application)
    elif [[ "$1" = "asgi" ]]; then
        STARTUP_ARGS=(-k uvicorn.workers.UvicornWorker climweb.config.asgi:application)
    else
        echo -e "\e[31mUnknown run_server argument $1 \e[0m" >&2
        exit 1
    fi

    # Gunicorn args explained in order:
    #
    # 1. See https://docs.gunicorn.org/en/stable/faq.html#blocking-os-fchmod for
    #    why we set worker-tmp-dir to /dev/shm by default.
    # 2. Log to stdout
    # 3. Log requests to stdout
    exec gunicorn --workers="$GUNICORN_NUM_OF_WORKERS" \
        --worker-tmp-dir "${TMPDIR:-/dev/shm}" \
        --log-file=- \
        --access-logfile=- \
        --capture-output \
        -b "0.0.0.0:8000" \
        --log-level="${CLIMWEB_LOG_LEVEL}" \
        "${STARTUP_ARGS[@]}" \
        "${@:2}"
}

# ======================================================
# COMMANDS
# ======================================================

if [[ -z "${1:-}" ]]; then
    echo "Must provide arguments to docker-entrypoint.sh"
    show_help
    exit 1
fi

# activate virtualenv
source /climweb/venv/bin/activate

# get the current version of the app
CLIMWEB_APP_VERSION=$(python /climweb/web/src/climweb/manage.py get_climweb_version)

show_startup_banner

# wait for required services to be available, using docker-compose-wait
/wait

# load plugin utils
source /climweb/plugins/utils.sh

case "$1" in
gunicorn)
    run_server asgi "${@:2}"
    ;;
gunicorn-wsgi)
    run_server wsgi "${@:2}"
    ;;
manage)
    exec python3 /climweb/web/src/climweb/manage.py "${@:2}"
    ;;
shell)
    exec python3 /climweb/web/src/climweb/manage.py shell
    ;;
celery-worker)
    start_celery_worker -Q celery -n default-worker@%h "${@:2}"
    ;;
celery-beat)
    exec celery -A climweb beat -l "${CLIMWEB_CELERY_BEAT_DEBUG_LEVEL}" -S django_celery_beat.schedulers:DatabaseScheduler "${@:2}"
    ;;
install-plugin)
    exec /climweb/plugins/install_plugin.sh --runtime "${@:2}"
    ;;
list-plugins)
    exec /climweb/plugins/list_plugins.sh "${@:2}"
    ;;
*)
    echo "Command given was $*"
    show_help
    exit 1
    ;;
esac
