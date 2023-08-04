from nmhs_cms.utils.version import get_version

# major.minor.patch.release.number
# release must be one of alpha, beta, rc, or final
VERSION = (0, 5, 3, "final", 0)

__version__ = get_version(VERSION)