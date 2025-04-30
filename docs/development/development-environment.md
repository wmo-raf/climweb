## Local Development With Docker

Below are instructions to run ClimWeb locally using Docker. This way, you can test the application make changes and
contribute to the project.

For production deployment, please visit https://github.com/wmo-raf/climweb-docker

### Prerequisites

- Docker + Docker Compose installed

### Getting Started

1. Clone the repository

```bash
git clone https://github.com/wmo-raf/climweb.git
cd climweb
```

2. Copy the example environment file. See [Environment Variables](#environment-variables) for more details.

```bash
cp .env.sample .env
```

3. Edit the `.env` file and set the required environment variables.

```bash
nano .env
```

4. Build the Docker images

```bash
docker compose build
```

5. Start the containers

```bash
docker compose up
```

6. Create superuser. You can open a new terminal, navigate to the project root and run the command below to create a
   superuser

```bash
docker compose exec climweb_dev climweb createsuperuser
```

### Environment Variables

| Variable                  | Description                                                                                                                                                                                                                                          | Required | Default         | More Details                                                                                           |
|:--------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:---------|:----------------|:-------------------------------------------------------------------------------------------------------|
| CMS_DB_USER               | CMS Database user                                                                                                                                                                                                                                    | YES      |                 |                                                                                                        |
| CMS_DB_NAME               | CMS Database name                                                                                                                                                                                                                                    | YES      |                 |                                                                                                        |
| CMS_DB_PASSWORD           | CMS Database password.                                                                                                                                                                                                                               | YES      |                 |                                                                                                        |
| CMS_DB_VOLUME             | Mounted docker volume path for persisting database data                                                                                                                                                                                              | YES      |                 |                                                                                                        |
| CMS_SITE_NAME             | The human-readable name of your Wagtail installation which welcomes users upon login to the Wagtail admin.                                                                                                                                           | YES      |                 |                                                                                                        |
| CMS_ADMIN_URL_PATH        | Base Path to admin pages. Do not use `admin` or an easy to guess path. Should be one word and can include an hyphen. DO NOT include any slashes at the start or the end.                                                                             | YES      |                 |                                                                                                        |
| CMS_DEBUG                 | A boolean that turns on/off debug mode. Never deploy a site into production with DEBUG turned on                                                                                                                                                     | NO       | False           |                                                                                                        |
| CMS_PORT                  | Port to run cms                                                                                                                                                                                                                                      | YES      | 80              |                                                                                                        |
| CMS_BASE_URL              | This is the base URL used by the Wagtail admin site. It is typically used for generating URLs to include in notification emails.                                                                                                                     | NO       |                 |                                                                                                        |
| CMS_DEFAULT_LANGUAGE_CODE | The language code for the CMS. Availabe codes are `en` for English, `fr` from French, `ar` for Arabic, `am` for Amharic, `es` for Spanish, `sw` for Swahili. Default is `en` if not set                                                              | NO       | en              |                                                                                                        |
| CSRF_TRUSTED_ORIGINS      | This variable can be set when CMS_PORT is not 80 e.g if CMS_PORT=8000, CSRF_TRUSTED_ORIGINS would be the following: http://{YOUR_IP_ADDRESS}:8000, http://{YOUR_IP_ADDRESS}, http://localhost:8000 and http://127.0.0.1:8000                         | NO       |                 |                                                                                                        |
| TIME_ZONE                 | A string representing the time zone for this installation. See the [list of time zones](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones). Set this to your country timezone                                                             | NO       | UTC             | [List of tz database time zones](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones)         |
| SECRET_KEY                | A secret key for a particular Django installation. This is used to provide cryptographic signing, and should be set to a unique, unpredictable value. Django will refuse to start if SECRET_KEY is not set                                           | YES      |                 | You can use this online tool [https://djecrety.ir](https://djecrety.ir/) to generate the key and paste |
| ALLOWED_HOSTS             | A list of strings representing the host/domain names that this Django site can serve. This is a security measure to prevent HTTP Host header attacks, which are possible even under many seemingly-safe web server configurations.                   | YES      |                 | [Django Allowed Hosts](https://docs.djangoproject.com/en/4.2/ref/settings/#std-setting-ALLOWED_HOSTS)  |                                                                                                                                                                                                                          |          |         |                                                                                                       |
| SMTP_EMAIL_HOST           | The host to use for sending email                                                                                                                                                                                                                    | NO       |                 |                                                                                                        |
| SMTP_EMAIL_PORT           | Port to use for the SMTP server defined in `SMTP_EMAIL_HOST`                                                                                                                                                                                         | NO       | 25              |                                                                                                        |
| SMTP_EMAIL_USE_TLS        | Whether to use a TLS (secure) connection when talking to the SMTP server. This is used for explicit TLS connections, generally on port 587                                                                                                           | NO       | True            |                                                                                                        |
| SMTP_EMAIL_HOST_USER      | Username to use for the SMTP server defined in `SMTP_EMAIL_HOST`. If empty, Django won’t attempt authentication.                                                                                                                                     | NO       |                 |                                                                                                        |
| SMTP_EMAIL_HOST_PASSWORD  | Password to use for the SMTP server defined in `SMTP_EMAIL_HOST`. This setting is used in conjunction with `SMTP_EMAIL_HOST_USER` when authenticating to the SMTP server. If either of these settings is empty, Django won’t attempt authentication. | NO       |                 |                                                                                                        |
| CMS_ADMINS                | A list of all the people who get code error notifications, in format `"Name <name@example.com>, Another Name <another@example.com>"`                                                                                                                 | NO       |                 |                                                                                                        |
| DEFAULT_FROM_EMAIL        | Default email address to use for various automated correspondence from the site manager(s)                                                                                                                                                           | NO       |                 |                                                                                                        |
| RECAPTCHA_PUBLIC_KEY      | Google Recaptcha Public Key. https://www.google.com/recaptcha/about/ will need a Google account for RECAPTCHA_PRIVATE_KEY and RECAPTCHA_PUBLIC_KEY creation                                                                                          | NO       |                 |                                                                                                        |
| RECAPTCHA_PRIVATE_KEY     | Google Recaptcha Private Key                                                                                                                                                                                                                         | NO       |                 |                                                                                                        |
| CMS_NUM_OF_WORKERS        | Gunicorn number of workers. Recommended value should be `(2 x $num_cores) + 1 `. For example, if your server has `4 CPU Cores`, this value should be set to `9`, which is the result of `(2 x 4) + 1 = 9`                                            | YES      |                 | [Gunicorn Workers details](https://docs.gunicorn.org/en/latest/design.html#how-many-workers)           |
| CMS_STATIC_VOLUME         | Mounted docker volume path for persisting CMS static files                                                                                                                                                                                           | YES      | ./climeb/static |                                                                                                        |
| CMS_MEDIA_VOLUME          | Mounted docker volume path for persisting CMS media files                                                                                                                                                                                            | YES      | ./climeb/media  |                                                                                                        |
| CMS_UPGRADE_HOOK_URL      | [Webhook](https://github.com/adnanh/webhook) url to your server that triggers a cms upgrade script                                                                                                                                                   | NO       |                 |                                                                                                        |
| BACKUP_VOLUME             | Mounted docker volume path for persisting Backup dp and media files                                                                                                                                                                                  | YES      | ./climeb/backup |                                                                                                        |
