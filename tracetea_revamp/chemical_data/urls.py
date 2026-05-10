from django.conf.urls import url
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views, farm_diary_views

app_name = 'chemical_data'

urlpatterns = [
    path('fertilizer/list/', views.FertilizerListView.as_view(), name='fertilizer_list'),
    path('chemical/list/', views.ChemicalListView.as_view(), name='chemical_list'),
    # path('chemical/list/',
    #     views.chemical_list, name='chemical_list'),
    path('chemical/create/',
        views.ChemicalCreateView.as_view(), name='chemical_create'),    
    # profile create urls 
    url(r'^chemical/edit/(?P<id>[-\w]+)/$', views.ChemicalDataUpdateView.as_view(),
         name='chemical_edit'),  
    url(r'^chemical/view/(?P<id>[-\w]+)/$', views.chemical_view,
         name='chemical_view'),      
    # Delete Chemical
    url(r'^chemical/delete/(?P<id>[-\w]+)/$',
        views.chemical_delete, name='chemical_delete'), 
    url(r'^chemcial/delete/(?P<id>[-\w]+)/$',
        views.chemical_delete, name='chemical_delete_old'), 
    # ### search Chemical data
    url(r'^chemical-search/',
        views.chemical_search, name='chemical_search'),
######### STG FARM DIARY URLS ###########
    url(r'^stg/farm/diary/user/list/',
        farm_diary_views.farmdiary_user_list, name='farmdiary_user_list'),
    url(r'^stg/farm/diary/chemical/type/list/(?P<grower_pk>[-\w]+)/',
        farm_diary_views.chemical_type_list, name='chemical_type_list'),
    url(r'^stg/farm/diary/download/available/(?P<grower_pk>[-\w]+)/',
        farm_diary_views.farm_diary_download_available, name='farm_diary_download_available'),

    # url(r'^stg/farm/diary/chemical/type/list/(?P<grower_pk>[-\w]+)/',
    #     farm_diary_views.chemical_type_list, name='chemical_type_list'),

    # url(r'^stg/farm/diary/use-of-chemicals/list/(?P<grower_pk>[-\w]+)/(?P<chemical_type>[-\w]+)/',
    #     farm_diary_views.UseOfChemicalListView.as_view(), name='use_of_chemical_list'),
    url(r'^stg/farm/diary/use-of-chemical/list/(?P<grower_pk>[-\w]+)/(?P<chemical_type>[-\w]+)/',
        farm_diary_views.chemical_view_list, name='chemical_view_list'),
    url(r'^stg/farm/diary/record/(?P<record_type>[-\w]+)/(?P<pk>[-\w]+)/',
        farm_diary_views.farm_diary_record_detail, name='farm_diary_record_detail'),
    url(r'^stg/farm/diary/use-of-chemical/search/',
        farm_diary_views.use_of_chemical_search, name='use_of_chemical_search'),
    url(r'^stg/farm/diary/use-of-chemical/create/(?P<grower_pk>[-\w]+)/(?P<chemical_type>[-\w]+)/',
        farm_diary_views.UseOfChemicalCreateView.as_view(), name='chemical_view_create'),
    url(r'^stg/farm/diary/use-of-chemical/edit/(?P<grower_pk>[-\w]+)/(?P<use_of_chemical_pk>[-\w]+)/',
        farm_diary_views.UseOfChemicalUpdateView.as_view(), name='use_of_chemical_edit'),
    url(r'^stg/farm/diary/associated/grower/search/',
        farm_diary_views.search_as_gr_list, name='farmdiary_user_list_search'),
    url(r'^stg/farm/diary/use-of-chemical/delete/(?P<grower_pk>[-\w]+)/(?P<use_of_chemical_pk>[-\w]+)/',
        farm_diary_views.use_of_chemical_delete, name='use_of_chemical_delete'),
    # Plucking DATA
    url(r'^stg/farm/diary/plucking/data/list/(?P<grower_pk>[-\w]+)/',
        farm_diary_views.farmdiary_plucking_data_list, name='plucking_data_view_list'),
    url(r'^stg/farm/diary/plucking/data/create/(?P<grower_pk>[-\w]+)/',
        farm_diary_views.PluckingDataCreateView.as_view(), name='plucking_data_view_create'),
    url(r'^stg/farm/diary/plucking/data/edit/(?P<grower_pk>[-\w]+)/(?P<plucking_data_pk>[-\w]+)/',
        farm_diary_views.PluckingDataUpdateView.as_view(), name='plucking_data_view_edit'),
    url(r'^stg/farm/diary/plucking/data/delete/(?P<plucking_data_pk>[-\w]+)/',
        farm_diary_views.plucking_data_delete, name='plucking_data_delete'),
    url(r'^stg/farm/diary/plucking/data/search/',
        farm_diary_views.plucking_data_search, name='plucking_data_search'),
    # Labour List DATA FarmDIary
    url(r'^stg/farm/diary/labour/list/(?P<grower_pk>[-\w]+)/',
        farm_diary_views.farmdiary_labour_list, name='farmdiary_labour_list'),
    url(r'^stg/farm/diary/labour/create/(?P<grower_pk>[-\w]+)/',
        farm_diary_views.LabourDataCreateView.as_view(), name='farmdiary_labour_create'),
    url(r'^stg/farm/diary/labour/edit/(?P<grower_pk>[-\w]+)/(?P<labour_pk>[-\w]+)/',
        farm_diary_views.LabourDataUpdateView.as_view(), name='farmdiary_labour_edit'),
    url(r'^stg/farm/diary/labour/data/search/',
        farm_diary_views.labour_data_search, name='labour_data_search'),
    url(r'^stg/farm/diary/labour/data/delete/(?P<labour_data_pk>[-\w]+)/',
        farm_diary_views.labour_data_delete, name='labour_data_delete'),
    # Monthly Schedule of Work	
    url(r'^stg/farm/diary/monthly/shedule/work/list/(?P<grower_pk>[-\w]+)/',
        farm_diary_views.farmdiary_monthly_shedule_list, name='farmdiary_monthly_shedule_list'),
    url(r'^stg/farm/diary/monthly/shedule/work/create/(?P<grower_pk>[-\w]+)/',
        farm_diary_views.MonthlyScheduleCreateView.as_view(), name='farmdiary_monthly_shedule_create'),
    url(r'^stg/farm/diary/monthly/shedule/work/edit/(?P<grower_pk>[-\w]+)/(?P<monthly_shedule_pk>[-\w]+)/',
        farm_diary_views.MonthlyScheduleUpdateView.as_view(), name='farmdiary_monthly_shedule_edit'),
    url(r'^stg/farm/diary/monthly/shedule/delete/(?P<pk>[-\w]+)/',
        farm_diary_views.monthly_schedule_data_delete, name='monthly_schedule_data_delete'),
    url(r'^stg/farm/diary/monthly/shedule/search/',
        farm_diary_views.monthly_schedule_data_search, name='monthly_schedule_data_search'),
    # PDF URL
    path('use-of-chemical-generate_pdf/', farm_diary_views.use_of_chemical_pdf_reports, name='use_of_chemical_pdf_reports'),
    path('plucking-data-generate-pdf/', farm_diary_views.plucking_data_generate_pdf, name='generate_plucking_data_pdf'),
    path('labour-generate-pdf/', farm_diary_views.generate_labour_pdf, name='generate_labour_pdf'),
    
    path('grower/farm-diary/pdf/', farm_diary_views.grower_farmdiary_pdf, name='grower_farmdiary_pdf'),
    # Farm Diary Pdf Downlaod
    path('stg/farm-diary/pdf/generate/<int:grower_id>/', farm_diary_views.stg_farm_diary_pdf_generate,\
             name='stg_farm_diary_pdf_generate'),

    # for APP
    path('save-image/<int:grower_id>/', farm_diary_views.save_image, name='save_image'),
    path('api/save-image/', farm_diary_views.SaveMapImageAPI.as_view()),

    ######  Add Google Map #########
    url(r'^farmer/farm-diary/map/create/(?P<grower_pk>[-\w]+)/',
        farm_diary_views.farm_diary_map_create, name='farm_diary_map_create'),
    url(r'^farmer/farm-diary/mannual/map/create/(?P<grower_pk>[-\w]+)/',
        farm_diary_views.farm_diary_mannual_map_create, name='farm_diary_mannual_map_create'),
    url(r'^farmer/farm-diary/mannual/map/edit/(?P<grower_pk>[-\w]+)/',
        farm_diary_views.farm_diary_manual_map_edit, name='farm_diary_mannual_map_edit'),
    url(r'^stg/farm-diary-add-map/(?P<grower_pk>[-\w]+)/(?P<map_area>[-\w]+)',
        farm_diary_views.farm_diary_add_map, name='farm_diary_add_map'),    
    url(r'^stg/farm-diary-edit-map/(?P<grower_pk>[-\w]+)/(?P<map_area>[-\w]+)/',
        farm_diary_views.farm_diary_edit_map, name='farm_diary_edit_map'),
    url(r'^stg/farm-diary-edit-map-text/data/(?P<grower_pk>[-\w]+)/(?P<map_area>[-\w]+)/',
        farm_diary_views.farm_diary_edit_map_text_data, name='farm_diary_edit_map_text_data'),
    url(r'^farm-diary/farmers-aggreements-forms-list/(?P<grower_pk>[-\w]+)/',
        farm_diary_views.farmers_aggreements_forms_list, name='farmers_aggreements_forms_list'),
    url(r'^farm-diary/farmers-aggreements/farmers-signature/(?P<grower_pk>[-\w]+)',
        views.farmers_aggreements_forms_details, name='farmers_aggreements_forms_details'),
    url(r'^farm-diary/farmers-aggreements/blf-signature/(?P<grower_pk>[-\w]+)',
        views.farmers_aggreements_blf_signature, name='farmers_aggreements_blf_signature'),
    url(r'^farm-diary/upload-farmers-signature/',
        views.uplaod_farmers_signature, name='uplaod_farmers_signature'),
    url(r'^farm-diary/upload-blf-signature/',
        views.uplaod_blf_signature_upload, name='uplaod_blf_signature'),
    url(r'^farm-diary/edit-farmers-signature/',
        views.edit_farmers_signature, name='edit_farmers_signature'),
    url(r'^farm-diary/farmers-aggreements/form/downlaod/(?P<grower_pk>[-\w]+)/(?P<id>[-\w]+)',
        views.farmers_aggreements_form_view, name='farmers_aggreements_form_view'),
    url(r'^farm-diary/ajax/form-aggreement-date/',
        views.aggreements_form_date, name='aggreements_form_date'),
    # Farmer Final Map HTML
    url(r'^farmers/map-area-total-pdf/(?P<grower_pk>[-\w]+)/',
        views.farmers_map_area_total_pdf, name='farmers_map_area_total_pdf'),
    url(r'^farm-diary/farmers_agreement_pdf_generate/(?P<grower_pk>[-\w]+)/(?P<form_id>[-\w]+)', views.farmers_agreement_pdf_generate, name="farmers_agreement_pdf_generate"),
    url(r'^farm-diary/pdf/generate/(?P<grower_pk>[-\w]+)/', views.farm_diary_pdf_generate, name="farm_diary_pdf_generate"),
    url(r'^map-area/pdf/screenshot/', views.map_area_take_screenshot, name="map_area_take_screenshot"),
    
    
    ###### Map data API url###
    path('api/map-area-image-details-apis/', farm_diary_views.MapAreaImageUploadAPIView.as_view(), name='map_area_image_details_api'),
    
    path('api/map_area_details/', farm_diary_views.MapAreaDetailsAPIView.as_view(), name='map_area_details_api'),
    path('api/grower/map-area-details-view/', farm_diary_views.GrowerMapAreaDetailsAPIView.as_view()),
    

    path('api/map-area-details/<int:grower_id>/<str:area_type>/', farm_diary_views.grower_map_area_details_api_view, name='grower_map_area_details_api_view'),
    path('api/total/map-area-details/<int:grower_id>/<str:area_type>/', farm_diary_views.grower_map_area_details_total_api_view, name='grower_map_area_details_total_api_view'),
    path('farm-diary/form-pdf-download/', views.FarmersAgreementPDFAPIView.as_view()),
    path('api/upload/farmer/signature/', farm_diary_views.FarmersAggreementFormsUploadView.as_view()),
    # mobile app map template url
    path('farm-diary/mobile-app-map-template/', views.mobile_app_map_template),
    path('farm-diary/digiatl-signature/upload/', views.digital_signature_app_template),
    #Revamp NEW API URLS
    path('farm-diary/chemical-type/', views.FarmDiaryChemicalTypeAPIView.as_view()),
    path('farm-diary/chemical-data/', views.FarmDiaryChemicalDataAPIView.as_view()),
    path('farm-diary/use-of-chemical/', views.FarmDiaryUseOfChemicalAPIView.as_view()),
    # NEW REVAMAP
    path('farmers-aggreement-master/', farm_diary_views.FarmersAggreementMasterAPIView.as_view()),
    path('farmers-aggreement-form/', farm_diary_views.FarmersAggreementFormsAPIView.as_view()),

    path('map_area_name_master/', farm_diary_views.MapAreaNameMasterAPIView.as_view(), name='map_area_name_master'),
    path('map-area-detail/', farm_diary_views.MapAreaDetailsAPIView.as_view(), name='map_area_details_api'),
    
    path('monthly-shedule-generate-pdf/', farm_diary_views.MOnthlyShedulePdfGenerateAPIView.as_view()),    
    # path('farm-dairy-pdf/', farm_diary_views.stg_farm_diary_pdf_generate_app),
    path('farm-dairy-pdf/',farm_diary_views.GenerateFarmDiaryPdfAPIView.as_view()),

    
]   
