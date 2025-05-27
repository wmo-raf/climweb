# Backup and Restore Guide

## Backup Mechanism

Climweb uses [django-dbbackup](https://github.com/jazzband/django-dbbackup) for backup and restore of the database and
media files. The backup process is scheduled using Celery tasks, and currently runs every midnight.

The https://django-dbbackup.readthedocs.io/en/stable documentation provides detailed information on how the package
works.

## Backup Location

Currently, the backup files are store in the local filesystem of the server. The location is defined in the settings
file as below:

```python
# src/climweb/config/settings/base.py
DBBACKUP_STORAGE_OPTIONS = {
    'location': os.path.join(BASE_DIR, "backup")
}
```

## DB and Media files restoration

The restore process is done using the `dbrestore` management command.

Ensure you have placed your recent backup files in the backup directory. Usually these are two files, the database dump
file and media files tar file

You need to start with an empty database with PostGIS as the only external extension installed.

If you have extensions like `postgis_topology` or `postgis_tiger_geocoder` installed, you might need to drop these
extensions using similar command as below:

```sql
DROP
EXTENSION IF EXISTS postgis_topology;
DROP
EXTENSION IF EXISTS postgis_tiger_geocoder;
```

Then, you can run the restore command as below:

```bash
python manage.py dbrestore
```










