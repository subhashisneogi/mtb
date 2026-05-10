from django.shortcuts import render
from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse
from django.db.models import Q
from django.http import JsonResponse
from django.db.models.functions import Coalesce
from django.db.models import Sum, Count, Value
from django.template.loader import render_to_string
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.contrib.auth import get_user_model
User = get_user_model()
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView, UpdateView, CreateView
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.paginator import Paginator , EmptyPage, PageNotAnInteger
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, IsAuthenticatedOrReadOnly, AllowAny
from django.core.paginator import Paginator
from knox.auth import TokenAuthentication
from django.db import transaction
from rest_framework import status
from rest_framework.exceptions import APIException
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import smart_str, force_str, smart_bytes, DjangoUnicodeDecodeError
from django.db import transaction
from django.db.models import Q
from master.common import CommonMixin
from .models import *
from master.forms import *
from accounts.forms import *
# Create your views here.
from accounts.models import *
from accounts.serializers import *
import collections
from django.contrib.auth import authenticate, login 
from knox.auth import TokenAuthentication
from rest_framework import permissions
from knox.models import AuthToken
#from AuthTokenSerializer import *
from knox.views import LoginView as KnoxLoginView
from user_profile.models import *
from user_profile.serializers import *
from .serializers import *
from chemical_data.models import *
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
import uuid
import time
import random
from django.db.models import Max
from master.utils import send_sms
from user_profile.helpers import *
from django.db.models.functions import Cast, Replace
from django.core.files.storage import FileSystemStorage
from django.template.loader import get_template
import pdfkit
from django.utils import timezone
from datetime import timedelta


# Create your views here.
class GrowerProfileListAPIView(APIView):
    """ Grower list mapped or associated with aggregator View"""
    authentication_classes = (TokenAuthentication,)
    permission_classes=(IsAuthenticated,)
    queryset = GrowerProfile.objects.filter(is_deleted=False).exclude(associated_aggregator__isnull=True)
    serializer_class = GrowerProfileSerializer
    def get(self, request, *args, **kwargs):
        try:
            id = self.request.query_params.get('id', None )        
            if id:
                queryset = self.queryset.filter(id=id,associated_aggregator__user=request.user).order_by('-id')
            else:
                queryset=self.queryset.filter(associated_aggregator__user=request.user).order_by('name')    
            page_size = int(request.query_params.get('page_size', 10))
            paginator = Paginator(queryset, page_size)
            page_number = self.request.query_params.get('page', 1)
            page = paginator.get_page(page_number)
            serializer = GrowerProfileSerializer(queryset, many=True)           
            return Response({
                'count': paginator.count,
                'next': page.next_page_number() if page.has_next() else None,
                'previous': page.previous_page_number() if page.has_previous() else None,
                'results': serializer.data,
            })
        except Exception as e:
            raise serializers.ValidationError({'status': status.HTTP_400_BAD_REQUEST,'request_status': 0, 'msg': e},code='authorization')    
        
class PlotListAPIView(APIView):
    """ Plot API View for Farm Diary , Plucking Data, Collection From Grower & Aggregator"""
    authentication_classes = (TokenAuthentication,)
    permission_classes=(IsAuthenticated,)
    # queryset = Plot.objects.filter(plot_status=True).\
    #     exclude(garden__grower__associated_aggregator__isnull=True)
    queryset=Plot.objects.filter(plot_status=True)
    print(queryset)
    serializer_class = PlotListSerializer
    def get(self, request, *args, **kwargs):
        try:
            id = self.request.query_params.get('id', None)   
            grower_id = self.request.query_params.get('grower_id', None)  # plot list according to particular grower 
            aggregator_id = self.request.query_params.get('aggregator_id', None) # mapped aggregator id(used for collection from aggregator)
            if id:
                queryset = self.queryset.filter(id=id,garden__grower__associated_aggregator__user=request.user).order_by('-id')
            elif grower_id:
                queryset=self.queryset.filter(garden__grower_id=grower_id).order_by('-id') 
                print("grower",queryset)
            elif aggregator_id:
                queryset=self.queryset.filter(garden__grower__associated_aggregator__id=aggregator_id).order_by('-id') 
                print("aggregator",queryset)
            else:
                queryset=""
                # queryset=self.queryset.filter(garden__grower__associated_aggregator__user=request.user).order_by('-id')    
            page_size = int(request.query_params.get('page_size', 10))
            paginator = Paginator(queryset, page_size)
            page_number = self.request.query_params.get('page', 1)
            page = paginator.get_page(page_number)
            serializer = PlotListSerializer(queryset, many=True)

            return Response({
                'count': paginator.count,
                'next': page.next_page_number() if page.has_next() else None,
                'previous': page.previous_page_number() if page.has_previous() else None,
                'results': serializer.data
            })
        except Exception as e:
            raise serializers.ValidationError({'status': status.HTTP_400_BAD_REQUEST,'request_status': 0, 'msg': e},code='authorization')
    
class DivisonListAggregatorAPIView(APIView):
    """ Division List API View for Farm Diary , Plucking Data, Collection From Grower & Aggregator """
    authentication_classes = (TokenAuthentication,)
    permission_classes=(IsAuthenticated,)
    queryset = Division.objects.all().exclude(garden__grower__associated_aggregator__isnull=True)
    print(queryset)
    serializer_class = DivisionListSerializer
    def get(self, request, *args, **kwargs):
        try:
            id = self.request.query_params.get('id', None)   
            grower_id = self.request.query_params.get('grower_id', None)
            aggregator_id = self.request.query_params.get('aggregator_id', None)    
            if id:
                queryset = self.queryset.filter(id=id,garden__grower__associated_aggregator__user=request.user).order_by('-id')
            elif grower_id:
                queryset=self.queryset.filter(garden__grower__associated_aggregator__user=request.user,garden__grower_id=grower_id).order_by('-id') 
            elif aggregator_id :
                queryset=self.queryset.filter(garden__grower__associated_aggregator__id=aggregator_id).order_by('-id') 
      
            else:
                queryset=""
            #     queryset=self.queryset.filter(garden__grower__associated_aggregator__user=request.user).order_by('-id')    
            page_size = int(request.query_params.get('page_size', 10))
            paginator = Paginator(queryset, page_size)
            page_number = self.request.query_params.get('page', 1)
            page = paginator.get_page(page_number)
            serializer = DivisionListSerializer(queryset, many=True)

            return Response({
                'count': paginator.count,
                'next': page.next_page_number() if page.has_next() else None,
                'previous': page.previous_page_number() if page.has_previous() else None,
                'results': serializer.data,
            })
        except Exception as e:
            raise serializers.ValidationError({'status': status.HTTP_400_BAD_REQUEST,'request_status': 0, 'msg': e},code='authorization')    
class VehicleAvailableListAPIView(APIView):
    """Available vehicle list API View"""
    authentication_classes = (TokenAuthentication,)
    permission_classes=(IsAuthenticated,)
    queryset = VehicleManagement.objects.filter(is_deleted=False)
    serializer_class = VehicleManagementSerializer
    def get(self, request, *args, **kwargs):
        try:
            id = self.request.query_params.get('id', None) 
            user_type= self.request.query_params.get('user_type', "") 
            if id:
                queryset = self.queryset.filter(id=id,is_available=True,).order_by('-id')
            elif user_type.lower() == "aggregator":
                queryset1= self.queryset.filter(is_available=True,created_by=request.user).order_by('-id')
                # queryset2= self.queryset.filter(is_available=True,\
                #                                 created_by__profile_id_grower__associated_aggregator__user=request.user)\
                #                                     .order_by('-id')
                # queryset=queryset1.union(queryset2)
                queryset=queryset1
            elif user_type.lower() == "grower":  
                # grower_details=GrowerProfile.objects.filter(user=request.user).values('associated_aggregator__user_id')
                # aggregator_list=[]
                queryset1= self.queryset.filter(is_available=True,created_by=request.user).order_by('-id')
                # if grower_details:
                #     for data in grower_details:
                #         queryset2= self.queryset.filter(is_available=True,\
                #                                     created_by_id=data.get('associated_aggregator__user_id'))
                #         # print("queryset2",queryset2)
                #         # queryset3=queryset2.union(quer)
                #         aggregator_list.append(queryset2)
                #         # .exclude(created_by__profile_id_grower__associated_aggregator__isnull=True).order_by('-id')
                #         # queryset3=[item for item in range(aggregator_list) ]
                #         if aggregator_list:
                #             for data in aggregator_list:
                #                 queryset2=queryset2.union(data) 
                #     queryset=queryset1.union(queryset2)  
                    # queryset=queryset1.order_by('-id')

                # else :
                queryset=queryset1             
            elif user_type.lower() == "blf":
                queryset1=self.queryset.filter(is_available=True,\
                                               created_by__profile_id_grower__associated_entity__user=request.user)
                print("queryset1",queryset1)
                queryset2=self.queryset.filter(is_available=True,\
                                               created_by__profile_id_aggregator__associated_entity__user=request.user)
                print(queryset2)
                queryset=queryset1.union(queryset2)
                queryset=queryset.order_by('-id')
            else:
                # queryset = self.queryset.filter(is_available=True,).order_by('-id')
                queryset=""

            page_size = int(request.query_params.get('page_size', 10))
            paginator = Paginator(queryset ,page_size)
            page_number = self.request.query_params.get('page', 1)
            page = paginator.get_page(page_number)
            serializer = VehicleManagementSerializer(queryset, many=True)

            return Response({
                'count': paginator.count,
                'next': page.next_page_number() if page.has_next() else None,
                'previous': page.previous_page_number() if page.has_previous() else None,
                'results': serializer.data,
            })
        except Exception as e:
            raise serializers.ValidationError({'status': status.HTTP_400_BAD_REQUEST,'request_status': 0, 'msg': e},code='authorization')
import re

class CollectionFromGrowerAPIView(APIView):
    """ Collection from grower View"""
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    queryset = CollectionFromGrower.objects.filter(is_deleted=False)
    serializer_class = CollectionFromGrowerSerializer
    def get(self, request, *args, **kwargs):
        try:
            id = self.request.query_params.get('id', None)   
            date_from=self.request.query_params.get('date_from', None)
            date_to=self.request.query_params.get('date_to', None)
            if id:
                queryset = self.queryset.filter(created_by=request.user,id=id).order_by('-id')
            elif (date_from and date_to):
                 queryset = self.queryset.filter(created_by=request.user,date__range=[date_from,date_to]).order_by('-id')

            else:
                queryset=self.queryset.filter(created_by=request.user).order_by('-id')    
                print(queryset)
            page_size = int(request.query_params.get('page_size', 10))
            paginator = Paginator(queryset, page_size)
            page_number = self.request.query_params.get('page', 1)
            page = paginator.get_page(page_number)
            serializer = CollectionFromGrowerSerializer(queryset, many=True)          
            return Response({
                'count': paginator.count,
                'next': page.next_page_number() if page.has_next() else None,
                'previous': page.previous_page_number() if page.has_previous() else None,
                'results': serializer.data,
            })
        except Exception as e:
            raise serializers.ValidationError({'status': status.HTTP_400_BAD_REQUEST,'request_status': 0, 'msg': e},code='authorization')
    def post(self, request, format=None):
        # try:
			
            grower_id = request.data.get('grower_id', None)
            date= request.data.get('date', None)
            vehicle_option= request.data.get('vehicle_option', None)
            vehicle_number_id= request.data.get('vehicle_number_id', None)
            quantity= request.data.get('quantity', None)
            keep_record= request.data.get('keep_record', None)
            rate= request.data.get('rate', None)
            plot_id= request.data.get('plot_id', None)
            division_id= request.data.get('division_id', None)
            latitude= request.data.get('latitude', None)
            longitude= request.data.get('longitude', None)
       
            with transaction.atomic(): 
                created =  CollectionFromGrower.objects.create(grower_id=grower_id,date=date,\
                		vehicle_option=vehicle_option,\
                             quantity=quantity,keep_record=keep_record,rate=rate,\
                               latitude=latitude,longitude=longitude,  created_by=request.user)
                created.save()
                if vehicle_number_id:
                    created.vehicle_number_id=vehicle_number_id
                    created.save()
                if plot_id:
                    created.plot_id=plot_id
                    created.save()    
                if division_id:
                    created.division_id=division_id
                    created.save()      
                serializer = CollectionFromGrowerSerializer(created)
                agg_details = AggregatorProfile.cmobjects.filter(user_id=request.user.id).first()

                if agg_details:
                    if agg_details.region:
                        region_code = agg_details.region.region_id
                    else:
                        region_code = ""  # Default region code if no region is found
                else:
                    region_code = ""  # Default region code if AggregatorProfile does not exist
                # last_challan = CollectionFromGrower.objects.aggregate(Max('receipt_no'))
                # last_challan = CollectionFromGrower.objects.filter(receipt_no__contains=str(region_code)+str(request.user).upper(),created_by_id=request.user.id)\
                # .aggregate(Max('receipt_no'))
                # last_challan_id = last_challan.get('receipt_no__max')
                last_challan_id= CollectionFromGrower.objects.filter(receipt_no__contains=str(region_code)+str(request.user).upper(),\
                created_by_id=request.user.id).last()
                # Calcula te the next receipt number
                if last_challan_id and last_challan_id.receipt_no.startswith(str(region_code) + str(request.user).upper()):
                    # Extract the numeric part and increment it
                    # numeric_part = int(re.search(r'\d+$', last_challan_id).group()) + 1

                    # numeric_part = int(last_challan_id[-2:]) + 1
                  
                    numeric_part_index = len(str(region_code)) + len(str(request.user).upper())
    
                    # Extract the numeric part
                    numeric_part = int(last_challan_id.receipt_no[numeric_part_index:]) + 1

                                

                    # Format the nume   ric part with leading zeros and concatenate with region code and user ID
                    next_receipt_no = f"{region_code}{str(request.user).upper()}{numeric_part:0>2d}"  # Assuming a fixed length of 2 for the numeric part    
                else:
                # Handle the case when there are no existing supply_challan_id values
                    # next_challan_id = "TXN-000000001"
                    next_receipt_no=f"{region_code}{str(request.user).upper()}01" 
                #     next_receipt_no = f"{region_code}-{numeric_part:09d}"
                # else:
                #     # Handle the case when there are no existing receipt numbers
                #     next_receipt_no = f"{region_code}-000000001"

                # Set the new receipt number
                created.receipt_no = next_receipt_no
                created.save()

                ###### send sms ###############

                grower_obj=GrowerProfile.objects.filter(id=grower_id).first()
                print(grower_obj)
                if grower_obj:
                    grower_name=grower_obj.name
                else :
                    grower_name="NA"    
                aggregator_obj=AggregatorProfile.objects.filter(user=request.user).first()
                if aggregator_obj:
                    aggregator_name=aggregator_obj.name
                else :
                    aggregator_name="NA" 
                if rate:
                    rate =rate
                else :
                    rate="NA"           
                if aggregator_obj:
                    if aggregator_obj.mobile_number:
                        mobile_number = aggregator_obj.mobile_number
                        # template_id='1007983856203558873'
                        template_id='1007925551670075044'
                        # message = f"{grower_name} has supplied {quantity} Kg.Leaf to {aggregator_name} with Rate of Rs. {rate} vide Receipt No. {next_receipt_no} - Trustea" # Your message content
                        message=f"{grower_name} has supplied {quantity} Kg. Leaf to M/S {aggregator_name} with Rate of Rs. {rate} vide Receipt No. {next_receipt_no} - Trustea"
                        # message="hello"
                        if mobile_number:
                            send_sms(mobile_number, message,template_id)
                if grower_obj:
                    if grower_obj.mobile_number:
                        mobile_number = grower_obj.mobile_number
                        # template_id='1007983856203558873'
                        template_id='1007925551670075044'
                        # message = f"{grower_name} has supplied {quantity} Kg.Leaf to {aggregator_name} with Rate of Rs. {rate} vide Receipt No. {next_receipt_no} - Trustea" # Your message content
                        message=f"{grower_name} has supplied {quantity} Kg. Leaf to M/S {aggregator_name} with Rate of Rs. {rate} vide Receipt No. {next_receipt_no} - Trustea"
                        # message="hello"
                        if mobile_number:
                            send_sms(mobile_number, message,template_id)        	


                return Response({'results':{
                                        'Data':serializer.data ,
                                        },
                                        'msg': 'Collection From Grower Created Successfully',
                                        'status':status.HTTP_201_CREATED,
                                        "request_status": 1})
        # except Exception as e:
        #     raise serializers.ValidationError({'status': status.HTTP_400_BAD_REQUEST,'request_status': 0, 'msg': e},code='authorization')   
    def put(self, request, *args, **kwargs):
        """
        Below are the methods for Edit method and Delete method
        """
        try:
            method = self.request.query_params.get('method', None)
            id = self.request.query_params.get('id', None)


            with transaction.atomic():
                if method.lower() == 'edit':
                    grower_id = request.data.get('grower_id', None)
                    date= request.data.get('date', None)
                    vehicle_option= request.data.get('vehicle_option', None)
                    vehicle_number_id= request.data.get('vehicle_number_id', None)
                    quantity= request.data.get('quantity', None)
                    keep_record= request.data.get('keep_record', None)
                    rate= request.data.get('rate', None)
                    plot_id= request.data.get('plot_id', None)
                    division_id= request.data.get('division_id', None)
                    latitude= request.data.get('latitude', None)
                    longitude= request.data.get('longitude', None)

                    collection_details= CollectionFromGrower.cmobjects.filter(pk=id).first()
                    if not collection_details:
                        return Response({'results': [],
                                        'msg': "Selected Collection Data Does'nt exists!",
                                        "request_status": 0}, status=status.HTTP_400_BAD_REQUEST)

                    update=CollectionFromGrower.cmobjects.filter(id=id)\
                        .update(grower_id=grower_id,date=date,\
                		vehicle_option=vehicle_option,\
                             quantity=quantity,keep_record=keep_record,rate=rate,\
                               latitude=latitude,longitude=longitude,  updated_by=request.user)
                    if vehicle_number_id:
                        collection_details.vehicle_number_id=vehicle_number_id
                        collection_details.save()
                    if plot_id:
                        collection_details.plot_id=plot_id
                        collection_details.save()  
                    if division_id:
                        collection_details.division_id=division_id
                        collection_details.save()      
                    return Response({'results':{
                                            'Data':CollectionFromGrower.objects.filter(pk=id).values(),
                                            },
                                            'msg': 'Collection From Aggregator Data Updated SuccessFully',
                                            'status':status.HTTP_200_OK,
                                            "request_status": 1})
          
                elif method.lower() == 'delete':
                    """
                    Delete 
                    """
                    if CollectionFromGrower.cmobjects.filter(id=id).exists():
                        collection_details= CollectionFromGrower.cmobjects.filter(id=id).first()
                        collection_details.is_deleted = True
                        collection_details.save()

                        return Response({'results':{
                                            'form_details':CollectionFromGrower.objects.filter(pk=id).values(),
                                            },
                                            'msg': 'Collection From Grower Data Deleted Successfully',
                                            "request_status": 1})
                    else:
                        return Response({'results': [],
                                        'msg': "Selected Collection From Grower Data Does'nt exists!",
                                        'status': status.HTTP_404_NOT_FOUND,
                                        "request_status": 0})   
        except Exception as e:
            raise serializers.ValidationError({'status': status.HTTP_400_BAD_REQUEST,'request_status': 0, 'msg': e},code='authorization')
class CollectionFromAggregatorAPIView(APIView):
    """ collection from aggreator View"""
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    queryset = CollectionFromAggregator.objects.filter(is_deleted=False)
    serializer_class = CollectionFromAggregatorSerializer
    def get(self, request, *args, **kwargs):
        try:
            id = self.request.query_params.get('id', None)    
            date_from=self.request.query_params.get('date_from', None)
            date_to=self.request.query_params.get('date_to', None)
                 
            if id:
                queryset = self.queryset.filter(created_by=request.user,id=id).order_by('-id')
            
            elif (date_from and date_to):
                 queryset = self.queryset.filter(created_by=request.user,date__range=[date_from,date_to]).order_by('-id')
            else:
                queryset=self.queryset.filter(created_by=request.user).order_by('-id')    
                print(queryset)
            page_size = int(request.query_params.get('page_size', 10))
            paginator = Paginator(queryset, page_size)
            page_number = self.request.query_params.get('page', 1)
            page = paginator.get_page(page_number)
            serializer = CollectionFromAggregatorSerializer(queryset, many=True)

            return Response({
                'count': paginator.count,
                'next': page.next_page_number() if page.has_next() else None,
                'previous': page.previous_page_number() if page.has_previous() else None,
                'results': serializer.data,
            })
        except Exception as e:
            raise serializers.ValidationError({'status': status.HTTP_400_BAD_REQUEST,'request_status': 0, 'msg': e},code='authorization')
    def post(self, request, format=None):
        try:
			
            aggregator_id = request.data.get('aggregator_id', None)
            date= request.data.get('date', None)
            vehicle_option= request.data.get('vehicle_option', None)
            vehicle_number_id= request.data.get('vehicle_number_id', None)
            quantity= request.data.get('quantity', None)
            keep_record= request.data.get('keep_record', None)
            rate= request.data.get('rate', None)
            plot_id= request.data.get('plot_id', None)
            division_id= request.data.get('division_id', None)
            latitude= request.data.get('latitude', None)
            longitude= request.data.get('longitude', None)
       
            with transaction.atomic(): 
                created =  CollectionFromAggregator.objects.create(aggregator_id=aggregator_id,date=date,\
                		vehicle_option=vehicle_option,\
                             quantity=quantity,keep_record=keep_record,rate=rate,\
                              latitude=latitude,longitude=longitude,  created_by=request.user)
                created.save()
                if vehicle_number_id:
                    created.vehicle_number_id=vehicle_number_id
                    created.save()
                if plot_id:
                    created.plot_id=plot_id
                    created.save() 
                if division_id:
                    created.division_id=division_id
                    created.save()    
                serializer = CollectionFromAggregatorSerializer(created)
                agg_details = AggregatorProfile.cmobjects.filter(user_id=request.user.id).first()

                if agg_details:
                    if agg_details.region:
                        region_code = agg_details.region.abbrevation
                    else:
                        region_code = ""  # Default region code if no region is found
                else:
                    region_code = ""  # Default region code if AggregatorProfile does not exist

                # last_challan = CollectionFromGrower.objects.aggregate(Max('receipt_no'))
                # last_challan = CollectionFromAggregator.objects.filter(receipt_no__contains=str(region_code)+str(request.user).upper(),\
                # created_by_id=request.user.id).aggregate(Max('receipt_no'))
                # last_challan_id = last_challan.get('receipt_no__max')
                last_challan_id= CollectionFromAggregator.objects.filter(receipt_no__contains=str(region_code)+str(request.user).upper(),\
                created_by_id=request.user.id).last()
                # Calculate the next receipt number
                if last_challan_id and last_challan_id.startswith(str(region_code) + str(request.user).upper()):
                    # Extract the numeric part and increment it
                    # numeric_part = int(re.search(r'\d+$', last_challan_id).group()) + 1
                    # numeric_part = int(last_challan_id[-2:]) + 1
                    numeric_part_index = len(str(region_code)) + len(str(request.user).upper())
    
                    # Extract the numeric part
                    numeric_part = int(last_challan_id[numeric_part_index:]) + 1
                    next_receipt_no = f"{region_code}{str(request.user).upper()}{numeric_part:0>2d}"

                else:
              
                    next_receipt_no=f"{region_code}{str(request.user).upper()}01" 
               
                
                created.receipt_no = next_receipt_no
                created.save()

                return Response({'results':{
                                        'Data':serializer.data ,
                                        },
                                        'msg': 'Collection From Aggregator Created Successfully',
                                        'status':status.HTTP_201_CREATED,
                                        "request_status": 1})
        except Exception as e:
            raise serializers.ValidationError({'status': status.HTTP_400_BAD_REQUEST,'request_status': 0, 'msg': e},code='authorization')    
    def put(self, request, *args, **kwargs):
        """
        Below are the methods for Edit method and Delete method
        """
        try:
            method = self.request.query_params.get('method', None)
            id = self.request.query_params.get('id', None)


            with transaction.atomic():
                if method.lower() == 'edit':
                    aggregator_id = request.data.get('aggregator_id', None)
                    date= request.data.get('date', None)
                    vehicle_option= request.data.get('vehicle_option', None)
                    vehicle_number_id= request.data.get('vehicle_number_id', None)
                    quantity= request.data.get('quantity', None)
                    keep_record= request.data.get('keep_record', None)
                    rate= request.data.get('rate', None)
                    plot_id= request.data.get('plot_id', None)
                    division_id= request.data.get('division_id', None)
                    latitude= request.data.get('latitude', None)
                    longitude= request.data.get('longitude', None)

                    collection_details= CollectionFromAggregator.cmobjects.filter(pk=id).first()




                    if not collection_details:
                        return Response({'results': [],
                                        'msg': "Selected Collection Data Does'nt exists!",
                                        "request_status": 0}, status=status.HTTP_400_BAD_REQUEST)




                    update=CollectionFromAggregator.cmobjects.filter(id=id)\
                        .update(aggregator_id=aggregator_id,date=date,\
                		vehicle_option=vehicle_option,\
                             quantity=quantity,keep_record=keep_record,rate=rate,\
                                latitude=latitude,longitude=longitude, updated_by=request.user)
                    if vehicle_number_id:
                        collection_details.vehicle_number_id=vehicle_number_id
                        collection_details.save()
                    if  plot_id:
                        collection_details.plot_id=plot_id
                        collection_details.save()
                    if  division_id:
                        collection_details.division_id=division_id
                        collection_details.save()        
                    return Response({'results':{
                                            'Data':CollectionFromAggregator.objects.filter(pk=id).values(),
                                            },
                                            'msg': 'Collection From Aggregator Data Updated SuccessFully',
                                            'status':status.HTTP_200_OK,
                                            "request_status": 1})
          
                elif method.lower() == 'delete':
                    """
                    Delete 
                    """
                    if CollectionFromAggregator.cmobjects.filter(id=id).exists():
                        collection_details= CollectionFromAggregator.cmobjects.filter(id=id).first()
                        collection_details.is_deleted = True
                        collection_details.save()

                        return Response({'results':{
                                            'form_details':CollectionFromAggregator.objects.filter(pk=id).values(),
                                            },
                                            'msg': 'Collection From Aggregator Data Deleted Successfully',
                                            "request_status": 1})
                    else:
                        return Response({'results': [],
                                        'msg': "Selected Collection From Aggregator Data Does'nt exists!",
                                        'status': status.HTTP_404_NOT_FOUND,
                                        "request_status": 0})   
        except Exception as e:
            raise serializers.ValidationError({'status': status.HTTP_400_BAD_REQUEST,'request_status': 0, 'msg': e},code='authorization')

class LabourAPIView(APIView):
    """ Labour API View created by Aggregator and Grower"""
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    queryset = Labour.objects.filter(is_deleted=False)
    serializer_class = Labour
    def get(self, request, *args, **kwargs):
        try:
            id = self.request.query_params.get('id', None)
            name = self.request.query_params.get('name', None) 
            type = self.request.query_params.get('type', None) 
            date_from=self.request.query_params.get('date_from', None) 
            date_to=self.request.query_params.get('date_to', None)
            grower_id= self.request.query_params.get('grower_id', None)
            if id and grower_id:
                queryset = self.queryset.filter(grower_id=grower_id,created_by=request.user,id=id).order_by('-id')
                queryset1 = self.queryset.filter(grower_id=grower_id,id=id).order_by('-id')
                queryset=queryset.union(queryset1)
                queryset=queryset.order_by('-id')
            elif (name and type and grower_id):   
                queryset = self.queryset.filter(grower_id=grower_id,name__icontains=name,created_by=request.user,type__iexact=type,).order_by('-id') 
                queryset1 = self.queryset.filter(grower_id=grower_id,name__icontains=name,type__iexact=type).order_by('-id')
                queryset=queryset.union(queryset1)
                queryset=queryset.order_by('-id')  
            elif (type and grower_id):
                queryset = self.queryset.filter(grower_id=grower_id,created_by=request.user,type__iexact=type).order_by('-id') 
                queryset1 = self.queryset.filter(grower_id=grower_id,type__iexact=type).order_by('-id')
                queryset=queryset.union(queryset1)
                queryset=queryset.order_by('-id')  
            elif (date_from and date_to and grower_id):
                queryset = self.queryset.filter(grower_id=grower_id,created_by=request.user,created_at__range=[date_from,date_to]).order_by('-id')        
                queryset1 = self.queryset.filter(grower_id=grower_id,created_at__range=[date_from,date_to]).order_by('-id')
                queryset=queryset.union(queryset1)
                queryset=queryset.order_by('-id') 
            elif grower_id:
                queryset=self.queryset.filter(grower_id=grower_id,created_by=request.user).order_by('-id') 
                queryset1 = self.queryset.filter(grower_id=grower_id).order_by('-id')
                queryset=queryset.union(queryset1)
                queryset=queryset.order_by('-id')    
                print(queryset)
            else:
                queryset=""    
            page_size = int(request.query_params.get('page_size', 10))
            paginator = Paginator(queryset, page_size)
            page_number = self.request.query_params.get('page', 1)
            page = paginator.get_page(page_number)
            serializer = LabourSerializer(queryset, many=True)

            return Response({
                'count': paginator.count,
                'next': page.next_page_number() if page.has_next() else None,
                'previous': page.previous_page_number() if page.has_previous() else None,
                'results': serializer.data,
            })
        except Exception as e:
            raise serializers.ValidationError({'status': status.HTTP_400_BAD_REQUEST,'request_status': 0, 'msg': e},code='authorization')
    def post(self, request, format=None):
        try:
            grower_id=request.data.get('grower_id',None)
            name = request.data.get('name', None)
            type= request.data.get('type', None)
            gender= request.data.get('gender', None)
            age= request.data.get('age', None)
            with transaction.atomic(): 
                if grower_id:
                    created =  Labour.objects.create(grower_id=grower_id,name=name,type=type,\
                    		gender=gender,age=age,\
                       created_by=request.user)
                    created.save()

                    serializer = LabourSerializer(created)

                    return Response({'results':{
                                            'Data':serializer.data ,
                                            },
                                            'msg': 'Labour Created Successfully',
                                            'status':status.HTTP_201_CREATED,
                                            "request_status": 1})
        except Exception as e:
            raise serializers.ValidationError({'status': status.HTTP_400_BAD_REQUEST,'request_status': 0, 'msg': e},code='authorization') 
    

    def put(self, request, *args, **kwargs):
        """
        Below are the methods for Edit method and Delete method
        """
        try:
            method = self.request.query_params.get('method', None)
            id = self.request.query_params.get('id', None)
            with transaction.atomic():
                if method.lower() == 'edit':
                    grower_id=request.data.get('grower_id',None)
                    name = request.data.get('name', None)
                    type= request.data.get('type', None)
                    gender= request.data.get('gender', None)
                    age= request.data.get('age', None)

                    labour_details = Labour.cmobjects.filter(pk=id).first()

                    if not labour_details:
                        return Response({'results': [],
                                        'msg': "Selected labour Does'nt exists!",
                                        "request_status": 0}, status=status.HTTP_400_BAD_REQUEST)

                    update=Labour.cmobjects.filter(id=id)\
                        .update(grower_id=grower_id,name=name,type=type,\
                    		gender=gender,age=age,updated_by=request.user)
                    return Response({'results':{
                                            'Data':Labour.objects.filter(pk=id).values(),
                                            },
                                            'msg': 'Labour data  Updated SuccessFully',
                                            'status':status.HTTP_200_OK,
                                            "request_status": 1})

                elif method.lower() == 'delete':
                    """
                    Delete labour
                    """
                    if Labour.cmobjects.filter(id=id).exists():
                        labour_details= Labour.cmobjects.filter(id=id).first()
                        labour_details.is_deleted = True
                        labour_details.save()
                        return Response({'results':{
                                            'form_details':Labour.objects.filter(pk=id).values(),
                                            },
                                            'msg': 'Selected Labour Details Deleted Successfully',
                                            "request_status": 1})
                    else:
                        return Response({'results': [],
                                        'msg': "Selected Labour Does'nt exists!",
                                        'status': status.HTTP_404_NOT_FOUND,
                                        "request_status": 0})   
        except Exception as e:
            raise serializers.ValidationError({'status': status.HTTP_400_BAD_REQUEST,'request_status': 0, 'msg': e},code='authorization')              

class FertilizerListAPIView(APIView):
    """ Fetilizer List  View"""
    authentication_classes = (TokenAuthentication,)
    permission_classes=(IsAuthenticated,)   
    queryset = ChemicalData.objects.filter(chemical_type__name__iexact="Fertilizer",is_deleted=False)
    serializer_class = ChemicalDataSerializer
    def get(self, request, *args, **kwargs):
        try:
            id = self.request.query_params.get('id', None)          
            if id:
                queryset = self.queryset.filter(id=id).order_by('-id')
            else:
                queryset=self.queryset.order_by('-id') 
                print(queryset)   
            page_size = int(request.query_params.get('page_size', 10))
            paginator = Paginator(queryset, page_size)
            page_number = self.request.query_params.get('page', 1)
            page = paginator.get_page(page_number)
            serializer = ChemicalDataSerializer(queryset, many=True)

            return Response({
                'count': paginator.count,
                'next': page.next_page_number() if page.has_next() else None,
                'previous': page.previous_page_number() if page.has_previous() else None,
                # 'results': queryset.values('id','chemical_name','manufacturer',\
                #                                                              'brand_local_name' ,'composition',\
                #                                                                'chemical_type__name','created_by' ) ,
                'results':serializer.data ,
            })
        except Exception as e:
            raise serializers.ValidationError({'status': status.HTTP_400_BAD_REQUEST,'request_status': 0, 'msg': e},code='authorization')

class HerbicidesListAPIView(APIView):
    """ Herbicides List  View"""
    authentication_classes = (TokenAuthentication,)
    permission_classes=(IsAuthenticated,)   
    queryset = ChemicalData.objects.filter(chemical_type__name__iexact="Herbicides",is_deleted=False)
    serializer_class = ChemicalDataSerializer
    def get(self, request, *args, **kwargs):
        try:
            id = self.request.query_params.get('id', None)          
            if id:
                queryset = self.queryset.filter(id=id).order_by('-id')
            else:
                queryset=self.queryset.order_by('-id')    
            page_size = int(request.query_params.get('page_size', 10))
            paginator = Paginator(queryset, page_size)
            page_number = self.request.query_params.get('page', 1)
            page = paginator.get_page(page_number)
            serializer = ChemicalDataSerializer(queryset, many=True)
            return Response({
                'count': paginator.count,
                'next': page.next_page_number() if page.has_next() else None,
                'previous': page.previous_page_number() if page.has_previous() else None,
                'results':serializer.data ,
            })
        except Exception as e:
            raise serializers.ValidationError({'status': status.HTTP_400_BAD_REQUEST,'request_status': 0, 'msg': e},code='authorization')

class InsecticidesListAPIView(APIView):
    """  Insecticides & Fungicide List  View"""
    authentication_classes = (TokenAuthentication,)
    permission_classes=(IsAuthenticated,)   
    queryset = ChemicalData.objects.filter(chemical_type__name__iexact="Insecticides & Fungicides",is_deleted=False)
    serializer_class = ChemicalDataSerializer
    def get(self, request, *args, **kwargs):
        try:
            id = self.request.query_params.get('id', None)
            if id:
                queryset = self.queryset.filter(id=id).order_by('-id')
            else:
                queryset=self.queryset.order_by('-id')    
            page_size = int(request.query_params.get('page_size', 10))
            paginator = Paginator(queryset, page_size)
            page_number = self.request.query_params.get('page', 1)
            page = paginator.get_page(page_number)
            serializer = ChemicalDataSerializer(queryset, many=True)          
            return Response({
                'count': paginator.count,
                'next': page.next_page_number() if page.has_next() else None,
                'previous': page.previous_page_number() if page.has_previous() else None,
                'results':serializer.data ,
            })
        except Exception as e:
            raise serializers.ValidationError({'status': status.HTTP_400_BAD_REQUEST,'request_status': 0, 'msg': e},code='authorization')

class AcaricidesListAPIView(APIView):
    """ Acaricides List  View"""
    authentication_classes = (TokenAuthentication,)
    permission_classes=(IsAuthenticated,)
    queryset = ChemicalData.objects.filter(chemical_type__name__iexact="Acaricides",is_deleted=False)
    serializer_class = ChemicalDataSerializer
    def get(self, request, *args, **kwargs):
        try:
            id = self.request.query_params.get('id', None)
            if id:
                queryset = self.queryset.filter(id=id).order_by('-id')
            else:
                queryset=self.queryset.order_by('-id')    
            page_size = int(request.query_params.get('page_size', 10))
            paginator = Paginator(queryset, page_size)
            page_number = self.request.query_params.get('page', 1)
            page = paginator.get_page(page_number)
            serializer = ChemicalDataSerializer(queryset, many=True)
            return Response({
                'count': paginator.count,
                'next': page.next_page_number() if page.has_next() else None,
                'previous': page.previous_page_number() if page.has_previous() else None,
                'results':serializer.data ,
            })
        except Exception as e:
            raise serializers.ValidationError({'status': status.HTTP_400_BAD_REQUEST,'request_status': 0, 'msg': e},code='authorization')

class UseOfChemicalAPIView(APIView):
    """ Use of chemical API View"""
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    queryset = UseOfChemical.objects.filter(is_deleted=False)
    serializer_class = UseOfChemicalSerializer
    def get(self, request, *args, **kwargs):
        try:
            id = self.request.query_params.get('id', None) 
            grower_id = self.request.query_params.get('grower_id', None) #for grower specific
            chemical_type=self.request.query_params.get('chemical_type', None) #for list according to chemical type
            date_from= self.request.query_params.get('date_from', None)
            date_to= self.request.query_params.get('date_to', None)         
            if id:
                queryset = self.queryset.filter(grower_id=grower_id,created_by=request.user,id=id,\
                                                chemical__chemical_type__name__iexact=chemical_type).order_by('-id')
                # queryset1 = self.queryset.filter(created_by__profile_id_grower__id=grower_id,id=id,\
                #                                 chemical__chemical_type__name__iexact=chemical_type).order_by('-id')
                queryset1 = self.queryset.filter(grower_id=grower_id,id=id,\
                                                chemical__chemical_type__name__iexact=chemical_type).order_by('-id')
                queryset=queryset.union(queryset1)
                queryset=queryset.order_by('-id')
            elif (date_from and date_to ) :
                queryset=self.queryset.filter(grower_id=grower_id,created_by=request.user,\
                                               chemical__chemical_type__name__iexact=chemical_type,date__range=[date_from,date_to]).\
                    order_by('-id') 
                queryset1=self.queryset.filter(grower_id=grower_id,\
                                               chemical__chemical_type__name__iexact=chemical_type,date__range=[date_from,date_to]).\
                    order_by('-id')    
                queryset=queryset.union(queryset1)
                queryset=queryset.order_by('-id')
            else:
                queryset=self.queryset.filter(grower_id=grower_id,created_by=request.user,\
                                              chemical__chemical_type__name__iexact=chemical_type).order_by('-id')    
                # print(queryset)
                queryset1=self.queryset.filter(grower_id=grower_id,\
                                               chemical__chemical_type__name__iexact=chemical_type).\
                    order_by('-id') 
                print("queryset1",queryset1)   
                queryset=queryset.union(queryset1)
                queryset=queryset.order_by('-id')
            page_size = int(request.query_params.get('page_size', 10))
            paginator = Paginator(queryset, page_size)
            page_number = self.request.query_params.get('page', 1)
            page = paginator.get_page(page_number)
            serializer = UseOfChemicalSerializer(queryset, many=True)
            return Response({
                'count': paginator.count,
                'next': page.next_page_number() if page.has_next() else None,
                'previous': page.previous_page_number() if page.has_previous() else None,
                'results': serializer.data,
            })
        except Exception as e:
            raise serializers.ValidationError({'status': status.HTTP_400_BAD_REQUEST,'request_status': 0, 'msg': e},code='authorization')
    def post(self, request, format=None):
        try:
            grower_id= request.data.get('grower_id', None)
            date= request.data.get('date', None)
            chemical_id= request.data.get('chemical_id', None)
            labour_id= request.data.get('labour_id', None)
            plot_id= request.data.get('plot_id', None)
            division_id= request.data.get('division_id', None)
            quantity= request.data.get('quantity', None)
            unit= request.data.get('unit', None)

            with transaction.atomic(): 
                if grower_id:
                    created =  UseOfChemical.objects.create(grower_id=grower_id,date=date,\
                    		chemical_id=chemical_id,quantity=quantity,unit=unit,\
                       created_by=request.user)
                    created.save()
                    if labour_id:
                        created.labour_id=labour_id
                        created.save()
                    if plot_id:
                        created.plot_id=plot_id
                        created.save()    
                    if division_id:    
                        created.division_id=division_id
                        created.save() 
                    serializer = UseOfChemicalSerializer(created)
                    return Response({'results':{
                                            'Data':serializer.data ,
                                            },
                                            'msg': 'Use of Chemical Created Successfully',
                                            'status':status.HTTP_201_CREATED,
                                            "request_status": 1})
        except Exception as e:
            raise serializers.ValidationError({'status': status.HTTP_400_BAD_REQUEST,'request_status': 0, 'msg': e},code='authorization') 
    

    def put(self, request, *args, **kwargs):
        """
        Below are the methods for Edit method and Delete method
        """
        try:
            method = self.request.query_params.get('method', None)
            id = self.request.query_params.get('id', None)


            with transaction.atomic():
                if method.lower() == 'edit':
                    grower_id= request.data.get('grower_id', None)
                    date= request.data.get('date', None)
                    chemical_id= request.data.get('chemical_id', None)
                    labour_id= request.data.get('labour_id', None)
                    plot_id= request.data.get('plot_id', None)
                    division_id=request.data.get('division_id', None)
                    quantity= request.data.get('quantity', None)
                    unit= request.data.get('unit', None)
                    chemical_details = UseOfChemical.cmobjects.filter(pk=id).first()

                    if not chemical_details:
                        return Response({'results': [],
                                        'msg': "Selected Chemical Does'nt exists!",
                                        "request_status": 0}, status=status.HTTP_400_BAD_REQUEST)

                    # update=UseOfChemical.cmobjects.filter(id=id)\
                    #     .update(grower_id=grower_id,date=date,\
                    # 		chemical_id=chemical_id,quantity=quantity,updated_by=request.user)
                    chemical_details.grower_id=grower_id
                    chemical_details.date=date
                    chemical_details.chemical_id=chemical_id
                    chemical_details.quantity=quantity
                    chemical_details.unit=unit
                    chemical_details.updated_by=request.user
                    if labour_id:
                        chemical_details.labour_id=labour_id
                    else:
                        chemical_details.labour_id=None
                    if plot_id:
                        chemical_details.plot_id=plot_id 
                    else:
                        chemical_details.plot_id=None 
                    if division_id:
                        chemical_details.division_id=division_id
                    else:
                        chemical_details.division_id=division_id      
                    chemical_details.save()

                    return Response({'results':{
                                            'Data':UseOfChemical.objects.filter(pk=id).values(),
                                            },
                                            'msg': ' User of Chemical Updated SuccessFully',
                                            'status':status.HTTP_200_OK,
                                            "request_status": 1})
            
                elif method.lower() == 'delete':
                   """
                   Delete a Use of chemical
                   """
                   if UseOfChemical.cmobjects.filter(id=id).exists():
                       chemical_details= UseOfChemical.cmobjects.filter(id=id).first()
                       chemical_details.is_deleted = True
                       chemical_details.save()
                       
                       return Response({'results':{
                                           'form_details':UseOfChemical.objects.filter(pk=id).values(),
                                           },
                                           'msg': 'Selected Use of chemicals Details Deleted Successfully',
                                           "request_status": 1})
                   else:
                       return Response({'results': [],
                                       'msg': "Selected Labour Does'nt exists!",
                                       'status': status.HTTP_404_NOT_FOUND,
                                       "request_status": 0})   
        except Exception as e:
            raise serializers.ValidationError({'status': status.HTTP_400_BAD_REQUEST,'request_status': 0, 'msg': e},code='authorization')            

class PluckingDataAPIView(APIView):
    """ Plucking Data API View"""
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    queryset = PluckingData.objects.filter(is_deleted=False)
    serializer_class = PluckingDataSerializer
    def get(self, request, *args, **kwargs):
        try:
            id = self.request.query_params.get('id', None)     
            date_from= self.request.query_params.get('date_from', None)
            date_to= self.request.query_params.get('date_to', None) 
            grower_id= self.request.query_params.get('grower_id', None)   
            if id:
                queryset = self.queryset.filter(created_by=request.user,id=id,grower_id=grower_id).order_by('-id')
                queryset1 = self.queryset.filter(grower_id=grower_id).order_by('-id')
                queryset=queryset.union(queryset1)
                queryset=queryset.order_by('-id')
            elif (date_from and date_to ) :
                queryset=self.queryset.filter(created_by=request.user,grower_id=grower_id,date__range=[date_from,date_to]).\
                   order_by('-id') 
                queryset1= self.queryset.filter(grower_id=grower_id,date__range=[date_from,date_to]).\
                   order_by('-id')  
                queryset=queryset.union(queryset1)
                queryset=queryset.order_by('-id')
            else:
                queryset=self.queryset.filter(created_by=request.user,grower_id=grower_id).order_by('-id')
                queryset1=self.queryset.filter(grower_id=grower_id).order_by('-id') 
                queryset=queryset.union(queryset1)
                queryset=queryset.order_by('-id')    
                print(queryset)
            page_size = int(request.query_params.get('page_size', 10))
            paginator = Paginator(queryset, page_size)
            page_number = self.request.query_params.get('page', 1)
            page = paginator.get_page(page_number)
            serializer = PluckingDataSerializer(queryset, many=True)

            return Response({
                'count': paginator.count,
                'next': page.next_page_number() if page.has_next() else None,
                'previous': page.previous_page_number() if page.has_previous() else None,
                'results': serializer.data,
            })
        except Exception as e:
            raise serializers.ValidationError({'status': status.HTTP_400_BAD_REQUEST,'request_status': 0, 'msg': e},code='authorization')
    def post(self, request, format=None):
        try:
			
            grower_id= request.data.get('grower_id', None)
            date= request.data.get('date', None)
            start_time= request.data.get('start_time', None)
            end_time= request.data.get('end_time', None)
            labour_id= request.data.get('labour_id', None)
            plot_id= request.data.get('plot_id', None)
            division_id= request.data.get('division_id', None)
            area_plucked= request.data.get('area_plucked', None)
            quantity_plucked= request.data.get('quantity_plucked', None)

            
            with transaction.atomic(): 
                if grower_id:
                    created =  PluckingData.objects.create(grower_id=grower_id,date=date,\
                    		start_time=start_time,end_time=end_time,\
                                area_plucked=area_plucked,quantity_plucked=quantity_plucked,\
                       created_by=request.user)
                    created.save()
                    if labour_id:
                        created.labour_id=labour_id
                        created.save()
                    if plot_id:
                        created.plot_id=plot_id
                        created.save()
                    if division_id:
                        created.division_id=division_id
                        created.save()            

                serializer = PluckingDataSerializer(created)


                return Response({'results':{
                                        'Data':serializer.data ,
                                        },
                                        'msg': 'Plucking Data Created Successfully',
                                        'status':status.HTTP_201_CREATED,
                                        "request_status": 1})
        except Exception as e:
            raise serializers.ValidationError({'status': status.HTTP_400_BAD_REQUEST,'request_status': 0, 'msg': e},code='authorization') 
    

    def put(self, request, *args, **kwargs):
        """
        Below are the methods for Edit method and Delete method
        """
        try:
            method = self.request.query_params.get('method', None)
            id = self.request.query_params.get('id', None)


            with transaction.atomic():
                if method.lower() == 'edit':
                    grower_id= request.data.get('grower_id', None)
                    date= request.data.get('date', None)
                    start_time= request.data.get('start_time', None)
                    end_time= request.data.get('end_time', None)
                    labour_id= request.data.get('labour_id', None)
                    plot_id= request.data.get('plot_id', None)
                    area_plucked= request.data.get('area_plucked', None)
                    quantity_plucked= request.data.get('quantity_plucked', None)
                    division_id= request.data.get('division_id', None)
                    plucking_details= PluckingData.cmobjects.filter(pk=id).first()




                    if not plucking_details:
                        return Response({'results': [],
                                        'msg': "Selected Plucking Data Does'nt exists!",
                                        "request_status": 0}, status=status.HTTP_400_BAD_REQUEST)



                    if grower_id:
                        # update=PluckingData.cmobjects.filter(id=id)\
                        #     .update(grower_id=grower_id,date=date,\
                        # 		start_time=start_time,end_time=end_time,labour_id=labour_id,plot_id=plot_id,\
                        #             area_plucked=area_plucked,quantity_plucked=quantity_plucked,updated_by=request.user)
                        plucking_details.grower_id=grower_id
                        plucking_details.date=date
                        plucking_details.start_time=start_time
                        plucking_details.end_time=end_time
                        plucking_details.area_plucked=area_plucked
                        plucking_details.quantity_plucked=quantity_plucked
                        plucking_details.updated_by=request.user
                        if labour_id:
                            plucking_details.labour_id=labour_id
                        else:
                            plucking_details.labour_id=None
                        if plot_id:
                            plucking_details.plot_id=plot_id
                        else:
                              plucking_details.plot_id=None   
                        if division_id:
                            plucking_details.division_id=division_id
                        else:
                            plucking_details.division_id=None    
                        plucking_details.save()    
                        return Response({'results':{
                                                'Data':PluckingData.objects.filter(pk=id).values(),
                                                },
                                                'msg': 'Plucking Data Updated SuccessFully',
                                                'status':status.HTTP_200_OK,
                                                "request_status": 1})
          
                elif method.lower() == 'delete':
                    """
                    Delete a Plucking Data
                    """
                    if PluckingData.cmobjects.filter(id=id).exists():
                        plucking_details= PluckingData.cmobjects.filter(id=id).first()
                        plucking_details.is_deleted = True
                        plucking_details.save()

                        return Response({'results':{
                                            'form_details':PluckingData.objects.filter(pk=id).values(),
                                            },
                                            'msg': 'Selected Plucking Data Deleted Successfully',
                                            "request_status": 1})
                    else:
                        return Response({'results': [],
                                        'msg': "Selected Plucking Data Does'nt exists!",
                                        'status': status.HTTP_404_NOT_FOUND,
                                        "request_status": 0})   
        except Exception as e:
            raise serializers.ValidationError({'status': status.HTTP_400_BAD_REQUEST,'request_status': 0, 'msg': e},code='authorization')
class CollectionDetailsVehicleAPIView(APIView):
    """ Collection Details list API View"""
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    queryset = CollectionFromGrower.objects.filter(is_deleted=False)
    serializer_class = CollectionFromGrowerSerializer
    def get(self, request, *args, **kwargs):
        try:
            id = self.request.query_params.get('vehicle_id', None)          
            if id:
                queryset = self.queryset.filter(vehicle_number_id=id,is_complete=False).values('id','created_at','date','vehicle_option','grower','grower__name','vehicle_number',\
        'vehicle_number__vehicle_number','vehicle_option','keep_record','rate','latitude','longitude','created_by','quantity').order_by('-id')
            else:
                queryset=self.queryset.values('id','created_at','date','vehicle_option','grower','grower__name','vehicle_number',\
        'vehicle_number__vehicle_number','vehicle_option','keep_record','rate','latitude','longitude','created_by','quantity').order_by('-id')    
                print(queryset)
            page_size = int(request.query_params.get('page_size', 10))
            paginator = Paginator(queryset, page_size)
            page_number = self.request.query_params.get('page', 1)
            page = paginator.get_page(page_number)
            serializer = CollectionFromGrowerSerializer(queryset, many=True)

            return Response({
                'count': paginator.count,
                'next': page.next_page_number() if page.has_next() else None,
                'previous': page.previous_page_number() if page.has_previous() else None,
                # 'results': serializer.data,
                'results': queryset,
            })
        except Exception as e:
            raise serializers.ValidationError({'status': status.HTTP_400_BAD_REQUEST,'request_status': 0, 'msg': e},code='authorization')


class RegionAPIView(APIView):
    """ Region List API View"""
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    def get(self, request):
        id = self.request.query_params.get('id', None)
        all = self.request.query_params.get('all', None)
        order_by = self.request.query_params.get('order_by', '-id')
        search = {}
        search['is_deleted'] = False
        search = custom_filters(self.request, search, [])
        if id:
            list_data = Region.cmobjects.filter(id=id).first()
            serializer = RegionSerializer(list_data)
            return Response(serializer.data)
        list_data = Region.cmobjects.filter(*search).order_by(*str(order_by).split(","))
        if all == 'true':
            serializer = RegionSerializer(list_data, many=True)
            return Response({'results': serializer.data})
        page_size = int(request.query_params.get('page_size', settings.MIN_PAGE_SIZE))
        paginator = Paginator(list_data, page_size)
        page_number = self.request.query_params.get('page', 1)
        page = paginator.get_page(page_number)
        serializer = RegionSerializer(page, many=True)
        return Response({
            'count': paginator.count,
            'next': page.next_page_number() if page.has_next() else None,
            'previous': page.previous_page_number() if page.has_previous() else None,
            'results': serializer.data,
        })
    

class StateAPIView(APIView):
    """ State list API View"""
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    def get(self, request):
        id = self.request.query_params.get('id', None)
        all = self.request.query_params.get('all', None)
        order_by = self.request.query_params.get('order_by', '-id')
        search = {}
        search['is_deleted'] = False
        search = custom_filters(self.request, search, [])
        if id:
            list_data = State.objects.filter(id=id).first()
            serializer = StateSerializer(list_data)
            return Response(serializer.data)
        list_data = State.objects.filter(*search).order_by(*str(order_by).split(","))
        if all == 'true':
            serializer = StateSerializer(list_data, many=True)
            return Response({'results': serializer.data})
        page_size = int(request.query_params.get('page_size', settings.MIN_PAGE_SIZE))
        paginator = Paginator(list_data, page_size)
        page_number = self.request.query_params.get('page', 1)
        page = paginator.get_page(page_number)
        serializer = StateSerializer(page, many=True)
        return Response({
            'count': paginator.count,
            'next': page.next_page_number() if page.has_next() else None,
            'previous': page.previous_page_number() if page.has_previous() else None,
            'results': serializer.data,
        })
class DistrictAPIView(APIView):
    """ District list API View"""
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    def get(self, request):
        id = self.request.query_params.get('id', None)
        all = self.request.query_params.get('all', None)
        order_by = self.request.query_params.get('order_by', '-id')
        search = {}
        search['is_deleted'] = False
        search = custom_filters(self.request, search, [])
        if id:
            list_data = District.objects.filter(id=id).first()
            serializer = DistrictSerializer(list_data)
            return Response(serializer.data)
        list_data = District.objects.filter(*search).order_by(*str(order_by).split(","))
        if all == 'true':
            serializer = DistrictSerializer(list_data, many=True)
            return Response({'results': serializer.data})
        page_size = int(request.query_params.get('page_size', settings.MIN_PAGE_SIZE))
        paginator = Paginator(list_data, page_size)
        page_number = self.request.query_params.get('page', 1)
        page = paginator.get_page(page_number)
        serializer = DistrictSerializer(page, many=True)
        return Response({
            'count': paginator.count,
            'next': page.next_page_number() if page.has_next() else None,
            'previous': page.previous_page_number() if page.has_previous() else None,
            'results': serializer.data,
        })

class AggregatorListAPIView(APIView):
    """ Aggregator  list to be map with aggregator View"""
    authentication_classes = (TokenAuthentication,)
    permission_classes=(IsAuthenticated,)
    serializer_class = AggregatorProfileSerializer
    def get(self, request, *args, **kwargs):
        try:
            region_id=self.request.query_params.get('region_id', None)   
            state_id=self.request.query_params.get('state_id', None)
            if region_id and state_id:
                queryset=AggregatorProfile.objects.filter(is_deleted=False,region_id=region_id,state_id=state_id).exclude(user=request.user).order_by('-id')
            # serializer_class = AggregatorProfileSerializer
            # id = self.request.query_params.get('id', None)
    
            # if id:
            #     queryset = self.queryset.filter(id=id).order_by('-id')
            else:
                queryset=""
            page_size = int(request.query_params.get('page_size', 10))
            paginator = Paginator(queryset, page_size)
            page_number = self.request.query_params.get('page', 1)
            page = paginator.get_page(page_number)
            serializer = AggregatorProfileSerializer(queryset, many=True)

            return Response({
                'count': paginator.count,
                'next': page.next_page_number() if page.has_next() else None,
                'previous': page.previous_page_number() if page.has_previous() else None,
                'results': serializer.data,
            })
        except Exception as e:
            raise serializers.ValidationError({'status': status.HTTP_400_BAD_REQUEST,'request_status': 0, 'msg': e},code='authorization')
       
class AggregatorMappedAPIView(APIView):
    """ Aggregator  with aggregator mapping View"""
    authentication_classes = (TokenAuthentication,)
    permission_classes=(IsAuthenticated,)

    queryset=AggregatorProfile.objects.filter(is_deleted=False).exclude(associated_aggregator__isnull=True).order_by('-id')
    serializer_class = AggregatorProfileSerializer
    def get(self, request, *args, **kwargs):
       
        try:
            id = self.request.query_params.get('id', None)
    
            if id:
                queryset = self.queryset.filter(user=request.user,id=id).order_by('-id')
            else:
                queryset=self.queryset.filter(user=request.user).order_by('-id')    
            page_size = int(request.query_params.get('page_size', 10))
            paginator = Paginator(queryset, page_size)
            page_number = self.request.query_params.get('page', 1)
            page = paginator.get_page(page_number)
            serializer = AggregatorProfileSerializer(queryset, many=True)

            return Response({
                'count': paginator.count,
                'next': page.next_page_number() if page.has_next() else None,
                'previous': page.previous_page_number() if page.has_previous() else None,
                # 'results': queryset.values('id','updated_by_id','user_id','associated_aggregator','associated_aggregator__user__id',\
                #                            'associated_aggregator__name','associated_aggregator__region','associated_aggregator__state',
                #                            'name','mobile_number','email','region_id','state_id','district_id','user_file','is_active',\
                #                             'aggregator_type',),
                'result':serializer.data
            })
        except Exception as e:
            raise serializers.ValidationError({'status': status.HTTP_400_BAD_REQUEST,'request_status': 0, 'msg': e},code='authorization')
    def put(self, request, *args, **kwargs):
        try:
            method = self.request.query_params.get('method', None)
            # id = self.request.query_params.get('id', None)
            id=request.user
            with transaction.atomic():
                if method.lower() == 'edit':
                    # region_id= request.data.get('region_id', None)
                    # state_id= request.data.get('state_id', None)
                    aggregator_id= request.data.get('aggregator_id', None)

                    agent_details= AggregatorProfile.cmobjects.filter(user=id).first()
                    aggregator_details=AggregatorProfile.cmobjects.filter(id=aggregator_id).first()
                    print(agent_details)
                    if not agent_details:
                        return Response({'results': [],
                                        'msg': "Selected Agent Does'nt exists!",
                                        "request_status": 0}, status=status.HTTP_400_BAD_REQUEST)
                    # aggregator_details.region_id=region_id
                    # aggregator_details.state_id=state_id
                    agent_details.associated_aggregator.add(aggregator_id)
                    agent_details.updated_by=id
                    agent_details.save()
                    # aggregator_details.save()
                    # update=AggregatorProfile.cmobjects.filter(user=id)\
                    #     .update(region_id=region_id,state_id=state_id,\
                    # 		associated_aggregator_id=aggregator_id,updated_by=request.user)
                    return Response({'results':{
                                            'Data':AggregatorProfile.objects.filter(user=id).values('id','associated_aggregator','associated_aggregator__name',),
                                            },
                                            'msg': 'Aggregator Mapped SuccessFully',
                                            'status':status.HTTP_200_OK,
                                            "request_status": 1})   
                elif method.lower() == 'delete':
                    # region_id= request.data.get('region_id', None)
                    # state_id= request.data.get('state_id', None)
                    aggregator_id= self.request.query_params.get('aggregator_id', None)

                    agent_details= AggregatorProfile.cmobjects.filter(user=id).first()
                    if not agent_details:
                        return Response({'results': [],
                                        'msg': "Selected Agent Does'nt exists!",
                                        "request_status": 0}, status=status.HTTP_400_BAD_REQUEST)
                    # agent_details.region_id=region_id
                    # agent_details.state_id=state_id
                    agent_details.associated_aggregator.remove(aggregator_id)
                    agent_details.updated_by=id
                    agent_details.save()
                    # update=AggregatorProfile.cmobjects.filter(user=id)\
                    #     .update(region_id=region_id,state_id=state_id,\
                    # 		associated_aggregator_id=aggregator_id,updated_by=request.user)
                    return Response({
                                            'msg': 'Aggregator Removed SuccessFully',
                                            'status':status.HTTP_200_OK,
                                            "request_status": 1})           
        except Exception as e:
            raise serializers.ValidationError({'status': status.HTTP_400_BAD_REQUEST,'request_status': 0, 'msg': e},code='authorization')   

class BlfListAPIView(APIView):
    """ Blf list for map with aggregator or agent View"""
    authentication_classes = (TokenAuthentication,)
    permission_classes=(IsAuthenticated,)

    queryset=BlfProfile.objects.filter(is_deleted=False)    
    serializer_class = BlfProfileSerializer
    def get(self, request, *args, **kwargs):
       
        # queryset=AggregatorProfile.objects.filter(is_deleted=False).exclude(user=request.user).order_by('-id')
        try:    
            id = self.request.query_params.get('id', None)
            region_id= self.request.query_params.get('region_id', None)
            state_id=self.request.query_params.get('state_id', None)
            # if id:
            #     queryset = self.queryset.filter(id=id).order_by('-id')
            if region_id and state_id:
                queryset=self.queryset.filter(region_id=region_id,state_id=state_id).order_by('-id') 
            else:
                queryset = ""     
            page_size = int(request.query_params.get('page_size', 10))
            paginator = Paginator(queryset, page_size)
            page_number = self.request.query_params.get('page', 1)
            page = paginator.get_page(page_number)
            serializer = BlfProfileSerializer(queryset, many=True)

            return Response({
                'count': paginator.count,
                'next': page.next_page_number() if page.has_next() else None,
                'previous': page.previous_page_number() if page.has_previous() else None,
                'results': serializer.data,
            })
        except Exception as e:
            raise serializers.ValidationError({'status': status.HTTP_400_BAD_REQUEST,'request_status': 0, 'msg': e},code='authorization')

class BlfMappedAPIView(APIView):
    """ Aggregator  with aggregator mapping View"""
    authentication_classes = (TokenAuthentication,)
    permission_classes=(IsAuthenticated,)

    queryset=AggregatorProfile.objects.filter(is_deleted=False).exclude(associated_entity__isnull=True).order_by('-id')
    serializer_class = AggregatorProfileSerializer
    def get(self, request, *args, **kwargs):
       
        try:
            id = self.request.query_params.get('id', None)
    
            if id:
                queryset = self.queryset.filter(user=request.user,id=id).order_by('-id')
            else:
                queryset=self.queryset.filter(user=request.user).order_by('-id')    
            page_size = int(request.query_params.get('page_size', 10))
            paginator = Paginator(queryset, page_size)
            page_number = self.request.query_params.get('page', 1)
            page = paginator.get_page(page_number)
            serializer = AggregatorProfileSerializer(queryset, many=True)

            return Response({
                'count': paginator.count,
                'next': page.next_page_number() if page.has_next() else None,
                'previous': page.previous_page_number() if page.has_previous() else None,
                'results': serializer.data,
                # 'results':queryset.values('id','updated_by_id','user_id','associated_entity','associated_entity__user__id',\
                #                            'associated_entity__user__username','associated_entity__region',\
                #                            'associated_entity__state',
                #                            'name','mobile_number','email','region_id','state_id','district_id','user_file','is_active',\
                #                             'aggregator_type',),
            })
        except Exception as e:
            raise serializers.ValidationError({'status': status.HTTP_400_BAD_REQUEST,'request_status': 0, 'msg': e},code='authorization')
    def put(self, request, *args, **kwargs):
        try:
            method = self.request.query_params.get('method', None)
            # id = self.request.query_params.get('id', None)
            id=request.user
            with transaction.atomic():
                if method.lower() == 'edit':
                    # region_id= request.data.get('region_id', None)
                    # state_id= request.data.get('state_id', None)
                    blf_id= request.data.get('blf_id', None)


                    agent_details= AggregatorProfile.cmobjects.filter(user=id).first()
                    blf_details=BlfProfile.cmobjects.filter(id=blf_id).first()
                    print(agent_details)
                    if not agent_details:
                        return Response({'results': [],
                                        'msg': "Selected Agent Does'nt exists!",
                                        "request_status": 0}, status=status.HTTP_400_BAD_REQUEST)
                    # blf_details.region_id=region_id
                    # blf_details.state_id=state_id
                    agent_details.associated_entity.add(blf_id)
                    # agent_details.associated_entity_id=blf_id
                    agent_details.updated_by=id
                    agent_details.save()
                    # blf_details.save()
                    # update=AggregatorProfile.cmobjects.filter(user=id)\
                    #     .update(region_id=region_id,state_id=state_id,\
                    # 		associated_aggregator_id=aggregator_id,updated_by=request.user)
                    return Response({'results':{
                                            'Data':AggregatorProfile.objects.filter(user=id).values('id','associated_entity','associated_entity__user__username'),
                                            },
                                            'msg': 'Blf or Factory  Mapped SuccessFully',
                                            'status':status.HTTP_200_OK,
                                            "request_status": 1})   
                elif method.lower() == 'delete':
                    # region_id= request.data.get('region_id', None)
                    # state_id= request.data.get('state_id', None)
                    blf_id=self.request.query_params.get('blf_id', None)


                    agent_details= AggregatorProfile.cmobjects.filter(user=id).first()
                    print(agent_details)
                    if not agent_details:
                        return Response({'results': [],
                                        'msg': "Selected Agent Does'nt exists!",
                                        "request_status": 0}, status=status.HTTP_400_BAD_REQUEST)
                    # agent_details.region_id=region_id
                    # agent_details.state_id=state_id
                    agent_details.associated_entity.remove(blf_id)
                    # agent_details.associated_entity_id=blf_id
                    agent_details.updated_by=id
                    agent_details.save()
                    # update=AggregatorProfile.cmobjects.filter(user=id)\
                    #     .update(region_id=region_id,state_id=state_id,\
                    # 		associated_aggregator_id=aggregator_id,updated_by=request.user)
                    return Response({
                                            'msg': 'Blf or Factory  Remove SuccessFully',
                                            'status':status.HTTP_200_OK,
                                            "request_status": 1})              
        except Exception as e:
            raise serializers.ValidationError({'status': status.HTTP_400_BAD_REQUEST,'request_status': 0, 'msg': e},code='authorization')   

class SupplyManagementAPIView(APIView):
    """ Supply Management API View"""
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    def get(self, request):
        id = self.request.query_params.get('id', None)
        all = self.request.query_params.get('all', None)
        order_by = self.request.query_params.get('order_by', '-id')
        search = {}
        user_type = Profile.cmobjects.filter(user=request.user).values_list('user_type__name', flat=True).first()
        if user_type != "blf":
            search['created_by'] = request.user
        search = custom_filters(self.request, search, [])
        if id:
            list_data = SupplyManagement.cmobjects.filter(id=id).first()
            serializer = SupplyManagementSerializer(list_data)
            return Response(serializer.data)
        list_data = SupplyManagement.cmobjects.filter(*search).order_by(*str(order_by).split(","))
        if all == 'true':
            serializer = SupplyManagementSerializer(list_data, many=True)
            return Response({'results': serializer.data})
        
        today = timezone.now().date()
        thirty_days_ago = today - timedelta(days=30)
        tot_gross_leaf_in_30_days_factory = (
            SupplyManagement.cmobjects
            .filter(
                created_by=request.user,
                supply_to="Factory",
                date_of_supply__range=[thirty_days_ago, today],
                gross_leaf__isnull=False,
            )
            .annotate(gross_leaf_float=Cast(F("gross_leaf"), FloatField()))
            .aggregate(total=Sum("gross_leaf_float"))["total"] or 0
        )
        tot_gross_leaf_in_30_days_aggregator = (
            SupplyManagement.cmobjects
            .filter(
                created_by=request.user,
                supply_to="Aggregator",
                date_of_supply__range=[thirty_days_ago, today],
                gross_leaf__isnull=False,
            )
            .annotate(gross_leaf_float=Cast(F("gross_leaf"), FloatField()))
            .aggregate(total=Sum("gross_leaf_float"))["total"] or 0
        )

        page_size = int(request.query_params.get('page_size', settings.MIN_PAGE_SIZE))
        paginator = Paginator(list_data, page_size)
        page_number = self.request.query_params.get('page', 1)
        page = paginator.get_page(page_number)
        serializer = SupplyManagementSerializer(page, many=True)
        return Response({
            'count': paginator.count,
            'next': page.next_page_number() if page.has_next() else None,
            'previous': page.previous_page_number() if page.has_previous() else None,
            'results': serializer.data,
            "tot_gross_leaf_in_30_days_factory" : tot_gross_leaf_in_30_days_factory,
            "tot_gross_leaf_in_30_days_aggregator" : tot_gross_leaf_in_30_days_aggregator,
        })
    
    def post(self, request):
        request.data['created_by'] = request.user.id
        serializer = SupplyManagementSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            # try:
            serializer.save()
            # except Exception as e:
            #     error_message = str(e.args[0]) if e.args else str(e)
            #     raise APIException({'request_status': 0, 'msg': error_message})
            return Response(
                {'results': {'Data': serializer.data,},
                    'msg': 'Successfully created',
                    'status': status.HTTP_201_CREATED,
                    "request_status": 1})
        raise APIException({'request_status': 0, 'msg': serializer.errors})
    def put(self, request):
        method = request.query_params.get('method')
        supply_id = request.query_params.get('id')
        if not method:
            raise APIException({'request_status': 0, 'msg': "Method parameter is required"})
        if not supply_id:
            raise APIException({'request_status': 0, 'msg': "ID parameter is required"})
        with transaction.atomic():
            if method.lower() == 'edit':
                supply = SupplyManagement.cmobjects.filter(pk=supply_id).first()
                if not supply:
                    raise APIException({'request_status': 0, 'msg': "Supply not found"})

                serializer = SupplyManagementSerializer(
                    supply, data=request.data, context={'request': request}
                )
                if serializer.is_valid():
                    try:
                        serializer.save()
                    except Exception as e:
                        error_message = str(e.args[0]) if e.args else str(e)
                        raise APIException({'request_status': 0, 'msg': error_message})
                    return Response({
                        'results': {'Data': serializer.data},
                        'msg': "Successfully updated",
                        'status': status.HTTP_202_ACCEPTED,
                        'request_status': 1
                    })
                else:
                    raise APIException({'request_status': 0, 'msg': serializer.errors})
            elif method.lower() == 'delete':
                supply = SupplyManagement.cmobjects.filter(pk=supply_id).first()
                if not supply:
                    raise APIException({'request_status': 0, 'msg': "Supply not found"})
                supply.is_deleted = True
                supply.updated_by_id = request.user.id
                supply.save()
                return Response({
                    'results': {'data': SupplyManagement.cmobjects.filter(pk=supply_id).values()},
                    'msg': 'Successfully deleted',
                    'request_status': 1
                })
            else:
                raise APIException({'request_status': 0, 'msg': "Invalid method parameter"})
            
class SupplyAndEarnBookAPIView(APIView):
    """ Supply and Earn Book View"""
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    queryset= SupplyManagement.objects.filter(is_deleted=False)
    serializer_class = SupplyManagementSerializer
    def get(self, request, *args, **kwargs):
        try:
            id = self.request.query_params.get('id', None) 
            supply_to_type= self.request.query_params.get('supply_to_type', None)
            print(supply_to_type) 
            date_from= self.request.query_params.get('date_from', None)
            date_to= self.request.query_params.get('date_to', None)          
            if id:
                queryset = self.queryset.filter(created_by=request.user,supply_to__iexact=supply_to_type,id=id).order_by('-id')
            elif (date_from and date_to ) :
                 queryset=self.queryset.filter(created_by=request.user,supply_to__iexact=supply_to_type,date_of_supply__range=[date_from,date_to]).\
                    order_by('-id')     
            else:
                queryset=self.queryset.filter(created_by=request.user,supply_to__iexact=supply_to_type).order_by('-id')    
                print(queryset)
            page_size = int(request.query_params.get('page_size', 10))
            paginator = Paginator(queryset, page_size)
            page_number = self.request.query_params.get('page', 1)
            page = paginator.get_page(page_number)
            serializer = SupplyManagementSerializer(queryset, many=True)
            return Response({
                'count': paginator.count,
                'next': page.next_page_number() if page.has_next() else None,
                'previous': page.previous_page_number() if page.has_previous() else None,
                # 'result': queryset.values('id','supply_to','consumer','consumer__username','consumer__profile_id_blf','consumer__profile_id_aggregator',
                #                           'consumer__profile_id_aggregator__name',\
                #                           'date_of_supply',\
                #                          'alloted_vehicle', 'alloted_vehicle__vehicle_number','gross_leaf',\
                #                             ),
                'result':serializer.data
            })
        except Exception as e:
            raise serializers.ValidationError({'status': status.HTTP_400_BAD_REQUEST,'request_status': 0, 'msg': e},\
                                              code='authorization')
        
class TotalCollectionAndSupplyAPIView(APIView):
    """ Total Collection and Supply """
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    queryset1 = CollectionFromAggregator.objects.filter(is_deleted=False)
    queryset2 = CollectionFromGrower.objects.filter(is_deleted=False)
    queryset3= SupplyManagement.objects.filter(is_deleted=False)
    def get(self, request, *args, **kwargs):
        try:
            id = self.request.query_params.get('id', None)    
            date_from=self.request.query_params.get('date_from', None)
            date_to=self.request.query_params.get('date_to', None)
            total_supply=0
            total_quantity_agg=0
            total_quantity_grow=0
            total_collected_quantity_grower_details = 0
            total_collected_quantity_grower_details_vehicle=0
            if (date_from and date_to):
                queryset1= self.queryset1.filter(created_by=request.user,date__range=[date_from,date_to]).order_by('-id')
                queryset2 = self.queryset2.filter(created_by=request.user,date__range=[date_from,date_to]).order_by('-id')
                queryset3=self.queryset3.filter(created_by=request.user,date_of_supply__range=[date_from,date_to]).\
                    order_by('-id') 
                grower_details_queryset = GrowerDetailsSupply.objects.filter(created_by=request.user,collected_date__range=[date_from,date_to])
                for data in grower_details_queryset:
                    if data.collected_quantity:
                        total_collected_quantity_grower_details += float(data.collected_quantity)
                    if data.collected_quantity_vehicle:
                        total_collected_quantity_grower_details_vehicle +=float(data.collected_quantity_vehicle) 
                total_collection_grower=0
                total_collection_grower=0   
                total_collected_quantity=0
                total_supply_qty=0
                if queryset1:
                    for data in queryset1:
                        if data.quantity is not None:
                            quantity=(data.quantity)
                            total_quantity_agg=total_quantity_agg+float(quantity)
                        else:
                            total_quantity_agg=0    
                total_collection_aggregator=total_quantity_agg
                if queryset2:    
                    for data in queryset2:
                        if data.quantity is not None:
                            quantity=(data.quantity)
                            print('qunaitty grower',quantity)
                            total_quantity_grow=total_quantity_grow+float(quantity)
                        else:
                            total_quantity_grow=0    
                total_collection_grower=total_quantity_grow   
                total_collected_quantity=total_collection_grower + total_collection_aggregator + total_collected_quantity_grower_details - total_collected_quantity_grower_details_vehicle
                if queryset3:
                    for data in queryset3:
                        if data.gross_leaf is not None:
                            gross_leaf=(data.gross_leaf)
                            print('qunaitty gross_leaf',gross_leaf)
                            total_supply=total_supply+float(gross_leaf)
                        else:
                            total_supply=0    

                total_supply_qty=total_supply   
                # total_collected_quantity=total_collection_grower + total_collection_aggregator
            else:
                queryset1=self.queryset1.filter(created_by=request.user)
                queryset2=self.queryset2.filter(created_by=request.user)
                queryset3=self.queryset3.filter(created_by=request.user)
                print(queryset3)
                grower_details_queryset = GrowerDetailsSupply.objects.filter(created_by=request.user,)
                for data in grower_details_queryset:
                    if data.collected_quantity:
                        total_collected_quantity_grower_details += float(data.collected_quantity)
                    if data.collected_quantity_vehicle:
                        total_collected_quantity_grower_details_vehicle +=float(data.collected_quantity_vehicle)
                total_quantity_agg=0
                total_quantity_grow=0
                total_supply=0
                total_collection_grower=0
                total_collection_grower=0   
                total_collected_quantity=0
                total_supply_qty=0
                if queryset1:
                    for data in queryset1:
                        if data.quantity is not None:
                            quantity=(data.quantity)
                            total_quantity_agg=total_quantity_agg+float(quantity)
                        else:
                             total_quantity_agg=0   
                total_collection_aggregator=total_quantity_agg
                if queryset2:    
                    for data in queryset2:
                        if data.quantity is not None:
                            quantity=(data.quantity)
                            print('qunaitty grower',quantity)
                            total_quantity_grow=total_quantity_grow+float(quantity)
                        else:
                             total_quantity_grow=0   

                total_collection_grower=total_quantity_grow 
                # total_collected_quantity_growerdetails_also=total_collection_grower + total_collection_aggregator + total_collected_quantity_grower_details
                total_collected_quantity=total_collection_grower + total_collection_aggregator + total_collected_quantity_grower_details - total_collected_quantity_grower_details_vehicle
                # if total_collected_quantity_growerdetails_also > total_collected_quantity:
                #     total_collected_quantity=total_collected_quantity_growerdetails_also
                # else:
                #     total_collected_quantity=  total_collected_quantity  

                
                
                if queryset3:
                    for data in queryset3:
                        if data.gross_leaf is not None:
                            gross_leaf=(data.gross_leaf)
                            print('qunaitty gross_leaf',gross_leaf)
                            total_supply=total_supply+float(gross_leaf)
                        else:
                            total_supply=0    
                total_supply_qty=total_supply   
                
                     
            return Response({
                
                # 'results': queryset.values('quantity'),
                'total_collection_from_grower': total_collection_grower,
                'total_collection_from_aggregator':total_collection_aggregator,
                'total_collected_quantity':total_collected_quantity,
                'total_supply_quantity':total_supply_qty
            })
        except Exception as e:
            raise serializers.ValidationError({'status': status.HTTP_400_BAD_REQUEST,'request_status': 0, 'msg': e},code='authorization')        

class ProfileUpdateAPIView(APIView):
    """ Profile Update API View"""
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    
    def put(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                profile_type=self.request.query_params.get('profile_type', None) 
                
                if profile_type.lower() == "agggregator":
                    user_details=AggregatorProfile.objects.filter(user=request.user)
                    if not user_details:
                            return Response({'results': [],
                                            'msg': "Selected User Does'nt exists!",
                                            "request_status": 0}, status=status.HTTP_400_BAD_REQUEST)
                    user_details.name=request.data.get('name', user_details.name)
                    user_details.save()
                    return Response({
                        'status': status.HTTP_200_OK,'request_status': 1,
                        'msg': 'profile updated sucessfully'
                    })  

                elif profile_type.lower() == "blf":
                    user_details=BlfProfile.objects.filter(user=request.user)
                    if not user_details:
                            return Response({'results': [],
                                            'msg': "Selected User Does'nt exists!",
                                            "request_status": 0}, status=status.HTTP_400_BAD_REQUEST)
                    user_details.entity_unit=request.data.get('name', user_details.entity_unit)
                    user_details.region_id=request.data.get('region_id',user_details.region_id)
                    user_details.state_id=request.data.get('state_id',user_details.state_id)
                    user_details.mobile_number=request.data.get('mobile_number',user_details.mobile_number)
                    user_details.address=request.data.get('address',user_details.address)
                    user_details.save() 
                    return Response({
                        'status': status.HTTP_200_OK,'request_status': 1,
                        'msg': 'profile updated sucessfully'
                    }) 
                elif profile_type.lower() == "grower":
                    user_details=GrowerProfile.objects.filter(user=request.user)
                    if not user_details:
                            return Response({'results': [],
                                            'msg': "Selected User Does'nt exists!",
                                            "request_status": 0}, status=status.HTTP_400_BAD_REQUEST)
                    user_details.name=request.data.get('name', user_details.name)
                    user_details.save()
                    return Response({
                        'status': status.HTTP_200_OK,'request_status': 1,
                        'msg': 'profile updated sucessfully'
                    })
                else:
                    return Response({
                        'status': status.HTTP_400_BAD_REQUEST,'request_status': 0,
                        'msg': 'profile type is missing( may be blf, grower or aggregator)'
                    })
        except Exception as e:
            raise serializers.ValidationError({'status': status.HTTP_400_BAD_REQUEST,'request_status': 0, 'msg': e},\
 
 
                                              code='authorization')
from django.db.models import Sum
class GenerateChallanPdfAPIView(APIView):
    """ Generate Challan pdf"""
    permission_classes = [AllowAny]
    # authentication_classes = (TokenAuthentication,)
    # permission_classes = (IsAuthenticated,)
    def get(self, request, *args, **kwargs):
        try:
            id = self.request.query_params.get('id', None)    
             # Replace with the path to your HTML template
            challan_details = SupplyManagement.cmobjects.filter(pk=id).first()
            grower_details_supply=GrowerDetailsSupply.objects.filter(supply_id=challan_details.id)
            blf_details = BlfProfile.cmobjects.filter(user_id=challan_details.consumer_id).first()
            print("blf details",blf_details)
            agg_supplier_details = AggregatorProfile.cmobjects.filter(user_id=challan_details.created_by_id).first()
            grower_supplier_details = GrowerProfile.cmobjects.filter(user_id=challan_details.created_by_id).first()
            profile_type = None
            if grower_supplier_details:
                profile_type = "grower"
            elif agg_supplier_details:
                profile_type = "aggregator"
            else:
                profile_type = None
            profile_type = str(Profile.objects.filter(user_id=challan_details.created_by_id).first().user_type)
            print(grower_details_supply)
            print("profilettype",profile_type)
            total_qty = grower_details_supply.aggregate(total_supply_quantity=Sum('supply_quantity'))['total_supply_quantity'] or 0
            total_collected_qty = grower_details_supply.aggregate(total_collected_qty=Sum('collected_quantity'))['total_collected_qty'] or 0

            alloted_vehicle=VehicleManagement.objects.filter(id= challan_details.alloted_vehicle_id).first()
            
            context = {
            'challan_details': challan_details,
            'blf_details': blf_details,
            'vehicle_details':alloted_vehicle.vehicle_number if alloted_vehicle else None,
            'grower_details_supply': grower_details_supply,
            'total_qty': total_qty, # Pass the total supply quantity to the context
            'total_collected_qty':total_collected_qty,
            'agg_supplier_details': agg_supplier_details,
            'grower_supplier_details': grower_supplier_details,
            'profile_type': profile_type,
            }# Provide context data if needed
            template_path = 'delivery_challan_pdf.html'
            # return render(request,"delivery_challan_pdf.html", context)
            template = get_template(template_path)
            html = template.render(context)

            response = HttpResponse(content_type='application/pdf')
            # response['Content-Disposition'] = 'attachment; filename="delivery_challan.pdf"'
            response['Content-Disposition'] = 'filename="delivery_challan.pdf"'

            pisa_status = pisa.CreatePDF(html, dest=response)
            if pisa_status.err:
                return HttpResponse('Error generating PDF', status=500)

            return response
        except Exception as e:
            raise serializers.ValidationError({'status': status.HTTP_400_BAD_REQUEST,'request_status': 0, 'msg': e},code='authorization') 

class GenerateLabourListPdfAPIView(APIView):
    """ Generate Labour List pdf"""
    permission_classes = [AllowAny]
    # authentication_classes = (TokenAuthentication,)
    # permission_classes = (IsAuthenticated,)
   
    def get(self, request, *args, **kwargs):
        try:
            grower_id = self.request.query_params.get('grower_id', None)   
            name = self.request.query_params.get('name', None) 
            type = self.request.query_params.get('type', None) 
            date_from=self.request.query_params.get('date_from', None) 
            date_to=self.request.query_params.get('date_to', None) 
            template_path = 'labour_list_pdf.html' # Replace with the path to your HTML template
            grower_details = GrowerProfile.cmobjects.filter(id=grower_id).first()
            garden_details=Gardens.objects.filter(grower_id=grower_id).first()
            # labour_list = Labour.cmobjects.filter(Q(grower_id=id) | Q(created_by_id=request.user.id)).order_by('-id')
            # if grower_details.photo:
            #     user_file_path = os.path.join(settings.MEDIA_URL, str(grower_details.photo))
            #     complete_url = request.build_absolute_uri(user_file_path)
            #     image_url=complete_url
            # else:
            #     image_url=""    
            if (date_from and date_to and grower_id):
                labour_list = Labour.cmobjects.filter(grower_id=grower_id,created_at__range=[date_from,date_to]).order_by('-id')
            elif type and grower_id:
                 labour_list = Labour.cmobjects.filter(grower_id=grower_id,type__iexact=type).order_by('-id')
                 print("labour_list_data",labour_list)   
            else :
                 labour_list = Labour.cmobjects.filter(grower_id=grower_id).order_by('-id')
                 print("labour_list_data",labour_list)
        
            context = {
		    # 'grower_pk' : grower_id,
		    'grower_details' : grower_details,
		    'labours_list' : labour_list,
            'garden_details' : garden_details,
            # 'image_url':image_url
	        }# Provide context data if needed
    

            template = get_template(template_path)
            html = template.render(context)

            response = HttpResponse(content_type='application/pdf')
            # response['Content-Disposition'] = 'attachment; filename="delivery_challan.pdf"'
            response['Content-Disposition'] = 'filename="labour_list.pdf"'

            pisa_status = pisa.CreatePDF(html, dest=response)
            if pisa_status.err:
                return HttpResponse('Error generating PDF', status=500)

            return response
        except Exception as e:
            raise serializers.ValidationError({'status': status.HTTP_400_BAD_REQUEST,'request_status': 0, 'msg': e},code='authorization')         
        



class GenerateMonthlySchedulePdfAPIView(APIView):
    """ Generate Plucking Data pdf"""
    permission_classes = [AllowAny]
    # authentication_classes = (TokenAuthentication,)
    # permission_classes = (IsAuthenticated,)
   
    def get(self, request, *args, **kwargs):
        try:
            # id = self.request.query_params.get('grower_id', None)    
            template_path = 'monthly_wages_pdf.html' # Replace with the path to your HTML template
            year_id= self.request.query_params.get('year_id', None)     
            grower_id= self.request.query_params.get('grower_id', None)  
            grower_details = GrowerProfile.cmobjects.filter(id=grower_id).first()
 
            
            if year_id and grower_id:
                schedule_list=  MonthlySchedule.cmobjects.filter(grower_id=grower_id,year_id=year_id).order_by('-id')    
            else:
                schedule_list =  MonthlySchedule.cmobjects.filter(grower_id=grower_id).order_by('-id')    
           


            context = {
		    'grower_pk' : id,
		    'grower_details' : grower_details,
		    'schedule_list' : schedule_list,
	        }# Provide context data if needed
    

            template = get_template(template_path)
            html = template.render(context)

            response = HttpResponse(content_type='application/pdf')
            # response['Content-Disposition'] = 'attachment; filename="delivery_challan.pdf"'
            response['Content-Disposition'] = 'filename="monthly_wages_data.pdf"'

            pisa_status = pisa.CreatePDF(html, dest=response)
            if pisa_status.err:
                return HttpResponse('Error generating PDF', status=500)

            return response
        except Exception as e:
            raise serializers.ValidationError({'status': status.HTTP_400_BAD_REQUEST,'request_status': 0, 'msg': e},code='authorization') 

       
    
class SupplyReportListAggregatorAPIView(APIView):
    """Aggregator supply report list """
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        try:
            id = self.request.query_params.get('id', None) 
            date_from= self.request.query_params.get('date_from', None)
            date_to= self.request.query_params.get('date_to', None) 
            user_type=self.request.query_params.get('consumer_type', "") 
            total_collected_quantity_sum = 0
            total_supply_quantity_sum = 0
            if user_type.lower() == 'factory' :      
                if id:
                    supply_data = SupplyManagement.objects.filter(is_deleted=False,created_by=request.user, id=id,supply_to__iexact='Factory').values('id', 'consumer', 'alloted_vehicle', 'quantity', 'date_of_supply', 'supply_to', 'supply_challan_id', 'gross_leaf').order_by('-id')
                elif (date_from and date_to ) :

                    supply_data = SupplyManagement.objects.filter(is_deleted=False,created_by=request.user, date_of_supply__range=[date_from,date_to],\
                                                   supply_to__iexact='Factory').values('id', 'consumer', 'alloted_vehicle', 'quantity', 'date_of_supply', 'supply_to', 'supply_challan_id', 'gross_leaf').order_by('-id')

                else:
                    supply_data = SupplyManagement.objects.filter(is_deleted=False,created_by=request.user,supply_to__iexact='Factory').values('id', 'consumer', 'alloted_vehicle', 'quantity', 'date_of_supply', 'supply_to', 'supply_challan_id', 'gross_leaf').order_by('-id')
                    print(supply_data)
                aggregator_details=AggregatorProfile.objects.filter(user=request.user).first()
                response_data = []
                for data in supply_data:
                    grower_details_supply = GrowerDetailsSupply.objects.filter(supply_id=data['id']).first()

                    # Initialize grower data dictionary
                    grower_data = {
                    'id' :""   ,
                    'grower_name': "",
                    'grower_type': "",
                    'grower_address': "",
                    # Add more fields as needed
                    }

                    if grower_details_supply:
                        grower = grower_details_supply.grower
                        grower_data = {
                         'id':grower.id  ,
                        'grower_name': grower.name,
                        'grower_type': grower.grower_type,
                        'grower_address': grower.address,
                        # Add more fields as needed
                        }
                    total_collected_quantity = GrowerDetailsSupply.objects.filter(supply_id=data['id']).aggregate(total=Sum('collected_quantity'))['total'] or 0
                    total_supply_quantity = GrowerDetailsSupply.objects.filter(supply_id=data['id']).aggregate(total=Sum('supply_quantity'))['total'] or 0
                    
                    data['total_collected_quantity'] = total_collected_quantity
                    
                    data['total_supply_quantity'] = total_supply_quantity
                    if data['total_collected_quantity'] is not None and str(data['total_collected_quantity']).strip():
                        total_collected_quantity_sum += float(data['total_collected_quantity'])
                    if data['total_supply_quantity'] is not None and str(data['total_supply_quantity']).strip():
                        total_supply_quantity_sum += float(data['total_supply_quantity'])
                    consumer=BlfProfile.objects.filter(user_id=data['consumer']).first()
                    alloted_vehicle=VehicleManagement.objects.filter(id= data['alloted_vehicle']).first()
                    response_data.append({
                    'consumer_name': consumer.entity_unit if consumer else "",
                    'consumer_user_name': consumer.user.username if  consumer.user else "",
                    'consumer_id': consumer.id if consumer else "",
                    'vehicle_number': alloted_vehicle.vehicle_number if alloted_vehicle else "",
                    
                    'total_supply_quantity': total_supply_quantity,
                    'total_collected_quantity': total_collected_quantity,
                    'date_of_supply': data['date_of_supply'],
                    'supply_to': data['supply_to'],
                    'supply_challan_id': data['supply_challan_id'],
                    'gross_leaf': data['gross_leaf'],
                    'grower_details': grower_data,
                    })

               
                # serializer = SupplyDetailsSerializer(response_data, many=True)
                return Response({
                
                            'result': response_data,
                            'aggregator_details':aggregator_details.name if aggregator_details else "",
                            'aggregator_details_username':aggregator_details.user.username if aggregator_details.user else "",
                            "date_from":date_from  if date_from else "",
                            'date_to':date_to if date_to else "",
                            'total_collected_quantity_sum': total_collected_quantity_sum,
                            'total_supply_quantity_sum': total_supply_quantity_sum,
                        },status=status.HTTP_200_OK)      
            elif user_type.lower() == 'aggregator' :      
                if id:
                    supply_data = SupplyManagement.objects.filter(is_deleted=False,created_by=request.user, id=id,supply_to__iexact='Aggregator').values('id', 'consumer', 'alloted_vehicle', 'quantity', 'date_of_supply', 'supply_to', 'supply_challan_id', 'gross_leaf').order_by('-id')
                elif (date_from and date_to ) :

                    supply_data = SupplyManagement.objects.filter(is_deleted=False,created_by=request.user, date_of_supply__range=[date_from,date_to],\
                                                   supply_to__iexact='Aggregator').values('id', 'consumer', 'alloted_vehicle', 'quantity', 'date_of_supply', 'supply_to', 'supply_challan_id', 'gross_leaf').order_by('-id')

                else:
                    supply_data = SupplyManagement.objects.filter(is_deleted=False,created_by=request.user,supply_to__iexact='Aggregator').values('id', 'consumer', 'alloted_vehicle', 'quantity', 'date_of_supply', 'supply_to', 'supply_challan_id', 'gross_leaf').order_by('-id')
                aggregator_details=AggregatorProfile.objects.filter(user=request.user).first()

                esponse_data = []
                for data in supply_data:
                    grower_details_supply = GrowerDetailsSupply.objects.filter(supply_id=data['id']).first()

                    grower_data = {
                    'id' :""   ,
                    'grower_name': "",
                    'grower_type': "",
                    'grower_address': "",
                    # Add more fields as needed
                    }

                    if grower_details_supply:
                        grower = grower_details_supply.grower
                        grower_data = {
                         'id':grower.id  ,
                        'grower_name': grower.name,
                        'grower_type': grower.grower_type,
                        'grower_address': grower.address,
                        # Add more fields as needed
                        }
                    total_collected_quantity = GrowerDetailsSupply.objects.filter(supply_id=data['id']).aggregate(total=Sum('collected_quantity'))['total'] or 0
                    total_supply_quantity = GrowerDetailsSupply.objects.filter(supply_id=data['id']).aggregate(total=Sum('supply_quantity'))['total'] or 0
                   
                    data['total_collected_quantity'] = total_collected_quantity
                    data['total_supply_quantity'] = total_supply_quantity
                    if data['total_collected_quantity'] and data['total_collected_quantity'].strip():
                        total_collected_quantity_sum += float(data['total_collected_quantity'])
                    if data['total_supply_quantity'] and data['total_supply_quantity'].strip():
                        total_supply_quantity_sum += float(data['total_supply_quantity'])
                    consumer=AggregatorProfile.objects.filter(user_id=data['consumer']).first()
                    alloted_vehicle=VehicleManagement.objects.filter(id= data['alloted_vehicle']).first()
                    response_data.append({
                    'consumer_name': consumer.name if consumer else None,
                    'consumer_user_name': consumer.user.username if consumer.user else None,
                    'consumer_id': consumer.id if consumer else None,
                    'vehicle_number': alloted_vehicle.vehicle_number if alloted_vehicle else None,
                    'total_supply_quantity': total_supply_quantity,
                    'total_collected_quantity': total_collected_quantity,
                    'date_of_supply': data['date_of_supply'],
                    'supply_to': data['supply_to'],
                    'supply_challan_id': data['supply_challan_id'],
                    'gross_leaf': data['gross_leaf'],
                    'grower_details': grower_data,
                    })

              
                # serializer = SupplyDetailsSerializer(response_data, many=True)
                return Response({
                
                            'result': response_data,
                            'aggregator_details':aggregator_details.name if aggregator_details else "",
                            'aggregator_user_name':aggregator_details.user.username if aggregator_details.user else "",
                            'aggregator_address':aggregator_details.address if aggregator_details else "",
                            "date_from":date_from  if date_from else "",
                            'date_to':date_to if date_to else "",
                            'total_collected_quantity_sum': total_collected_quantity_sum,
                            'total_supply_quantity_sum': total_supply_quantity_sum,
                        },status=status.HTTP_200_OK)        
            else:
                return Response({'msg': 'Consumer type required either factory or aggregator.'},\
                                          status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            raise serializers.ValidationError({'status': status.HTTP_400_BAD_REQUEST,'request_status': 0, 'msg': e},code='authorization')
        
class GenerateSupplyReportPdfAPIView(APIView):
    """ Supply Report List pdf"""
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
   
    def get(self, request, *args, **kwargs):
        try:
            date_from= self.request.query_params.get('date_from', None)
            date_to= self.request.query_params.get('date_to', None) 
            user_type=self.request.query_params.get('consumer_type', "") 
            # user_id=self.request.query_params.get('user_id', None) 
            # total_collected_quantity_sum = 0
            # total_supply_quantity_sum = 0
            template_path = 'supply_report_pdf.html' 
            if user_type.lower() == 'factory' :    
                
                if (date_from and date_to ) :

                    supply_data = SupplyManagement.objects.filter(is_deleted=False,created_by=request.user, date_of_supply__range=[date_from,date_to],\
                                                       supply_to__iexact='Factory')
                    # supply_data = SupplyManagement.objects.filter(is_deleted=False,created_by_id=user_id, date_of_supply__range=[date_from,date_to],\
                    #                                    supply_to__iexact='Factory')

                else:
                    supply_data = SupplyManagement.objects.filter(is_deleted=False,created_by=request.user,supply_to__iexact='Factory')
                    # supply_data = SupplyManagement.objects.filter(is_deleted=False,created_by=request.user,supply_to__iexact='Factory')

                supply_details = []
                # aggregator_details=AggregatorProfile.objects.filter(user_id=user_id).first()
                aggregator_details=AggregatorProfile.objects.filter(user=request.user).first()
                for data in supply_data:
                    grower_details_supply = GrowerDetailsSupply.objects.filter(supply_id=data.id).first()
                    consumer = BlfProfile.objects.filter(user=data.consumer).first()
                    alloted_vehicle = VehicleManagement.objects.filter(id=data.alloted_vehicle_id).first()
                    total_collected_quantity = GrowerDetailsSupply.objects.filter(supply_id=data.id).aggregate(total=Sum('collected_quantity'))['total'] or 0
                    total_supply_quantity = GrowerDetailsSupply.objects.filter(supply_id=data.id).aggregate(total=Sum('supply_quantity'))['total'] or 0
                    # total_collected_quantity_sum += total_collected_quantity
                    # total_supply_quantity_sum += float(total_supply_quantity)
                    consumer_name = consumer.entity_unit if consumer else None
                    consumer_user_name = consumer.user.username if consumer else None

                    # Add spaces after every 8 characters
                    if len(consumer_name) > 11 and ' ' not in consumer_name:
                        consumer_name = ' '.join([consumer_name[i:i+11] for i in range(0, len(consumer_name), 11)])

                    if len(consumer_user_name) > 11 and ' ' not in consumer_user_name:
                        consumer_user_name = ' '.join([consumer_user_name[i:i+11] for i in range(0, len(consumer_user_name), 11)])
                    challan_id = data.supply_challan_id if data.supply_challan_id else None
                    if challan_id and len(challan_id) > 11 and ' ' not in challan_id:
                        challan_id = ' '.join([challan_id[i:i+11] for i in range(0, len(challan_id), 11)])
                    supply_details.append({
                    'consumer_name': consumer_name,
                    'consumer_user_name': consumer_user_name,
                    'vehicle_number': alloted_vehicle.vehicle_number if alloted_vehicle else None,
                    'total_collected_quantity': total_collected_quantity,
                    'total_supply_quantity': total_supply_quantity,
                    'date_of_supply': data.date_of_supply,
                    'challan_id': challan_id,
                    'gross_leaf':data.gross_leaf,
                   

                    })
            elif user_type.lower() == 'aggregator' :    
                
                if (date_from and date_to ) :

                    supply_data = SupplyManagement.objects.filter(is_deleted=False,created_by=request.user, date_of_supply__range=[date_from,date_to],\
                                                       supply_to__iexact='Aggregator')

                else:
                    supply_data = SupplyManagement.objects.filter(is_deleted=False,created_by=request.user,supply_to__iexact='Aggregator')
                supply_details = []
                aggregator_details=AggregatorProfile.objects.filter(user_id=request.user.id).first()
                for data in supply_data:
                    grower_details_supply = GrowerDetailsSupply.objects.filter(supply_id=data.id).first()
                    consumer = AggregatorProfile.objects.filter(user=data.consumer).first()
                    alloted_vehicle = VehicleManagement.objects.filter(id=data.alloted_vehicle_id).first()
                    total_collected_quantity = GrowerDetailsSupply.objects.filter(supply_id=data.id).aggregate(total=Sum('collected_quantity'))['total'] or 0
                    total_supply_quantity = GrowerDetailsSupply.objects.filter(supply_id=data.id).aggregate(total=Sum('supply_quantity'))['total'] or 0
                    consumer_name = consumer.entity_unit if consumer else None
                    consumer_user_name = consumer.user.username if consumer else None

                    # Add spaces after every 8 characters
                    if len(consumer_name) > 11 and ' ' not in consumer_name:
                        consumer_name = ' '.join([consumer_name[i:i+11] for i in range(0, len(consumer_name), 11)])

                    if len(consumer_user_name) > 11 and ' ' not in consumer_user_name:
                        consumer_user_name = ' '.join([consumer_user_name[i:i+11] for i in range(0, len(consumer_user_name), 11)])
                    challan_id = data.supply_challan_id if data.supply_challan_id else None
                    if challan_id and len(challan_id) > 11 and ' ' not in challan_id:
                        challan_id = ' '.join([challan_id[i:i+11] for i in range(0, len(challan_id), 11)])
                    supply_details.append({
                    'consumer_name': consumer_name,
                    'consumer_user_name': consumer_user_name,
                    'vehicle_number': alloted_vehicle.vehicle_number if alloted_vehicle else None,
                    'total_collected_quantity': total_collected_quantity,
                    'total_supply_quantity': total_supply_quantity,
                    'date_of_supply': data.date_of_supply,
                    'challan_id':challan_id,
                    'gross_leaf':data.gross_leaf,
                   
                    })        
            else:
                return Response({'msg': 'consumer type required either factory or aggregator.'},\
                                          status=status.HTTP_400_BAD_REQUEST)
            total_supply_quantity_sum = sum(
                float(item['total_supply_quantity']) for item in supply_details) or 0
            if date_from and date_to :    
                datetime_object_from = datetime.strptime(date_from, "%Y-%m-%d")
                date_from = datetime_object_from.strftime("%d-%m-%Y")    
                datetime_object_to = datetime.strptime(date_to, "%Y-%m-%d")
                date_to= datetime_object_to.strftime("%d-%m-%Y")   
            else:
                date_from =""
                date_to="" 
            context = {
            'aggregator_details':aggregator_details.name if aggregator_details else "",
            'aggregator_user_name':aggregator_details.user if aggregator_details else "",
            'aggregator_address':aggregator_details.address if aggregator_details else "",
            "date_from":date_from  if date_from else "",
            'date_to':date_to if date_to else "",
		    'supply_details' : supply_details,
            'consumer_type':user_type.lower() if user_type else '',
            # 'total_collected_quantity_sum': total_collected_quantity_sum,
            'total_supply_quantity_sum': total_supply_quantity_sum,
           
            
	        }# Provide context data if needed
    

            template = get_template(template_path)
            html = template.render(context)

            response = HttpResponse(content_type='application/pdf')
            # response['Content-Disposition'] = 'attachment; filename="delivery_challan.pdf"'
            response['Content-Disposition'] = 'filename="supply_report.pdf"'

            pisa_status = pisa.CreatePDF(html, dest=response)
            if pisa_status.err:
                return HttpResponse('Error generating PDF', status=500)

            return response
        except Exception as e:
            raise serializers.ValidationError({'status': status.HTTP_400_BAD_REQUEST,'request_status': 0, 'msg': e},code='authorization') 
                

class GenerateSupplyEarnReportPdfAPIView(APIView):
    """ Supply Report List pdf"""
    # permission_classes = [AllowAny]
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
   
    def get(self, request, *args, **kwargs):
        try:
            date_from= self.request.query_params.get('date_from', None)
            date_to= self.request.query_params.get('date_to', None) 
            user_type=self.request.query_params.get('consumer_type', "") 
            template_path = 'supply_earn_report.html' 
            # total_collected_quantity_sum = 0
            # total_supply_quantity_sum = 0
            if user_type.lower() == 'factory' :    
                if (date_from and date_to ) :

                    supply_data = SupplyManagement.objects.filter(is_deleted=False,created_by=request.user, date_of_supply__range=[date_from,date_to],\
                                                       supply_to__iexact='Factory')

                else:
                    supply_data = SupplyManagement.objects.filter(is_deleted=False,created_by=request.user,supply_to__iexact='Factory')
                supply_details = []

                aggregator_details=AggregatorProfile.objects.filter(user=request.user).first()
                for data in supply_data:
                    grower_details_supply = GrowerDetailsSupply.objects.filter(supply_id=data.id).first()
                    consumer = BlfProfile.objects.filter(user=data.consumer).first()
                    alloted_vehicle = VehicleManagement.objects.filter(id=data.alloted_vehicle_id).first()
                    total_collected_quantity = GrowerDetailsSupply.objects.filter(supply_id=data.id).aggregate(total=Sum('collected_quantity'))['total'] or 0
                    total_supply_quantity = GrowerDetailsSupply.objects.filter(supply_id=data.id).aggregate(total=Sum('supply_quantity'))['total'] or 0
                    consumer_name = consumer.entity_unit if consumer else None
                    consumer_user_name = consumer.user.username if consumer else None

                    # Add spaces after every 8 characters
                    if len(consumer_name) > 11 and ' ' not in consumer_name:
                        consumer_name = ' '.join([consumer_name[i:i+11] for i in range(0, len(consumer_name), 11)])

                    if len(consumer_user_name) > 11 and ' ' not in consumer_user_name:
                        consumer_user_name = ' '.join([consumer_user_name[i:i+11] for i in range(0, len(consumer_user_name), 11)])
                    challan_id = data.supply_challan_id if data.supply_challan_id else None
                    if challan_id and len(challan_id) > 11 and ' ' not in challan_id:
                        challan_id = ' '.join([challan_id[i:i+11] for i in range(0, len(challan_id), 11)])
                    supply_details.append({
                    'consumer_name': consumer_name,
                    'consumer_user_name': consumer_user_name,
                    'vehicle_number': alloted_vehicle.vehicle_number if alloted_vehicle else None,
                    'total_collected_quantity': total_collected_quantity,
                    'total_supply_quantity': total_supply_quantity,
                    'date_of_supply': data.date_of_supply,
                    'challan_id':challan_id,
                    'gross_leaf':data.gross_leaf,
                   

                    })
            elif user_type.lower() == 'aggregator' :    
                
                if (date_from and date_to ) :

                    supply_data = SupplyManagement.objects.filter(is_deleted=False,created_by=request.user, date_of_supply__range=[date_from,date_to],\
                                                       supply_to__iexact='Aggregator')

                else:
                    supply_data = SupplyManagement.objects.filter(is_deleted=False,created_by=request.user,supply_to__iexact='Aggregator')
                supply_details = []
                aggregator_details=AggregatorProfile.objects.filter(user_id=request.user.id).first()
                for data in supply_data:
                    grower_details_supply = GrowerDetailsSupply.objects.filter(supply_id=data.id).first()
                    consumer = AggregatorProfile.objects.filter(user=data.consumer).first()
                    alloted_vehicle = VehicleManagement.objects.filter(id=data.alloted_vehicle_id).first()
                    total_collected_quantity = GrowerDetailsSupply.objects.filter(supply_id=data.id).aggregate(total=Sum('collected_quantity'))['total'] or 0
                    total_supply_quantity = GrowerDetailsSupply.objects.filter(supply_id=data.id).aggregate(total=Sum('supply_quantity'))['total'] or 0
                    # total_collected_quantity_sum += float(total_collected_quantity)
                    # total_supply_quantity_sum += float(total_supply_quantity)
                    consumer_name = consumer.entity_unit if consumer else None
                    consumer_user_name = consumer.user.username if consumer else None

                    # Add spaces after every 8 characters
                    if len(consumer_name) > 11 and ' ' not in consumer_name:
                        consumer_name = ' '.join([consumer_name[i:i+11] for i in range(0, len(consumer_name), 11)])

                    if len(consumer_user_name) > 11 and ' ' not in consumer_user_name:
                        consumer_user_name = ' '.join([consumer_user_name[i:i+11] for i in range(0, len(consumer_user_name), 11)])
                    challan_id = data.supply_challan_id if data.supply_challan_id else None
                    if challan_id and len(challan_id) > 11 and ' ' not in challan_id:
                        challan_id = ' '.join([challan_id[i:i+11] for i in range(0, len(challan_id), 11)])
                    supply_details.append({
                    'consumer_name': consumer_name,
                    'consumer_user_name': consumer_user_name,
                    'vehicle_number': alloted_vehicle.vehicle_number if alloted_vehicle else None,
                    'total_collected_quantity': total_collected_quantity,
                    'total_supply_quantity': total_supply_quantity,
                    'date_of_supply': data.date_of_supply,
                    'challan_id':challan_id,
                    'gross_leaf':data.gross_leaf,
                   
                    })        
            else:
                return Response({'msg': 'consumer type required either factory or aggregator.'},\
                                          status=status.HTTP_400_BAD_REQUEST)
            total_supply_quantity_sum = sum(
                float(item['total_supply_quantity']) for item in supply_details) or 0
            if date_from and date_to :    
                datetime_object_from = datetime.strptime(date_from, "%Y-%m-%d")
                date_from = datetime_object_from.strftime("%d-%m-%Y")    
                datetime_object_to = datetime.strptime(date_to, "%Y-%m-%d")
                date_to= datetime_object_to.strftime("%d-%m-%Y")   
            else:
                date_from =""
                date_to="" 
            context = {
            'aggregator_details':aggregator_details.name if aggregator_details else "",
            'aggregator_user_name':aggregator_details.user if aggregator_details else "",
            'aggregator_address':aggregator_details.address if aggregator_details else "",
            "date_from":date_from  if date_from else "",
            'date_to':date_to if date_to else "",
		    'supply_details' : supply_details,
           'consumer_type':user_type.lower() if user_type else '',
        #    'total_collected_quantity_sum': total_collected_quantity_sum,
            'total_supply_quantity_sum': total_supply_quantity_sum,
            
	        }# Provide context data if needed
    

            template = get_template(template_path)
            html = template.render(context)

            response = HttpResponse(content_type='application/pdf')
            # response['Content-Disposition'] = 'attachment; filename="supply_report.pdf"'
            response['Content-Disposition'] = 'filename="supply_earn_report.pdf"'

            pisa_status = pisa.CreatePDF(html, dest=response)
            if pisa_status.err:
                return HttpResponse('Error generating PDF', status=500)

            return response
        except Exception as e:
            raise serializers.ValidationError({'status': status.HTTP_400_BAD_REQUEST,'request_status': 0, 'msg': e},code='authorization') 

class KhataBookAggregatorAPIView(APIView):
    """Khata Book API """
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        try:
            id = self.request.query_params.get('id', None) 
            date_from= self.request.query_params.get('date_from', None)
            date_to= self.request.query_params.get('date_to', None) 
            user_type=self.request.query_params.get('user_type', "") 
            if user_type.lower() == 'grower' :      
                if id:
                    # collected_data = CollectionFromGrower.objects.filter(is_deleted=False,created_by=request.user, id=id,keep_record='Yes').order_by('-id')
                    collected_data = CollectionFromGrower.objects.filter(is_deleted=False,created_by=request.user, id=id,).order_by('-id')

                elif (date_from and date_to ) :

                    collected_data = CollectionFromGrower.objects.filter(is_deleted=False,created_by=request.user, date__range=[date_from,date_to],\
                                                   ).order_by('-id')

                else:
                    collected_data = CollectionFromGrower.objects.filter(is_deleted=False,created_by=request.user,).order_by('-id')
                    # collected_data = CollectionFromAggregator.objects.filter(is_deleted=False,created_by=request.user,keep_record='Yes').order_by('-id')

                aggregator_details=AggregatorProfile.objects.filter(user=request.user).first()
                

               
                serializer = KhataBookGetSerializer(collected_data, many=True)
                total_collected_quantity = sum(float(data.quantity) for data in collected_data) or 0
                if date_from and date_to :    
                    datetime_object_from = datetime.strptime(date_from, "%Y-%m-%d")
                    date_from = datetime_object_from.strftime("%d-%m-%Y")    
                    datetime_object_to = datetime.strptime(date_to, "%Y-%m-%d")
                    date_to= datetime_object_to.strftime("%d-%m-%Y")   
                else:
                    date_from =""
                    date_to="" 

                return Response({
                
                            'result': serializer.data,
                            'aggregator_details':aggregator_details.name if aggregator_details else "",
                            'aggregator_details_user_name':aggregator_details.user.username if aggregator_details.user else "",
                            "date_from":date_from  if date_from else "",
                            'date_to':date_to if date_to else "",
                            "total_collected_quantity_sum":total_collected_quantity
                        },status=status.HTTP_200_OK)      
                 
            else:
                return Response({'msg': 'User type Required i.e grower .'},\
                                          status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            raise serializers.ValidationError({'status': status.HTTP_400_BAD_REQUEST,'request_status': 0, 'msg': e},code='authorization')              
# import datetime

class GenerateKhataBookPdfAPIView(APIView):
    """ Khata Book List pdf"""
    # permission_classes = [AllowAny]
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
   
    def get(self, request, *args, **kwargs):
        try:
            date_from= self.request.query_params.get('date_from', None)
            date_to= self.request.query_params.get('date_to', None) 
            user_type=self.request.query_params.get('user_type', "") 
            # user_id=self.request.query_params.get('user_id', None) 

            template_path = 'khata_book.html' 
            if user_type.lower() == 'grower' :    
                
                if (date_from and date_to ) :

                    collected_data = CollectionFromGrower.objects.filter(is_deleted=False,created_by=request.user, date__range=[date_from,date_to],\
                                                   ).order_by('-id')

                else:
                    collected_data = CollectionFromGrower.objects.filter(is_deleted=False,created_by=request.user,).order_by('-id')
                    
                collection_details = []
                aggregator_details=AggregatorProfile.objects.filter(user=request.user).first()
                for data in collected_data:
                    grower = GrowerProfile.objects.filter(id=data.grower.id).first()
                    alloted_vehicle = VehicleManagement.objects.filter(id=data.vehicle_number_id).first()
                    
                    name = grower.name if grower else None
                    user_name = grower.user.username if grower else None
                    receipt_no = data.receipt_no if data.receipt_no else None
 
                    # Add spaces after every 11 characters
                    if name and len(name) > 10 and ' ' not in name:
                        name = ' '.join([name[i:i+10] for i in range(0, len(name), 10)])

                    if user_name and len(user_name) > 10 and ' ' not in user_name:
                        user_name = ' '.join([user_name[i:i+10] for i in range(0, len(user_name), 10)])

                    if receipt_no and len(receipt_no) > 10 and ' ' not in receipt_no:
                        receipt_no = ' '.join([receipt_no[i:i+10] for i in range(0, len(receipt_no), 10)])
                    collection_details.append({
                    'name': name,
                    'user_name': user_name,
                    'vehicle_number': alloted_vehicle.vehicle_number if alloted_vehicle else None,
                    'total_collected_quantity': data.quantity,
                    
                    'date_of_purchase': data.date,
                    'rate':data.rate,
                    'receipt_no':receipt_no,
                   

                    })
            elif user_type.lower() == 'aggregator' :    
                
                if (date_from and date_to ) :

                    collected_data = CollectionFromAggregator.objects.filter(is_deleted=False,created_by=request.user, date__range=[date_from,date_to],\
                                                   ).order_by('-id')

                else:
                    collected_data = CollectionFromAggregator.objects.filter(is_deleted=False,created_by=request.user,).order_by('-id')

                collection_details = []
                aggregator_details=AggregatorProfile.objects.filter(user=request.user).first()
                for data in collected_data:
                    aggregator = AggregatorProfile.objects.filter(id=data.aggregator.id).first()
                    alloted_vehicle = VehicleManagement.objects.filter(id=data.vehicle_number_id).first()
                    
                    name = aggregator.name if aggregator else None
                    user_name = aggregator.user.username if aggregator else None
                    receipt_no = data.receipt_no if data.receipt_no else None

                    # Add spaces after every 11 characters
                    if name and len(name) > 10 and ' ' not in name:
                        name = ' '.join([name[i:i+10] for i in range(0, len(name), 10)])

                    if user_name and len(user_name) > 10 and ' ' not in user_name:
                        user_name = ' '.join([user_name[i:i+10] for i in range(0, len(user_name), 10)])

                    if receipt_no and len(receipt_no) > 10 and ' ' not in receipt_no:
                        receipt_no = ' '.join([receipt_no[i:i+10] for i in range(0, len(receipt_no), 10)])
                    collection_details.append({
                    'name': name,
                    'user_name': user_name,
                    'vehicle_number': alloted_vehicle.vehicle_number if alloted_vehicle else None,
                    'total_collected_quantity': data.quantity,
                    'date_of_purchase': data.date,
                    'rate':data.rate,
                    'receipt_no':receipt_no,
                   

                    })   
            else:
                return Response({'msg': 'user type required either grower or aggregator.'},\
                                          status=status.HTTP_400_BAD_REQUEST)
            total_collected_quantity_sum = sum(
                float(item['total_collected_quantity']) for item in collection_details) or 0
            if date_from and date_to :    
                datetime_object_from = datetime.strptime(date_from, "%Y-%m-%d")
                date_from = datetime_object_from.strftime("%d-%m-%Y")    
                datetime_object_to = datetime.strptime(date_to, "%Y-%m-%d")
                date_to= datetime_object_to.strftime("%d-%m-%Y")   
            else:
                date_from =""
                date_to=""   
            context = {
            'aggregator_details':aggregator_details.name if aggregator_details else "",
            'aggregator_user_name':aggregator_details.user if aggregator_details else "",
            'aggregator_address':aggregator_details.address if aggregator_details else "",
            "date_from":date_from  if date_from else "",
            'date_to':date_to if date_to else "",
		    'collection_details' : collection_details,
            'user_type':user_type.lower() if user_type else '',
            'total_collected_quantity_sum':total_collected_quantity_sum,
            
           
            
	        }# Provide context data if needed
    

            template = get_template(template_path)
            html = template.render(context)
            # timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            # if aggregator_details:
            #     user_name = aggregator_details.user.username # Replace this with the actual username if available
            # else :
            #     user_name=""
            # Generate dynamic file name
            # filename = f'""KHB"{user_name}_{timestamp}.pdf"'
            
            response = HttpResponse(content_type='application/pdf')
            # response['Content-Disposition'] = 'attachment; filename="delivery_challan.pdf"'
            # response['Content-Disposition'] = f'filename={filename}'
            response['Content-Disposition'] = 'filename="khata_book.pdf"'

            pisa_status = pisa.CreatePDF(html, dest=response)
            if pisa_status.err:
                return HttpResponse('Error generating PDF', status=500)

            return response
        except Exception as e:
            raise serializers.ValidationError({'status': status.HTTP_400_BAD_REQUEST,'request_status': 0, 'msg': e},code='authorization')         


# from weasyprint import HTML
# import subprocess
from django.http import HttpResponse
from django.template.loader import render_to_string
from io import BytesIO
from django.template.loader import get_template
class GenerateConsolidatedFarmDiaryPdfAPIView(APIView):
    # permission_classes = [AllowAny]
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    def get(self, request, *args, **kwargs):
        # template_path = 'consolidate_farm_diary_pdf.html'  # Replace with the path to your HTML template
        template_path = 'consolidate.html'
        grower_id = self.request.query_params.get('grower_id', None)
        date_from = self.request.query_params.get('date_from', None)
        date_to = self.request.query_params.get('date_to', None)

        if not date_from or not date_to:
            raise APIException({'request_status': 0, 'msg': "date_from and date_to are mandatory"})

        grower_details = GrowerProfile.cmobjects.filter(id=grower_id).first()
        garden_details = Gardens.objects.filter(grower_id=grower_id).first()
        
        if date_from and date_to and grower_id:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')

            year_from = date_from_obj.year
            year_to = date_to_obj.year
            fertilizer_chemical_list= UseOfChemical.cmobjects.filter(
                grower_id=grower_id,chemical__chemical_type__name__iexact="Fertilizer",
                date__range=[date_from, date_to]
            ).order_by('-id')
            herbicides_chemical_list= UseOfChemical.cmobjects.filter(
                grower_id=grower_id,chemical__chemical_type__name__iexact="Herbicides",
                date__range=[date_from, date_to]
            ).order_by('-id')
            acaricides_chemical_list= UseOfChemical.cmobjects.filter(
                grower_id=grower_id,chemical__chemical_type__name__iexact="Acaricides",
                date__range=[date_from, date_to]
            ).order_by('-id')
            insecticides_chemical_list= UseOfChemical.cmobjects.filter(
                grower_id=grower_id,chemical__chemical_type__name__iexact="Insecticides & Fungicides",
                date__range=[date_from, date_to]
            ).order_by('-id')
            plucking_data_list = PluckingData.cmobjects.filter(
                grower_id=grower_id,
                date__range=[date_from, date_to]
            ).order_by('-id')
            # labour_list = Labour.cmobjects.filter(
            #     grower_id=grower_id,
            #     created_at__range=[date_from, date_to]
            # ).order_by('-id')
            labour_list = Labour.cmobjects.filter(
                grower_id=grower_id,
            ).order_by('-id')
            # schedule_list = MonthlySchedule.cmobjects.filter(
            #     grower_id=grower_id,
            #     year__year__range=[year_from, year_to]
            # ).order_by('-id')
            schedule_list = MonthlySchedule.cmobjects.filter(grower_id=grower_id).order_by('-id')
        else:
            fertilizer_chemical_list = UseOfChemical.cmobjects.filter(grower_id=grower_id,chemical__chemical_type__name__iexact="Fertilizer").order_by('-id')
            herbicides_chemical_list = UseOfChemical.cmobjects.filter(grower_id=grower_id,chemical__chemical_type__name__iexact="Herbicides").order_by('-id')
            acaricides_chemical_list = UseOfChemical.cmobjects.filter(grower_id=grower_id,chemical__chemical_type__name__iexact="Acaricides").order_by('-id')
            insecticides_chemical_list = UseOfChemical.cmobjects.filter(grower_id=grower_id,chemical__chemical_type__name__iexact="Insecticides & Fungicides").order_by('-id')

            plucking_data_list = PluckingData.cmobjects.filter(grower_id=grower_id).order_by('-id')
            labour_list = Labour.cmobjects.filter(grower_id=grower_id).order_by('-id')
            schedule_list = MonthlySchedule.cmobjects.filter(grower_id=grower_id).order_by('-id')
        if grower_details is not None:
            if grower_details.photo:
                grower_details_photo_url = request.build_absolute_uri(grower_details.photo.url)
            else:
                grower_details_photo_url = None
        else:
            grower_details_photo_url = None
        if date_from and date_to :    
            datetime_object_from = datetime.strptime(date_from, "%Y-%m-%d")
            date_from = datetime_object_from.strftime("%d-%m-%Y")    
            datetime_object_to = datetime.strptime(date_to, "%Y-%m-%d")
            date_to= datetime_object_to.strftime("%d-%m-%Y")   
        else:
            date_from =""
            date_to=""    
        context = {
            'grower_details': grower_details,
            'garden_details': garden_details,
            # 'chemical_list': chemical_list,
            'fertilizer_chemical_list':fertilizer_chemical_list,
            'herbicides_chemical_list':herbicides_chemical_list,
            'acaricides_chemical_list':acaricides_chemical_list,
            'insecticides_chemical_list':insecticides_chemical_list,
            'plucking_data_list': plucking_data_list,
            'labour_list': labour_list,
            'schedule_list': schedule_list,
            "date_from": date_from if date_from else "",
            'date_to': date_to if date_to else "",
            'year_from':date_from if  date_from else "",
            'year_to':year_to if date_to else "",
            'grower_details_photo_url':grower_details_photo_url,

        }  # Provide context data if needed
        template = get_template(template_path)
        html = template.render(context)
        options = {
            'page-size': 'A4',
            'encoding': "UTF-8",
            'dpi': 300,             
            'zoom': 1.3,             
            'no-outline': None,
            'margin-top': '0.75in',
            'margin-right': '0.75in',
            'margin-bottom': '0.75in',
            'margin-left': '0.75in',
            'enable-smart-shrinking': True,  # Better layout scaling
        }
        config = pdfkit.configuration(wkhtmltopdf=str(os.getenv('WKHTMLTOPDF_PATH', '')))
        pdf = pdfkit.from_string(html, False, options=options, configuration=config)

        filename = f"consolidated_farm_diary_{date_from}_to_{date_to}_{uuid.uuid4().hex}.pdf"
        fs = FileSystemStorage(location=settings.MEDIA_ROOT)
        file_path = fs.save(filename, ContentFile(pdf))
        file_url = fs.url(file_path)

        # response = HttpResponse(content_type='application/pdf')
        # response['Content-Disposition'] = 'filename="consolidated_farm_diary.pdf"'
        # pisa_status = pisa.CreatePDF(html, dest=response)
        # if pisa_status.err:
        #     return HttpResponse('Error generating PDF', status=500)
        # return response
        return Response({
            'request_status': 1,
            'msg': 'PDF generated successfully',
            'file_url': request.build_absolute_uri(file_url)
        })

# class GenerateUseOfChemicalListPdfAPIView(APIView):
#     """ Generate Labour List pdf"""
#     permission_classes = [AllowAny]
#     # authentication_classes = (TokenAuthentication,)
#     # permission_classes = (IsAuthenticated,)
   
#     def get(self, request, *args, **kwargs):
#             grower_id = self.request.query_params.get('grower_id', None) 
#             chemical_type=self.request.query_params.get('chemical_type_id', None)
#             date_from= self.request.query_params.get('date_from', None)
#             date_to= self.request.query_params.get('date_to', None)    
#             template_path = 'use_of_chemical_list_pdf.html' 
#             chemical_type_name=UseOfChemical.objects.filter( chemical__chemical_type__name__iexact=chemical_type).first()
#             grower_details = GrowerProfile.cmobjects.filter(id=grower_id).first()


#             chemical_list = UseOfChemical.cmobjects.filter(grower_id=grower_id,\
#                                             chemical__chemical_type_id=chemical_type, 
#                                             date__range=[date_from,date_to]).order_by('-id')

#             if date_from and date_to :    
#                 datetime_object_from = datetime.strptime(date_from, "%Y-%m-%d")
#                 date_from = datetime_object_from.strftime("%d-%m-%Y")    
#                 datetime_object_to = datetime.strptime(date_to, "%Y-%m-%d")
#                 date_to= datetime_object_to.strftime("%d-%m-%Y")   
#             else:
#                 date_from =""
#                 date_to="" 
#             context = {
#                 "chemical_type":chemical_type_name.chemical.chemical_type.name if chemical_type_name else "",
#                 'grower_details' : grower_details,
#                 'chemical_list' : chemical_list,
#                 "date_from":date_from  if date_from else "",
#                 'date_to':date_to if date_to else "",
# 	        }# Provide context data if needed
    
#             template = get_template(template_path)
#             html = template.render(context)

#             response = HttpResponse(content_type='application/pdf')
#             # response['Content-Disposition'] = 'attachment; filename="delivery_challan.pdf"'
#             response['Content-Disposition'] = 'filename="chemical_list.pdf"'

#             pisa_status = pisa.CreatePDF(html, dest=response)
#             if pisa_status.err:
#                 return HttpResponse('Error generating PDF', status=500)

#             template = get_template('supply_report_grower.html')
#             html = template.render(context)
#             options = {
#                 'page-size': 'A4',
#                 'encoding': "UTF-8",
#                 'dpi': 300,             
#                 'zoom': 1.3,             
#                 'no-outline': None,
#                 'margin-top': '0.75in',
#                 'margin-right': '0.75in',
#                 'margin-bottom': '0.75in',
#                 'margin-left': '0.75in',
#                 'enable-smart-shrinking': True,  # Better layout scaling
#             }
#             config = pdfkit.configuration(wkhtmltopdf=str(os.getenv('WKHTMLTOPDF_PATH', '')))
#             pdf = pdfkit.from_string(html, False, options=options, configuration=config)

#             filename = f"chemical_list_{date_from}_to_{date_to}_{uuid.uuid4().hex}.pdf"
#             fs = FileSystemStorage(location=settings.MEDIA_ROOT)
#             file_path = fs.save(filename, ContentFile(pdf))
#             file_url = fs.url(file_path)
#             return Response({
#                 'request_status': 1,
#                 'msg': 'PDF generated successfully',
#                 'file_url': request.build_absolute_uri(file_url)
#             })

class GenerateUseOfChemicalListPdfAPIView(APIView):
    """ Generate Use of Chemical List PDF """
    # permission_classes = [AllowAny]
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    def get(self, request, *args, **kwargs):
        grower_id = request.query_params.get('grower_id')
        chemical_type = request.query_params.get('chemical_type_id')
        exclude_chemical_type_id = request.query_params.get('exclude__chemical__chemical_type_id')
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')

        template_path = 'use_of_chemical_list_pdf.html'

        chemical_type_name = UseOfChemical.objects.filter(
            chemical__chemical_type__name__iexact=chemical_type
        ).first()
        grower_details = GrowerProfile.cmobjects.filter(id=grower_id).first()

        if exclude_chemical_type_id:
            chemical_list = UseOfChemical.cmobjects.filter(
                grower_id=grower_id,
                date__range=[date_from, date_to]
            ).exclude(chemical__chemical_type_id=exclude_chemical_type_id).order_by('-id')
        else:
            chemical_list = UseOfChemical.cmobjects.filter(
                grower_id=grower_id,
                chemical__chemical_type_id=chemical_type,
                date__range=[date_from, date_to]
            ).order_by('-id')

        # Format dates for display
        if date_from and date_to:
            date_from = datetime.strptime(date_from, "%Y-%m-%d").strftime("%d-%m-%Y")
            date_to = datetime.strptime(date_to, "%Y-%m-%d").strftime("%d-%m-%Y")
        else:
            date_from, date_to = "", ""

        context = {
            "chemical_type": chemical_type_name.chemical.chemical_type.name if chemical_type_name else "",
            "grower_details": grower_details,
            "chemical_list": chemical_list,
            "date_from": date_from,
            "date_to": date_to,
        }

        # Render HTML
        template = get_template(template_path)
        html = template.render(context)

        # PDF options
        options = {
            'page-size': 'A4',
            'encoding': "UTF-8",
            'dpi': 300,
            'zoom': 1.3,
            'no-outline': None,
            'margin-top': '0.75in',
            'margin-right': '0.75in',
            'margin-bottom': '0.75in',
            'margin-left': '0.75in',
            'enable-smart-shrinking': True,
        }

        config = pdfkit.configuration(wkhtmltopdf=str(os.getenv('WKHTMLTOPDF_PATH', '')))
        pdf = pdfkit.from_string(html, False, options=options, configuration=config)

        # Save PDF to MEDIA_ROOT
        filename = f"chemical_list_{date_from}_to_{date_to}_{uuid.uuid4().hex}.pdf"
        fs = FileSystemStorage(location=settings.MEDIA_ROOT)
        file_path = fs.save(filename, ContentFile(pdf))
        file_url = fs.url(file_path)

        return Response({
            'request_status': 1,
            'msg': 'PDF generated successfully',
            'file_url': request.build_absolute_uri(file_url)
        })

class GeneratePluckingDataPdfAPIView(APIView):
    """ Generate Plucking Data pdf"""
    # permission_classes = [AllowAny]
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    
    def get(self, request, *args, **kwargs):
        template_path = 'plucking_data_pdf.html'
        date_to= self.request.query_params.get('date_to', None) 
        date_from= self.request.query_params.get('date_from', None) 
        grower_id= self.request.query_params.get('grower_id', None) 
        grower_details = GrowerProfile.cmobjects.filter(id=grower_id).first()  
        if not date_from or not date_to:
            raise APIException({'request_status': 0, 'msg': "date_from and date_to are mandatory"})
        plucking_data_list = PluckingData.cmobjects.filter(created_by=request.user, date__range=[date_from,date_to]).\
            order_by('-id')
        if date_from and date_to :    
            datetime_object_from = datetime.strptime(date_from, "%Y-%m-%d")
            date_from = datetime_object_from.strftime("%d-%m-%Y")    
            datetime_object_to = datetime.strptime(date_to, "%Y-%m-%d")
            date_to= datetime_object_to.strftime("%d-%m-%Y")   
        else:
            date_from =""
            date_to=""
        context = {
            # 'grower_pk' : grower_id,
            'grower_details' : grower_details,
            'plucking_data_list' : plucking_data_list,
            "date_from":date_from  if date_from else "",
            'date_to':date_to if date_to else "",
        }# Provide context data if needed

        template = get_template(template_path)
        html = template.render(context)

        # response = HttpResponse(content_type='application/pdf')
        # # response['Content-Disposition'] = 'attachment; filename="delivery_challan.pdf"'
        # response['Content-Disposition'] = 'filename="plucking_data.pdf"'
        # pisa_status = pisa.CreatePDF(html, dest=response)
        # if pisa_status.err:
        #     return HttpResponse('Error generating PDF', status=500)
        # return response
        options = {
            'page-size': 'A4',
            'encoding': "UTF-8",
            'dpi': 300,             
            'zoom': 1.3,             
            'no-outline': None,
            'margin-top': '0.75in',
            'margin-right': '0.75in',
            'margin-bottom': '0.75in',
            'margin-left': '0.75in',
            'enable-smart-shrinking': True,  # Better layout scaling
        }
        config = pdfkit.configuration(wkhtmltopdf=str(os.getenv('WKHTMLTOPDF_PATH', '')))
        pdf = pdfkit.from_string(html, False, options=options, configuration=config)

        # Generate unique filename
        filename = f"plucking_data_{date_from}_to_{date_to}_{uuid.uuid4().hex}.pdf"
        fs = FileSystemStorage(location=settings.MEDIA_ROOT)
        file_path = fs.save(filename, ContentFile(pdf))
        file_url = fs.url(file_path)
        return Response({
            'request_status': 1,
            'msg': 'PDF generated successfully',
            'file_url': request.build_absolute_uri(file_url)
        })