#!/bin/bash
# Bash strict mode: http://redsymbol.net/articles/unofficial-bash-strict-mode/
set -euo pipefail

show_help(){
    echo """
Usage: install_plugin.sh [-d] [-f <plugin folder>]
  -f, --folder <plugin folder>        The folder where the plugin to install is located.
  -g, --git <https git repo url>      An url to a git repo containing the plugin to install.
  -u, --url <plugin url>              An url to a .tar.gz file containing the plugin to install.
      --hash <plugin hash>            If provided the plugin's contents will be hashed and checked against this hash, if they do not match the install will fail.
  -d, --dev                           Install the plugin for development.
  -r, --runtime                       If provided any runtime plugin setup scripts will be run if found. Should never be set if being called from a Dockerfile.
  -o, --overwrite                     If provided any existing plugin of the same name will be overwritten and force re-installed, built and/or setup.
  -h, --help                          Show this help message and exit.

A ClimWeb plugin is a folder named after the plugin. This must be a valid Python package.
"""
}

source /climweb/plugins/utils.sh

# First parse the args using getopt
VALID_ARGS=$(getopt -o u:dhf:rg:o --long hash:,url:,git:,help,dev,folder:,runtime,overwrite -- "$@")
if [[ $? -ne 0 ]]; then
    error "Incorrect options provided."
    show_help
    exit 1;
fi
eval set -- "$VALID_ARGS"

if [[ "$*" == "--" ]]; then
    error "No arguments provided."
    show_help
    exit 1;
fi

# Next loop over the user provided args and set flags accordingly.
dev=false
url=
folder=
hash=
git=
exclusive_flag_count=0
runtime=
overwrite=
# shellcheck disable=SC2078
while [ : ]; do
  case "$1" in
    -d | --dev)
        log "Installing plugin in dev mode."
        dev=true
        shift
        ;;
    -f | --folder)
        folder="$2"
        shift 2
        exclusive_flag_count=$((exclusive_flag_count+1))
        ;;
    --hash)
        hash="$2"
        shift 2
        ;;
    -u | --url)
        url="$2"
        shift 2
        exclusive_flag_count=$((exclusive_flag_count+1))
        ;;
    -g | --git)
        git="$2"
        shift 2
        exclusive_flag_count=$((exclusive_flag_count+1))
        ;;
    -r | --runtime)
        runtime="true"
        shift
        ;;
    -o | --overwrite)
        overwrite="true"
        shift
        ;;
   -h | --help)
        show_help
        exit 0;
        ;;
    --)
        shift
        break
        ;;
  esac
done

if [[ "$exclusive_flag_count" -eq "0" ]]; then
    error "You must provide one of the following flags: --folder, --url or --git"
    show_help
    exit 1;
fi

if [[ "$exclusive_flag_count" -gt "1" ]]; then
    echo "You must provide only one of the following flags: --folder, --url or --git"
    show_help
    exit 1;
fi

# --git was provided, download the plugin using git..
if [[ -n "$git" ]]; then
    log "Downloading plugin from git repo at $git."
    temp_work_dir=$(mktemp -d)
    cd "$temp_work_dir"
    git clone "$git" .

    dirs=("$temp_work_dir"/plugins/*/)
    num_dirs=${#dirs[@]}
    if [[ "$num_dirs" -ne 1 ]]; then
        error "$git does not look like a ClimWeb plugin. The plugins/ subdirectory in the repo must contain exactly one sub-directory."
        exit 1;
    fi
    folder=${dirs[0]}
fi

# --url was set, download the url, untar it to a temp dir, and verify it only has one
# sub dir.
if [[ -n "$url" ]]; then
    log "Downloading and extracting plugin from $url."
    temp_work_dir=$(mktemp -d)
    curl -Ls "$url" | tar xz -C "$temp_work_dir"

    dirs=("$temp_work_dir"/*/plugins/*/)
    num_dirs=${#dirs[@]}
    if [[ "$num_dirs" -ne 1 ]]; then
        error "$url does not look like a ClimWeb plugin. The plugin archive must contain a plugins/ sub-directory itself containing exactly one sub-directory for the plugin."
        exit 1;
    fi
    folder=${dirs[0]}
fi

# copy the plugin at the folder location into the plugin dir if it has not been already.
plugin_name="$(basename -- "$folder")"
plugin_install_dir="$CLIMWEB_PLUGIN_DIR/$plugin_name"
if [[ ! "$folder" -ef "$plugin_install_dir" ]]; then
  if [[ ! -d "$plugin_install_dir" || "$overwrite" == "true" ]]; then
    log "Copying plugin $plugin_name into plugins folder at $plugin_install_dir."
    mkdir -p "$CLIMWEB_PLUGIN_DIR"
    rm -rf "$plugin_install_dir"
    cp -Tr "$folder" "$plugin_install_dir"
  else
    log "Found an existing plugin installed at $plugin_install_dir, not overwriting it
        as the --overwrite flag was not provided to this script."
  fi
  folder="$CLIMWEB_PLUGIN_DIR/$plugin_name"
fi
chown -R "$DOCKER_USER": "$folder"

# Now we've copied the plugin into the plugin dir we can delete the tmp download dir
# if we used it.
if [[ -n "${temp_work_dir:-}" ]]; then
  rm -rf "$temp_work_dir"
fi

# --hash was set, hash the plugin folder and check it matches.
if [[ -n "$hash" ]]; then
  plugin_hash=$(find "$folder" -type f -print0 | sort -z | xargs -0 sha1sum | sha1sum | cut -d " " -f 1 )
  if [[ "$plugin_hash" != "$hash" ]]; then
    error "Plugin $plugin_name does not match the provided hash. This could mean it has been maliciously modified and it is not safe to install."
    error "The plugins hash was: $plugin_hash"
    error "Instead we expected : $hash"
    exit 1;
  else
    log "Plugin ${plugin_name}'s hash matches provided hash."
  fi
fi

check_and_run_script(){
    if [[ -f "$1/$2" ]]; then
        log "Running ${plugin_name}'s custom $2 script"
        bash "$1/$2"
    fi
}

run_as_docker_user(){
  CURRENT_USER=$(whoami)
  if [[ "$CURRENT_USER" != "$DOCKER_USER" ]]; then
    gosu "$DOCKER_USER" "$@"
  else
    "$@"
  fi
}

# Make sure we create the container markers folder which we will use to check if a
# plugin has been installed or not already inside this container.
mkdir -p /climweb/container_markers

# Install plugin
if [[ -d "$folder" ]]; then
    BUILT_MARKER=/climweb/container_markers/$plugin_name.built
    if [[ ! -f "$BUILT_MARKER" || "$overwrite" == "true" ]]; then
      log "Building ${plugin_name}."

      cd /climweb

      if [[ "$dev" == true ]]; then
          run_as_docker_user pip3 install -e "$folder"
      else
          run_as_docker_user pip3 install "$folder"
      fi

      check_and_run_script "$folder" build.sh
      touch "$BUILT_MARKER"
    else
      log "Skipping install of ${plugin_name} as it is already installed."
    fi

    PLUGIN_RUNTIME_SETUP_MARKER=/climweb/container_markers/$plugin_name.runtime-setup
    if [[ ( ! -f "$PLUGIN_RUNTIME_SETUP_MARKER" || "$overwrite" == "true" ) && $runtime == "true" ]]; then
      check_and_run_script "$folder" runtime_setup.sh
      touch "$PLUGIN_RUNTIME_SETUP_MARKER"
    else
      log "Skipping runtime setup of ${plugin_name}."
    fi
fi

log "Fixing ownership of plugins from $(id -u) to $DOCKER_USER in $CLIMWEB_PLUGIN_DIR"
chown -R "$DOCKER_USER": "$CLIMWEB_PLUGIN_DIR"
chown -R "$DOCKER_USER": /climweb/container_markers/
log_success "Finished setting up ${plugin_name} successfully."
