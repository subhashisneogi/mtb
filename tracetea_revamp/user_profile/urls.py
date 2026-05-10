
"""
Profiles Urls (URLs)
"""

from django.conf.urls import url
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views, api_views
from user_profile.aggregator_api_views import *
from user_profile.blf_api_views import *
from user_profile.grower_api_views import *
app_name = 'user_profile'

urlpatterns = [
	# url(r'^all-user/list/(?P<usertype_slug>[\w-]+)/$', views.ProfileListView.as_view(), name='all_users'),
    url(r'^user-list/(?P<usertype_slug>[\w-]+)/$', views.users_list, name='all_users'),
    url(r'^user/list/(?P<usertype_slug>[\w-]+)/$', views.EstateUserList.as_view(), name='estate_user_list'),
    url(r'^user/create/(?P<usertype_slug>[\w-]+)/$', views.user_create, name='user_create'),
    path('user/create/validate-fields/ajax/', views.validate_user_create_fields, name='validate_user_create_fields'),
    # AJAX URLS FOR GROWER FORM
    path('blf/list/region/wise/ajax/', views.blf_list_region_wise, name='blf_list_region_wise'),
    path('aggregators/list/blf/wise/ajax/', views.aggregator_list_blf_wise, name='aggregator_list_blf_wise'),
    #  Grower profile urls 
    url(r'^grower/profile/create/(?P<user_create_pk>[-\w]+)/$', views.GrowerCreateView.as_view(),
         name='grower_profile_create'),  
    url(r'^grower/profile/edit/(?P<user_create_pk>[-\w]+)/$', views.update_profile,
         name='grower_profile_edit'),
    # BLF PROFILE
    url(r'^blf/profile/update/(?P<user_create_pk>[\w-]+)/$',
        views.BlfProfileUpdateView.as_view(), name='blf_profile_create'),
    url(r'^blf/profile/view/(?P<user_create_pk>[\w-]+)/$',
        views.BlfProfileDetailView.as_view(), name='blf_profile_view'),
    # Estate Profile
    url(r'^estate/profile/create/(?P<user_create_pk>[\w-]+)/$',
        views.EstateCreateView.as_view(), name='estate_profile_create'),
    url(r'^estate/profile/edit/(?P<user_create_pk>[\w-]+)/$',
        views.EstateProfileUpdateView.as_view(), name='estate_profile_edit'),
    url(r'^estate/trough/create/(?P<user_create_pk>[\w-]+)/$',
        views.EstateTroughCreate.as_view(), name='estate_trough_details_create'),
    url(r'^estate/trough/edit/(?P<user_create_pk>[\w-]+)/(?P<factory_pk>[\w-]+)/$',
        views.EstateTroughUpdate.as_view(), name='estate_trough_details_update'),
    url(r'^estate/trough/list/(?P<user_create_pk>[\w-]+)/$',
    views.EstateTroughList.as_view(), name='estate_trough_details_list'),
    url(r'^estate/trough/details/(?P<user_create_pk>[\w-]+)/(?P<factory_pk>[\w-]+)/$',
        views.estate_factory_trough_details, name='estate_factory_trough_details'),
    url(r'^estate/trough/delete/(?P<user_create_pk>[\w-]+)/(?P<factory_pk>[\w-]+)/$',
        views.estate_factory_delete, name='estate_factory_delete'),
    # Aggregator Profile
    url(r'^user/aggregator/list/(?P<usertype_slug>[\w-]+)/$', views.aggregator_list, name='aggregator_list'),
    url(r'^aggregator/profile/create/(?P<user_create_pk>[\w-]+)/$',
    views.AggregatorProfileUpdateView.as_view(), name='aggregator_profile_create'),
    url(r'^advisory/profile/create/(?P<user_create_pk>[-\w]+)/$', views.AdvisoryProfileUpdateView.as_view(),
        name='advisory_profile_create'), 
    url(r'^consignee/profile/create/(?P<user_create_pk>[-\w]+)/$', views.ConsigneeProfileUpdateView.as_view(),
        name='consignee_profile_create'),      
    url(r'^shg/profile/create/(?P<user_create_pk>[-\w]+)/$', views.ShgProfileUpdateView.as_view(),
        name='shg_profile_create'),   
    # profile update urls 
     url(r'^advisory/profile/edit/(?P<user_create_pk>[-\w]+)/$', views.AdvisoryProfileUpdateView.as_view(),
         name='advisory_profile_edit'), 
     url(r'^consignee/profile/edit/(?P<user_create_pk>[-\w]+)/$', views.ConsigneeProfileUpdateView.as_view(),
         name='consignee_profile_edit'),      
     url(r'^shg/profile/edit/(?P<user_create_pk>[-\w]+)/$', views.ShgProfileUpdateView.as_view(),
         name='shg_profile_edit'),    
     url(r'^aggregator/profile/edit/(?P<user_create_pk>[\w-]+)/$',
        views.AggregatorProfileUpdateView.as_view(), name='aggregator_profile_edit'),
     url(r'^blf/profile/edit/(?P<user_create_pk>[\w-]+)/$',
        views.BlfProfileUpdateView.as_view(), name='blf_profile_edit'),
    # Delete User Profile
    url(r'^user/profile/view/(?P<user_create_pk>[\w-]+)/(?P<user_type>[\w-]+)$',
        views.profile_detail, name='user_profile_view'), 
    url(r'^user/profile/delete/(?P<user_create_pk>[\w-]+)/(?P<user_type>[\w-]+)$',
        views.delete_profile, name='user_profile_delete'), 
    ### search user profile
    url(r'^user-search/',
        views.search_profile, name='user_profile_search'),
    url(r'^user/profile/activate/(?P<user_create_pk>[\w-]+)/(?P<user_type>[\w-]+)$',
        views.user_profile_active, name='user_profile_active'), 
    url(r'^user/profile/deactivate/(?P<user_create_pk>[\w-]+)/(?P<user_type>[\w-]+)$',
        views.user_profile_deactive, name='user_profile_deactive'), 
    # API urls
    url(r'^api/entity/list/$', views.get_entity_list_view, name='entity_details_api'), 
    url(r'^ajax/entity/unit/list/$', views.ajax_entity_unit_list, name='ajax_entity_unit_list'), 
    path('ajax/unit/details/', views.unit_details, name='unit_details'),
    path('ajax/entity/details/', views.entity_details, name='entity_details'),
    # path('factory/mark/create/', views.create_factory_marks, name='create_factory_marks'),
    url(r'^profile/edit/(?P<user_create_pk>[\w-]+)/$',
        views.ProfileUpdateView.as_view(), name='profile_edit'),
    url(r'^profile/qr/code/$',
        views.ProfileUpdateView.as_view(), name='profile_edit'),
    url(r'^grower/profile/qr/code/(?P<grower_pk>[\w-]+)$',
        views.grower_qr_code, name='grower_qr_code'),
    url(r'^aggregator/profile/qr/code/(?P<aggragator_pk>[\w-]+)$',
        views.aggregator_qr_code, name='aggregator_qr_code'),
    url(r'^grower/profile/visiting/card/(?P<grower_pk>[\w-]+)$',
        views.GrowerVistingCard, name='grower_visting_card'),
    url(r'^aggregator/profile/visiting/card/(?P<aggregator_pk>[\w-]+)$',
        views.AggregatorVistingCard, name='aggregator_visting_card'),    
    url(r'^visiting/card/download/(?P<user_pk>[\w-]+)/(?P<user_type>[\w-]+)$',
        views.DownloadVistingCard, name='visting_card_download'),    
    path('visiting-card-pdf/', views.DownloadVistingCardPDF.as_view(),), 
    ## api url##
    path('visiting-card-url/', views.VisitingCardGenerateWebAPIViewUrl.as_view(),), #visiting card web view 
    path('visiting-card-web-view/<str:user_type>/<int:id>', views.VistingCardWebView.as_view(), name='visiting_card_web'),
    path('grower-list-aggregator/', GrowerProfileListAPIView.as_view()),#grower profile list api for aggregator app
    path('plot-list-aggregator/',PlotListAPIView.as_view()),#plot list associated with grower API
    path('vehicle-available-aggregator/',VehicleAvailableListAPIView.as_view()),#vehicle available list
    path('collection-from-grower/',CollectionFromGrowerAPIView.as_view()),#collection from grower  API in aggregator app
    path('labour-details/',LabourAPIView.as_view()),#Labour API in aggregator app
    path('fertilizer-list-aggregator/',FertilizerListAPIView.as_view()),#Fetilizer list  API
    path('herbicides-list-aggregator/',HerbicidesListAPIView.as_view()),#Herbicides list API
    path('insecticides-list-aggregator/',InsecticidesListAPIView.as_view()),#Insecticides List API
    path('acaricides-list-aggregator/',AcaricidesListAPIView.as_view()),#acaricides list API
    path('use-of-chemical-aggregator/',UseOfChemicalAPIView.as_view()),#Use of chemical i.e fertilizer, herbicides etc API
    path('plucking-data/',PluckingDataAPIView.as_view()),# Plucking Data API 
    path('collection-details_vehicle-grower/',CollectionDetailsVehicleAPIView.as_view()),
    path('region-master/',RegionAPIView.as_view()),
    path('state-list/',StateAPIView.as_view()),
    path('district-list/',DistrictAPIView.as_view()),
    path('aggregator-list-api/',AggregatorListAPIView.as_view()),
    path('aggregator-map-api/',AggregatorMappedAPIView.as_view()),
    path('blf-list-api/',BlfListAPIView.as_view()),
    path('blf-map-api/',BlfMappedAPIView.as_view()),
    
    path('collection-from-aggregator/',CollectionFromAggregatorAPIView.as_view()),
    path('supply-book-aggregator/',SupplyAndEarnBookAPIView.as_view()),
    path('total-collection-aggregator/',TotalCollectionAndSupplyAPIView.as_view()),
    path('division-list-aggregator/',DivisonListAggregatorAPIView.as_view()),
    path('supply-report-aggregator/',SupplyReportListAggregatorAPIView.as_view()),
    path('khata-book-aggregator/',KhataBookAggregatorAPIView.as_view()),
    ### BLF APP API ###
    path('grower-list-blf/', BlfGrowerProfileListAPIView.as_view()),#grower profile list api for blf app
    path('aggregator-list-blf/', BlfAggregatorProfileListAPIView.as_view()),#aggregator profile list api for blf app
    path('weighment-supply-blf/', WeighmentSupplyAPIView.as_view()),
    path('delivery-challan-blf/', DeliveryChallanListAPIView.as_view()),
    path('available_weightment-list-blf/', WeighmentSupplyAvailableTxnIdAPIView.as_view()),#weighment txn id for leaf receipt
    path('weightment-list-supply-exit-blf/', WeighmentTxnIdSupplyExitListAPIView.as_view()),#weighment txn id for supplier exit
    path('leaf-receipt-blf/', LeafReceiptAPIView.as_view()),#leaf receipt blf app
    path('supplier-exit-blf/', SupplierExitAPIView.as_view()),#supplier exit blf app    

    ### Grower APP API###
    path('supply-factory-grower/', SupplyToFactoryGrowerAPIView.as_view()),#supply to factory from grower
    
    path('all-blf-list-grower/', BlfListGrowerAPIView.as_view()),#all list of blf to be map with grower 
    path('all-aggregator-list-grower/', AggregatorListGrowerAPIView.as_view()),#all list of Aggregator to be map with grower 
    path('year-list-grower/', YearGrowerAPIView.as_view()),#year list for monthly schedule of work
    path('blf-map-grower/', BlfManagementGrowerAPIView.as_view()),#blf map with grower
    path('aggregator-map-grower/', AggregatorManagementGrowerAPIView.as_view()),#aggrgator map with grower
    path('chemical-report-grower/', ChemicalRegisterReportAPIView.as_view()),#chemical register report
    path('plot-list-grower/', PlotListGrowerAPIView.as_view()),#plot list for use of chemical and plucking data
    path('total-supply-grower/',TotalSupplyGrowerAPIView.as_view()),#total supply by grower
    path('labour-list-grower/',LabourGrowerAPIView.as_view()),
    path('use-of-chemical-grower/',UseOfChemicalGrowerAPIView.as_view()),#chemical list according to specific grower
    path('division-list-grower/',DivisionListGrowerAPIView.as_view()),#division list grower
    path('supply-report-grower/',SupplyReportListGrowerAPIView.as_view()),

    
    ########### PDF generate API url #################
    path('challan-pdf-download/',GenerateChallanPdfAPIView.as_view()),
    
    path('labour-pdf-download/',GenerateLabourListPdfAPIView.as_view()),
    path('monthly-wages-pdf-download/',GenerateMonthlySchedulePdfAPIView.as_view()),
    
    path('supply-report-pdf/',GenerateSupplyReportPdfAPIView.as_view()),
    path('supply-earn-report-pdf/',GenerateSupplyEarnReportPdfAPIView.as_view()),


    path('supply-report-grower-pdf/',GenerateSupplyReportGrowerPdfAPIView.as_view()),
    

    path('khata-book-aggregator-pdf/',GenerateKhataBookPdfAPIView.as_view()),
    
    ######## Profile Update ###################
    path('profile-update-all/',ProfileUpdateAPIView.as_view()),
    path('mobile-number-update/',MobileNumberUpdateAPIView.as_view()),
    # Tea grade dependent ajax
    url(r'^blf-tea-grade-ajax/$', views.blf_tea_grade_ajax, name='blf_tea_grade_ajax'),
    ############### REPORTS URLS ###############
    url(r'^reports/supply-management/$', views.supply_management_report, name='supply_management_report'),
    url(r'^reports/supply-management/details/(?P<id>[\w-]+)/$', views.supply_management_report_detail, name='supply_management_report_detail'),
    url(r'^reports/aggregator_register_list_blf/', views.aggregator_register_list_blf_report, name='aggregator_register_reports'),
    path('reports/aggregator_register/pdf/', views.report_aggregator_register_pdf, name='report_aggregator_register_pdf'),
    path('reports/aggregator_register/excel/', views.report_aggregator_register_excel, name='report_aggregator_register_excel'),
    url(r'^reports/grower_register_list_blf/', views.grower_register_list_blf_report, name='grower_register_reports'),## grower register report 
    path('reports/grower_register/excel/', views.report_grower_register_excel, name='report_grower_register_excel'),
    url(r'^reports/entity_register_list/', views.entity_register_list_blf_report, name='entity_register_list'),
    path('region/list/mode/wise/ajax/', views.region_list_easy_mode_wise, name='region_list_easy_mode_wise'),
    path('grower-username-generate-api/',GenerateGrowerUsernameAPIView.as_view()),
    path('grower-user-import-api/',ImportGrowerExcelView.as_view()),
    path('grower-user-import-old-api/',ImportGrowerExcelViewBack.as_view()),
    path('agg-username-generate-api/',GenerateAggUsernameAPIView.as_view()),
    path('agg-user-import-api/', ImportAggregatorView.as_view()),

    ## Revamp NEW API URLS
    path('user-profile-main/', views.UserProfileMainAPIView.as_view()),
    path('user-profile/', views.UserProfileAPIView.as_view()),
    path('blf-list-associated-grower/', BlfMappedGrowerAPIView.as_view()),
    
    path('farm-diary-labour/', api_views.FarmDiaryLabourAPIView.as_view()),
    path('farm-diary-plucking-data/', api_views.FarmDiaryPluckingDataAPIView.as_view()),

    # path('farm-diary-labour/', api_views.FarmDiaryLabourAPIView.as_view()),
    # validate users
    path('tcms-users-profile-validate/', views.ValidateTcmsBlfUsers.as_view()),
    path('tcms-supplier-profile-validate/', views.ValidateTcmsSupplierUsers.as_view()),
    path('monthly-schedule-work/', MonthlyScheduleGrowerAPIView.as_view()),
    # supply management
    path('supply-management/',SupplyManagementAPIView.as_view()),
    #Revamap Url 

    path('users-profile-list/<str:usertype_slug>/', views.users_profile_list, name='users_profile_list'),
    path('grower-profile-all-update/', views.GrowerProfileALLUpdateAPIView.as_view()),
    path('suuplly-report-pdf-generate/',SupplyReportPdfGenerateAPIView.as_view()),
    path('use-of-chemical-pdf-download/',GenerateUseOfChemicalListPdfAPIView.as_view()),

    # path('farm-dairy-pdf/',GenerateConsolidatedFarmDiaryPdfAPIView.as_view()),
    path('plucking-pdf-download/',GeneratePluckingDataPdfAPIView.as_view()),

    
]
