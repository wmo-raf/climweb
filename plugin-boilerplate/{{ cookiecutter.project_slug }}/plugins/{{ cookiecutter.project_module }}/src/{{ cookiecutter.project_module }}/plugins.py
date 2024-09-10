from climweb.base.registries import Plugin


class PluginNamePlugin(Plugin):
    type = "{{ cookiecutter.project_module }}"

    def get_urls(self):
        return []
