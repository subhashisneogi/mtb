"""
Urls
"""
from django.conf.urls import url
from . import views

app_name = 'packaging'

urlpatterns = [
    url(r'^packaging/list/', views.PackagingListView.as_view(), name='packaging_list'),
    url(r'^packaging/create/', views.PackagingCreateView.as_view(),
         name='packaging_create'), 
    url(r'^packaging/edit/(?P<packaging_pk>\d+)/$',
        views.PackagingUpdateView.as_view(), name='packaging_update'),
    url(r'^packaging/delete/(?P<packaging_pk>\d+)/delete/$',
        views.packaging_delete, name='packaging_delete'),

    # url(r'^packaging/details/(?P<packaging_pk>\d+)/$',
    #     views.packaging_view, name='packaging_details'),

    # url(r'^packaging/load_range/$',
    #     views.load_range, name='load_range'),



]


