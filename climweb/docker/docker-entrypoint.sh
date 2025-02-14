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
CLIMWEB_NUM_OF_CELERY_WORKERS=${CLIMWEB_NUM_OF_CELERY_WORKERS:-}
GUNICORN_NUM_OF_WORKERS=${GUNICORN_NUM_OF_WORKERS:-}

CLIMWEB_CELERY_BEAT_DEBUG_LEVEL=${CLIMWEB_CELERY_BEAT_DEBUG_LEVEL:-INFO}

CLIMWEB_PORT="${CLIMWEB_PORT:-8000}"

# get the current version of the app
CLIMWEB_APP_VERSION=$(PYTHONPATH=/climweb/web/src/climweb python -c "import version; print(version.__version__)")

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

DEV COMMANDS:
django-dev      : Start a normal Baserow backend django development server, performs
                  the same checks and setup as the gunicorn command above.

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

    # initialize geomanager
    /climweb/web/src/climweb/manage.py initialize_geomanager

    # reset cms upgrade status
    /climweb/web/src/climweb/manage.py reset_cms_upgrade_status

    # watch for new files in the geomanager auto-ingest data dir
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

    if [[ -n "$CLIMWEB_NUM_OF_CELERY_WORKERS" ]]; then
        EXTRA_CELERY_ARGS+=(--concurrency "$CLIMWEB_NUM_OF_CELERY_WORKERS")
    fi
    exec celery -A climweb worker "${EXTRA_CELERY_ARGS[@]}" -l INFO "$@"
}

# Lets devs attach to this container running the passed command, press ctrl-c and only
# the command will stop. Additionally they will be able to use bash history to
# re-run the containers command after they have done what they want.
attachable_exec(){
    echo "$@"
    exec bash --init-file <(echo "history -s $*; $*")
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
        -b "0.0.0.0:${CLIMWEB_PORT}" \
        --log-level="${CLIMWEB_LOG_LEVEL}" \
        "${STARTUP_ARGS[@]}" \
        "${@:2}"
}

setup_otel_vars(){
  # These key value pairs will be exported on every log/metric/trace by any otel
  # exporters running in subprocesses launched by this script.
  EXTRA_OTEL_RESOURCE_ATTRIBUTES="service.namespace=ClimWeb,"
  EXTRA_OTEL_RESOURCE_ATTRIBUTES+="service.version=${CLIMWEB_APP_VERSION},"
  EXTRA_OTEL_RESOURCE_ATTRIBUTES+="deployment.environment=${CLIMWEB_DEPLOYMENT_ENV:-production}"

  if [[ -n "${OTEL_RESOURCE_ATTRIBUTES:-}" ]]; then
    # If the container has been launched with some extra otel attributes, make sure not
    # to override them with our ClimWeb specific ones.
    OTEL_RESOURCE_ATTRIBUTES="${EXTRA_OTEL_RESOURCE_ATTRIBUTES},${OTEL_RESOURCE_ATTRIBUTES}"
  else
    OTEL_RESOURCE_ATTRIBUTES="$EXTRA_OTEL_RESOURCE_ATTRIBUTES"
  fi
  export OTEL_RESOURCE_ATTRIBUTES
  echo "OTEL_RESOURCE_ATTRIBUTES=$OTEL_RESOURCE_ATTRIBUTES"
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

show_startup_banner

# wait for required services to be available, using docker-compose-wait
/wait

# load plugin utils
source /climweb/plugins/utils.sh

setup_otel_vars

case "$1" in
django-dev)
    run_setup_commands_if_configured
    echo "Running Development Server on 0.0.0.0:${CLIMWEB_PORT}"
    echo "Press CTRL-p CTRL-q to close this session without stopping the container."
    attachable_exec python3 /climweb/web/src/climeb/manage.py runserver "0.0.0.0:${CLIMWEB_PORT}"
    ;;
django-dev-no-attach)
    run_setup_commands_if_configured
    echo "Running Development Server on 0.0.0.0:${CLIMWEB_PORT}"
    python /climweb/web/src/climweb/manage.py runserver "0.0.0.0:${CLIMWEB_PORT}"
    ;;
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
    startup_plugin_setup
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
