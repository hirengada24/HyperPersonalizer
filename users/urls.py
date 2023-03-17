from django.urls import re_path as url
from django.contrib import admin
from . import views

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^button', views.button),
    url(r'^$', views.base1),
    url(r'^external', views.external),
    url(r'^logout', views.logout),
    url(r'^hyper', views.hyper),
    # url(r'^index', views.index),
    url(r'^register', views.register),
]
