from django.conf.urls import url
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'leaf_receipt'

urlpatterns = [

    path('leaf/receipt/list/', views.LeafManagementListView.as_view(), name='leaf_list'),

    path('leaf/receipt/create/',
        views.LeafManagementCreateView.as_view(), name='leaf_create'),    

     url(r'^leaf/receipt/edit/(?P<id>[-\w]+)/$', views.LeafManagementUpdateView.as_view(),
         name='leaf_edit'),  
    url(r'^leaf/receipt/view/(?P<id>[-\w]+)/$', views.leaf_management_view,
         name='leaf_view'),      



    url('leaf/receipt/load-supply-date/', views.load_supply_date, name="load_supply_date"),






    # # Delete Chemical

    url(r'^leaf/receipt/delete/(?P<id>[-\w]+)/$',
        views.leaf_management_delete, name='leaf_delete'), 

        
    # # ### search Chemical data
    # url(r'^lea/receipt/search/',
    #     views.leaf_management_search, name='leaf_search'),





]