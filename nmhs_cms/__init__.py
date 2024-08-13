from nmhs_cms.utils.version import get_version, get_semver_version

# major.minor.patch.release.number
# release must be one of alpha, beta, rc, or final
VERSION = (0, 9, 2, "final", 0)

__version__ = get_version(VERSION)

__semver__ = get_semver_version(VERSION)
