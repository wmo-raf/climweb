from climweb.config.celery_init import app as celery_app
from climweb.utils.version import get_version, get_semver_version
from climweb.version import VERSION

__version__ = get_version(VERSION)

__semver__ = get_semver_version(VERSION)

__all__ = ["celery_app"]
