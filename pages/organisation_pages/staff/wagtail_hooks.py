from django.urls import reverse
from wagtail.contrib.modeladmin.options import ModelAdmin, modeladmin_register
from wagtail import hooks
from django.urls import path
from django.views.generic import View
from django.shortcuts import render
from wagtail.admin.menu import MenuItem


@hooks.register('register_admin_urls')
def register_custom_admin_urls():
    return [
        path('organizational-chart/', OrganizationalChartView.as_view(), name='organizational_chart'),
    ]

class OrganizationalChartView(View):
    def get(self, request):
        return render(request, 'orgchart/organizational_chart_editor.html')
    

@hooks.register('construct_settings_menu')
def add_custom_menu_item(request, menu_items):
    menu_items.append(MenuItem('Organizational Chart', reverse('organizational_chart'), classnames='icon icon-fa-sitemap', order=100))