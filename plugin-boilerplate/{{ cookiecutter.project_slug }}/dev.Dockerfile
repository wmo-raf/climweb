# This a dev image for testing your plugin when installed into the climweb image
FROM climweb_dev:latest AS base

FROM climweb_dev:latest

USER root

ARG PLUGIN_BUILD_UID
ENV PLUGIN_BUILD_UID=${PLUGIN_BUILD_UID:-9999}
ARG PLUGIN_BUILD_GID
ENV PLUGIN_BUILD_GID=${PLUGIN_BUILD_GID:-9999}

# If we aren't building as the same user that owns all the files in the base
# image/installed plugins we need to chown everything first.
COPY --from=base --chown=$PLUGIN_BUILD_UID:$PLUGIN_BUILD_GID /climweb /climweb
RUN usermod -u $PLUGIN_BUILD_UID $DOCKER_USER

# Install your dev dependencies manually.
COPY --chown=$PLUGIN_BUILD_UID:$PLUGIN_BUILD_GID ./plugins/{{ cookiecutter.project_module }}/requirements/dev.txt /tmp/plugin-dev-requirements.txt
RUN . /climweb/venv/bin/activate && pip3 install -r /tmp/plugin-dev-requirements.txt

COPY --chown=$PLUGIN_BUILD_UID:$PLUGIN_BUILD_GID ./plugins/{{ cookiecutter.project_module }}/ $CLIMWEB_PLUGIN_DIR/{{ cookiecutter.project_module }}/
RUN . /climweb/venv/bin/activate && /climweb/plugins/install_plugin.sh --folder $CLIMWEB_PLUGIN_DIR/{{ cookiecutter.project_module }} --dev

USER $PLUGIN_BUILD_UID:$PLUGIN_BUILD_GID

# Add the venv to the path. This ensures that the venv is always activated when the container starts.
ENV PATH="/climweb/venv/bin:$PATH"

ENV DJANGO_SETTINGS_MODULE='climweb.config.settings.dev'
CMD ["django-dev"]