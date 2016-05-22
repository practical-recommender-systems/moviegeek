from django.conf.urls import url, include
from collector import views

urlpatterns = [
    url(r'^log/$', views.log, name='log'),
]


