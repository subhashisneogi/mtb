
"""
weighment_supply Urls (URLs)
"""
from django.conf.urls import url
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'weighment_supply'

urlpatterns = [
    url(r'^weighment/list/', views.WeighmentSupplyListView.as_view(), name='weighment_list'),
    url(r'^weighment/supply/create/profile/$',
        views.WeighmentSupplyCreateProfile.as_view(), name='weighment_create_profile'),
    url('weighment/supply/load-supply-date/', views.weighment_load_supply_date, name="weighment_load_supply_date"),
    url('weighment/supply/load-gross-leaf/', views.weighment_load_supply_gross_leaf, name="weighment_load_supply_gross_leaf"),
    
    url(r'^weighment/supply/challan/$',
        views.load_challan, name='load_challan'),
    url(r'^weighment/get/agg/supplier/$',
        views.load_suppliers, name='blf_supplier'),

    url(r'^weighment/get/grower/supplier/$',
        views.grower_supplier, name='grower_supplier'),
    url(r'^weighment/supply/add/(?P<supplier_type>[\w-]+)/(?P<supplier_id>[\w-]+)/(?P<challan_id>[\w-]+)/$',
        views.weighment_supply_add, name='weighment_add'), 
    url(r'^weighment/edit/(?P<weighment_pk>\d+)/(?P<supplier_type>[\w-]+)/(?P<supplier_id>[\w-]+)/(?P<challan_id>[\w-]+)/$',
        views.weighment_supply_edit, name='weighment_update'),
        
    url(r'^weighment/delete/(?P<weighment_pk>\d+)/$',
        views.weighmentsupply_delete, name='weighment_delete'),

    # url(r'^tea-grade/details/(?P<weighment_pk>\d+)/$',
    #     views.grade_details, name='weighment_details'),
    url(r'^challan/details/(?P<challn_pk>\d+)/(?P<item_pk>\d+)/$',
        views.challan_details, name='challan_details'),

    ############### SUPPLIER EXIT ################
    url(r'^supplier_exit/list/', views.SupplierExitListView.as_view(), name='supplier_exit_list'),
    url(r'^supplier_exit/create/', views.SupplierExitCreateView.as_view(), name='supplier_exit_create'),
    url(r'^supplier_exit/edit/(?P<pk>\d+)/', views.SupplierExitUpdateView.as_view(), name='supplier_exit_edit'),
    url(r'^supplier_exit/details/(?P<pk>\d+)/', views.SupplierExitDetailsView.as_view(), name='supplier_exit_details'),
    url(r'^supplier_exit/delete/(?P<pk>\d+)/', views.supplier_exit_delete, name='supplier_exit_delete'),



    ############### REPORTS URLS ###############
    url(r'^reports/leaf-collections-list/', views.leaf_collection_reports, name='lef_collection_reports'),
    url(r'^reports/leaf-collections-register/admin/', views.lef_collection_reports_register_admin, name='lef_collection_reports_register_admin'),
    url(r'^leaf-collections-excel/', views.lef_collection_reports_register_admin_excel, name='lef_collection_reports_xls'),

    


    # REPORTS PDF GENERATE
    url(r'^reports/leaf-collection/supplier-wise/', views.lef_collection_supplier_wise_export, name='lef_collection_supplier_wise_export'),
    





]
