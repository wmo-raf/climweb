# Ensure looping over globs doesn't match nothing
shopt -s nullglob

if [ -t 0 ]; then
  TPUTTERM=()
else
  # if we are in a non-interactive environment set a default -T for tput so it doesn't
  # crash
  TPUTTERM=(-T xterm-256color)
fi

safe_tput(){
  if [[ -z "${NO_COLOR:-}" ]]; then
    tput "${TPUTTERM[@]}" "$@"
  fi
}

# shellcheck disable=SC2034
RED=$(safe_tput setaf 1)
# shellcheck disable=SC2034
GREEN=$(safe_tput setaf 2)
# shellcheck disable=SC2034
YELLOW=$(safe_tput setaf 3)
# shellcheck disable=SC2034
BLUE=$(safe_tput setaf 4)
# shellcheck disable=SC2034
PURPLE=$(safe_tput setaf 5)
# shellcheck disable=SC2034
CYAN=$(safe_tput setaf 6)
# shellcheck disable=SC2034
BOLD="$(safe_tput bold)"

NC=$(safe_tput sgr0) # No Color

CLIMWEB_PLUGIN_DIR=${CLIMWEB_PLUGIN_DIR:-/climweb/plugins}

simple_log(){
  echo -e "${BLUE}[PLUGIN] $*${NC}"
}
log(){
  echo -e "${BLUE}[PLUGIN][${plugin_name:-SETUP}] $*${NC}"
}
log_success(){
  echo -e "${GREEN}[PLUGIN][${plugin_name:-SETUP}] $*${NC}"
}
error(){
  echo -e "${RED}[PLUGIN][${plugin_name:-SETUP}] ERROR: $*${NC}"
}


# Remove build artifacts left behind in a plugin's source tree by a previous
# install.
#
# Plugin directories are usually bind-mounted from the host, so `build/` and
# `*.egg-info` survive container recreates. setuptools' bdist_wheel reuses
# `build/bdist.<platform>/wheel/` and aborts with
#
#   error: [Errno 17] File exists: 'build/bdist.linux-x86_64/wheel/<pkg>.dist-info'
#
# the next time the plugin is built. /climweb/container_markers is a tmpfs, so
# the ".built" marker is wiped on every recreate and the plugin is rebuilt on
# every start — which means one stale tree breaks startup indefinitely.
clean_plugin_build_artifacts(){
  local folder="$1"

  if [[ -z "$folder" || ! -d "$folder" ]]; then
    return 0
  fi

  local artifact
  for artifact in "$folder"/build "$folder"/dist "$folder"/*.egg-info "$folder"/src/*.egg-info; do
    if [[ -e "$artifact" ]]; then
      log "Removing stale build artifact $artifact"
      rm -rf "$artifact" || log "Could not remove $artifact, continuing anyway."
    fi
  done
}


# Plugins that ClimWeb now ships as built-in apps.
#
# CLIMWEB_PLUGIN_DIR is a persistent volume, so upgrading does not remove a plugin that
# an instance installed previously. Leaving one in place breaks startup in two ways:
#
#   1. The plugin registers a Django app with the same label as the built-in one, and
#      Django aborts with "Application labels aren't unique".
#   2. The upstream repo is now packaged as a normal pip module, so it no longer has the
#      plugins/<name>/ layout install_plugin.sh expects. The install fails, and because
#      the entrypoint runs with `set -e` that failure takes the whole container down.
#
# Each entry is "<plugin folder name>:<pip distribution name>".
CLIMWEB_SUPERSEDED_PLUGINS=(
  "dataset_helper_plugin:dataset-helper-plugin"
)

# Match a git repo url or tarball url against a superseded plugin. Repo urls do not
# have to match the folder name (dataset-helper-plugin vs dataset_helper_plugin), so
# compare on a normalised basename with punctuation folded to underscores.
is_superseded_source(){
  local source_url="$1"
  local base
  base="$(basename -- "${source_url%.git}")"
  base="${base%.tar.gz}"
  base="${base//-/_}"

  local entry
  for entry in "${CLIMWEB_SUPERSEDED_PLUGINS[@]}"; do
    if [[ "$base" == "${entry%%:*}" ]]; then
      return 0
    fi
  done
  return 1
}

# Delete any superseded plugin left over from a previous install, so the settings module
# never sees it and install_plugin.sh is never asked to rebuild it.
remove_superseded_plugins(){
  local entry plugin dist folder
  for entry in "${CLIMWEB_SUPERSEDED_PLUGINS[@]}"; do
    plugin="${entry%%:*}"
    dist="${entry##*:}"
    folder="$CLIMWEB_PLUGIN_DIR/$plugin"

    if [[ -d "$folder" ]]; then
      simple_log "Removing superseded plugin $plugin from $folder. It now ships with
      ClimWeb as a built-in app, and keeping the plugin would stop the site from starting."
      rm -rf "$folder" || simple_log "Could not remove $folder, continuing anyway."
      rm -f "/climweb/container_markers/$plugin.built" || true
      rm -f "/climweb/container_markers/$plugin.runtime-setup" || true
    fi

    # The plugin was pip installed into the venv. Its database tables are kept by the
    # built-in app, so only the now-orphaned distribution is removed - never the data.
    if pip3 show "$dist" >/dev/null 2>&1; then
      simple_log "Uninstalling superseded plugin distribution $dist."
      pip3 uninstall -y "$dist" >/dev/null 2>&1 || simple_log "Could not uninstall $dist, continuing anyway."
    fi
  done
}


startup_plugin_setup(){
  if [[ -z "${CLIMWEB_PLUGIN_SETUP_ALREADY_RUN:-}" ]]; then
    if [[ -z "${CLIMWEB_DISABLE_PLUGIN_INSTALL_ON_STARTUP:-}" ]]; then
      # Drop plugins that have become built-in apps before anything tries to build them.
      remove_superseded_plugins

      # Make sure any plugins found in the data dir are installed in this container if not
      # already.
      for plugin_dir in "$CLIMWEB_PLUGIN_DIR"/*/; do
        log "Found a plugin in $plugin_dir, ensuring it is installed..."
        if [[ -d "$plugin_dir" ]]; then
          /climweb/plugins/install_plugin.sh --runtime --folder "$plugin_dir"
        fi
      done

      # Make sure any plugins configured via the environment variable are installed.
      for url in $(echo "${CLIMWEB_PLUGIN_URLS:-}" | tr "," "\n")
      do
        if is_superseded_source "$url"; then
          simple_log "Skipping $url from CLIMWEB_PLUGIN_URLS: it now ships with ClimWeb as
          a built-in app. Remove it from the variable to silence this message."
          continue
        fi
        log "Downloading and installing the plugin found at $url"
        /climweb/plugins/install_plugin.sh --runtime --url "$url"
      done

      for repo in $(echo "${CLIMWEB_PLUGIN_GIT_REPOS:-}" | tr "," "\n")
      do
        if is_superseded_source "$repo"; then
          simple_log "Skipping $repo from CLIMWEB_PLUGIN_GIT_REPOS: it now ships with
          ClimWeb as a built-in app. Remove it from the variable to silence this message."
          continue
        fi
        log "Downloading and installing the plugin found at $repo"
        /climweb/plugins/install_plugin.sh --runtime --git "$repo"
      done

      # Ensure we don't run this function multiple times in the same shell.
      export CLIMWEB_PLUGIN_SETUP_ALREADY_RUN="yes"
    else
      log "Not installing any plugins found in CLIMWEB_PLUGIN_DIR or set in the
      CLIMWEB_PLUGIN_URLS or CLIMWEB_PLUGIN_GIT_REPOS env variables as
      CLIMWEB_DISABLE_PLUGIN_INSTALL_ON_STARTUP is set."
    fi
  fi
}