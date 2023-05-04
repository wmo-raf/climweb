import argparse
import subprocess


DOCKER_COMPOSE_ARGS = """
    --file docker-compose.yml
    --env-file .env
    """

parser = argparse.ArgumentParser(
    description='manage a composition of docker containers to implement a nmhs cms instance',
    formatter_class=argparse.RawTextHelpFormatter)

parser.add_argument(
    '--simulate',
    dest='simulate',
    action='store_true',
    help='simulate execution by printing action rather than executing')

commands = [
    'build',
    'config',
    'down',
    'execute',
    'logs',
    'login',
    'prune',
    'restart',
    'start',
    'status',
    'stop',
    'up',
    'update',

    # python manage.py commands 
    'dumpdata',
    'loaddata',
    'forecast',
    'migrate',
    'collectstatic',
]

parser.add_argument('command',
                    choices=commands,
                    help="""
    - config: validate and view Docker configuration
    - build [containers]: build all services
    - start [containers]: start system
    - login [container]: login to the container (default: cms_web)
    - login-root [container]: login to the container as root
    - stop: stop [container] system
    - update: update Docker images
    - prune: cleanup dangling containers and images
    - restart [containers]: restart one or all containers
    - status [containers|-a]: view status of containers
    - dumpdata: creates a dump_data.json of the database in cms_web container
    - loaddata: loads dump_data.json into database in cms_web container
    - migrate: migrates columns and tables of database in cms_web container
    - collectstatic: collects static files into a single location that can easily be served in production in cms_web container
    - forecast: ingests next 7-day forecast in cms_web container from yr.no weather forecast API
    """)

parser.add_argument('args', nargs=argparse.REMAINDER)

args = parser.parse_args()

def split(value: str) -> list:
    """
    Splits string and returns as list
    :param value: required, string. bash command.
    :returns: list. List of separated arguments.
    """
    return value.split()

def run(args, cmd, asciiPipe=False) -> str:

    if args.simulate:
        if asciiPipe:
            print(f"simulation: {' '.join(cmd)} >/tmp/temp_buffer$$.txt")
        else:
            print(f"simulation: {' '.join(cmd)}")
        return '`cat /tmp/temp_buffer$$.txt`'
    else:
        if asciiPipe:
            return subprocess.run(
                cmd, stdout=subprocess.PIPE).stdout.decode('ascii')
        else:
            subprocess.run(cmd)
    return None


def make(args) -> None:
    """
    Serves as pseudo Makefile using Python subprocesses.
    :param command: required, string. Make command.
    :returns: None.
    """

    docker_compose_args = DOCKER_COMPOSE_ARGS

    # if you selected a bunch of them, default to all
    containers = "" if not args.args else ' '.join(args.args)

    # if there can be only one, default to web
    container = "cms_web" if not args.args else ' '.join(args.args)

    if args.command == "config":
        run(args, split(f'docker-compose {docker_compose_args} config'))
    elif args.command == "build":
        run(args, split(
            f'docker-compose {docker_compose_args} build {containers}'))
    elif args.command in ["up", "start"]:
        if containers:
            run(args, split(f"docker-compose {docker_compose_args} start {containers}"))
        else:
            run(args, split(f'docker-compose {docker_compose_args} up -d'))
    elif args.command == "execute":
        run(args, ['docker', 'exec', '-i', 'cms_web', 'sh', '-c', containers])
    elif args.command == "login":
        run(args, split(f'docker exec -it {container} /bin/bash'))
    elif args.command == "login-root":
        run(args, split(f'docker exec -u -0 -it {container} /bin/bash'))
    elif args.command == "logs":
        run(args, split(
            f'docker-compose {docker_compose_args} logs --follow {containers}'))
    elif args.command in ["stop", "down"]:
        if containers:
            run(args, split(f"docker-compose {docker_compose_args} {containers}"))
        else:
            run(args, split(
                f'docker-compose {docker_compose_args} down --remove-orphans {containers}')) 
    elif args.command == "update":
        run(args, split(f'docker-compose {docker_compose_args} pull'))
    elif args.command == "prune":
        run(args, split('docker builder prune -f'))
        run(args, split('docker container prune -f'))
        run(args, split('docker volume prune -f'))
        _ = run(args,
                split('docker images --filter dangling=true -q --no-trunc'),
                asciiPipe=True)
        run(args, split(f'docker rmi {_}'))
        _ = run(args, split('docker ps -a -q'), asciiPipe=True)
        run(args, split(f'docker rm {_}'))
    elif args.command == "restart":
        if containers:
            run(args, split(
                f'docker-compose {docker_compose_args} stop {containers}'))
            run(args, split(
                f'docker-compose {docker_compose_args} start {containers}'))
        else:
            run(args, split(
                f'docker-compose {docker_compose_args} down --remove-orphans'))
            run(args, split(
                f'docker-compose {docker_compose_args} up -d --force-recreate'))
    elif args.command == "status":
        run(args, split(
            f'docker-compose {docker_compose_args} ps {containers}'))
    elif args.command == "dumpdata":
        run(args, split(
            f'docker-compose {docker_compose_args} exec -T cms_web python manage.py dumpdata --natural-foreign --natural-primary --indent 2'   
            ' --exclude wagtailcore.ReferenceIndex -e wagtailsearch.indexentry -e wagtailimages.rendition -e sessions > dumpdata.json'))
    elif args.command == "loaddata":
        run(args, split(
            f'docker-compose {docker_compose_args} exec -T cms_web python manage.py loaddata dumpdata.json'))
    elif args.command == "forecast":
        run(args, split(
            f'docker-compose {docker_compose_args} exec -T cms_web python manage.py shell < forecast_manager/yr.py'))
    elif args.command == "migrate":
        run(args, split(
            f'docker-compose {docker_compose_args} exec -T cms_web python manage.py migrate'))
    elif args.command == "collectstatic":
        run(args, split(
            f'docker-compose {docker_compose_args} exec -T cms_web python manage.py collectstatic --clear --no-input'))


if __name__ == "__main__":
    make(args)
