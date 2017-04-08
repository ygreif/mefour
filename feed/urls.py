from django.conf.urls import url

import views

urlpatterns = [
    url(r'^$', views.IndexPageView.as_view(), name='index'),
]
