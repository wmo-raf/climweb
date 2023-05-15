# nmhs-cms

Template Content Management System for NMHSs in Africa

---

## User Guide

User guide - https://github.com/wmo-raf/nmhs-cms/wiki

---
## Quickstart Installation with Test Data

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

### 1. Download latest version

```sh
wget -cO - https://github.com/wmo-raf/nmhs-cms/archive/refs/tags/v0.0.3.zip > nmhs-cms.zip
```

`unzip`

`cd nmhs-cms-0.0.3`

### 2. Setup environmental variables

To set up environmental variables, execute the command below and answer the prompts. To use default variables press enter.

CMS Variables:

`python3 nmhs-ctl.py setup_cms`

Output as below:

```sh
Setting up CMS Configs...
 ENTER ENVIRONMENT: (default -> dev).  Press enter to accept default
 ENTER DEBUG: (default -> True).  Press enter to accept default
 ENTER CMS_HOST: (default -> 127.0.0.1).  Press enter to accept default
 ENTER CMS_PORT: (default -> 3031).  Press enter to accept default 8000
 ENTER BASE_PATH: (default -> ).  Press enter to accept default
nginx.conf updated successfully.
✓ Completed CMS Setup... Run 'python3 nmhs-ctl.py restart' to reload changes
```

Database Variables:

`python3 nmhs-ctl.py setup_db`

This command will create a .env file from the .env.sample and set the specified varibales.

Output as below:

```sh
Setting up PostgreSQL Configs...
 ENTER POSTGRES_PORT_CMS: (default -> 5432).  Press enter to accept default
 ENTER POSTGRES_PASSWORD_CMS: (default -> test1234).  Press enter to accept default
✓ Completed PostgreSQL Setup... Run 'python3 nmhs-ctl.py restart' to reload changes
```

### 3. Build Images

`python3 nmhs-ctl.py build`

### 4. Start all Containers

`python3 nmhs-ctl.py up`

### 5. Load Dumpdata / Fixtures

Load all fixtures / import backup of CMS

`python3 nmhs-ctl.py loaddata`

### 6. Generate 7-Day Forecast

Fetch 7-day forecast from external source (https://developer.yr.no/).

`python3 nmhs-ctl.py forecast`

### 7. Create CMS Admin superuser

`python3 manage.py createsuperuser`

### Apply New changes?

This command can be executed when changes are made to files in the project 

`python3 nmhs-ctl.py restart`

