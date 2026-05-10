
"""
Tea Production Urls (URLs)
"""

from django.conf.urls import url
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'collection_center'

urlpatterns = [
    url(r'^collection-center/list/', views.CollectionCenterListView.as_view(), name='collection_center_list'),
    url(r'^collection-center/create/', views.CollectionCenterCreateView.as_view(),
         name='collection_center_create'), 
    url(r'^collection-center/edit/(?P<collection_center_pk>\d+)/$',
        views.CollectionCenterUpdateView.as_view(), name='collection_center_update'),

    url(r'^collection-center/delete/(?P<collection_center_pk>\d+)/delete/$',
        views.CollectionCenterDeleteView, name='collection_center_delete'),

    # url(r'^collection-center/search/',
    #     views.search_tea_collection_center, name='search_tea_collection_center'),    

    url(r'^collection-center/details/(?P<collection_center_pk>\d+)/$',
        views.collection_center_details, name='collection_center_details'),


    
    
        # url(r'^blf/profile/collection-center/$',
    #     views.BlfCollectionCenterCreate.as_view(), name='blf_collection_center_create'),

]