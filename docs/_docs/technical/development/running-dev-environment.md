# Running the dev environment

If you want to contribute to Climweb you need to setup the development environment on your local computer. The best way
to do this is via Docker compose so that you can start the app with the least amount of hassle.

```{note}
For production deployment, please visit [https://github.com/wmo-raf/climweb-docker](https://github.com/wmo-raf/climweb-docker)
```

## Cloning the repository

The first step is to clone the Climweb repository from GitHub. You can do this by running the following command in your
terminal:

```
$ git clone https://github.com/wmo-raf/climweb.git
$ cd climweb
```

## Create `.env` file

Next, you need to create an environment file that contains the necessary configuration for the development environment.
You can do this by copying the sample dev environment file provided in the repository:

```
$ cp .env.dev.sample .env
```

Update the `.env` file with the required configuration. See the Environment Variables section
for reference on the available environment variables and their descriptions.

## Quickstart

If you are familiar with git and Docker Compose run these commands to launch Climweb’s dev environment locally,
otherwise please start from the Installing Requirements section below.

```
$ git clone https://github.com/wmo-raf/climweb.git

# Our supplied ./dev.sh script wraps Docker Compose setting the correct env vars for

# you to get hot code reloading working well.

$ ./dev.sh

# Run ./dev.sh help for further details.

$ ./dev.sh help
```

## Installing requirements

If you haven’t already installed docker and Docker Compose on your computer you can do so by following the instructions
on [https://docs.docker.com/desktop](https://docs.docker.com/desktop)
and [https://docs.docker.com/compose/install](https://docs.docker.com/compose/install)

```{note}
Docker version 19.03 is the minimum required to build Climweb. It is strongly advised however that you install the
latest version of Docker available. Please check that your docker is up to date by running `docker -v`.
```

You will also need git installed which you can do by following the instructions
on [https://www.linode.com/docs/development/version-control/how-to-install-git-on-linux-mac-and-windows](https://www.linode.com/docs/development/version-control/how-to-install-git-on-linux-mac-and-windows).

Once you have finished installing all the required software you should be able to run the following commands in your
terminal.

```

$ docker -v
Docker version 28.1.1, build 4eba377
$ docker compose version
Docker Compose version v2.35.1-desktop.1
$ git --version
git version 2.37.1
```

If all commands return something similar as described in the example, then you are ready to proceed!

### Starting the development environment

First, you need to clone the repository. Execute the following commands to clone the main branch. If you are not
familiar with git clone, this will download a copy of Climweb’s code to your computer.

```
$ git clone https://github.com/wmo-raf/climweb.git
Cloning into 'climweb'...
...
$ cd climweb
```

Now that we have our copy of the repo and have changed directories to the newly created climweb, we can bring up the
containers.

If you do not want to use the provided `dev.sh` script, you can run the following command to start the development
environment:

```
$ docker compose -f docker-compose.yml -f docker-compose.dev.yml up
```

```{note}
Note that the `docker-compose.dev.yml` file is used to override the default `docker-compose.yml` file with development
specific settings.
```

### Accessing the web application

Once the containers are up and running, you can access the Climweb application in your web browser at
[http://localhost:8000](http://localhost:8000). The port can be changed in the `.env` file if needed by modifying the
`CLIMWEB_DEV_PORT`
variable.

### Creating a superuser

To create a superuser for the Climweb application, you can run the following command in a separate terminal window:

```
$ docker compose -f docker-compose.yml -f docker-compose.dev.yml exec climweb climweb createsuperuser
```

### Keep the container running

The containers need to keep running while you are developing. They also monitor file
changes and update automatically, so you don’t need to worry about reloading. Any change to the code will trigger a
reload and you can see the changes immediately.