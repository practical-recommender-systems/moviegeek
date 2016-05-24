from django.conf.urls import url, include
from django.contrib import admin
from moviegeeks import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^movie/(?P<movie_id>\d+)/$', views.detail, name='detail'),
    url(r'^genre/(?P<genre_id>\w+)/$', views.genre, name='genre'),
]
