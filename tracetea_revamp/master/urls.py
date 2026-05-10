from django.conf.urls import url
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views


urlpatterns = [
    path('region/list/', views.RegionListView.as_view(), name='region_list'),
    path('region/search/',
        views.RegionSearch, name='region_search'),
    path('region/add/', views.RegionCreateView.as_view(), name='region_add'),    

    url(r'^region/delete/(?P<id>[-\w]+)/$',
        views.RegionDelete, name='region_delete'), 
     url(r'^region/view/(?P<id>[-\w]+)/$', views.RegionView,
         name='region_view'),
     url(r'^region/edit/(?P<id>[-\w]+)/$', views.RegionUpdateView.as_view(),
         name='region_edit'),     
    path('state/view/',
        views.state_view, name='state_view'),  
    # url(r'^state/view/(?P<id>[-\w]+)/$', views.state_view,
    #      name='state_view'),
    # 
    #         
    path('ajax/load-state/', views.load_state, name='ajax_load_state'),
    path('ajax/load-district/', views.load_district, name='ajax_load_district'), 
    # path('ajax/load-entity/', views.load_associated_entity, name='ajax_load_entity'),  
    path('export/region/', views.ExportRegionData, name='export_region'),  
    path('export/state/', views.ExportStateData, name='export_state'),  
    # path('export/data/', views.export_data_to_excel, name='export_data'),  


    path('export/district/', views.ExportDistrictData, name='export_district'),  


    path('export/grower/', views.ExportGrowerTemplate, name='export_grower'),  
    path('bulk-enrollment/grower/', views.BulkEnrollmentGrower, name='bulk_import_grower'),
    
    path('export/aggregator/', views.ExportAggregatorTemplate, name='export_aggregator'),  
    path('bulk-enrollment/aggregator/', views.BulkEnrollmentAggregator, name='bulk_import_aggregator'),
    path('master/list/', views.ViewMasterData, name='master_list'),  
    # url(r'^master/list/(?P<user_type>[-\w]+)/$', views.ViewMasterData,
    #      name='master_list'),  
    #######warehouse #############################
    path('warehouse/list/', views.WarehouseListView.as_view(), name='warehouse_list'),

   
    path('warehouse/create/',
        views.WarehouseCreateView.as_view(), name='warehouse_create'),    





     url(r'^warehouse/edit/(?P<id>[-\w]+)/$', views.WarehouseUpdateView.as_view(),
         name='warehouse_edit'),  
    url(r'^warehouse/view/(?P<id>[-\w]+)/$', views.warehouse_view,
         name='warehouse_view'),      

    # Delete warehouse

    url(r'^warehouse/delete/(?P<id>[-\w]+)/$',
        views.warehouse_delete, name='warehouse_delete'), 
    # ### search warehouse
    url(r'^warehouse-search/',
        views.warehouse_search, name='warehouse_search'),
    # Android Version
    url('api/android-version/', views.AndroidVersionAPIView.as_view()),    
    # TYPE SPEED
    path('type-speed/test/',
        views.typing_speed_view, name='type_speed'),
    path('api-model-to-json-payload/', views.ModelPayloadAPIView.as_view()),   


]