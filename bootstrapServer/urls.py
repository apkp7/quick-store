from django.urls import path

from . import views

urlpatterns = [
    path('<hostIp>', views.index, name='index'),
]
