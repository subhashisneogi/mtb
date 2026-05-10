from django.conf.urls import url
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'easy_weight_master'


urlpatterns = [




    
 



    # path('export/easy-weight/', views.ExportEasyWeightTemplate, name='export_easy_weight'),  
    path('bulk-import/easy-weight/', views.BulkImportEasyWeight, name='bulk_import_easy_weight'),
    path('download/easy-weight/', views.DownloadEasyWeightTemplate, name='download_easy_weight'),  

    path('export/easy-weight/', views.export_easy_weight_data, name='export_easy_weight_data'),  


  
  
 
  
   
]