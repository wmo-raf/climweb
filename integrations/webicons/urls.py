from django.urls import path

from .views import chooser, webicons, multiple

app_name = 'webicons'

urlpatterns = [
    path('', webicons.index, name='index'),
    path('<int:icon_id>/', webicons.edit, name='edit'),
    path('<int:image_id>/delete/', webicons.delete, name='delete'),
    path('add/', webicons.add, name='add'),

    path('multiple/add/', multiple.add, name='add_multiple'),
    path('multiple/<int:icon_id>/', multiple.edit, name='edit_multiple'),
    path('multiple/<int:icon_id>/delete/', multiple.delete, name='delete_multiple'),

    path('chooser/', chooser.chooser, name='chooser'),
    path('chooser/<int:icon_id>/', chooser.icon_chosen, name='icon_chosen'),
    path('chooser/upload/', chooser.chooser_upload, name='chooser_upload'),
]
