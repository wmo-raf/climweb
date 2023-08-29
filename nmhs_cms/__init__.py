from nmhs_cms.utils.version import get_version
from nmhs_cms.settings.base import CMS_VERSION

# major.minor.patch.release.number
# release must be one of alpha, beta, rc, or final
VERSION = (CMS_VERSION.split('.')[0], CMS_VERSION.split('.')[1], CMS_VERSION.split('.')[2], "final", 0)

__version__ = get_version(VERSION)