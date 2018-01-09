from django.conf.urls import url
from analytics import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^user/(?P<user_id>\d+)/$', views.user, name='user'),
    url(r'^content/(?P<content_id>\d+)/$', views.content, name='content'),
     url(r'^cluster/(?P<cluster_id>\d+)/$', views.cluster, name='cluster'),
    url(r'^api/get_statistics', views.get_statistics, name='get statistics'),
	url(r'^api/events_on_conversions', views.events_on_conversions, name='events_on_conversions'),
    url(r'^api/ratings_distribution', views.ratings_distribution, name='ratings_distribution'),
	url(r'^api/top_content', views.top_content, name='top_content'),
    url(r'^api/clusters', views.clusters, name='clusters'),
    url(r'^lda', views.lda, name='lda'),
    url(r'^similarity', views.similarity_graph, name='similarity_graph'),
]