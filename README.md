# nmhs-cms

Template Content Management System for NMHSs in Africa

---

## User Guide

User guide - https://github.com/wmo-raf/nmhs-cms/wiki

---

## Prerequisites

Before installing the CMS, there are a few prerequisites to consider installing on your server:

1. **Docker Engine:** Ensure that Docker Engine is installed and running on the machine where you plan to execute the docker-compose command https://docs.docker.com/engine/install/. Docker Engine is the runtime environment for containers.

2. **Docker Compose:** Install Docker Compose https://docs.docker.com/compose/install/ on the machine where you intend to run the command. Docker Compose is a tool that allows you to define and manage multi-container Docker applications using a YAML configuration file.

3. **Python 3:** Ensure that Python 3 is installed on your machine. You can download the Python installer from the official Python website (https://www.python.org/downloads/) and follow the installation instructions for your operating system.

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

```sh
unzip nmhs-cms.zip
```

```sh
cd nmhs-cms-0.0.3
```

### 2. Setup environmental variables

To set up environmental variables, execute the command below and answer the prompts. To use default variables press enter.

CMS Variables:

```sh
python3 nmhs-ctl.py setup_cms
```

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

```sh
python3 nmhs-ctl.py setup_db
```

This command will create a .env file from the .env.sample and set the specified varibales.

Output as below:

```sh
Setting up PostgreSQL Configs...
 ENTER POSTGRES_PORT_CMS: (default -> 5432).  Press enter to accept default
 ENTER POSTGRES_PASSWORD_CMS: (default -> test1234).  Press enter to accept default
✓ Completed PostgreSQL Setup... Run 'python3 nmhs-ctl.py restart' to reload changes
```

### 3. Build Images

```sh
python3 nmhs-ctl.py build
```

### 4. Start all Containers

```sh
python3 nmhs-ctl.py up
```

### 5. Load Dumpdata / Fixtures

Load all fixtures / import backup of CMS

```sh
python3 nmhs-ctl.py loaddata
```

### 6. Generate 7-Day Forecast

Fetch 7-day forecast from external source (https://developer.yr.no/).

```sh
python3 nmhs-ctl.py forecast
```

### 7. Create CMS Admin superuser

```sh
python3 manage.py createsuperuser
```

---

## Other useful commands

| Command      | Purpose |
| -------- | ----- | 
| `restart`   | apply all changes made to files in the project |
| `config` |  validate and view the Compose file configuration |
| `login` | interact with the container's command line and execute commands as if you were directly logged into the container |
| `login-root` | access a running Docker container and open a Bash shell inside it with the root user |
| `logs` | real-time output of the containers' logs |
| `stop/down` | stop and remove Docker containers |
| `prune` | clean up unused Docker resources such as containers, images, networks, and volumes. ***Exercise caution when using these commands and ensure that you do not accidentally remove resources that are still needed.*** |
| `status` | display container names, their status (running, stopped), the associated services, and their respective health states |
| `dumpdata` | export the data in json format (dumodata.json) that can be used for backups, migrations, or transferring data between different environments |
| `migrate` | managing database schema changes and applying those changes to the database |
| `collectstatic` | collect all static files from your applications and copy them to a single location |
| `setup_mautic` | setup mautic environmental variables i.e `MAUTIC_DB_USER`,`MAUTIC_DB_PASSWORD` and  `MYSQL_ROOT_PASSWORD`,    |
| `setup_recaptcha` | setup recaptcha environmental variables i.e `RECAPTCHA_PRIVATE_KEY` and `RECAPTCHA_PUBLIC_KEY`|

