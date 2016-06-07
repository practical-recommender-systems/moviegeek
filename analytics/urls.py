from django.conf.urls import url
from analytics import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^user/(?P<user_id>\d+)/$', views.user, name='user'),
    url(r'^content/?P<content_id>/$', views.content, name='content'),
    url(r'^api/get_statistics', views.get_statistics, name='get statistics'),
	url(r'^api/events_on_conversions', views.events_on_conversions, name='events_on_conversions'),
	url(r'^api/top_content_by_eventtype', views.top_content_by_eventtype, name='top_content_by_eventtype'),
	url(r'^api/top_content', views.top_content, name='top_content'),
	url(r'^api/user_evidence/(?P<userid>[a-zA-Z0-9]+)', views.user_evidence, name='user_evidence')
]