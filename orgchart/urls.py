from django.urls import path
from orgchart.views import organizational_chart_editor, load_organizational_structure, save_organizational_structure

urlpatterns = [
    path('organizational-chart-editor/', organizational_chart_editor, name='organizational_chart_editor'),
    path('load-organizational-structure/', load_organizational_structure, name='load_organizational_structure'),
    path('save-organizational-structure/', save_organizational_structure, name='save_organizational_structure'),
    # Add other URLs as needed
]