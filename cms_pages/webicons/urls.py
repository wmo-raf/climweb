from django.urls import path

from .views import chooser, webicons, multiple

app_name = 'webicons'

urlpatterns = [
    path('', webicons.index, name='index'),
    path('<int:pk>/', webicons.edit, name='edit'),
    path('<int:pk>/delete/', webicons.delete, name='delete'),
    path('add/', webicons.add, name='add'),

    path('multiple/add/', multiple.add, name='add_multiple'),
    path('multiple/<int:pk>/', multiple.edit, name='edit_multiple'),
    path('multiple/<int:pk>/delete/', multiple.delete, name='delete_multiple'),

    path('chooser/', chooser.chooser, name='chooser'),
    path('chooser/<int:pk>/', chooser.icon_chosen, name='icon_chosen'),
    path('chooser/upload/', chooser.chooser_upload, name='chooser_upload'),
]
