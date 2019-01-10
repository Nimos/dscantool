from django.conf.urls import include, url
from dscan import views

app_name = 'dscan'

urlpatterns = [
    url(r'^$', views.landing, name="landing"),
    url(r'^parse', views.parse, name="parse"),
    url(r'^about', views.about, name="about"),
    url(r'^(?P<token>.*)$', views.show, name="show")
]