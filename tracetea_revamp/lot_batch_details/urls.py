
"""
Tea Production Urls (URLs)
"""

from django.conf.urls import url
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'lot_batch_details'

urlpatterns = [
    url(r'^lot-batch/list/', views.LotBatchListView.as_view(), name='lot_batch_list'),
    url(r'^lot-batch/create/', views.LotBatchCreateView.as_view(),
         name='lot_batch_create'), 

    url(r'^lot-batch/edit/(?P<lot_batch_pk>\d+)/$',
        views.LotBatchUpdateView.as_view(), name='lot_batch_update'),

    url(r'^lot-batch/delete/(?P<lot_batch_pk>\d+)/delete/$',
        views.LotBatchDeleteView, name='lot_batch_delete'),

    url(r'^lot-batch/details/(?P<lot_batch_pk>\d+)/$',
        views.lot_batch_details, name='lot_batch_details'),


]