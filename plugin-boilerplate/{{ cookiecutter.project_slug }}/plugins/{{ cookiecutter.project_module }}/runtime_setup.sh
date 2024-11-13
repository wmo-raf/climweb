#!/bin/bash
# Bash strict mode: http://redsymbol.net/articles/unofficial-bash-strict-mode/
set -euo pipefailb
# This file is automatically run by climweb when a climweb container starts up for the
# first time with this plugin already installed and built. It should impotently run
# any runtime setup that involves doing things with the  postgres database
# and/or the data volume.
