import collections
import dateutil
import datetime
from types import SimpleNamespace
from uuid import uuid4
from datetime import datetime, date
import csv
from datetime import date, timedelta
from rest_framework.response import Response

from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import JsonResponse
from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.template.loader import render_to_string
from django.views.decorators.cache import cache_page
from django.db.models import Sum, Value, Count, Avg, Case, When, F, Q
from django.db.models.functions import Coalesce
from django.utils.http import url_has_allowed_host_and_scheme
from master.common import CommonMixin
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView, DeleteView
from rest_framework.decorators  import api_view, permission_classes, authentication_classes
from .models import *
from .forms import *
from .serializers import *
import pandas as pd
from django.db import transaction
import numpy as np
import datetime




from master.decorators import *
from leaf_receipt.models import *
from user_profile.blf_api_models import SupplierExit
from user_profile.grower_api_models import *
from user_profile.helpers import soft_delete_instance_for_web

from django.db.models import FloatField

from django.db.models.functions import ExtractYear, ExtractMonth
from django.db.models import Count, F, Sum, Avg

from chemical_data.models import *

from .utils import months,  get_year_dict


def daterange(start, end, step=1):
    current_year = start
    while current_year <= end:
        yield current_year
        current_year += step


def is_ajax_request(request):
    return request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'


def get_safe_next_url(request, default_url):
    next_url = request.GET.get('next') or request.POST.get('next')
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        return next_url
    return default_url




def landing_page(request):
    """ Landing page view """

    if request.user.is_authenticated:
        return redirect(reverse('index'))

    region_list = Region.cmobjects.all()
    # grower_count = BlfProfile.cmobjects.filter().aggregate(
    #                 partial_total=Coalesce(Count('id'), Value(0)))['partial_total']
    
    # BLF
    west_bengal_blf_count = BlfProfile.cmobjects.filter(region_id=4).aggregate(
                    partial_total=Coalesce(Count('id'), Value(0)))['partial_total']

    south_india_blf_count = BlfProfile.cmobjects.filter(region_id=5).aggregate(
                    partial_total=Coalesce(Count('id'), Value(0)))['partial_total']
    
    assam_blf_count = BlfProfile.cmobjects.filter(region_id=6).aggregate(
                    partial_total=Coalesce(Count('id'), Value(0)))['partial_total']

    north_east_blf_count = BlfProfile.cmobjects.filter(region_id=7).aggregate(
                    partial_total=Coalesce(Count('id'), Value(0)))['partial_total']
    

    # STG
    west_bengal_stg_count = GrowerProfile.cmobjects.filter(region_id=4).aggregate(
                    partial_total=Coalesce(Count('id'), Value(0)))['partial_total']
    
    south_india_stg_count = GrowerProfile.cmobjects.filter(region_id=5).aggregate(
                    partial_total=Coalesce(Count('id'), Value(0)))['partial_total']
    
    assam_stg_count = GrowerProfile.cmobjects.filter(region_id=6).aggregate(
                    partial_total=Coalesce(Count('id'), Value(0)))['partial_total']

    north_east_stg_count = GrowerProfile.cmobjects.filter(region_id=7).aggregate(
                    partial_total=Coalesce(Count('id'), Value(0)))['partial_total']


    # AGGREGATOR

    west_bengal_agg_count = AggregatorProfile.cmobjects.filter(region_id=4).aggregate(
                    partial_total=Coalesce(Count('id'), Value(0)))['partial_total']
    
    south_india_agg_count = AggregatorProfile.cmobjects.filter(region_id=5).aggregate(
                    partial_total=Coalesce(Count('id'), Value(0)))['partial_total']
    
    assam_agg_count = AggregatorProfile.cmobjects.filter(region_id=6).aggregate(
                    partial_total=Coalesce(Count('id'), Value(0)))['partial_total']

    north_east_agg_count = AggregatorProfile.cmobjects.filter(region_id=7).aggregate(
                    partial_total=Coalesce(Count('id'), Value(0)))['partial_total']

    # farmer
    # west_bengal_farmers_count = GrowerProfile.cmobjects.filter(grower_type__in=['STG', 'LTG']).aggregate(
    #                 partial_total=Coalesce(Count('id'), Value(0)))['partial_total']
    # south_india_farmers_count = GrowerProfile.cmobjects.filter(grower_type__in=['STG', 'LTG']).aggregate(
    #                 partial_total=Coalesce(Count('id'), Value(0)))['partial_total']
    # assam_farmers_count = GrowerProfile.cmobjects.filter(grower_type__in=['STG', 'LTG']).aggregate(
    #                 partial_total=Coalesce(Count('id'), Value(0)))['partial_total']
    # north_east_farmers_count = GrowerProfile.cmobjects.filter(grower_type__in=['STG', 'LTG']).aggregate(
    #                 partial_total=Coalesce(Count('id'), Value(0)))['partial_total']
    

    #use Of chemical
    west_bengal_farmers_useof_chemical = UseOfChemical.cmobjects.filter(grower__region_id=4).aggregate(
                    partial_total=Coalesce(Count('id'), Value(0)))['partial_total']
    south_india_farmers_useof_chemical = UseOfChemical.cmobjects.filter(grower__region_id=5).aggregate(
                    partial_total=Coalesce(Count('id'), Value(0)))['partial_total']
    assam_farmers_useof_chemical = UseOfChemical.cmobjects.filter(grower__region_id=6).aggregate(
                    partial_total=Coalesce(Count('id'), Value(0)))['partial_total']
    north_east_farmers_useof_chemical = UseOfChemical.cmobjects.filter(grower__region_id=7).aggregate(
                    partial_total=Coalesce(Count('id'), Value(0)))['partial_total']
    
    #plucking Data
    west_bengal_farmers_plucking = PluckingData.cmobjects.filter(grower__region_id=4).aggregate(
                    partial_total=Coalesce(Count('id'), Value(0)))['partial_total']
    south_india_farmers_plucking = PluckingData.cmobjects.filter(grower__region_id=5).aggregate(
                    partial_total=Coalesce(Count('id'), Value(0)))['partial_total']
    assam_farmers_plucking = PluckingData.cmobjects.filter(grower__region_id=6).aggregate(
                    partial_total=Coalesce(Count('id'), Value(0)))['partial_total']
    north_east_farmers_plucking = PluckingData.cmobjects.filter(grower__region_id=7).aggregate(
                    partial_total=Coalesce(Count('id'), Value(0)))['partial_total']


    #Labours Data
    west_bengal_farmers_labour = Labour.cmobjects.filter(grower__region_id=4).aggregate(
                    partial_total=Coalesce(Count('id'), Value(0)))['partial_total']
    south_india_farmers_labour = Labour.cmobjects.filter(grower__region_id=5).aggregate(
                    partial_total=Coalesce(Count('id'), Value(0)))['partial_total']
    assam_farmers_labour = Labour.cmobjects.filter(grower__region_id=6).aggregate(
                    partial_total=Coalesce(Count('id'), Value(0)))['partial_total']
    north_east_farmers_labour= Labour.cmobjects.filter(grower__region_id=7).aggregate(
                    partial_total=Coalesce(Count('id'), Value(0)))['partial_total']


    #Monthly Schedule Data
    west_bengal_farmers_monthly = MonthlySchedule.cmobjects.filter(grower__region_id=4).aggregate(
                    partial_total=Coalesce(Count('id'), Value(0)))['partial_total']
    south_india_farmers_monthly = MonthlySchedule.cmobjects.filter(grower__region_id=5).aggregate(
                    partial_total=Coalesce(Count('id'), Value(0)))['partial_total']
    assam_farmers_monthly = MonthlySchedule.cmobjects.filter(grower__region_id=6).aggregate(
                    partial_total=Coalesce(Count('id'), Value(0)))['partial_total']
    north_east_farmers_monthly = MonthlySchedule.cmobjects.filter(grower__region_id=7).aggregate(
                    partial_total=Coalesce(Count('id'), Value(0)))['partial_total']

    wb_total_farm_diary = west_bengal_farmers_useof_chemical + west_bengal_farmers_plucking + west_bengal_farmers_labour + west_bengal_farmers_monthly
   
    print("wb_total_farm_diary", wb_total_farm_diary)
   
    si_total_farm_diary = south_india_farmers_useof_chemical + south_india_farmers_plucking + south_india_farmers_labour + south_india_farmers_monthly
    assam_total_farm_diary = assam_farmers_useof_chemical + assam_farmers_plucking + assam_farmers_labour + assam_farmers_monthly
    north_east_total_farm_diary = north_east_farmers_useof_chemical + north_east_farmers_plucking + north_east_farmers_labour + north_east_farmers_monthly


    context ={
        "region_list" : region_list,

        "west_bengal_blf_count" : west_bengal_blf_count,
        "south_india_blf_count" : south_india_blf_count,
        "assam_blf_count" : assam_blf_count,
        "north_east_blf_count" : north_east_blf_count,

        "west_bengal_stg_count" : west_bengal_stg_count,
        "south_india_stg_count" : south_india_stg_count,
        "assam_stg_count" : assam_stg_count,
        "north_east_stg_count" : north_east_stg_count,

        "west_bengal_agg_count" : west_bengal_agg_count,
        "south_india_agg_count" : south_india_agg_count,
        "assam_agg_count" : assam_agg_count,
        "north_east_agg_count" : north_east_agg_count,

        "wb_total_farm_diary" : wb_total_farm_diary,
        "si_total_farm_diary" : si_total_farm_diary,
        "assam_total_farm_diary" : assam_total_farm_diary,
        "north_east_total_farm_diary" : north_east_total_farm_diary,

        # "west_bengal_farmers_count" : west_bengal_farmers_count,
        # "south_india_farmers_count" : south_india_farmers_count,
        # "assam_farmers_count" : assam_farmers_count,
        # "north_east_farmers_count" : north_east_farmers_count,
    }

    return render(request, 'landing_page.html', context)



# @cache_page(60 * 15)
@login_required
# @user_type_required(user_type='blf')s
def index(request):
    """
    Index Dashboard View View
    """
    logged_user_type = Profile.objects.filter(user_id=request.user.id).first()
    user_type = logged_user_type.user_type

    todays_date = date.today()
    year = todays_date.year

    results = get_monthly_total_qty_dict(year, request.user.id)[0]
    tot_net_weight = get_monthly_total_qty_dict(year, request.user.id)[1]

    invoice_result = get_monthly_total_invoice_dict(int(year), request.user.id)[0]
    tot_invoice = get_monthly_total_invoice_dict(int(year), request.user.id)[1]


    year = []
    for i in range(2022, todays_date.year+1):
        year.append(i)

    # if not request.user.id == 1:

    if not request.user.is_superuser and str(user_type.name) == "blf":
        user_blf_account_details = request.user.profile_id_blf
        grower_male_count = user_blf_account_details.grower_associated_entity.filter(gender='Male', grower_type="STG").aggregate(
                partial_total=Coalesce(Count('id'), Value(0)))['partial_total']
        grower_female_count = user_blf_account_details.grower_associated_entity.filter(gender='Female', grower_type="STG").aggregate(
                partial_total=Coalesce(Count('id'), Value(0)))['partial_total']
        
        grower_other_count = user_blf_account_details.grower_associated_entity.filter(gender='Other', grower_type="STG").aggregate(
                partial_total=Coalesce(Count('id'), Value(0)))['partial_total']
        
        tot_stg_growers = grower_male_count + grower_female_count + grower_other_count

        # Aggregator

        total_growers = user_blf_account_details.grower_associated_entity.all().aggregate(
                partial_total=Coalesce(Count('id'), Value(0)))['partial_total']
        
        total_aggegators = AggregatorProfile.cmobjects.filter(associated_entity=user_blf_account_details).aggregate(
                        partial_total=Coalesce(Count('id'), Value(0)))['partial_total']

        tot_growers_agg = total_growers + total_aggegators


    else:
        grower_male_count = ""
        grower_female_count = ""
        grower_other_count = ""
        tot_net_weight =""
        tot_stg_growers = ""
        total_aggegators = ""
        tot_growers_agg =""
        total_growers = ""

    #### ADMIN DASHBOARD
    region_list = Region.cmobjects.all()
    
    # BLF
    west_bengal_blf_count = BlfProfile.cmobjects.filter(region_id=4, is_active=True).aggregate(
                    partial_total=Coalesce(Count('id'), Value(0)))['partial_total']
    south_india_blf_count = BlfProfile.cmobjects.filter(region_id=5, is_active=True).aggregate(
                    partial_total=Coalesce(Count('id'), Value(0)))['partial_total']
    assam_blf_count = BlfProfile.cmobjects.filter(region_id=6, is_active=True).aggregate(
                    partial_total=Coalesce(Count('id'), Value(0)))['partial_total']
    north_east_blf_count = BlfProfile.cmobjects.filter(region_id=7, is_active=True).aggregate(
                    partial_total=Coalesce(Count('id'), Value(0)))['partial_total']    
    
    others_blf = BlfProfile.cmobjects.filter(region_id__isnull=True, is_active=True).aggregate(
                    partial_total=Coalesce(Count('id'), Value(0)))['partial_total']

    tot_blf = BlfProfile.cmobjects.filter(is_active=True).aggregate(
                    partial_total=Coalesce(Count('id'), Value(0)))['partial_total']
    

    # STG
    west_bengal_stg_count = GrowerProfile.cmobjects.filter(region_id=4, is_active=True).aggregate(
                    partial_total=Coalesce(Count('id'), Value(0)))['partial_total']
    south_india_stg_count = GrowerProfile.cmobjects.filter(region_id=5, is_active=True).aggregate(
                    partial_total=Coalesce(Count('id'), Value(0)))['partial_total']
    assam_stg_count = GrowerProfile.cmobjects.filter(region_id=6, is_active=True).aggregate(
                    partial_total=Coalesce(Count('id'), Value(0)))['partial_total']
    north_east_stg_count = GrowerProfile.cmobjects.filter(region_id=7, is_active=True).aggregate(
                    partial_total=Coalesce(Count('id'), Value(0)))['partial_total']
    others_stg = GrowerProfile.cmobjects.filter(region_id__isnull=True, is_active=True).aggregate(
                    partial_total=Coalesce(Count('id'), Value(0)))['partial_total'] 

    tot_stg = GrowerProfile.cmobjects.filter(is_active=True).aggregate(
                    partial_total=Coalesce(Count('id'), Value(0)))['partial_total']

    # AGGREGATOR
    west_bengal_agg_count = AggregatorProfile.cmobjects.filter(region_id=4, is_active=True).aggregate(
                    partial_total=Coalesce(Count('id'), Value(0)))['partial_total']
    south_india_agg_count = AggregatorProfile.cmobjects.filter(region_id=5, is_active=True).aggregate(
                    partial_total=Coalesce(Count('id'), Value(0)))['partial_total']
    assam_agg_count = AggregatorProfile.cmobjects.filter(region_id=6, is_active=True).aggregate(
                    partial_total=Coalesce(Count('id'), Value(0)))['partial_total']
    north_east_agg_count = AggregatorProfile.cmobjects.filter(region_id=7, is_active=True).aggregate(
                    partial_total=Coalesce(Count('id'), Value(0)))['partial_total']
    
    others_agg = AggregatorProfile.cmobjects.filter(region_id__isnull=True, is_active=True).aggregate(
                    partial_total=Coalesce(Count('id'), Value(0)))['partial_total']     
    tot_agg = AggregatorProfile.cmobjects.filter(is_active=True).aggregate(
                    partial_total=Coalesce(Count('id'), Value(0)))['partial_total']
                    
    # FARM DIARY 

    #use Of chemical
    west_bengal_farmers_useof_chemical = UseOfChemical.cmobjects.filter(grower__region_id=4).aggregate(
                    partial_total=Coalesce(Count('id'), Value(0)))['partial_total']
    south_india_farmers_useof_chemical = UseOfChemical.cmobjects.filter(grower__region_id=5).aggregate(
                    partial_total=Coalesce(Count('id'), Value(0)))['partial_total']
    assam_farmers_useof_chemical = UseOfChemical.cmobjects.filter(grower__region_id=6).aggregate(
                    partial_total=Coalesce(Count('id'), Value(0)))['partial_total']
    north_east_farmers_useof_chemical = UseOfChemical.cmobjects.filter(grower__region_id=7).aggregate(
                    partial_total=Coalesce(Count('id'), Value(0)))['partial_total']
    
    #plucking Data
    west_bengal_farmers_plucking = PluckingData.cmobjects.filter(grower__region_id=4).aggregate(
                    partial_total=Coalesce(Count('id'), Value(0)))['partial_total']
    south_india_farmers_plucking = PluckingData.cmobjects.filter(grower__region_id=5).aggregate(
                    partial_total=Coalesce(Count('id'), Value(0)))['partial_total']
    assam_farmers_plucking = PluckingData.cmobjects.filter(grower__region_id=6).aggregate(
                    partial_total=Coalesce(Count('id'), Value(0)))['partial_total']
    north_east_farmers_plucking = PluckingData.cmobjects.filter(grower__region_id=7).aggregate(
                    partial_total=Coalesce(Count('id'), Value(0)))['partial_total']


    #Labours Data
    west_bengal_farmers_labour = Labour.cmobjects.filter(grower__region_id=4).aggregate(
                    partial_total=Coalesce(Count('id'), Value(0)))['partial_total']
    south_india_farmers_labour = Labour.cmobjects.filter(grower__region_id=5).aggregate(
                    partial_total=Coalesce(Count('id'), Value(0)))['partial_total']
    assam_farmers_labour = Labour.cmobjects.filter(grower__region_id=6).aggregate(
                    partial_total=Coalesce(Count('id'), Value(0)))['partial_total']
    north_east_farmers_labour= Labour.cmobjects.filter(grower__region_id=7).aggregate(
                    partial_total=Coalesce(Count('id'), Value(0)))['partial_total']


    #Monthly Schedule Data
    west_bengal_farmers_monthly = MonthlySchedule.cmobjects.filter(grower__region_id=4).aggregate(
                    partial_total=Coalesce(Count('id'), Value(0)))['partial_total']
    south_india_farmers_monthly = MonthlySchedule.cmobjects.filter(grower__region_id=5).aggregate(
                    partial_total=Coalesce(Count('id'), Value(0)))['partial_total']
    assam_farmers_monthly = MonthlySchedule.cmobjects.filter(grower__region_id=6).aggregate(
                    partial_total=Coalesce(Count('id'), Value(0)))['partial_total']
    north_east_farmers_monthly = MonthlySchedule.cmobjects.filter(grower__region_id=7).aggregate(
                    partial_total=Coalesce(Count('id'), Value(0)))['partial_total']

    wb_total_farm_diary = west_bengal_farmers_useof_chemical + west_bengal_farmers_plucking + west_bengal_farmers_labour + west_bengal_farmers_monthly
   
    # print("wb_total_farm_diary", wb_total_farm_diary)
   
    si_total_farm_diary = south_india_farmers_useof_chemical + south_india_farmers_plucking + south_india_farmers_labour + south_india_farmers_monthly
    assam_total_farm_diary = assam_farmers_useof_chemical + assam_farmers_plucking + assam_farmers_labour + assam_farmers_monthly
    north_east_total_farm_diary = north_east_farmers_useof_chemical + north_east_farmers_plucking + north_east_farmers_labour + north_east_farmers_monthly

    tot_farms = si_total_farm_diary + wb_total_farm_diary + assam_total_farm_diary + north_east_total_farm_diary

    # BAR CHAT for supply collection
    select_year = request.GET.get('select_year', None)
    region = request.GET.get('region', None)

    if request.method == 'GET' and select_year and region:
        graph_select_year = select_year
        results = get_monthly_total_supply_entity_wise_qty_dict(int(select_year), region)[0]
        region_entity_wise_tot_net_weight = get_monthly_total_supply_entity_wise_qty_dict(int(select_year), region)[1]

    else:
         results = get_monthly_total_supply_entity_wise_qty_dict(int(todays_date.year), region)[0]
         region_entity_wise_tot_net_weight = get_monthly_total_supply_entity_wise_qty_dict(int(todays_date.year), region)[1]
         graph_select_year = todays_date.year

    region_entity_wise_tot_net_weight = 0

    # BAR CHAT for supply collection with Entity
    region = request.GET.get('region', None)
    entity_id = request.GET.get('entity_id', None)

    if request.method == 'GET' and select_year and region and entity_id:
        pass

    context = {
            "region_list" : region_list,
            'year' : year,
            'results': results,
            'current_year' : todays_date.year,
            'grower_male_count' : grower_male_count,
            'grower_female_count' : grower_female_count, 
            'grower_other_count' : grower_other_count,
            'tot_net_weight' : tot_net_weight,
            'tot_stg_growers' : tot_stg_growers,
            'total_aggegators' : total_aggegators,
            'tot_growers_agg' : tot_growers_agg,
            'total_growers' : total_growers,
            'invoice_result' : invoice_result,
            'tot_invoice' : tot_invoice,

            "region_list" : region_list,
            # blf region wise
            "west_bengal_blf_count" : west_bengal_blf_count,
            "south_india_blf_count" : south_india_blf_count,
            "assam_blf_count" : assam_blf_count,
            "north_east_blf_count" : north_east_blf_count,
            "tot_blf" : tot_blf,
            "others_blf" : others_blf,
            # stg
            "west_bengal_stg_count" : west_bengal_stg_count,
            "south_india_stg_count" : south_india_stg_count,
            "assam_stg_count" : assam_stg_count,
            "north_east_stg_count" : north_east_stg_count,
            "tot_stg" : tot_stg,
            "others_stg" : others_stg,
            # agg
            "west_bengal_agg_count" : west_bengal_agg_count,
            "south_india_agg_count" : south_india_agg_count,
            "assam_agg_count" : assam_agg_count,
            "north_east_agg_count" : north_east_agg_count,
            "tot_agg" : tot_agg,
            "others_agg" : others_agg,

            # Farm Diary
            "wb_total_farm_diary" : wb_total_farm_diary,
            "si_total_farm_diary" : si_total_farm_diary,
            "assam_total_farm_diary" : assam_total_farm_diary,
            "north_east_total_farm_diary" : north_east_total_farm_diary,
            "tot_farms" : tot_farms,

            # 'year' : year,
            "results" : results,
            "select_year" : select_year,
            "region_entity_wise_tot_net_weight" : region_entity_wise_tot_net_weight,

            "graph_select_year" : graph_select_year,
            
    }

    return CommonMixin.render(request, 'index.html', context)






def dashboard_supply_collection_region_wise_graph(request):
    """
    Supply Collection Graph Region for ADMIN 
    """
    year = request.GET.get('year', None)
    region = request.GET.get('region', None)

    region_details = Region.cmobjects.filter(pk=region).first()

    print(region)
    print(year)

    results = get_monthly_total_supply_qty_dict(int(year), region)[0]
    tot_net_weight = get_monthly_total_supply_qty_dict(int(year), region)[1]

    context = {
        'results': results,
        'tot_net_weight' : tot_net_weight,
        'year' : year,
        "region" : region,
        "region_details" : region_details,
    }
    if request.is_ajax():
        html = render_to_string('suply_collection_region_wise.html',
                                context, request=request)
        
    data = {"html" : html, 'tot_net_weight' : tot_net_weight, 'year' : year}

    return JsonResponse(data)




def dashboard_invoice_entity_wise_graph(request):
    """
     Invoice  Graph Region for ADMIN 
    """
    year = request.GET.get('year', None)
    region = request.GET.get('region', None)
    entity_id = request.GET.get('entity_id', None)

    blf_details = BlfProfile.cmobjects.filter(id=entity_id).first()
    user_details = User.objects.filter(username=blf_details).first()
    user_id = user_details.pk


    print(region)
    print(year)
    print(entity_id)

    results = get_monthly_total_invoice_entity_dict(int(year), user_id)[0]
    tot_invoice = get_monthly_total_invoice_entity_dict(int(year), user_id)[1]

    context = {
        'results': results,
        'tot_invoice' : tot_invoice,
        'year' : year,
        "region" : region,
        "blf_details" : blf_details,
    }
    if request.is_ajax():
        html = render_to_string('invoice_entity_wise_graph.html',
                                context, request=request)
        
    data = {"html" : html, 'tot_invoice' : tot_invoice, 'year' : year}

    return JsonResponse(data)




def dashboard_supply_collection_entity_wise_graph(request):
    """
    Supply Collection Graph for ADMIN 
    """
    year = request.GET.get('year', None)
    region = request.GET.get('region', None)
    entity_id = request.GET.get('entity_id', None)

    blf_details = BlfProfile.cmobjects.filter(id=entity_id).first()
    user_details = User.objects.filter(username=blf_details).first()
    user_id = user_details.pk

    results = get_monthly_total_supply_entity_wise_qty_dict(int(year), user_id)[0]
    tot_net_weight = get_monthly_total_supply_entity_wise_qty_dict(int(year), user_id)[1]
    
    context = {
        'results': results,
        'tot_net_weight' : tot_net_weight,
        'year' : year,
        "blf_details" : blf_details,
    }

    if request.is_ajax():
        html = render_to_string('suply_collection_entity_wise.html',
                                context, request=request)
        
    data = {"html" : html, 'tot_net_weight' : tot_net_weight, 'year' : year}

    return JsonResponse(data)





def dashboard_graph_ajax(request):
    """
    Ajax Request To Update Bar Graph Based on Year
    """
    year = request.GET.get('year', None)

    results = get_monthly_total_qty_dict(int(year), request.user.id)[0]

    usertype_list = ProfileType.objects.exclude(name="ADMIN").order_by('-id')
    blf_details = BlfProfile.objects.filter(user_id=request.user.id).first()
    user_details = Profile.objects.filter(user_id=request.user.id).first()
    logged_user_type = str(user_details.user_type)
    tot_net_weight = get_monthly_total_qty_dict(int(year), request.user.id)[1]

    invoice_result = get_monthly_total_invoice_dict(int(year), request.user.id)[0]

    tot_invoice = get_monthly_total_invoice_dict(int(year), request.user.id)[1]

    context = {
        'results': results,
        'usertype_list': usertype_list,
        'blf_details' : blf_details,
        'logged_user_type': logged_user_type,
        'year' : year,
        'tot_net_weight' : tot_net_weight,
        'invoice_result' : invoice_result,
        'tot_invoice' : tot_invoice,
    }

    if request.is_ajax():
        html = render_to_string('leaf_collection_graph_ajax.html',
                                context, request=request)
        
    data = {"html" : html, 'tot_net_weight' : tot_net_weight, 'tot_invoice' : tot_invoice, 'year' : year}

    return JsonResponse(data)



def dashboard_invoice_graph_ajax(request):
    """
    Ajax Request To Update Bar Graph Based on Year -- Invoice graph
    """
    year = request.GET.get('year', None)
    results = get_monthly_total_qty_dict(int(year), request.user.id)[0]
    usertype_list = ProfileType.objects.exclude(name="ADMIN").order_by('-id')
    blf_details = BlfProfile.objects.filter(user_id=request.user.id).first()
    user_details = Profile.objects.filter(user_id=request.user.id).first()
    logged_user_type = str(user_details.user_type)
    tot_net_weight = get_monthly_total_qty_dict(int(year), request.user.id)[1]

    context = {
        'results': results,
        'usertype_list': usertype_list,
        'blf_details' : blf_details,
        'logged_user_type': logged_user_type,
        'year' : year,
        'tot_net_weight' : tot_net_weight
    }

    if request.is_ajax():
        html = render_to_string('graph_invoice_data.html',
                                context, request=request)
        
    data = {"html" : html, 'tot_net_weight' : tot_net_weight, 'year' : year}

    return JsonResponse(data)













################# Region Render Start ###############################################
# @api_view(['GET','POST'])

class RegionListView(LoginRequiredMixin, CommonMixin, ListView):
    """
    Region List View
    """
    model = Region
    context_object_name = 'region_list'
    template_name = 'master/region_list.html'
    paginate_by = 5

    def get(self, request, *args, **kwargs):
        try:
            if not self.request.user.is_superuser:
                messages.error(self.request, 'You have no permission to access the requested resource!')
                return redirect(reverse('index'))
        except AttributeError as error:
            messages.error(self.request, 'You have no permission to access the requested resource!')
            return redirect(reverse('index'))

        return super().get(request, *args, **kwargs)

    def get_queryset(self, *args, **kwargs):
        query = self.request.GET.get('q', '').strip()
        qs = Region.objects.prefetch_related('state').filter(is_deleted=False)
        if query:
            qs = qs.filter(
                Q(region_name__icontains=query) |
                Q(abbrevation__icontains=query) |
                Q(state__name__icontains=query)
            ).distinct()
        return qs.order_by('-id')
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '').strip()
        context['list_url'] = reverse('region_list')
        context['current_list_url'] = self.request.get_full_path()
        return context

    def render_to_response(self, context, **response_kwargs):
        if is_ajax_request(self.request):
            return render(self.request, 'master/_region_table.html', context)
        return super().render_to_response(context, **response_kwargs)
    



@login_required
def RegionSearch(request):

    if request.method == 'POST':
        """Search Region Trace Tea@vivek"""
        region_name=request.POST.get('region_name')
        region=Region.cmobjects.filter(region_name__icontains=region_name).order_by('-id')
        page = request.GET.get('page',1)  
        paginator = Paginator(region, 3)  ########### implementation of pagination 
        try:
            region_list = paginator.page(page)
        except PageNotAnInteger:
            region_list = paginator.page(1)
        except EmptyPage:
            region_list = paginator.page(paginator.num_pages)
        context = {'region_list':region_list}
    else:
             print("No information to show")
             return CommonMixin.render(request, 'master/region_list.html', {})      
    return CommonMixin.render(request, 'master/region_list.html',context)



class RegionCreateView(LoginRequiredMixin, CreateView, CommonMixin):
    """
    Region Create View
    """
    form_class = RegionForm
    template_name = 'master/region_add.html'

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_success_url(self, **kwargs):
        messages.success(self.request, 'Region Created Successfully')
        return get_safe_next_url(self.request, reverse('region_list'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['next_url'] = get_safe_next_url(self.request, reverse('region_list'))
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

    def form_invalid(self, form):
        error_message = 'Error saving the Form, check fields below.'
        messages.error(self.request, error_message)
        return super().form_invalid(form)



from django.shortcuts import get_object_or_404

class RegionUpdateView(LoginRequiredMixin, CommonMixin, UpdateView):
	"""
	Region Update View @vivek
	"""
	model = Region
	form_class = RegionForm
	template_name = 'master/region_add.html'

	def get(self, request, *args, **kwargs):
	# checking if the user is customer
		try:
			if not self.request.user.is_superuser:
				messages.error(self.request, 'You have no permission to access the requested resource!')
				return redirect(reverse('index'))
		except AttributeError as error:
			messages.error(self.request, 'You have no permission to access the requested resource!')
			return redirect(reverse('index'))

		return super().get(request, *args, **kwargs)

	def get_success_url(self, **kwargs):
		messages.success(self.request, 'Region Updated Successfully')
		return get_safe_next_url(self.request, reverse('region_list'))


	def get_object(self,queryset=None):
		region_details = get_object_or_404(Region, pk=self.kwargs['id'], is_deleted=False)
		return region_details

	def get_context_data(self, **kwargs):
		context = super(RegionUpdateView, self).get_context_data(**kwargs)

		context['region_details'] = self.get_object()
		context['next_url'] = get_safe_next_url(self.request, reverse('region_list'))
		return context
	def form_valid(self, form):
		
		self.id = self.kwargs['id']
		context = self.get_context_data()


		with transaction.atomic():
			self.object = form.save()


		return super(RegionUpdateView, self).form_valid(form)
	


# @login_required

# def RegionDelete(request,id):
#     if request.method == 'POST':
#         """Delete Region Trace Tea@vivek"""
#         # region_id=request.POST.get('region_id')
#         region_select=Region.cmobjects.filter(id=id)
#         region_select.delete()
#         messages.success(request, "Region Deleted")
#         return HttpResponseRedirect(reverse('region_list'))
#     return CommonMixin.render(request, 'master/region_list.html')



@login_required
def RegionDelete(request, id):

    try:
        if not request.user.is_superuser:
            messages.error(request, 'You have no permission to access the requested resource!')
            return redirect(reverse('index'))
    except AttributeError as error:
        messages.error(request, 'You have no permission to access the requested resource!')
        return redirect(reverse('index'))

    region = Region.objects.filter(id=id, is_deleted=False).first()
    return soft_delete_instance_for_web(
        request,
        region,
        get_safe_next_url(request, reverse('region_list')),
        success_message='Region Deleted Successfully',
        not_found_message='Region not found.',
    )


@login_required
def RegionView(request, id):
    region_details = Region.objects.filter(pk=id, is_deleted=False).first()
    context={
        'region_details' : region_details,
        'next_url': get_safe_next_url(request, reverse('region_list')),
     }
    return CommonMixin.render(request, 'master/region_view.html',context)    
	



############### Region Render End####################################

def load_state(request):
    """ load state according to region @vivek"""
    region_id = request.GET.get('region_id')
    states = Region.objects.filter(id=region_id).values('state__name','state__state_id','state__id')
  
    return render(request, 'master/state_dropdown_list_options.html', {'states':states,})

def load_district(request):
    """ load district according to state @vivek"""

    state_id= request.GET.get('state_id')
    state_name = State.objects.filter(id=state_id)
    for data in state_name:
        districts=District.objects.filter(state__name=data.name).values('name','id','district_id')

    return render(request, 'master/district_dropdown_list_options.html', {'districts': districts})

# def load_associated_entity(request):
#     """ load associated_entity according to region @vivek"""

#     region_id= request.GET.get('region_id')
#     entity = AssociatedEntity.objects.filter(region_id=region_id).values('name','id')
#     return render(request, 'master/associated_entity_list_options.html', {'entity': entity})



from .utils import *
# @csrf_exempt

import xlwt
@permission_required_admin

# def export_data_to_excel(request):
#     objs=Region.objects.all()
#     data=[]
     
#     output = BytesIO()
#     for obj in objs:
#         data.append({
#                "region_id":obj.region_id,
#                "region_name":obj.region_name,
#           })
#     df=pd.DataFrame(data).to_excel('out.xlsx')
    
   
def ExportRegionData(request):
    """Export or download template for bulk upload @vivek"""

    if request.method == 'GET':
        # Get selected option from form
        # type=request.GET.get('type')
        # if type=='region':
        master_resource = RegionResource()
        dataset = master_resource.export()
        response = HttpResponse(dataset.xls, content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = 'attachment; filename="region.xls"'
        # if type=='state':
        #     master_resource = MasterResource()
        #     dataset = master_resource.export()
        #     response = HttpResponse(dataset.xls, content_type='application/vnd.ms-excel')
        #     response['Content-Disposition'] = 'attachment; filename="state.xls"'
        # if type=='district':
        #     master_resource = MasterResource()
        #     dataset = master_resource.export() 
        #     response = HttpResponse(dataset.xls, content_type='application/vnd.ms-excel')
        #     response['Content-Disposition'] = 'attachment; filename="district.xls"'   
        
        # response2 = HttpResponse(dataset1.xls, content_type='application/vnd.ms-excel')

        
        # response2['Content-Disposition'] = 'attachment; filename="district.xls"'

        # wb = xlwt.Workbook(encoding='utf-8')
        # ws = wb.add_sheet('Region')
        # wb.save(response)
        return response
def ExportStateData(request):
    """Export or download template for bulk upload @vivek"""

    if request.method == 'GET':
     
        master_resource = StateResource()
        dataset = master_resource.export()
        response = HttpResponse(dataset.xls, content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = 'attachment; filename="state.xls"'
       
        return response    
def ExportDistrictData(request):
    """Export or download template for bulk upload @vivek"""

    if request.method == 'GET':
     
        master_resource = DistrictResource()
        dataset = master_resource.export()
        response = HttpResponse(dataset.xls, content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = 'attachment; filename="district.xls"'
       
        return response   



def ExportGrowerTemplate(request):
    """Export or download template for bulk upload @vivek"""

    if request.method == 'GET':
        # Get selected option from form
    
        grower_resource = GrowerProfileResource()
        # user_resource=user_resource.UserDetails()
        dataset = grower_resource.export()
    
        response = HttpResponse(dataset.xls, content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = 'attachment; filename="grower.xls"'
        return response   
    





@permission_required_admin
def BulkEnrollmentGrower(request):
    "Bulk import grower using the optimized Excel importer."
    if request.method == 'POST':
        uploaded_file = request.FILES.get('file')
        if not uploaded_file:
            messages.error(request, 'Please select a grower Excel file.')
            return CommonMixin.render(request, 'master/export_grower.html', {})

        if not uploaded_file.name.lower().endswith(('.xlsx', '.xls')):
            messages.error(request, 'Please upload a valid Excel file.')
            return CommonMixin.render(request, 'master/export_grower.html', {})

        try:
            from user_profile.grower_api_views import ImportGrowerExcelView

            excel_dir = os.path.join('media', 'excel')
            os.makedirs(excel_dir, exist_ok=True)
            original_name = os.path.basename(uploaded_file.name)
            extension = os.path.splitext(original_name)[1].lower()
            file_name = f"grower_import_{uuid4().hex}{extension}"
            file_path = os.path.join(excel_dir, file_name)

            with open(file_path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)

            importer_request = SimpleNamespace(data={'file_name': file_name})
            response = ImportGrowerExcelView().post(importer_request)
            response_data = getattr(response, 'data', {}) or {}
            count_data = response_data.get('data', {})
            import_errors = response_data.get('errors', [])

            if response_data.get('request_status') != 1:
                messages.error(request, response_data.get('msg', 'Grower import failed.'))
            else:
                messages.success(
                    request,
                    "Grower import completed. Created: {created}, Updated: {updated}, Errors: {errors}.".format(
                        created=count_data.get('items_created', 0),
                        updated=count_data.get('items_updated', 0),
                        errors=count_data.get('errors', 0),
                    )
                )
                for error in import_errors[:10]:
                    messages.warning(request, error)
                if count_data.get('errors', 0) > len(import_errors[:10]):
                    messages.warning(request, 'More import errors exist. Please use the API response for the full returned error list.')
        except Exception as e:
            messages.error(request, f"Grower import failed: {str(e)}")
          
    context={}

    return CommonMixin.render(request, 'master/export_grower.html',context)



@permission_required_admin
def ExportAggregatorTemplate(request):
    """Export or download template for Aggregator bulk upload @vivek"""

    if request.method == 'GET':
        # Get selected option from form
    
        aggregator_resource = AggregatorProfileResource()
        # user_resource=user_resource.UserDetails()
        dataset = aggregator_resource.export()
     
        
        response = HttpResponse(dataset.xls, content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = 'attachment; filename="aggregator.xls"'
        return response   

from django.db import transaction
from django.db.models import Q 

@permission_required_admin
def BulkEnrollmentAggregator(request):
    "Bulk import aggregator @vivek"
    if request.method == 'POST':
        file=request.FILES['file']
        df = pd.read_excel(file)
        columns_in_file = list(df.columns)
        required_columns = ['username', 'password', 'name', 'region', 'state', 'district', 'associated_entity', 'mobile_number']
        # Check if the uploaded file has all the required columns and no extra columns
        if set(columns_in_file) != set(required_columns):
            messages.error(request, 'Uploaded file should contain exactly the required columns of aggregator.')
            return CommonMixin.render(request, 'master/export_aggregator.html', {})
        path = 'media/excel/' + file.name
        if not os.path.exists('media/excel'):
            os.makedirs('media/excel')
        with open(path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)
        df = pd.read_excel(path)
        if df.empty == True:
            messages.error(request,'Empty excel file')
        df=df.replace({np.nan: None})
        successful_upload=0
        try:
            for index, row in df.iterrows(): 
                with transaction.atomic():   
                    # try:     
                        if row['username'] is None:
                             messages.error(request,'Username is not be blank ,Please enter Username in excel')
                        elif row['password'] is None:
                             messages.error(request,'Passwordd is not be blank,Please enter Password in excel')
                        elif User.objects.filter(username=row['username']).exists():
                            messages.error( request, 'Username'+ " : " + str(row['username']) + ' already exists in Aggregator List',\
                                             )
                        elif not Region.objects.filter(region_id=row['region']).exists() :  
                            messages.error(request,f"Entered region id for username {row['username']} is not exist,refer master list")  

                        elif not State.objects.filter(state_id=row['state']).exists():
                            
                            messages.error(request,f"Entered state id for username {row['username']} is not exist,refer master list")             
                        elif not District.objects.filter(district_id=row['district']).exists():
                            
                            messages.error(request,f"Entered district id for username {row['username']} is not exist,refer master list")            
                        
                        #         # if region:
                        #         #     obj2.region=region 
                        #     except  Region.DoesNotExist:
                        #             messages.error(request,f"Entered region id for username {row['username']} is not exist,refer master list")  
                        # elif row['state']:
                        #     try :
                        #         state=State.objects.get(state_id=row['state'])
                        #         # if state:
                        #         #       obj2.state=state
                        #     except  State.DoesNotExist:
                        #             messages.error(request,f"Entered state id for username {row['username']} is not exist, refer master list")
                        # elif row['district']:
                        #     try :
                        #         district=District.objects.get(district_id=row['district'])
                        #         # if district :
                        #         #     obj2.district=district
                        #     except  District.DoesNotExist:
                        #              messages.error(request,f"Entered district id for username {row['username']} is not exist,refer master list")  
                       
                        else:
                        
                            try:
                                # if str(row['password']) is not None:
                                password=str(row['password'])
                                # else:
                                #     password="123"    
                                obj = User.objects.create_user(username=row['username'],password= password)

                                obj2=AggregatorProfile(user=obj)
                                obj2.save()


                                # obj2.profile_type=ProfileType.objects.get(name='aggregator')
                                if row['name']:
                                    obj2.name=row['name']
                                if row['mobile_number'] :   
                                    obj2.mobile_number=int(row['mobile_number'])
                                obj2.profile_type=ProfileType.objects.get(name="aggregator")#insert profile type
                                obj5=Profile(user=obj, user_type_id=obj2.profile_type.id)
                                obj5.save()
                                if row['region']:
                                    # try :
                                    region=Region.objects.filter(region_id=row['region']).first()
                                    if region:
                                        obj2.region=region 
                                    # except  Region.DoesNotExist:
                                    #         messages.error(request,f"Entered region id for username {row['username']} is not exist,refer master list")  
                                if row['state']:
                                    # try :
                                    state=State.objects.filter(state_id=row['state']).first()
                                    if state:
                                         obj2.state=state
                                    # except  State.DoesNotExist:
                                    #         messages.error(request,f"Entered state id for username {row['username']} is not exist, refer master list")
                                if row['district']:
                                    # try :
                                    district=District.objects.filter(district_id=row['district']).first()
                                    if district :
                                        obj2.district=district
                                    # except  District.DoesNotExist:
                                    #          messages.error(request,f"Entered district id for username {row['username']} is not exist,refer master list")    
                                if row['associated_entity']:
                                    if isinstance(row['associated_entity'], str):
                                        associated_entities_list = row['associated_entity'].split(',')
                                    else:
                                        associated_entities_list = str(row['associated_entity']).split(',')
                                    for username in associated_entities_list:
                                        username = username.strip() 
                                        try :
                                            associated_entity=BlfProfile.objects.filter(user__username=username).first()
                                            if associated_entity: 
                                                obj2.associated_entity.add(associated_entity)
                                        except  BlfProfile.DoesNotExist:
                                            messages.error(request,"")  
                                # try :
                                #     # associated_entity=BlfProfile.objects.get(user__username=row['associated_entity']) 

                                #     # associated_entity=BlfProfile.objects.get(id=row['associated_entity'])
                                #     # if type(row['associated_entity']) == int:
                                        
                                #     #     associated_entity=BlfProfile.objects.get(Q(user__username=row['associated_entity']) | \
                                #     #                                          Q(id=row['associated_entity']))
                                #     # else:
                                #     associated_entity=BlfProfile.objects.filter(user__username=row['associated_entity']).first()
                                #     if associated_entity: 
                                #         obj2.associated_entity.add(associated_entity)
                                # except  BlfProfile.DoesNotExist:
                                #         messages.error(request,"")              
                            

                                obj2.save()
                                successful_upload +=1
                                # messages.success(request, str(row['username']) + ' Data uploaded successfully in aggregator list')
                            except  User.DoesNotExist:
                                    # messages.error(request,"something went wrong")
                                    pass
                    # except  KeyError:
                    #         messages.error(request,"something went wrong") 
            if successful_upload > 0  :    
                messages.success(request, "Total " +str(successful_upload) + ' data uploaded successfully in aggregator list')           
        except  KeyError:
                messages.error(request,"something went wrong")    
        except Exception as e:
            messages.error(request, f"Something went wrong")              
    context={}

    return CommonMixin.render(request, 'master/export_aggregator.html',context)


@permission_required_admin
def ViewMasterData(request):
    url = 'grower'
    if request.method== 'GET':

        type=request.GET.get('type')
        print(type)
  
        if type=='region':
            # master_list=Region.objects.all()
            master_list=Region.objects.filter(is_deleted=False).order_by('region_name')
            # state_list=Region.objects.filter(id=id).values('state__name')
            # state_list=Region.objects.values('state__name')

            print(master_list)
            
        elif type=='state':
            master_list=State.objects.filter(is_deleted=False).order_by('name') 
            # master_list=State.objects.all()
        elif type=='district':
            # master_list=District.objects.all()  
            master_list=District.objects.filter(is_deleted=False).order_by('name') 
        else:
            master_list= "" 
        # state_list=""
        context={'master_list':master_list,url:'url'}    
        return CommonMixin.render(request, 'master/master_list.html',context)
@login_required
def state_view(request):
        # if request.method=='GET':
     
    id=request.GET.get('id')  
    print(id)
    result = Region.objects.filter(id=id).values('state__name')
    print(result)


    context={
		    	'state_list' :result,
    
		    }

    return CommonMixin.render(request, 'master/state_view.html', context)	
	    



####################################################################
    #############  Warehouse Views  ###############
#####################################################################


# Create your views here.
class WarehouseListView(LoginRequiredMixin, CommonMixin, ListView):
    """
    Warehouse List View
    """
    model = WarehouseManagement
    context_object_name = 'warehouse_list'
    template_name = 'master/warehouse_list.html'
    paginate_by = 5

    def get(self, request, *args, **kwargs):
        try:
            if self.request.user.is_superuser:
                messages.error(self.request, 'You have no permission to access the requested resource!')
                return redirect(reverse('index'))
        except AttributeError as error:
            messages.error(self.request, 'You have no permission to access the requested resource!')
            return redirect(reverse('index'))

        return super().get(request, *args, **kwargs)


    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)
        name=self.request.GET.get('name')
        if name:
            return qs.filter(name__icontains=name)
        return WarehouseManagement.objects.filter(created_by_id=self.request.user.id).order_by('-id')


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['type_list'] = WarehouseType.objects.all().order_by('id')
        
        return context
    


class WarehouseCreateView(LoginRequiredMixin, CreateView, CommonMixin):
    """
    Stock Group Create View
    """
    form_class = WarehouseManagementForm
    template_name = 'master/warehouse_create.html'

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


    def get_success_url(self, **kwargs):
        messages.success(self.request, 'Warehouse Created Successfully')
        return reverse('warehouse_list')

    def form_valid(self, form):
    
        context = self.get_context_data()

        with transaction.atomic():
            form.instance.created_by_id = self.request.user.id
            self.object = form.save()

        return super(WarehouseCreateView, self).form_valid(form)




    def form_invalid(self, form):
        error_message = 'Error saving the Form, check fields below.'
        messages.error(self.request, error_message)
        return super().form_invalid(form)
    




from django.shortcuts import get_object_or_404

class WarehouseUpdateView(LoginRequiredMixin, CommonMixin, UpdateView):
	"""
	Chemical Data Create and Update View @vivek
	"""
	model = WarehouseManagement
	form_class = WarehouseManagementForm
	template_name = 'master/warehouse_create.html'

	def get(self, request, *args, **kwargs):
	# checking if the user is customer
		# try:
		# 	if self.request.user.is_superuser:
		# 		messages.error(self.request, 'You have no permission to access the requested resource!')
		# 		return redirect(reverse('index'))
		# except AttributeError as error:
		# 	messages.error(self.request, 'You have no permission to access the requested resource!')
		# 	return redirect(reverse('index'))

		return super().get(request, *args, **kwargs)

	def get_success_url(self, **kwargs):
		messages.success(self.request, 'Warehouse Updated Successfully')
		return reverse('warehouse_list')


	def get_object(self,queryset=None):
		warehouse_details = get_object_or_404(WarehouseManagement,pk=self.kwargs['id'])
		return warehouse_details

	def get_context_data(self, **kwargs):
		context = super(WarehouseUpdateView, self).get_context_data(**kwargs)

		context['warehouse_details'] = self.get_object()
		return context
     

	def form_valid(self, form):
		
		self.id = self.kwargs['id']
		context = self.get_context_data()


		with transaction.atomic():
               
			self.object = form.save()


		return super(WarehouseUpdateView, self).form_valid(form)
	
@login_required
def warehouse_delete(request, id):

	# try:
	# 	if not request.user.is_superuser:
	# 		messages.error(request, 'You have no permission to access the requested resource!')
	# 		return redirect(reverse('index'))
	# except AttributeError as error:
	# 	messages.error(request, 'You have no permission to access the requested resource!')
	# 	return redirect(reverse('index'))



	warehouse = WarehouseManagement.objects.filter(id=id).first()
	warehouse.delete()
	# user_type = 
	messages.success(
		request, 'Warehouse Deleted Successfully')
	
	return redirect(reverse('warehouse_list', ))    



@login_required
def warehouse_search(request):
	if request.method == "POST":
		name= request.POST.get('name')


		edit_url = 'warehouse_edit'



		filter = {}
		
		if name:
			filter["name__icontains"] = name


		result = WarehouseManagement.objects.filter(**filter)
		print(result)

		print(filter)

		context={
			'warehouse_list' : result,
			'edit_url' : edit_url,
			'name' : name,
		}

		return CommonMixin.render(request, 'master/warehouse_list.html', context)


@login_required
def warehouse_view(request,id):
		warehouse_details = WarehouseManagement.objects.filter(pk=id).first()
		context={
			'warehouse_details' : warehouse_details,
		}
		return CommonMixin.render(request, 'master/warehouse_view.html', context)	



# ERROR 500 and 400
def my_custom_permission_denied_view(request, *args, **kwargs):
    """
     404 Page  View
    """
    context = {

    }
    return CommonMixin.render(request,'404.html',context)


def error_500(request):
    return render(request, '500.html')





def account_details(request):

    user_details = Profile.objects.filter(user_id=request.user).first()


    context ={
        'user_details': user_details,
    }

    return  CommonMixin.render(request, 'account_details.html', context )






##############  TYPING SPEED ##############

def typing_speed_view(request):
    # from .type_speed import Game

    result =  "Game().run()"
    return  result



def privacy(request):
    """ Privacy Policy page """

    privacy_details = PrivacyPolicy.objects.filter(sample__exact='PRIVACY-POLICY').first()

    context = {
        'privacy_details': privacy_details,
    }
    return render(request, 'privacy.html', context)





from knox.auth import TokenAuthentication
from rest_framework import permissions
from knox.models import AuthToken
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, IsAuthenticatedOrReadOnly, AllowAny
from django.core.paginator import Paginator
from knox.auth import TokenAuthentication
from django.db import transaction
from rest_framework import status
from rest_framework.exceptions import APIException



from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import ValidationError
from django.core.paginator import Paginator



class AndroidVersionAPIView(APIView):
    # authentication_classes = (TokenAuthentication,)
    permission_classes = (AllowAny,)

    def get(self, request, *args, **kwargs):
        try:
            queryset = AndroidVersion.objects.all().order_by('-id')

            page_size = int(request.query_params.get('page_size', 10))
            paginator = Paginator(queryset, page_size)
            page_number = request.query_params.get('page', 1)
            page = paginator.get_page(page_number)
            serializer = AndroidVersionSerializer(page, many=True)

            return Response({
                'count': paginator.count,
                'next': page.next_page_number() if page.has_next() else None,
                'previous': page.previous_page_number() if page.has_previous() else None,
                'results': serializer.data,
            })

        except Exception as e:
            raise ValidationError({'status': '400 Bad Request', 'request_status': 0, 'msg': str(e)})

from django.apps import apps
class ModelPayloadAPIView(APIView):
    """
        API endpoint to generate JSON payload for a given Django model.
    """
    def get(self, request):
        model_name= self.request.query_params.get('model_name', "Labour")
        if not model_name:
            return Response(
                {"error": "Please provide a model name"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        app_labels = ['master', 'user_profile', 'vehicle_management', 'invoicing',
                      'leaf_receipt', 'lot_batch_details', 'chemical_data', 'gardens_managment']
        model_class = None
        for label in app_labels:
            try:
                model_class = apps.get_model(label, model_name)
                if model_class:
                    break
            except LookupError:
                continue
        if not model_class:
            return Response(
                {"error": f"Model '{model_name}' not found in any of {app_labels}."},
                status=status.HTTP_404_NOT_FOUND,
            )
        payload = model_to_json_payload(model_class)
        return Response(payload, status=status.HTTP_200_OK)
