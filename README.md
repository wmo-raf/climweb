# nmhs-cms

Template Content Management System for NMHSs in Africa

## Quickstart with test data

The `quickstart` arguement in `nmhs-ctl.py` deploys nmhs-cms with test data with a single command and requires python3 setup. When using nmhs-cms from source, the default port for web components is 8081.

1. Download from source:

    `git clone https://github.com/wmo-raf/nmhs-cms.git`

    `cd nmhs-cms`

2. Run quick instance.

    `python3 nmhs-ctl.py quickstart`


    The `quickstart` executes the following steps:

    ```py
    [1/6] BUILDING CONTAINERS
    [2/6] STARTING UP CONTAINERS 
    [3/6] MIGRATING DATABASE TABLES
    [4/6] LOADING DUMP DATA
    [5/6] COLLECTING STATIC FILES
    [6/6] FETCHING 7-DAY FORECAST
    ```

    The instance can be found at `http://localhost:8081`

3. Additionally, create superuser to access the CMS Admin interface:

    `python3 nmhs-ctl.py createsuperuser`

---

## Installation and configuration

In progress ...

<!-- git clone repo

`wget https://github.com/wmo-raf/nmhs-cms/archive/refs/tags/v0.0.1.zip`

`unzip 


python3 nmhs-ctl.py setup_cms

python3 nmhs-ctl.py setup_db

python3 nmhs-ctl.py build

python3 nmhs-ctl.py up

python3 nmhs-ctl.py loaddata

python3 nmhs-ctl.py forecast

python3 manage.py  createsuperuser -->


---

## User Guide

User guide - https://github.com/wmo-raf/nmhs-cms/wiki


