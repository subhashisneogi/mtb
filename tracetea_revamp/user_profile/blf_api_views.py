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
from leaf_receipt.models import *
import time
from django.db.models import Max
from master.utils import send_sms
class BlfGrowerProfileListAPIView(APIView):
    """ Grower list are mapped with blf or factory  View"""
    authentication_classes = (TokenAuthentication,)
    permission_classes=(IsAuthenticated,)   
    queryset = GrowerProfile.objects.filter(is_deleted=False).exclude(associated_entity__isnull=True)
    serializer_class = GrowerProfileSerializer
    def get(self, request, *args, **kwargs):
        try:
            id = self.request.query_params.get('id', None)          
            if id:
                queryset = self.queryset.filter(associated_entity__user=request.user,id=id).order_by('-id')
            else:
                queryset=self.queryset.filter(associated_entity__user=request.user).order_by('-id')    
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

class BlfAggregatorProfileListAPIView(APIView):
    """ aggregator list with blf or factory map View"""
    authentication_classes = (TokenAuthentication,)
    permission_classes=(IsAuthenticated,)
    queryset = AggregatorProfile.objects.filter(is_deleted=False)
    serializer_class = AggregatorProfileSerializer
    def get(self, request, *args, **kwargs):
        try:
            id = self.request.query_params.get('id', None)          
            if id:
                queryset = self.queryset.filter(associated_entity__user=request.user,id=id).order_by('-id')
            else:
                queryset=self.queryset.filter(associated_entity__user=request.user).order_by('-id')    
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

class DeliveryChallanListAPIView(APIView):
    """ Supply or delivery chalan list View"""
    authentication_classes = (TokenAuthentication,)
    permission_classes=(IsAuthenticated,)
	
    queryset_supply= SupplyManagement.objects.filter(is_deleted=False,is_weighment_proceed=False)
    serializer_class = SupplyManagementSerializer
    def get(self, request, *args, **kwargs):
        try:
            aggregator_id = self.request.query_params.get('aggregator_id', None)
            grower_id = self.request.query_params.get('grower_id', None)

            if aggregator_id:
                queryset_check = self.queryset_supply.filter(consumer=request.user,created_by__profile_id_aggregator=aggregator_id).order_by('-id')
                serializer = SupplyManagementSerializer(queryset_check, many=True)
                page_size = int(request.query_params.get('page_size', 10))
                paginator = Paginator(queryset_check, page_size)
                page_number = self.request.query_params.get('page', 1)
                page = paginator.get_page(page_number)
                return Response({
                'count': paginator.count,
                'next': page.next_page_number() if page.has_next() else None,
                'previous': page.previous_page_number() if page.has_previous() else None,

                'aggregator_result': serializer.data ,                      

                })	

            if grower_id :
                # queryset=GrowerDetailsSupply.objects.filter(is_deleted=False,supply__consumer=request.user,grower_id=grower_id)\
                #     .values('id','created_by_id','supply_id','grower_id','grower__name','collected_quantity',\
                #                            'collected_date','collected_time','supply_quantity','supply__supply_to',\
                #                             'supply__consumer','supply__consumer__username','supply__consumer__profile_id_blf__mobile_number',\
                #                                 'supply__alloted_vehicle','supply__alloted_vehicle__vehicle_number','supply__supply_challan_id').order_by('-id')  

                # queryset=GrowerDetailsSupply.objects.filter(is_deleted=False,supply__consumer=request.user,supply__is_weighment_proceed=False,grower_id=grower_id).order_by('-id')   
                # serializer = GrowerDetailsSupplySerializer(queryset, many=True)
                queryset_check = self.queryset_supply.filter(consumer=request.user,created_by__profile_id_grower=grower_id).order_by('-id')
                serializer = SupplyManagementSerializer(queryset_check, many=True)
                page_size = int(request.query_params.get('page_size', 10))
                paginator = Paginator(queryset_check, page_size)
                page_number = self.request.query_params.get('page', 1)
                page = paginator.get_page(page_number)
                return Response({
                'count': paginator.count,
                'next': page.next_page_number() if page.has_next() else None,
                'previous': page.previous_page_number() if page.has_previous() else None,

                'grower_results': serializer.data ,                      

                })	
        except Exception as e:
            raise serializers.ValidationError({'status': status.HTTP_400_BAD_REQUEST,'request_status': 0, 'msg': e},code='authorization')	

class WeighmentSupplyAPIView(APIView):
    """Weightment Supply View"""
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    queryset = WeighmentSupply.objects.filter(is_deleted=False)
    serializer_class = WeighmentSupplySerializer
    def get(self, request, *args, **kwargs):
        
            id = self.request.query_params.get('id', None)    
            date_from=self.request.query_params.get('date_from', None) 
            date_to = self.request.query_params.get('date_to', None)     
               
            if id:
                queryset = self.queryset.filter(created_by=request.user,id=id).order_by('-id')
            elif (date_from and date_to):
                 queryset = self.queryset.filter(created_by=request.user,supply_date__range=[date_from,date_to]).order_by('-id')    
            else:
                queryset=self.queryset.filter(created_by=request.user).order_by('-id')    
                print(queryset)
            page_size = int(request.query_params.get('page_size', 10))
            paginator = Paginator(queryset, page_size)
            page_number = self.request.query_params.get('page', 1)
            page = paginator.get_page(page_number)
            serializer = WeighmentSupplySerializer(queryset, many=True)

            return Response({
                'count': paginator.count,
                'next': page.next_page_number() if page.has_next() else None,
                'previous': page.previous_page_number() if page.has_previous() else None,
                'results': serializer.data,
            })
    def post(self, request, format=None):
        try:
            supplier_type=request.data.get('supplier_type', None)
            challan_id=request.data.get('challan_id', None)
            mode_of_supply = request.data.get('mode_of_supply', None)
            supply_date= request.data.get('supply_date', None)
            total_gross_weight_kg = request.data.get('total_gross_weight', None)
            vehicle_no_id= request.data.get('vehicle_no_id', None)
            mobile_number= request.data.get('mobile_number', None)
            supplier_id=SupplyManagement.objects.get(id=challan_id)
            if supplier_id.is_weighment_proceed:
                if supplier_id.is_weighment_proceed == True:
                    return Response({
                        'msg': 'Weightment already proceeded for the given challan ID',
                        'status': status.HTTP_400_BAD_REQUEST,
                        'request_status': 0
                    },status=status.HTTP_400_BAD_REQUEST)
            
       
            with transaction.atomic(): 
                created =  WeighmentSupply.objects.create(supplier_type=supplier_type,mode_of_supply=mode_of_supply,supply_challan_id=challan_id,\
                                                          supply_date=supply_date,mobile_number=mobile_number,\
                		total_gross_weight_kg=total_gross_weight_kg,supplier_id=supplier_id.created_by.id,\
                        created_by=request.user)
                if vehicle_no_id:
                    created.vehicle_no_id=vehicle_no_id
                    created.save()
                # blf_details = BlfProfile.cmobjects.filter(user_id=request.user.id).first()
                
                # if blf_details:
                #     if blf_details.region:
                #         region_code=blf_details.region.abbrevation
                #     else:
                #         region_code= "TXN-"    
                 
                # else :
                #     region_code= "TXN-"              
                # last_challan = WeighmentSupply.objects.aggregate(Max('weighment_txn_id'))
                # last_challan_id = last_challan.get('weighment_txn_id__max')
                
                # # Calculate the next supply_challan_id
                # # if last_challan_id and last_challan_id.startswith("TXN-"):
                # if last_challan_id and last_challan_id.startswith(region_code):
                # # Extract the numeric part and increment it
                #     numeric_part = int(last_challan_id.split('-')[1]) + 1
                #     next_challan_id = f"{region_code}-{numeric_part:09d}"
                # else:
                # # Handle the case when there are no existing supply_challan_id values
                #     next_challan_id = f"{region_code}-000000001"
                #### old code
                # last_challan = WeighmentSupply.objects.aggregate(Max('weighment_txn_id'))
                # last_challan_id = last_challan.get('weighment_txn_id__max')
                
                # # Calculate the next supply_challan_id
                # if last_challan_id and last_challan_id.startswith("TXN-"):
                # # Extract the numeric part and increment it
                #     numeric_part = int(last_challan_id.split('-')[1]) + 1
                #     next_challan_id = f"TXN-{numeric_part:09d}"
                # else:
                # # Handle the case when there are no existing supply_challan_id values
                #     next_challan_id = "TXN-000000001"
                last_challan = WeighmentSupply.objects.filter(weighment_txn_id__contains="TXN").aggregate(Max('weighment_txn_id'))
                last_challan_id = last_challan.get('weighment_txn_id__max')
                print(last_challan_id)

                # Calculate the next supply_challan_id
                if last_challan_id and last_challan_id.startswith("TXN"):
                    # Extract the numeric part and increment it
                    print("check")
                    numeric_part = int(last_challan_id[-1]) + 1
                    next_challan_id = f"TXN{numeric_part:09d}"
                    

                    # Check if the generated ID already exists
                    while WeighmentSupply.objects.filter(weighment_txn_id=next_challan_id).exists():
                        numeric_part += 2
                        next_challan_id = f"TXN{numeric_part:09d}"
                else:
                    # Handle the case when there are no existing supply_challan_id values
                    next_challan_id = "TXN000000001"
                created.weighment_txn_id=next_challan_id
                created.save()
                
                supplier_id.is_weighment_proceed=True # deliver challan used in weighmenht 
                supplier_id.save()

                serializer = WeighmentSupplySerializer(created)

                ###### send sms ##############################

                # if created.mobile_number:
                #     mobile_number = created.mobile_number
                #     template_id=''
                #     # message = f"{grower_name} has supplied {quantity} Kg.Leaf to {aggregator_name} with Rate of Rs. {rate} vide Receipt No. {next_receipt_no} - Trustea" # Your message content
                #     message=f"Your Supplt/Transaction ID is {next_challan_id}. Carry this reference up to the leaf receipt.From: Trustea Sustainable Tea Foundation."
                #     print(message)
                #     send_sms(mobile_number, message,template_id)  
                    
                return Response({'results':{
                                        'Data':serializer.data,
                                        },
                                        'msg': 'Weightment Supply Created Successfully',
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
                    supplier_type=request.data.get('supplier_type', None)
                    challan_id=request.data.get('challan_id', None)
                    mode_of_supply = request.data.get('mode_of_supply', None)
                    supply_date= request.data.get('supply_date', None)
                    total_gross_weight_kg = request.data.get('total_gross_weight', None)
                    vehicle_no_id= request.data.get('vehicle_no_id', None)
                    mobile_number= request.data.get('mobile_number', None)

                    weighment_details = WeighmentSupply.cmobjects.filter(pk=id).first()

                    if not weighment_details:
                        return Response({'results': [],
                                        'msg': "Selected Weighment Details Does'nt exists!",
                                        "request_status": 0}, status=status.HTTP_400_BAD_REQUEST)


                    update=WeighmentSupply.cmobjects.filter(id=id)\
                        .update(supplier_type=supplier_type,mode_of_supply=mode_of_supply,supply_challan_id=challan_id,\
                                                          supply_date=supply_date,mobile_number=mobile_number,\
                		total_gross_weight_kg=total_gross_weight_kg,updated_by=request.user)
                    if vehicle_no_id:
                        weighment_details.vehicle_no_id=vehicle_no_id
                        weighment_details.save()
                    return Response({'results':{
                                            'Data':WeighmentSupply.objects.filter(pk=id).values(),
                                            },
                                            'msg': ' Weighmnent Supply Data Updated SuccessFully',
                                            'status':status.HTTP_200_OK,
                                            "request_status": 1})
            
                elif method.lower() == 'delete':
                   """
                   Delete a weighment Details
                   """
                   if WeighmentSupply.cmobjects.filter(id=id).exists():
                       weighment_details= WeighmentSupply.cmobjects.filter(id=id).first()
                       weighment_details.is_deleted = True
                       weighment_details.save()
                       
                       return Response({'results':{
                                           'form_details':WeighmentSupply.objects.filter(pk=id).values(),
                                           },
                                           'msg': 'Selected Weighment Details Deleted Successfully',
                                           "request_status": 1})
                   else:
                       return Response({'results': [],
                                       'msg': "Selected Weighment Does'nt exists!",
                                       'status': status.HTTP_404_NOT_FOUND,
                                       "request_status": 0})   
        except Exception as e:
            raise serializers.ValidationError({'status': status.HTTP_400_BAD_REQUEST,'request_status': 0, 'msg': e},code='authorization') 
class WeighmentSupplyAvailableTxnIdAPIView(APIView):
    """Weightment un-processed txn id for leaf receipt View"""
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    queryset = WeighmentSupply.objects.filter(is_deleted=False)
    serializer_class = WeighmentSupplySerializer
    def get(self, request, *args, **kwargs):
        
            id = self.request.query_params.get('id', None)          
            if id:
                queryset = self.queryset.filter(created_by=request.user,id=id,is_processed=False).order_by('-id')
            else:
                queryset=self.queryset.filter(created_by=request.user,is_processed=False).order_by('-id')    
                print(queryset)
            page_size = int(request.query_params.get('page_size', 10))
            paginator = Paginator(queryset, page_size)
            page_number = self.request.query_params.get('page', 1)
            page = paginator.get_page(page_number)
            serializer = WeighmentSupplySerializer(queryset, many=True)

            return Response({
                'count': paginator.count,
                'next': page.next_page_number() if page.has_next() else None,
                'previous': page.previous_page_number() if page.has_previous() else None,
                'results': serializer.data,
            })
    

class LeafReceiptAPIView(APIView):
    """Leaf receipt API View"""
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    queryset = LeafManagement.objects.filter(is_deleted=False)
    serializer_class = LeafReceiptSerializer
    def get(self, request, *args, **kwargs):
        
            id = self.request.query_params.get('id', None)    
            date_from=self.request.query_params.get('date_from', None) 
            date_to = self.request.query_params.get('date_to', None)     
            if id:
                queryset = self.queryset.filter(created_by=request.user,id=id).order_by('-id')
            elif (date_from and date_to):
                 queryset = self.queryset.filter(created_by=request.user,supply_date__range=[date_from,date_to]).order_by('-id')    
            else:
                queryset=self.queryset.filter(created_by=request.user).order_by('-id')    
                print(queryset)
            page_size = int(request.query_params.get('page_size', 10))
            paginator = Paginator(queryset, page_size)
            page_number = self.request.query_params.get('page', 1)
            page = paginator.get_page(page_number)
            serializer = LeafReceiptSerializer(queryset, many=True)

            return Response({
                'count': paginator.count,
                'next': page.next_page_number() if page.has_next() else None,
                'previous': page.previous_page_number() if page.has_previous() else None,
                'results': serializer.data,
            })
    def post(self, request, format=None):
        try:
            weighment_txn=request.data.get('txn_id', None)
            supply_date = request.data.get('supply_date', None)
            deduction= request.data.get('deduction', None)
            final_leaf_count = request.data.get('final_leaf_count', None)
            quality_standard= request.data.get('quality', None)
            payment_record_option= request.data.get('keep_payment_record', None)
            acknowledge_status= request.data.get('acknowledge_status', None)
            weighment_details_check = WeighmentSupply.objects.filter(id=weighment_txn, is_processed=True).first()
            if weighment_details_check:
                return Response({
                    'msg': 'Leaf receipt for this weighment ID is already processed',
                    'status': status.HTTP_400_BAD_REQUEST,
                    'request_status': 0
                },status=status.HTTP_400_BAD_REQUEST)
            with transaction.atomic(): 
                created =  LeafManagement.objects.create(weighment_txn_id=weighment_txn,\
                                                          deduction=deduction,\
                		final_leaf_count=final_leaf_count,quality_standard=quality_standard,payment_record_option=\
                        payment_record_option,acknowledge_status=acknowledge_status,created_by=request.user)                
                created.save()

                # if acknowledge status is rejected then vehicle is free to use
                if str(created.acknowledge_status.lower()) == "rejected":
                    weighment_obj=WeighmentSupply.objects.filter(id=weighment_txn).first()
                    print(weighment_obj)
                    if weighment_obj:
                        weighment_obj.is_leaf_rejected = True # if leaf rejected 
                        weighment_obj.save()
                    if weighment_obj.vehicle_no:
                        VehicleManagement.objects.filter(vehicle_number=weighment_obj.vehicle_no).update(is_available=True)#vehicle availablity status
               
                # if acknowledge status is received then vehicle is not free to use
                if str(created.acknowledge_status.lower()) == "received":
                    weighment_obj=WeighmentSupply.objects.filter(id=weighment_txn).first()
                    if weighment_obj.vehicle_no:
                        VehicleManagement.objects.filter(vehicle_number=weighment_obj.vehicle_no).update(is_available=False)#vehicle availablity status
                


                ##calculate actual net leaf weight after leaf receipt##
                weighment_details=WeighmentSupply.objects.filter(id=weighment_txn).first()
                if weighment_details:
                    weighment_details.is_processed = True
                    weighment_details.save()
                    if str(weighment_details.mode_of_supply) != 'Motorised 3 / 4 wheelers vehicle':
                        if weighment_details.vehicle_no:
                            VehicleManagement.objects.filter(vehicle_number=weighment_details.vehicle_no).update(is_available=True)#vehicle availablity status
                            CollectionFromGrower.objects.filter(vehicle_number=weighment_details.vehicle_no).update(is_complete=True)
                        # if created.deduction:
                        moisture_deduction = created.deduction
                        total_gross_weight = weighment_details.total_gross_weight_kg
                        net_leaf_weight = total_gross_weight
                        x = net_leaf_weight * (float(moisture_deduction) / 100)
                        created.net_leaf_weight = round(float(net_leaf_weight) - float(x), 2)
                        created.save()
                # else:
                #     # Handle the case where weighment_details is None
                #     # You might want to raise an exception, return an error response, or handle it in another appropriate way
                #     pass            
                ## end calculation ##    
                serializer = LeafReceiptSerializer(created)
                ## data insert into leaf collection model for report ##
                if created.net_leaf_weight:
                    net_leaf_weight=created.net_leaf_weight
                else:
                    net_leaf_weight=0
                if str(weighment_details.supplier_type) == "aggregator":
                    profile_model = AggregatorProfile
                elif str(weighment_details.supplier_type) == "grower":
                    profile_model = GrowerProfile
                else:
                    profile_model = ""

                supplier_details = profile_model.cmobjects.filter(user_id=weighment_details.supplier).first()
                ## plucking code ######
                if str(weighment_details.supplier_type) == "grower":
                    if PluckingData.cmobjects.filter(grower_id=supplier_details).exists():
                        plucking_details = PluckingData.cmobjects.filter(grower_id=supplier_details).first()
                        plucking_details_id = plucking_details.id
                    else:
                        plucking_details = None
                        plucking_details_id = None
                else:
                    plucking_details = None


                if weighment_details and supplier_details:

                    if not str(weighment_details.mode_of_supply) == "Motorised 3 / 4 wheelers vehicle":
                        
                        if str(weighment_details.supplier_type) == "aggregator":

                            leaf_collection_create=LeafCollection.objects.create(
                                leaf_receipt_id_id = created.id,
                                weighment_supply_id_id=weighment_details.id,
                                supply_id_id = weighment_details.supply_challan.id,
                                supplier_id = weighment_details.supplier.id,
                                nt_wght=net_leaf_weight,
                                collection_date=weighment_details.supply_challan.date_of_supply,
                                supplier_type = weighment_details.supplier_type,
                                aggregator_id = supplier_details.id,
                                supply_date =weighment_details.supply_challan.date_of_supply,
                                created_by_id = request.user.id
                            )	
                            leaf_collection_create.save()	
                        elif str(weighment_details.supplier_type) == "grower":
                            leaf_collection_create=LeafCollection.objects.create(
                                leaf_receipt_id_id = created.id,
                                weighment_supply_id_id=weighment_details.id,
                                supply_id_id = weighment_details.supply_challan.id,
                                supplier_id = weighment_details.supplier.id,
                                nt_wght=net_leaf_weight,
                                collection_date= weighment_details.supply_challan.date_of_supply,
                                supplier_type = weighment_details.supplier_type,
                                grower_id = supplier_details.id,
                                supply_date = weighment_details.supply_challan.date_of_supply,
                                created_by_id = request.user.id
                            )
                            leaf_collection_create.save()
                            if plucking_details_id:
                                leaf_collection_create.plucking_data_id=plucking_details_id
                                leaf_collection_create.save()

                if weighment_details:
                    created.supply_date=weighment_details.supply_challan.date_of_supply
                    created.save()

                print(weighment_details.supplier_type)
                ###### send sms ####################    
                if  weighment_details.mobile_number: 
                    blf_obj=BlfProfile.cmobjects.filter(user_id=weighment_details.created_by.id).first()
                    if blf_obj:
                        blf_name=blf_obj.entity_unit
                    else :
                        blf_name="NA"   
                    if weighment_details.mobile_number:
                        mobile_number = weighment_details.mobile_number
                        template_id='1007337628231486262'
                        # message = f"{grower_name} has supplied {quantity} Kg.Leaf to {aggregator_name} with Rate of Rs. {rate} vide Receipt No. {next_receipt_no} - Trustea" # Your message content
                        message=f"Factory {blf_name} has received leaf vide TXN ID {weighment_details.weighment_txn_id}. From: Trustea Sustainable Tea Foundation."
                        print(message)
                        print(mobile_number)
                        if mobile_number:
                            send_sms(mobile_number, message,template_id)  
                    
                  
                if str(weighment_details.supplier_type) == "aggregator":
                    blf_obj=BlfProfile.cmobjects.filter(user_id=weighment_details.created_by.id).first()
                    if blf_obj:
                        blf_name=blf_obj.entity_unit
                    else :
                        blf_name="NA"  
                    aggregator_obj=AggregatorProfile.objects.filter(id=supplier_details.id).first()
                    if aggregator_obj:    
                        mobile_number = aggregator_obj.mobile_number
                        print(mobile_number)
                        template_id='1007337628231486262'
                        message=f"Factory {blf_name} has received leaf vide TXN ID {weighment_details.weighment_txn_id}. From: Trustea Sustainable Tea Foundation."
                        print(message)
                        if mobile_number:
                            send_sms(mobile_number, message,template_id)	        
                elif str(weighment_details.supplier_type) == "grower":    
                    grower_obj=GrowerProfile.objects.filter(id=supplier_details.id).first()
                    print(grower_obj)
                    if grower_obj:
                        mobile_number = grower_obj.mobile_number
                        template_id='1007653300295427731'
                        message=f"Collected leaf by agent has been received in factory with Deduction of {deduction} and FLC of {final_leaf_count}. From: Trustea Sustainable Tea Foundation."
                        print(message)
                        if mobile_number:
                            send_sms(mobile_number, message,template_id) 
                                   
                                   
                return Response({'results':{
                                        'Data':serializer.data ,
                                        },
                                        'msg': 'Leaf Receipt Created Successfully',
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
                    weighment_txn=request.data.get('txn_id', None)
                    supply_date = request.data.get('supply_date', None)
                    deduction= request.data.get('deduction', None)
                    final_leaf_count = request.data.get('final_leaf_count', None)
                    quality_standard= request.data.get('quality', None)
                    payment_record_option= request.data.get('keep_payment_record', None)
                    acknowledge_status= request.data.get('acknowledge_status', None)

                    leaf_details = LeafManagement.cmobjects.filter(pk=id).first()

                    if not leaf_details:
                        return Response({'results': [],
                                        'msg': "Selected Leaf Details Does'nt exists!",
                                        "request_status": 0}, status=status.HTTP_400_BAD_REQUEST)


                    update=LeafManagement.cmobjects.filter(id=id)\
                        .update(weighment_txn_id=weighment_txn,supply_date=supply_date,\
                                                          deduction=deduction,\
                		final_leaf_count=final_leaf_count,quality_standard=quality_standard,payment_record_option=\
                        payment_record_option,acknowledge_status=acknowledge_status,updated_by=request.user)
                    return Response({'results':{
                                            'Data':LeafManagement.objects.filter(pk=id).values(),
                                            },
                                            'msg': ' Leaf Receipt Data Updated SuccessFully',
                                            'status':status.HTTP_200_OK,
                                            "request_status": 1})
            
                elif method.lower() == 'delete':
                   """
                   Delete a Leaf receipt Details
                   """
                   if LeafManagement.cmobjects.filter(id=id).exists():
                       leaf_details= LeafManagement.cmobjects.filter(id=id).first()
                       leaf_details.is_deleted = True
                       leaf_details.save()
                       
                       return Response({'results':{
                                           'form_details':LeafManagement.objects.filter(pk=id).values(),
                                           },
                                           'msg': 'Selected Leaf Receipt Details Deleted Successfully',
                                           "request_status": 1})
                   else:
                       return Response({'results': [],
                                       'msg': "Selected Leaf  Does'nt exists!",
                                       'status': status.HTTP_404_NOT_FOUND,
                                       "request_status": 0})   
        except Exception as e:
            raise serializers.ValidationError({'status': status.HTTP_400_BAD_REQUEST,'request_status': 0, 'msg': e},code='authorization') 


class WeighmentTxnIdSupplyExitListAPIView(APIView):
    """Weightment txn id for 3/4 wheeler in Supply exit View"""
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    # queryset = WeighmentSupply.objects.filter(is_deleted=False)
    queryset = LeafManagement.objects.filter(is_deleted=False)
    serializer_class = LeafReceiptSerializer
    def get(self, request, *args, **kwargs):
            id = self.request.query_params.get('id', None)          
            if id:
                # queryset = self.queryset.filter(created_by=request.user,id=id,mode_of_supply ='Motorised 3 / 4 wheelers vehicle', \
                #                                 is_processed=False).order_by('-id')
                # queryset=self.queryset.filter(created_by=request.user,id=id,acknowledge_status='Received',\
                #                               weighment_txn__mode_of_supply='Motorised 3 / 4 wheelers vehicle', \
                #                                 is_processed=False).values('id','weighment_txn',\
                #                                 'weighment_txn__weighment_txn_id','acknowledge_status' ,'weighment_txn__mode_of_supply').\
                #                                 order_by('-id')  
                queryset=self.queryset.filter(created_by=request.user, acknowledge_status__iexact='Received',\
                                              weighment_txn__mode_of_supply__iexact='Motorised 3 / 4 wheelers vehicle', \
                                              weighment_txn__is_processed=True, weighment_txn__is_supplier_exit_proceed=False).order_by("-id")
            else:
              
                queryset=self.queryset.filter(created_by=request.user, acknowledge_status__iexact='Received',\
                                              weighment_txn__mode_of_supply__iexact='Motorised 3 / 4 wheelers vehicle', \
                                               weighment_txn__is_processed=True,weighment_txn__is_supplier_exit_proceed=False).order_by("-id")
            page_size = int(request.query_params.get('page_size', 10))
            paginator = Paginator(queryset, page_size)
            page_number = self.request.query_params.get('page', 1)
            page = paginator.get_page(page_number)
            serializer = LeafReceiptSerializer(queryset, many=True)
            return Response({
                'count': paginator.count,
                'next': page.next_page_number() if page.has_next() else None,
                'previous': page.previous_page_number() if page.has_previous() else None,
                # 'results':[{'txn_id':result.weighment_txn_id,'Weighment_trans_id':result.weighment_txn_id__weighment_txn_id}],
                'results':queryset.values('weighment_txn_id','weighment_txn_id__weighment_txn_id','weighment_txn_id__total_gross_weight_kg'),
                'msg':" List of TXN IDs were Received during leaf receipt having 3 /4 wheelers motorized vehicle for supply "
            })



class SupplierExitAPIView(APIView):
    """Supplier Exit API View"""
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    queryset = SupplierExit.objects.filter(is_deleted=False)
    serializer_class = SupplierExitSerializer
    def get(self, request, *args, **kwargs):
        
            id = self.request.query_params.get('id', None)
            date_from=self.request.query_params.get('date_from', None) 
            date_to = self.request.query_params.get('date_to', None)     
                       
            if id:
                queryset = self.queryset.filter(created_by=request.user,id=id).order_by('-id')
            elif (date_from and date_to):
                 queryset = self.queryset.filter(created_by=request.user,created_at__range=[date_from,date_to]).order_by('-id')    
            else:
                queryset=self.queryset.filter(created_by=request.user).order_by('-id')    
                print(queryset)
            page_size = int(request.query_params.get('page_size', 10))
            paginator = Paginator(queryset, page_size)
            page_number = self.request.query_params.get('page', 1)
            page = paginator.get_page(page_number)
            serializer = SupplierExitSerializer(queryset, many=True)
            return Response({
                'count': paginator.count,
                'next': page.next_page_number() if page.has_next() else None,
                'previous': page.previous_page_number() if page.has_previous() else None,
                'results': serializer.data,
            })
    def post(self, request, format=None):
        try:
            weighment_txn=request.data.get('txn_id', None)
            unloaded_vehicle_weight = request.data.get('unloaded_vehicle_weight', None)
            is_released= request.data.get('is_released', None)
            weighment_details_check = WeighmentSupply.objects.filter(id=weighment_txn, is_supplier_exit_proceed=True).first()
            if weighment_details_check:
                return Response({
                    'msg': 'Supplier exit has already been processed for transaction id',
                    'status': status.HTTP_400_BAD_REQUEST,
                    'request_status': 0
                },status=status.HTTP_400_BAD_REQUEST)
            with transaction.atomic(): 
                weighment_details=WeighmentSupply.objects.filter(id=weighment_txn).first()
                if float(weighment_details.total_gross_weight_kg) < float(unloaded_vehicle_weight):
                    return Response({'results':{
                                        'Data':[] ,
                                        },
                                        'msg': 'unloaded vehicle weight not be more than total gross during weighment  supply',
                                        'status':status.HTTP_400_BAD_REQUEST,
                                        "request_status": 0})


                created =  SupplierExit.objects.create(weighment_txn_id=weighment_txn, unloaded_vehicle_weight=\
                                                         unloaded_vehicle_weight,\
                                                          is_released=is_released,created_by=request.user)
                created.save()
               
                WeighmentSupply.objects.filter(id=weighment_txn).update(is_supplier_exit_proceed=True)
                # weighment_details=WeighmentSupply.objects.filter(id=weighment_txn).first()
                # print(weighment_details)
                if str(created.is_released.lower()) == 'yes' :
                    VehicleManagement.objects.filter(vehicle_number=weighment_details.vehicle_no).update(is_available=True)#vehicle availablity status
                    CollectionFromGrower.objects.filter(vehicle_number=weighment_details.vehicle_no).update(is_complete=True)

                ## calculate net quantity OR actual net weight after supplier exit##
                leaf_obj=LeafManagement.objects.filter(weighment_txn_id=weighment_txn).first()
                # if leaf_obj.deduction:
                if leaf_obj:
                    moisture_deduction=leaf_obj.deduction 
                    gross_weight=weighment_details.total_gross_weight_kg
                    net_leaf_weight=gross_weight-float(created.unloaded_vehicle_weight)
                    x=net_leaf_weight*(float(moisture_deduction)/100)
                    created.net_supplied_qty=round(float(net_leaf_weight)-float(x),2)
                    created.save()
                ## end calculation ##     

                serializer = SupplierExitSerializer(created)
                #### leaf collection data ###############
                weighment_details = WeighmentSupply.cmobjects.filter(created_by_id=request.user.id,\
                                     id=weighment_txn).first()
                if weighment_details:
                    if weighment_details.vehicle_no:
                        vehicle_number = weighment_details.vehicle_no
                    else:
                        vehicle_number = ""

                    if str(weighment_details.supplier_type) == "aggregator":
                        profile_model = AggregatorProfile
                    elif str(weighment_details.supplier_type) == "grower":
                        profile_model = GrowerProfile
                    else:
                        profile_model = ""


                    # PROFILE DETAILS
                    supplier_details = profile_model.cmobjects.filter(user_id=weighment_details.supplier).first()
                    if str(weighment_details.supplier_type) == "grower":
                        if PluckingData.cmobjects.filter(grower_id=supplier_details).exists():
                            plucking_details = PluckingData.cmobjects.filter(grower_id=supplier_details).first()
                            plucking_details_id = plucking_details.id
                        else:
                            plucking_details = None
                            plucking_details_id = None
                    else:
                        plucking_details = None
                    # SUPPLY DETAILS
                    supply_chalan_id = weighment_details.supply_challan.id
                    supply_details = SupplyManagement.cmobjects.filter(id=supply_chalan_id).first()
                    
                    if weighment_details and supplier_details :
                        if str(weighment_details.supplier_type) == "aggregator":
                            leaf_collection_create=LeafCollection.objects.create(
                                leaf_receipt_id_id = leaf_obj.id,
                                suppler_exit_id_id = created.id,
                                weighment_supply_id_id=weighment_details.id,
                                supply_id_id = supply_details.id,
                                supplier_id = weighment_details.supplier_id,
                                nt_wght= created.net_supplied_qty,
                                collection_date=  weighment_details.supply_challan.date_of_supply,
                                supplier_type = weighment_details.supplier_type,
                                aggregator_id = supplier_details.id,
                                supply_date =  weighment_details.supply_challan.date_of_supply,
                                created_by_id = request.user.id
                            )	
                            leaf_collection_create.save()

                        elif str(weighment_details.supplier_type) == "grower":
                            leaf_collection_create=LeafCollection.objects.create(
                                leaf_receipt_id_id = leaf_obj.id,
                                suppler_exit_id_id = created.id,
                                weighment_supply_id_id=weighment_details.id,
                                supply_id_id = supply_details.id,
                                supplier_id = weighment_details.supplier_id,
                                nt_wght= created.net_supplied_qty,
                                collection_date= weighment_details.supply_challan.date_of_supply,
                                supplier_type = weighment_details.supplier_type,
                                grower_id = supplier_details.id,
                                supply_date =  weighment_details.supply_challan.date_of_supply,
                                created_by_id = request.user.id
                            )
                            leaf_collection_create.save()
                            if plucking_details_id:
                                leaf_collection_create.plucking_data_id=plucking_details_id
                                leaf_collection_create.save()
                return Response({'results':{
                                        'Data':serializer.data ,
                                        },
                                        'msg': 'Supplier Exit processed  Successfully',
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
                    
                    if not id :
                        return Response({
                                        'msg': "Id is missing!",
                                        "request_status": 0}, status=status.HTTP_400_BAD_REQUEST)
                        
                    supplier_details = SupplierExit.cmobjects.filter(pk=id).first()
                    
                    if not supplier_details:
                        return Response({'results': [],
                                        'msg': "Selected Supplier Details Does'nt exists!",
                                        "request_status": 0}, status=status.HTTP_400_BAD_REQUEST)
                    weighment_txn=request.data.get('txn_id', supplier_details.weighment_txn)
                    unloaded_vehicle_weight = request.data.get('unloaded_vehicle_weight', supplier_details.unloaded_vehicle_weight)
                    is_released= request.data.get('is_released', supplier_details.is_released)
                    update=SupplierExit.cmobjects.filter(id=id)\
                        .update(weighment_txn_id=weighment_txn,unloaded_vehicle_weight=\
                                                         unloaded_vehicle_weight,\
                                                          updated_by=request.user)
                    WeighmentSupply.objects.filter(id=weighment_txn).update(is_supplier_exit_proceed=True)
                    weighment_details=WeighmentSupply.objects.filter(id=weighment_txn).first()
                    if str(is_released.lower()) == "yes":
                        supplier_details.is_released=is_released
                        supplier_details.save()
                        VehicleManagement.objects.filter(vehicle_number=weighment_details.vehicle_no).update(is_available=True)#vehicle availablity status
                    if str(is_released.lower()) == "no":
                        supplier_details.is_released=is_released
                        supplier_details.save()
                        VehicleManagement.objects.filter(vehicle_number=weighment_details.vehicle_no).update(is_available=False)#vehicle availablity status
                    return Response({'results':{
                                            'Data':SupplierExit.objects.filter(pk=id).values(),
                                            },
                                            'msg': ' Supplier Exit Data Updated SuccessFully',
                                            'status':status.HTTP_200_OK,
                                            "request_status": 1})
            
                elif method.lower() == 'delete':
                   """
                   Delete a Supplier Exit Details
                   """
                   if SupplierExit.cmobjects.filter(id=id).exists():
                       supplier_details= SupplierExit.cmobjects.filter(id=id).first()
                       supplier_details.is_deleted = True
                       supplier_details.save()
                       
                       return Response({'results':{
                                           'form_details':SupplierExit.objects.filter(pk=id).values(),
                                           },
                                           'msg': 'Selected Supplier Exit Details Deleted Successfully',
                                           "request_status": 1})
                   else:
                       return Response({'results': [],
                                       'msg': "Selected Supplier Exit Does'nt exists!",
                                       'status': status.HTTP_404_NOT_FOUND,
                                       "request_status": 0})   
        except Exception as e:
            raise serializers.ValidationError({'status': status.HTTP_400_BAD_REQUEST,'request_status': 0, 'msg': e},code='authorization')     