from django.conf.urls import url, include
from recommender import views

urlpatterns = [
    url(r'^chart/', views.chart, name='chart'),
    url(r'^association_rule/(?P<content_id>\w+)/$',
        views.get_association_rules_for,
        name='get_association_rules_for'),
]
