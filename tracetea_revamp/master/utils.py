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
import urllib.parse


import collections
from dateutil.relativedelta import relativedelta
from leaf_receipt.models import LeafManagement, LeafCollection
from user_profile.blf_api_models import SupplierExit
from django.db.models import Sum, Value, Count, Avg, Case, When, F, FloatField, CharField
from django.db.models.functions import Coalesce
from datetime import datetime, date

from invoicing.models import *

class GrowerProfileResource(resources.ModelResource):
    class Meta:
        model = GrowerProfile
        # model2= Gardens
        # model = list(chain(GrowerProfile ,Gardens))
        exclude = ('id','user','email','profile_type','created_by','is_verify','updated_by',\
                   'id_proof_type','id_proof_file','associated_unit','otp',\
                   'photo','is_active','is_deleted','created_at','updated_at',\
                    'certificate_no','postoffice','pincode','voter_id','aadhar_no','id_proof_type',\
                        'trustea_id','existing_trust_tea_id','father_name','tea_board_id','additional_information')
        
    def export(self, queryset = None, *args, **kwargs):
      
        # queryset=Gardens.objects.all().prefetch_related('grower')
        # print(queryset)
        queryset = GrowerProfile.objects.all()[0:0]
        return super().export(queryset, *args, **kwargs)

class AggregatorProfileResource(resources.ModelResource):
    class Meta:
        model = AggregatorProfile
        exclude = ('id','user','email','profile_type','created_by','updated_by','aggregator_type',\
                   'user_file','is_active','is_deleted','created_at','updated_at','trustea_id','gstin_no',\
                    'address','is_verify','otp','associated_aggregator')
    def export(self, queryset = None, *args, **kwargs):
      

        queryset = AggregatorProfile.objects.all()[0:0]
        return super().export(queryset, *args, **kwargs)    
    
class RegionResource(resources.ModelResource):
    class Meta:
        model = Region
        fields = ('region_id', 'region_name')
    def export(self, queryset = None, *args, **kwargs):
      

        queryset = Region.objects.filter(is_deleted=False).order_by('region_name')
        return super().export(queryset, *args, **kwargs) 
  
class StateResource(resources.ModelResource):
    class Meta:
        model = State
        fields = ('state_id', 'name')
        # ordering = ('state_id', 'name')
    def export(self, queryset = None, *args, **kwargs):
      

        queryset = State.objects.filter(is_deleted=False).order_by('name')
        return super().export(queryset, *args, **kwargs) 
class DistrictResource(resources.ModelResource):
    class Meta:
        model = District
        fields = ('district_id', 'name')
    def export(self, queryset = None, *args, **kwargs):
      

        queryset = District.objects.filter(is_deleted=False).order_by('name')
        return super().export(queryset, *args, **kwargs)  
        
# get from API 
def get_entity_list_from_api():
    reqUrl = "https://trusteacms.in/api/v2/entity-list"
    headersList = {
        "Accept": "*/*",
        "User-Agent": "Thunder Client (https://www.thunderclient.com)" 
    }
    payload = ""
    response = requests.request("GET", reqUrl, data=payload,  headers=headersList)
    dict_response = json.loads(str(response.text))

    result = []
    for i in dict_response['data']:
        result.append(i)

    return result



def get_unit_list_from_api():

    reqUrl = "https://trusteacms.in/api/v2/unit-list"

    headersList = {
        "Accept": "*/*",
        "User-Agent": "Thunder Client (https://www.thunderclient.com)" 
    }

    payload = ""

    response = requests.request("POST", reqUrl, data=payload,  headers=headersList)
    dict_response = json.loads(str(response.text))
    
    unit_list = []
    for i in dict_response['data']:
        unit_list.append(i)

    return unit_list

# GET UNIT DETAILS FROM ENTITY LIST

def get_unit_list_details_from_api(user_id):

    reqUrl = "https://trusteacms.in/api/v2/unit-list"

    headersList = {
    "Accept": "*/*",
    "User-Agent": "Thunder Client (https://www.thunderclient.com)",
    "Content-Type": "application/json" 
    }

    payload = json.dumps({"en_id": int(user_id)})

    response = requests.request("POST", reqUrl, data=payload,  headers=headersList)

    response_dict = json.loads(response.text)

    print(response_dict)

    reponse_data = response_dict.get('data', None)[0]

    name = reponse_data.get('name', None)

    return name



# GET ENTITY DETAILS FROM UNIT LIST

def get_entity_list_details_from_api(user_id):

    reqUrl = "https://trusteacms.in/api/v2/entity-list"

    headersList = {
        "Accept": "*/*",
        "User-Agent": "Thunder Client (https://www.thunderclient.com)",
        "Content-Type": "application/json" 
    }

    payload = json.dumps({"unit_id": int(user_id)})

    response = requests.request("POST", reqUrl, data=payload,  headers=headersList)

    response_dict = json.loads(response.text)
    print(response_dict)
    reponse_data = response_dict.get('data', None)[0]
    name = reponse_data.get('name', None)
    return name



# FOR DASHBOARD
months = [
    "January", "February", "March", "April",
    "May", "June", "July", "August",
    "September", "October", "November", "December"
]

def get_year_dict():
    year_dict = dict()

    for month in months:
        year_dict[month] = 0

    return year_dict




# ADMIN BAR CHART GRAPH

def get_monthly_total_supply_qty_dict(year, region):
    """"
    Utility Functions to track leafmanagement and supplyexit combined for bar graph presentations
    """
    results = collections.OrderedDict()

    start_date = date(year, 1, 1)
    end_date = date(year, 12, 31)

    region_id = region

    supplier_inventory_results = LeafCollection.objects.filter(
        supply_date__gte=start_date,
        supply_date__lte=end_date
    ).annotate(
        real_total=Case(When(nt_wght__isnull=True, then=0), default=F('nt_wght'), output_field=CharField())
    ).filter(
        Q(aggregator__region_id=region_id) | Q(grower__region_id=region_id)
    )

    date_cursor = start_date

    tot_net_weight = 0
    
    while date_cursor < end_date:
  
        total_supply_qty = supplier_inventory_results.filter(supply_date__month=date_cursor.month, supply_date__year=date_cursor.year).aggregate(
            partial_total=Coalesce(Sum('real_total'), Value(0), output_field=FloatField()))['partial_total']
        
        total_monthly_qty =  total_supply_qty

        tot_net_weight += total_monthly_qty

        results[(date_cursor.month, date_cursor.year)] = [total_monthly_qty]

        date_cursor += relativedelta(months=1)

    results = results.items()

    return results, tot_net_weight



# ENTITY WISE SUPPLY COLLECTION BAR CHART

def get_monthly_total_supply_entity_wise_qty_dict(year, user_id):
    """"
    Utility Functions to track supplycollection for bar graph presentations
    """
    results = collections.OrderedDict()

    start_date = date(year, 1, 1)
    end_date = date(year, 12, 31)

    supplier_inventory_results = LeafCollection.objects.filter(created_by_id=user_id,
        supply_date__gte=start_date,
        supply_date__lte=end_date
    ).annotate(
        real_total=Case(When(nt_wght__isnull=True, then=0), default=F('nt_wght'), output_field=CharField())
    )

    print("Supply Leaf Collection ###", supplier_inventory_results)
    
    date_cursor = start_date
    tot_net_weight = 0
    while date_cursor < end_date:
  
        total_supply_qty = supplier_inventory_results.filter(supply_date__month=date_cursor.month, supply_date__year=date_cursor.year).aggregate(
            partial_total=Coalesce(Sum('real_total'), Value(0), output_field=FloatField()))['partial_total']
        
        total_monthly_qty =  total_supply_qty

        tot_net_weight += total_monthly_qty

        results[(date_cursor.month, date_cursor.year)] = [total_monthly_qty]

        date_cursor += relativedelta(months=1)

    results = results.items()

    return results, tot_net_weight



# ENTY WISE INVOICE GRAPH FOR ADMIN
def get_monthly_total_invoice_entity_dict(year, user_id):
    """"
    Utility Functions to track Total generate invoice for bar graph presentations
    """
    results = collections.OrderedDict()

    start_date = date(year, 1, 1)
    end_date = date(year, 12, 31)

    date_cursor = start_date

    tot_invoice = 0

    while date_cursor < end_date:
        total_invoice_qty = Invoice.cmobjects.filter(created_by_id=user_id, invoice_date__month=date_cursor.month, invoice_date__year=date_cursor.year).aggregate(
        partial_total=Coalesce(Count('id'), Value(0)))['partial_total']

        tot_invoice += total_invoice_qty

        results[(date_cursor.month, date_cursor.year)] = [total_invoice_qty]
        
        date_cursor += relativedelta(months=1)

    results = results.items()

    print(tot_invoice)
    
    return results, tot_invoice




def get_monthly_total_qty_dict(year, user_id):
    """"
    Utility Functions to track leafmanagement and supplyexit combined for bar graph presentations
    """
    results = collections.OrderedDict()

    start_date = date(year, 1, 1)
    end_date = date(year, 12, 31)

    # leaf_inventory_results = LeafManagement.objects.filter(created_by_id=user_id, supply_date__gte=start_date, \
    #                                                        supply_date__lte=end_date).annotate(
    #                                                         real_total=Case(When(\
    #                                                              net_leaf_weight__isnull=True, then=0), \
    #                                                                 default=F('net_leaf_weight'), output_field=FloatField()))
    
    # supplier_inventory_results = SupplierExit.cmobjects.filter(created_by_id=user_id, \
    #                                                              date_of_supply__gte=start_date, \
    #                                                                 date_of_supply__lte=end_date).annotate(
    #                                                                     real_total=Case(When(\
    #                                                                         net_supplied_qty__isnull=True, then=0), \
    #                                                                             default=F('net_supplied_qty'), output_field=FloatField()))
    


    supplier_inventory_results = LeafCollection.objects.filter(created_by_id=user_id,
                                        supply_date__gte=start_date,
                                        supply_date__lte=end_date,).annotate(
                                                                        real_total=Case(When(\
                                                                            nt_wght__isnull=True, then=0), \
                                                                                default=F('nt_wght'), output_field=FloatField()))


    date_cursor = start_date

    tot_net_weight = 0
    
    while date_cursor < end_date:
         
        # total_leaf_qty = leaf_inventory_results.filter(supply_date__month=date_cursor.month, supply_date__year=date_cursor.year).aggregate(
        # partial_total=Coalesce(Sum('real_total'), Value(0), output_field=FloatField()))['partial_total']
         
        total_supply_qty = supplier_inventory_results.filter(supply_date__month=date_cursor.month, supply_date__year=date_cursor.year).aggregate(
            partial_total=Coalesce(Sum('real_total'), Value(0), output_field=FloatField()))['partial_total']
        
        total_monthly_qty =  total_supply_qty

        tot_net_weight += total_monthly_qty

        results[(date_cursor.month, date_cursor.year)] = [total_monthly_qty]

        date_cursor += relativedelta(months=1)

    results = results.items()
    tot_net_weight = round(tot_net_weight, 2)
    return results, tot_net_weight


def get_monthly_total_invoice_dict(year, user_id):
    """"
    Utility Functions to track Total generate invoice for bar graph presentations
    """
    results = collections.OrderedDict()

    start_date = date(year, 1, 1)
    end_date = date(year, 12, 31)

    date_cursor = start_date

    tot_invoice = 0

    while date_cursor < end_date:
        total_invoice_qty = Invoice.cmobjects.filter(created_by_id=user_id, invoice_date__month=date_cursor.month, invoice_date__year=date_cursor.year).aggregate(
        partial_total=Coalesce(Count('id'), Value(0)))['partial_total']

        tot_invoice += total_invoice_qty

        results[(date_cursor.month, date_cursor.year)] = [total_invoice_qty]
        
        date_cursor += relativedelta(months=1)

    results = results.items()

    return results, tot_invoice



def send_sms_back(numbers,message,template_id):
    url = 'https://api.textlocal.in/send/'
    
    data = {
        'apiKey': "NjgzODRkNGUzMjM0NjQ3OTQ1NTU0ZTQ0NDQ3MDY0NjI=",
        # 'apiKey':"APTbofVzkgw-wDiEyUEQsqbgBexBuzlFRA3GxoFVJL",
        'sender': "TRACET",
        'template_id': template_id,
        'numbers': numbers,
        'message': message,
    }

    try:
        headers = {'Content-type': 'application/x-www-form-urlencoded'}
        # Encode the data
        encoded_data = urllib.parse.urlencode(data)
        
        response = requests.post(url, data=encoded_data, headers=headers)
        response_data = response.json()
        print(response_data)

        if response_data.get('status') == 'success':
            return {'message': 'SMS sent successfully'}
        else:
            return {'message': 'Failed to send SMS. Error: {}'.format(response_data.get('errors'))}
    except requests.RequestException as e:
        print(str(e))
        return {'message': 'Failed to send SMS. Error: {}'.format(str(e))}

import requests
import urllib.parse
def send_sms(numbers, message, template_id):
    base_url = 'https://www.textguru.in/api/v22.0/'
    username = 'trustea.org'   
    password = '14278267'   

    if isinstance(numbers, list):
        numbers = ','.join(str(n).lstrip('+').replace(' ', '') for n in numbers)
    else:
        numbers = str(numbers).lstrip('+').replace(' ', '')
    params = {
        'username': username,
        'password': password,
        'dlttempid': template_id,
        'dmobile': numbers,
        'source': 'TRACET',  
        'message': message
    }
    try:
        response = requests.get(base_url, params=params, timeout=10)
        response_text = response.text.strip()
        if 'success' in response_text.lower() or 'sent' in response_text.lower():
            return {'message': 'SMS sent successfully'}
        # if 'success' in response_text.lower() or 'sent' in response_text.lower():
        #     return {'message': 'SMS sent successfully', 'details': response_text}
        # else:
        #     return {'message': 'Failed to send SMS', 'error': response_text}
        
    except requests.RequestException as e:
        error_msg = str(e)
        print("Request error:", error_msg)
        return {'message': 'Failed to send SMS due to network error', 'error': error_msg}
    
def model_to_json_payload(model_class):
    """
    Generate a JSON payload template for a given Django model class.
    Excludes auto fields and common base fields.
    """
    exclude_fields = {"id", "created_at", "updated_at", "created_by", "updated_by", "is_deleted", "is_verify"}
    payload = {}
    for field in model_class._meta.get_fields():
        if field.auto_created and not field.concrete:
            continue
        if field.name in exclude_fields:
            continue
        if isinstance(field, models.ForeignKey):
            payload[field.name] = 1
        elif isinstance(field, models.CharField):
            payload[field.name] = ""
        elif isinstance(field, models.IntegerField):
            payload[field.name] = ""
        elif isinstance(field, models.FloatField):
            payload[field.name] = "0.0"
        elif isinstance(field, models.BooleanField):
            payload[field.name] = False
        else:
            payload[field.name] = None
    return payload
