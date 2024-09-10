import logging

from .registry import Registry, Instance

logger = logging.getLogger(__name__)


class Plugin(Instance):

    def get_urls(self):
        """
        If needed root urls related to the plugin can be added here.

        Example:

            def get_urls(self):
                from . import api_urls

                return [
                    path('some-url/', include(api_urls, namespace=self.type)),
                ]

            # api_urls.py
            from django.urls import re_path

            urlpatterns = [
                url(r'some-view^$', SomeView.as_view(), name='some_view'),
            ]

        :return: A list containing the urls.
        :rtype: list
        """

        return []


class PluginRegistry(Registry):
    """
    With the plugin registry it is possible to register new plugins. A plugin is an
    abstraction made specifically for ClimWeb. It allows to extend and develop specific functionalities on top of ClimWeb.
    """

    name = "plugin"

    @property
    def urls(self):
        """
        Returns a list of all the urls that are in the registered instances. They
        are going to be added to the root url config.

        :return: The urls of the registered instances.
        :rtype: list
        """

        urls = []
        for types in self.registry.values():
            urls += types.get_urls()
        return urls

    def get_plugin_subpage_types_for_page(self, page_model_class_name):
        """
        Returns a list of all the subpage types that are available for a specific page model.

        :param page_model_class_name: The name of the page model class.
        :type page_model_class_name: str
        :return: A list of the subpage types.
        :rtype: list
        """

        name = page_model_class_name.lower()
        fn_name = f"get_{name}_subpage_types"

        subpage_types = []
        for types in self.registry.values():
            fn = getattr(types, fn_name, None)

            if fn:
                subpage_types += fn()

        return subpage_types


plugin_registry = PluginRegistry()
