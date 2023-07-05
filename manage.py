#!/usr/bin/env python
import os
import sys
import environ

env = environ.Env(
    # set casting, default value
    DEBUG=(bool, False),
)

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_DIR = os.path.dirname(PROJECT_DIR)

if os.path.exists(os.path.join(BASE_DIR, '.env')):
    # reading .env file
    environ.Env.read_env(os.path.join(BASE_DIR, '.env'))


if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", f"nmhs_cms.settings.{env.str('ENVIRONMENT', 'production')}")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
