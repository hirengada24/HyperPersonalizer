from django.urls import re_path as url
from django.contrib import admin
from . import views

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^$', views.button),
    # url(r'^output', views.output, name="script"),
    url(r'^external', views.external),
    url(r'^index', views.index),
    url(r'^buttonresult', views.buttonresult),
    # url(r'^my_view', views.my_view),
]
