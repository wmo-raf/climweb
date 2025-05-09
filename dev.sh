#!/bin/bash

# Bash strict mode: http://redsymbol.net/articles/unofficial-bash-strict-mode/
set -eo pipefail

RED=$(tput setaf 1)
GREEN=$(tput setaf 2)
YELLOW=$(tput setaf 3)
NC=$(tput sgr0) # No Color

DOCKER_COMPOSE="docker-compose"

if docker compose version &> /dev/null; then
  DOCKER_COMPOSE="docker compose"
fi

show_help() {
    echo """
./dev.sh Starts the Climweb development environment

Usage: ./dev.sh [optional start dev commands] [optional docker-compose up commands]

The ./dev.sh Commands are:
dev (default)   : Use the dev environment.
restart         : Stop the environment first before relaunching.
restart_wipe    : Stop the environment, delete all of the compose file named volumes.
down            : Down the environment and don't up after.
kill            : Kill the environment and don't up after.
dont_migrate    : Disable automatic database migration on climweb startup.
ignore_ownership: Don't exit if there are files in the repo owned by a different user
help            : Show this message.
"""
}

function ensure_only_one_env_selected_at_once() {
  if [ "$env_set" == true ]; then
    echo "${RED}You cannot select multiple different environments at once"
    exit 1
  else
    env_set=true
  fi
}

down=false
kill=false
build=false
run=false
exec=false
config=false
up=true
migrate=true
exit_if_other_owners_found=true
delete_volumes=false

env_set=false

while true; do
case "${1:-noneleft}" in
    dont_migrate)
        echo "./dev.sh: Automatic migration on startup has been disabled."
        shift
        migrate=false
    ;;
    restart)
        echo "./dev.sh: Restarting Dev Environment"
        shift
        down=true
        up=true
    ;;
    down)
        echo "./dev.sh: Stopping Dev Environment"
        shift
        up=false
        down=true
    ;;
    kill)
        echo "./dev.sh: Killing Dev Environment"
        shift
        up=false
        kill=true
    ;;
    run)
        echo "./dev.sh: docker-compose running the provided commands"
        shift
        up=false
        run=true
    ;;
    exec)
          echo "./dev.sh: docker-compose executing the provided commands"
          shift
          up=false
          exec=true
      ;;
    config)
          echo "./dev.sh: docker-compose config"
          shift
          up=false
          config=true
      ;;
    build_only)
        echo "./dev.sh: Disabled docker-compose up at end"
        shift
        build=true
        up=false
    ;;
    ignore_ownership)
        echo "./dev.sh: Continuing if files in repo are not owned by $USER."
        shift
        exit_if_other_owners_found=false
    ;;
    help)
        echo "Command given was $*"
        show_help
        exit 0
    ;;
    *)
        break
    ;;
esac
done

OWNERS=$(find . ! -user "$USER")

if [[ $OWNERS ]]; then
if [[ "$exit_if_other_owners_found" = true ]]; then
echo "${RED}./dev.sh ERROR${NC}: Files not owned by your current user: $USER found in this repo.
This will cause file permission errors when Climweb starts up.

They are probably build files created by the old Climweb Docker images owned by root.
Run the following command to show which files are causing this:
  find . ! -user $USER

Please run the following command to fix file permissions in this repository before using ./dev.sh:
  ${GREEN}sudo chown $USER -R .${NC}

OR you can ignore this check by running with the ignore_ownership arg:
  ${YELLOW}./dev.sh ignore_ownership ...${NC}"
exit;
else

echo "${YELLOW}./dev.sh WARNING${NC}: Files not owned by your current user: $USER found in this repo.
Continuing as 'ignore_ownership' argument provided."
fi

fi

# Set various env variables to sensible defaults if they have not already been set by
# the user.
if [[ -z "$UID" ]]; then
UID=$(id -u)
fi
export UID

if [[ -z "$GID" ]]; then
GID=$(id -g)
fi
export GID


if [[ -z "${MIGRATE_ON_STARTUP:-}" ]]; then
if [ "$migrate" = true ] ; then
export MIGRATE_ON_STARTUP="true"
else
# Because of the defaults set in the docker-compose file we need to explicitly turn
# this off as just not setting it will get the default "true" value.
export MIGRATE_ON_STARTUP="false"
fi
else
  echo "./dev.sh Using the already set value for the env variable MIGRATE_ON_STARTUP = $MIGRATE_ON_STARTUP"
fi

# Enable buildkit for faster builds with better caching.
export COMPOSE_DOCKER_CLI_BUILD=1
export DOCKER_BUILDKIT=1

echo "./dev.sh running docker-compose commands:
------------------------------------------------
"

CORE_FILE=docker-compose.yml
OVERRIDE_FILE=(-f docker-compose.dev.yml)

set -x

if [ "$down" = true ] ; then
# Remove the containers and remove the anonymous volumes for cleanliness sake.
$DOCKER_COMPOSE -f "$CORE_FILE" "${OVERRIDE_FILE[@]}" rm -s -v -f
$DOCKER_COMPOSE -f "$CORE_FILE" "${OVERRIDE_FILE[@]}" down --remove-orphans
fi

if [ "$kill" = true ] ; then
$DOCKER_COMPOSE -f "$CORE_FILE" "${OVERRIDE_FILE[@]}" kill
fi

if [ "$build" = true ] ; then
  $DOCKER_COMPOSE -f "$CORE_FILE" build "${OVERRIDE_FILE[@]}" "$@"
fi

if [ "$delete_volumes" = true ] ; then
  $DOCKER_COMPOSE -f "$CORE_FILE" "${OVERRIDE_FILE[@]}" down -v
fi

if [ "$up" = true ] ; then
$DOCKER_COMPOSE -f "$CORE_FILE" "${OVERRIDE_FILE[@]}" up "$@"
fi

if [ "$run" = true ] ; then
$DOCKER_COMPOSE -f "$CORE_FILE" "${OVERRIDE_FILE[@]}" run "$@"
fi

if [ "$exec" = true ] ; then
$DOCKER_COMPOSE -f "$CORE_FILE" "${OVERRIDE_FILE[@]}" exec "$@"
fi

if [ "$config" = true ] ; then
$DOCKER_COMPOSE -f "$CORE_FILE" "${OVERRIDE_FILE[@]}" config
fi

set +x