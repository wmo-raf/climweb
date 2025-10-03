# major.minor.patch.release.number
# release must be one of alpha, beta, rc, or final
<<<<<<< HEAD
VERSION = (1, 0, 6, "final", 0)
=======
VERSION = (1, 0, 5, "final", 0)
>>>>>>> 2937c452deffeed9e05c2fc9b12ecb62af34c58d

def get_semver_version(version):
    "Returns the semver version (X.Y.Z[-(alpha|beta)]) from VERSION"
    main = ".".join(str(x) for x in version[:3])
    
    sub = ""
    if version[3] != "final":
        sub = "-{}.{}".format(*version[3:])
    return main + sub


__version__ = get_semver_version(VERSION)
