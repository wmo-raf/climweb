# ./dev.sh

dev.sh is a helper bash script which makes working with Climweb’s development environment a breeze.

By default, running `./dev.sh` will start the dev env and make sure the containers
are running as your actual user.

## Examples of `./dev.sh` usage:

```
$ ./dev.sh # same as the up command above but also ensures the containers run as the running user!
$ ./dev.sh --build # ups and rebuilds
$ ./dev.sh restart # stops and then ups
$ ./dev.sh restart --build # stops, builds, ups
$ ./dev.sh build_only # just builds
$ ./dev.sh dont_migrate # ups but doesn't migrate automatically on startup
$ ./dev.sh dont_migrate dont_sync dont_attach restart --build # even more flags!
$ ./dev.sh run backend manage migrate
# Any commands found after the last `./dev.sh` command will be passed to the `docker compose up` call made by dev.sh
# This lets you say do --build on the end or any other docker-compose commands using dev.sh!
$ ./dev.sh restart {EXTRA_COMMANDS_PASSED_TO_UP}  
$ ./dev.sh down # downs the env
$ ./dev.sh kill # kills (the old stop_dev.sh)
# WARNING: restart_wipe will detail ALL volumes associated with that environment 
# permanently. 
$ ./dev.sh restart_wipe --build
```

## Why ./dev.sh ensures the containers run as you

In dev mode Climweb's source control directories are mounted from your local git repo into the containers. By mounting
these the containers will see source code changes and automatically rebuild. However, if the containers are not running
as your actual user then the containers might accidentally change the ownership or create files owned by the user
running inside the container. So by running the containers as your user there is no chance that your source control
directories will have file ownership problems. Additionally, it is best practice to not run Docker containers as the
default root user.

