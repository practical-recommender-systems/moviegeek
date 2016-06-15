"""prs_project URL Configuration"""
from django.conf.urls import url, include
from django.contrib import admin
from moviegeeks import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^movies/', include('moviegeeks.urls')),
    url(r'^collect/', include('collector.urls')),
    url(r'^analytics/', include('analytics.urls')),
    url(r'^admin/', admin.site.urls),
    url(r'^rec/', include('recommender.urls'))
]
