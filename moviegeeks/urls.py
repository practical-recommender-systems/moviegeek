from django.conf.urls import url

from moviegeeks import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^movie/(?P<movie_id>\d+)/$', views.detail, name='detail'),
    url(r'^genre/(?P<genre_id>[\w-]+)/$', views.genre, name='genre'),
    url(r'^search/$', views.search_for_movie, name='search_for_movie'),
]
