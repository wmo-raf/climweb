#!/usr/bin/env python

import os

try:
    from setuptools import find_packages, setup
except ImportError:
    from distutils.core import setup

PROJECT_DIR = os.path.dirname(__file__)
REQUIREMENTS_DIR = os.path.join(PROJECT_DIR, "requirements")


def get_requirements(env):
    with open(os.path.join(REQUIREMENTS_DIR, f"{env}.txt")) as fp:
        return [
            x.strip()
            for x in fp.read().split("\n")
            if not x.strip().startswith("#") and not x.strip().startswith("-")
        ]


def get_version():
    version = {}
    version_file = os.path.join("src", "climweb", "version.py")
    with open(version_file) as f:
        exec(f.read(), version)
    return version["VERSION"]


def get_semver_version(version):
    "Returns the semver version (X.Y.Z[-(alpha|beta)]) from VERSION"
    main = ".".join(str(x) for x in version[:3])

    sub = ""
    if version[3] != "final":
        sub = "-{}.{}".format(*version[3:])
    return main + sub


version = get_version()
semver_version = get_semver_version(version)

install_requires = get_requirements("base")

setup(
    name="climweb",
    version=semver_version,
    description="Template Content Management System for NMHSs in Africa",
    author="Erick Otenyo, Grace Amondi",
    author_email="eotenyo@wmo.int, gochieng@wmo.int",
    project_urls={
        "Documentation": "https://nmhs-cms.readthedocs.io/",
        "Source": "https://github.com/wmo-raf/nmhs-cms",
        "Tracker": "https://github.com/wmo-raf/nmhs-cms/issues",
    },
    packages=find_packages(include=["climweb", "climweb.*"]),
    include_package_data=True,
    license="MIT",
    long_description="""Climate Web is a template content management system for NMHSs in Africa.
    It includes tools and functionalities aimed at supporting the NMHSs in their daily website 
    management activities, in providing information and services to their users.\n\n\
    For more details, see https://github.com/wmo-raf/nmhs-cms.""",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Framework :: Django",
        "Framework :: Django :: 4.2",
        "Framework :: Wagtail",
        "Topic :: Internet :: WWW/HTTP :: Site Management",
    ],
    python_requires=">=3.9",
    install_requires=install_requires,
    zip_safe=False,
)
