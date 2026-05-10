import requests
import json

from import_export import resources
from .models import *
from user_profile.models import *
from django.contrib.auth import get_user_model
User = get_user_model()
from requests import request
from gardens_managment.models import *
from itertools import chain
from django.db.models import Q
import pandas as pd

class EasyWeightMasterResource(resources.ModelResource):
    class Meta:
        model = EasyWeightMaster
        # model2= Gardens
        # model = list(chain(GrowerProfile ,Gardens))
        # exclude = ('id','user','email','profile_type','created_by','is_verify','updated_by',\
        #            'id_proof_type','id_proof_file','associated_unit','otp',\
        #            'photo','is_active','is_deleted','created_at','updated_at',\
        #             'certificate_no','postoffice','pincode','voter_id','aadhar_no','id_proof_type',\
        #                 'trustea_id','existing_trust_tea_id','father_name','tea_board_id','additional_information')
        
    # def export(self, queryset = None, *args, **kwargs):
      
    #     # queryset=Gardens.objects.all().prefetch_related('grower')
    #     # print(queryset)
    #     queryset = GrowerProfile.objects.all()[0:0]
    #     return super().export(queryset, *args, **kwargs)
class EasyWeightWtResource(resources.ModelResource):
    class Meta:
        model = EasyWeightWt

class CombinedResource(resources.ModelResource):
    class Meta:
        model = EasyWeightMaster
    
    # def export(self,queryset = None, *args, **kwargs)  :
    #     model2_obj=  EasyWeightWt.objects.all()
    #     print(model2_obj)
    #     # row['easy_weight']=model2_obj.easy_weight
    #     row['wt']=model2_obj.wt
    #     return super().export(queryset, *args, **kwargs)