from django.conf.urls import url, include
from recommender import views

urlpatterns = [
    url(r'^chart/', views.chart, name='chart'),
    url(r'^association_rule/(?P<content_id>\w+)/$',
        views.get_association_rules_for,
        name='get_association_rules_for'),
    url(r'^ar/(?P<user_id>\w+)/$',
        views.recs_using_association_rules,
        name='recs_using_association_rules'),
    url(r'^sim/user/(?P<user_id>\w+)/(?P<type>\w+)/$',
        views.similar_users, name='similar_users'),
    url(r'^cb/item/(?P<content_id>\w+)/$',
        views.similar_content, name='similar_content'),
    url(r'^cb/user/(?P<user_id>\w+)/$',
        views.recs_cb, name='recs_cb'),
]
