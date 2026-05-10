from rest_framework import serializers
from django.contrib.auth.models import *
from rest_framework.exceptions import APIException
from django.contrib.auth import authenticate

from django.contrib import auth
from rest_framework.exceptions import AuthenticationFailed
""" Reset password and send link with token"""
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import smart_str, force_str, smart_bytes, DjangoUnicodeDecodeError
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from .models import *
from rest_framework import status
from django.db.models import Q
from gardens_managment.models import Plot,Gardens
from user_profile.aggregator_api_models import *
from user_profile.blf_api_models import *
from chemical_data.models import *
from weighment_supply.models import *
from leaf_receipt.models import *
from user_profile.grower_api_models import *
from django.core.files.base import ContentFile
import base64
from master.helper import get_details_from_instance
from vehicle_management.serializers import VehicleManagementSerializer
from django.db.models import Sum, IntegerField
from django.db.models.functions import Cast
from datetime import timedelta, date
from django.db import transaction
from .helpers import *
class CommonFilterListSerializer(serializers.ListSerializer):
    """
    ListSerializer
    cmobject: is_deleted=False
    """
    def to_representation(self, data):
        if hasattr(data, 'object_list'):
            data.object_list = [item for item in data.object_list if not item.is_deleted]
        else:
            data = data.filter(is_deleted=False)
        return super().to_representation(data)
    

class LandTypeSerializier(serializers.ModelSerializer):
    # grower=serializers.SerializerMethodField()
    class Meta:
        model = LandType
        fields = '__all__'
 
    
class GardenSerializer(serializers.ModelSerializer):
    # grower=serializers.SerializerMethodField()
    land_type_details=serializers.SerializerMethodField(read_only=True)
    class Meta:
        model = Gardens
        exclude=('is_deleted','is_verify','created_at','updated_at')
 
    def get_land_type_details(self, obj):
        land_details= obj.land_type
        land_data = LandTypeSerializier(land_details, context=self.context).data
        return land_data  
    
class PlotListSerializer(serializers.ModelSerializer):
    garden = serializers.SerializerMethodField()
    class Meta:
        model = Plot
        fields = '__all__'
    def get_garden(self, obj):
        garden_details= obj.garden
        garden_data = GardenSerializer(garden_details, context=self.context).data
        return garden_data  
   
    # def get_grower(self, obj):
    #     grower_details= obj.garden
    #     grower_data = GrowerProfileSerializer(grower_details, context=self.context).data
    #     return grower_data  
class DivisionListSerializer(serializers.ModelSerializer):
    garden = serializers.SerializerMethodField()
    class Meta:
        model = Division
        fields = '__all__'
        
 
    def get_garden(self, obj):
        garden_details= obj.garden
        garden_data = GardenSerializer(garden_details, context=self.context).data
        return garden_data  

class UserProfileAttachmentsSerializer(serializers.ModelSerializer):
    """
    User Profile ID Attachments Attachments Serializer
    """
    id = serializers.IntegerField(required=False)
    class Meta:
        model = UserProfileAttachments
        fields = '__all__'
        read_only_fields = ['id']
        list_serializer_class = CommonFilterListSerializer

class GrowerProfileSerializer(serializers.ModelSerializer):
    """ Grower Profile Model Serializer """
    garden_details = serializers.SerializerMethodField()
    plot_details = serializers.SerializerMethodField()
    division_details = serializers.SerializerMethodField() 
    associated_entity = serializers.SerializerMethodField()
    associated_aggregator = serializers.SerializerMethodField()
    state = serializers.SerializerMethodField()
    district = serializers.SerializerMethodField()
    region = serializers.SerializerMethodField()
    username = serializers.SerializerMethodField()
    plucked_quantity = serializers.SerializerMethodField()
    attachments = UserProfileAttachmentsSerializer(many=True, required=False, source="grower_proof_id_attachments")
    class Meta:
        model = GrowerProfile
        fields = '__all__'

    @transaction.atomic
    def create(self, validated_data):
        attachments_data = validated_data.pop('grower_proof_id_attachments', [])
        grower_data = GrowerProfile.objects.create(**validated_data)
        current_user = grower_data.created_by if grower_data.created_by else None
        for attachment_data in attachments_data:
            try:
                attachment = UserProfileAttachments.objects.create(
                    grower=grower_data,
                    attachment=process_attachments(attachment_data),
                    file_data="",
                    mime_type="", doc_type = attachment_data.get('doc_type', None),
                    attachment_name=attachment_data.get('attachment_name', None),
                    doc_no = attachment_data.get('doc_no', None),
                    created_by=current_user
                )
            except Exception as e:
                print(f"exception: {e}")
        grower_data.save()
        return grower_data
    @transaction.atomic
    def update(self, instance, validated_data):
        attachments_data = validated_data.get('grower_proof_id_attachments', [])
        for field in instance._meta.fields:
            field_name = field.name
            if field_name in validated_data:
                setattr(instance, field_name, validated_data[field_name])
        instance.save()
        current_user = instance.updated_by if instance.updated_by else None
        existing_attachments = instance.grower_proof_id_attachments.filter(is_deleted=False)
        for attachment_data in attachments_data:
            attachment_id = attachment_data.get('id')
            temp_attach_data = process_attachments(attachment_data)
            existing_attachment = next((attachment for attachment in existing_attachments if attachment.id == attachment_id), None)
            if not existing_attachment:
                existing_attachment = UserProfileAttachments.objects.create(

                    grower=instance,
                    attachment=process_attachments(attachment_data),
                    file_data="", doc_type = attachment_data.get('doc_type', None),
                    doc_no = attachment_data.get('doc_no', None),
                    mime_type="", attachment_name=attachment_data.get('attachment_name', None),
                    created_by=current_user
                )
            else:
                if temp_attach_data:
                    setattr(existing_attachment, 'attachment', temp_attach_data)
                setattr(existing_attachment, 'attachment_name', attachment_data.get('attachment_name', None))
                setattr(existing_attachment, 'doc_type', attachment_data.get('doc_type', None))
                setattr(existing_attachment, 'doc_no', attachment_data.get('doc_no', None))
                setattr(existing_attachment, 'updated_by', current_user)
                existing_attachment.save() 
              
        instance.save()
        return instance
    def get_garden_details(self, obj):
        """Return all gardens belonging to this grower"""
        gardens = obj.gardens_grower.all() 
        return GardenSerializer(gardens, many=True, context=self.context).data

    def get_plot_details(self, obj):
            """Return only: garden_id, name, plot_area, plot_status"""
            plots = Plot.objects.filter(garden__in=obj.gardens_grower.all())
            plot_data = []
            for plot in plots:
                plot_data.append({
                    "garden_id": plot.garden_id,      # or plot.garden.id if you prefer
                    "name": plot.name,
                    "plot_area": plot.plot_area,
                    "plot_status": plot.plot_status,
                })
            return plot_data

    def get_division_details(self, obj):
            """Return only: garden_id, name (add more fields if needed)"""
            divisions = Division.objects.filter(garden__in=obj.gardens_grower.all())
            return [
                {
                    "garden_id": division.garden_id,
                    "name": division.name,
                }
                for division in divisions
            ]

    def get_username(self, obj):
        return obj.user.username if obj.user else None

    def get_state(self, obj):
        if obj.state:
            return StateSerializer(obj.state, context=self.context).data
        return None

    def get_district(self, obj):
        if obj.district:
            return DistrictSerializer(obj.district, context=self.context).data
        return None

    def get_region(self, obj):
        if obj.region:
            return RegionSerializer(obj.region, context=self.context).data
        return None

    def get_plucked_quantity(self, instance):
        total_quantity_plucked = (
            PluckingData.cmobjects
            .filter(created_by=instance.user, quantity_plucked__isnull=False)
            .annotate(qty_float=Cast('quantity_plucked', FloatField()))
            .aggregate(total_qty=Sum('qty_float'))["total_qty"] or 0.0
        )
        return total_quantity_plucked

    def get_associated_entity(self, obj):
        """Returns list of associated entities"""
        return [
            {
                'id': entity.id,
                'user_id': entity.user.id,
                'username': entity.user.username,
                'email': entity.email,
                'profile_type': entity.profile_type.name if entity.profile_type else None,
                'tcmo_no': entity.tcmo_no,
                'is_tcms_user': entity.is_tcms_user,
                'mobile_number': entity.mobile_number,
                'address': entity.address,
                'entity_unit': entity.entity_unit,
            }
            for entity in obj.associated_entity.all()
        ]
    def get_associated_aggregator(self, obj):
        """Returns list of associated aggregators with proper handling"""
        data = []
        for aggregator in obj.associated_aggregator.all():
            aggregator_data = {
                'id': aggregator.id,
                'user_id': aggregator.user.id if aggregator.user else None,
                'username': aggregator.user.username if aggregator.user else None,
                'name': aggregator.name,
                'mobile_number': aggregator.mobile_number,
                'email': aggregator.email,
                'region': aggregator.region.region_name if aggregator.region else "",
                'state': aggregator.state.name if aggregator.state else "",
                'aggregator_type': aggregator.aggregator_type,
                'address': aggregator.address,
                'profile_type': aggregator.profile_type.name if aggregator.profile_type else None,
            }
            data.append(aggregator_data)
        
        return data
    
class AggregatorProfileSerializer(serializers.ModelSerializer):
    """ Aggregator Profile Model Serializer """

    associated_entity = serializers.SerializerMethodField()
    associated_aggregator = serializers.SerializerMethodField()
    state=serializers.SerializerMethodField()
    region=serializers.SerializerMethodField()
    username = serializers.SerializerMethodField()
    class Meta:
        model = AggregatorProfile
        exclude=('is_deleted','is_verify','created_at','updated_at')
    def get_associated_aggregator(self, obj):
        for associated_aggregator in obj.associated_aggregator.all():
            if (associated_aggregator.region and associated_aggregator.state ) is not None:
                print(associated_aggregator.region.region_name)
                data=[{'id': associated_aggregator.id, 'user_id':associated_aggregator.user.id,'username': associated_aggregator.user.username,'name': associated_aggregator.name ,'mobile_number': associated_aggregator.mobile_number,\
                 'email':associated_aggregator.email,'region':associated_aggregator.region.region_name,\
                    'state':associated_aggregator.state.name,\
                    'aggregator_type':associated_aggregator.aggregator_type,'address':associated_aggregator.address,'profile_type':associated_aggregator.profile_type.name,}]\
                 

            else:
               data=[{'id': associated_aggregator.id, 'user_id':associated_aggregator.user.id,'username': associated_aggregator.user.username,'name': associated_aggregator.name ,'mobile_number': associated_aggregator.mobile_number,\
                 'email':associated_aggregator.email,'region':"",'state':"",\
                    'aggregator_type':associated_aggregator.aggregator_type,'address':associated_aggregator.address,'profile_type':associated_aggregator.profile_type.name,}]
            return data      
    def get_associated_entity(self, obj):
       
        return  [{'id': associated_entity.id, 'user_id':associated_entity.user.id,'username': associated_entity.user.username,\
                  'email':associated_entity.email,'profile_type':associated_entity.profile_type.name,\
                  'mobile_number': associated_entity.mobile_number, 'address':associated_entity.address,'entity_unit':associated_entity.entity_unit}\
                      for associated_entity in obj.associated_entity.all()]        
    def get_state(self,obj):
        state_details= obj.state
        state_data = StateSerializer(state_details, context=self.context).data
        return state_data 
    def get_region(self,obj):
        region_details= obj.region
        region_data = RegionSerializer(region_details, context=self.context).data
        return region_data
    def get_username(self, obj):
        return obj.user.username if obj.user else None 
 

class CollectionFromGrowerSerializer(serializers.ModelSerializer):
    """ Collection from grower serializer """
    grower= serializers.SerializerMethodField()
    vehicle_number=serializers.SerializerMethodField()
    plot=serializers.SerializerMethodField()
    
    class Meta:
        model = CollectionFromGrower
        exclude=('is_deleted','is_verify','created_at','updated_at')        
    def get_grower(self, obj):
        details= obj.grower
        grower= GrowerProfileSerializer(details, context=self.context).data
        return grower
    def get_vehicle_number(self, obj):
        details= obj.vehicle_number
        vehicle_number= VehicleManagementSerializer(details, context=self.context).data
        return vehicle_number
    def get_plot(self, obj):
        details= obj.plot
        plot= PlotListSerializer(details, context=self.context).data
        return plot
   
class CollectionFromAggregatorSerializer(serializers.ModelSerializer):
    """ Collection from aggregator serializer """

    aggregator= serializers.SerializerMethodField()
    vehicle_number=serializers.SerializerMethodField()
    plot=serializers.SerializerMethodField()
    class Meta:
        model = CollectionFromAggregator
        exclude=('is_deleted','is_verify','created_at','updated_at')        
    def get_aggregator(self, obj):
        details= obj.aggregator
        aggregator= AggregatorProfileSerializer(details, context=self.context).data
        return aggregator
    def get_vehicle_number(self, obj):
        details= obj.vehicle_number
        vehicle_number= VehicleManagementSerializer(details, context=self.context).data
        return vehicle_number
    def get_plot(self, obj):
        details= obj.plot
        plot= PlotListSerializer(details, context=self.context).data
        return plot

class LabourSerializer(serializers.ModelSerializer):
    """ Labour serializer """
    class Meta:
        model = Labour
        fields = "__all__"


class ChemicalTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChemicalType
        fields = "__all__"

class ChemicalDataSerializer(serializers.ModelSerializer):
    chemical_type_details=serializers.SerializerMethodField()
    class Meta:
        model = ChemicalData
        fields = "__all__"
    def get_chemical_type_details(self, instance):
        return ChemicalType.cmobjects.filter(id=instance.chemical_type_id).values('id','name')

class UseOfChemicalSerializer(serializers.ModelSerializer):
    labour_details= serializers.SerializerMethodField()
    chemical_details=serializers.SerializerMethodField()
    plot_details=serializers.SerializerMethodField()
    division_details=serializers.SerializerMethodField()
    created_by_details = serializers.SerializerMethodField()
    grower_details = serializers.SerializerMethodField()
    aggregator_details = serializers.SerializerMethodField()
    blf_details = serializers.SerializerMethodField()

    class Meta:
        model = UseOfChemical
        fields = "__all__"
    def get_labour_details(self, instance):
        return get_details_from_instance(instance.labour)
    def get_chemical_details(self, instance):
        return get_details_from_instance(instance.chemical)
    def get_plot_details(self, instance):
        return get_details_from_instance(instance.plot)
    def get_division_details(self, instance):
        return get_details_from_instance(instance.division)
    
    def get_grower_details(self, instance):
        _details = None
        if instance.grower and instance.grower_id:
            _details = GrowerProfile.cmobjects.filter(pk=instance.grower_id).values('id','user__username', 'name')
        return _details
    def get_aggregator_details(self, instance):
        _details = None
        if instance.aggregator and instance.aggregator_id:
            _details = AggregatorProfile.cmobjects.filter(pk=instance.aggregator_id).values('id','user__username', 'name')
        return _details
    def get_blf_details(self, instance):
        _details = None
        if instance.blf and instance.blf_id:
            _details = BlfProfile.cmobjects.filter(pk=instance.blf_id).values('id','user__username', 'entity_unit', 'entity_name')
        return _details
    def get_created_by_details(self, instance):
        _details = None
        if instance.created_by and instance.created_by_id:
            _details = User.objects.filter(pk=instance.created_by_id).values('id','username')
        return _details

class PluckingDataSerializer(serializers.ModelSerializer):
    labour_details= serializers.SerializerMethodField()
    plot_details=serializers.SerializerMethodField()
    division_details=serializers.SerializerMethodField()
    created_by_details = serializers.SerializerMethodField()
    grower_details = serializers.SerializerMethodField()
    class Meta:
        model = PluckingData
        fields = "__all__"

    def get_labour_details(self, instance):
        labour_list = []
        for item in instance.labours.all():  
            labour_list.append({
                "id": item.id,
                "name": item.name,
                "type": item.type,
                "gender": item.gender,
                "age": item.age,
            })
        return labour_list

    def get_plot_details(self, instance):
        return get_details_from_instance(instance.plot)
    def get_division_details(self, instance):
        return get_details_from_instance(instance.division)
    def get_grower_details(self, instance):
        _details = None
        if instance.grower and instance.grower_id:
            _details = GrowerProfile.cmobjects.filter(pk=instance.grower_id).values('id','user__username', 'name')
        return _details
    def get_created_by_details(self, instance):
        _details = None
        if instance.created_by and instance.created_by_id:
            _details = User.objects.filter(pk=instance.created_by_id).values('id','username', 'profile__user_type__name')
        return _details 

class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        exclude=('is_deleted','created_at','updated_at')

class StateSerializer(serializers.ModelSerializer):
    class Meta:
        model = State
        exclude=('is_deleted','created_at','updated_at') 

class DistrictSerializer(serializers.ModelSerializer):
    class Meta:
        model = District
        exclude=('is_deleted','created_at','updated_at')  

class BlfProfileSerializer(serializers.ModelSerializer):
    state=serializers.SerializerMethodField()
    region=serializers.SerializerMethodField()
    username = serializers.SerializerMethodField()
    class Meta:
        model = BlfProfile
        exclude=('is_deleted','is_verify','created_at','updated_at')  
    def get_state(self,obj):
        state_details= obj.state
        state_data = StateSerializer(state_details, context=self.context).data
        return state_data 
    def get_region(self,obj):
        region_details= obj.region
        region_data = RegionSerializer(region_details, context=self.context).data
        return region_data    
    def get_username(self, obj):
        return obj.user.username if obj.user else None  
    

class GrowerDetailsSupplySerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False) 
    class Meta:
        model = GrowerDetailsSupply
        fields = '__all__'
        read_only_fields = ['id']
        list_serializer_class = CommonFilterListSerializer   

class SupplyManagementSerializer(serializers.ModelSerializer):
    alloted_vehicle_details = serializers.SerializerMethodField()
    consumer_details = serializers.SerializerMethodField()
    collection_items = GrowerDetailsSupplySerializer(many=True,required=False, source='supply_id')
    
    def get_consumer_details(self, instance):
        if instance.consumer:
            name = f"{instance.consumer.first_name} {instance.consumer.last_name}".strip()
            username = instance.consumer.username
            phone_no = getattr(instance.consumer.profile, "phone_no", "")
            full_name = getattr(instance.consumer.profile, "full_name", "")
            profile_username = getattr(instance.consumer.profile.user, "username", "")
            return {
                "id" : instance.consumer.profile.id or "",
                "username": username,
                "phone_no": phone_no,
                "full_name": full_name,
                "user_type" : instance.consumer.profile.user_type.name or "",
            }
        return {}

    def get_alloted_vehicle_details(self, instance):
        return get_details_from_instance(instance.alloted_vehicle, extras=[],)

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop('supply_id', [])
        _details = SupplyManagement.objects.create(**validated_data)
        current_user = _details.created_by if _details.created_by else None
        _details.save()
        for item_data in items_data:
            item = GrowerDetailsSupply.objects.create(
                supply=_details, created_by=current_user, **item_data
            )
        return _details
    
    @transaction.atomic
    def update(self, instance, validated_data):
        items_data = validated_data.pop('supply_id', [])
        current_user = instance.updated_by if instance.updated_by else None
        for field in instance._meta.fields:
            field_name = field.name
            if field_name in validated_data:
                setattr(instance, field_name, validated_data[field_name])
        instance.save()
        existing_items = list(instance.supply_id.filter(is_deleted=False))
        payload_ids = [item.get('id') for item in items_data if item.get('id')]
        for item_data in items_data:
            item_id = item_data.get('id')
            existing_item = next((i for i in existing_items if i.id == item_id), None)
            if existing_item:
                for field in existing_item._meta.fields:
                    field_name = field.name
                    if field_name in item_data:
                        setattr(existing_item, field_name, item_data[field_name])
                existing_item.updated_by = current_user
                existing_item.save()
            else:
                existing_item = GrowerDetailsSupply.objects.create(
                    supply=instance, created_by=current_user, **item_data
                )
            for existing_item in existing_items:
                if existing_item.id not in payload_ids:
                    existing_item.is_deleted = True
                    existing_item.updated_by = current_user
                    existing_item.save()
        return instance
    class Meta:
        model = SupplyManagement
        fields = '__all__'  



         
class WeighmentSupplySerializer(serializers.ModelSerializer):
    """ Weighment Supply Model Serializer """
    supply_challan=serializers.SerializerMethodField()
    vehicle_no=serializers.SerializerMethodField()
    supplier=serializers.SerializerMethodField()
    class Meta:
        model = WeighmentSupply
        exclude=('is_deleted','created_at','updated_at',)
    def get_vehicle_no(self, obj):
        details= obj.vehicle_no
        vehicle_no= VehicleManagementSerializer(details, context=self.context).data
        return vehicle_no    
    def get_supply_challan(self, obj):
        details= obj.supply_challan
        supply_challan= SupplyManagementSerializer(details, context=self.context).data
        return supply_challan  
    def get_supplier(self, obj):
        details=obj.supplier
        supplier_list=User.objects.filter(id=details.id).values('profile_id_aggregator__name','username','profile_id_blf__entity_unit')
        return supplier_list  
class LeafReceiptSerializer(serializers.ModelSerializer):
    """ Leaf Receipt Model Serializer """
    weighment_txn= serializers.SerializerMethodField()
    class Meta:
        model = LeafManagement
        exclude=('is_deleted','created_at','updated_at',)
    def get_weighment_txn(self, obj):
        details=obj.weighment_txn
        # weighment_details=WeighmentSupply.objects.filter(id=obj.id).values('id','weighment_txn_id','supply_date',\
        #                                                                         'vehicle_no','supply_challan','mode_of_supply',\
        #                                                                             )
        weighment_details=WeighmentSupplySerializer(details, context=self.context).data
        
        return weighment_details   
        
   
class SupplierExitSerializer(serializers.ModelSerializer):
    """  Supplier Exit Model Serializer """
    weighment_txn= serializers.SerializerMethodField()
    class Meta:
        model = SupplierExit
        exclude=('is_deleted','created_at','updated_at','is_verify')       

    
    
    def get_weighment_txn(self, obj):
        weighment_details=WeighmentSupply.objects.filter(id=obj.weighment_txn.id).values('id','weighment_txn_id','supply_date',\
                                                                                'vehicle_no','supply_challan',\
                                                                                    )
        
        return weighment_details  

class YearSerializer(serializers.ModelSerializer):
    class Meta:
        model = Year
        fields = '__all__'
class MonthlyScheduleDayHoursDetailsSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False) 
    class Meta:
        model = MonthlyScheduleDayHoursDetails
        fields = '__all__'
        read_only_fields = ['id']
        list_serializer_class = CommonFilterListSerializer

class MonthlyScheduleSerializer(serializers.ModelSerializer):
    """ Monthly Schedule Model Serializer """
    year_value = serializers.SerializerMethodField()
    day_hours_items = MonthlyScheduleDayHoursDetailsSerializer(
        many=True,required=False, source='monthly_schedule_hour_details'
    )
    class Meta:
        model = MonthlySchedule
        fields = '__all__'

    def get_year_value(self, instance):
        if instance.year:
            return instance.year.year
        return None
    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop('monthly_schedule_hour_details', [])
        _details = MonthlySchedule.objects.create(**validated_data)
        current_user = _details.created_by if _details.created_by else None
        _details.save()
        for item_data in items_data:
            item = MonthlyScheduleDayHoursDetails.objects.create(
                monthly_schedule=_details, created_by=current_user, **item_data
            )
        return _details
    
    @transaction.atomic
    def update(self, instance, validated_data):
        items_data = validated_data.pop('monthly_schedule_hour_details', [])
        current_user = instance.updated_by if instance.updated_by else None
        for field in instance._meta.fields:
            field_name = field.name
            if field_name in validated_data:
                setattr(instance, field_name, validated_data[field_name])
        instance.save()
        existing_items = list(instance.monthly_schedule_hour_details.filter(is_deleted=False))
        payload_ids = [item.get('id') for item in items_data if item.get('id')]
        for item_data in items_data:
            item_id = item_data.get('id')
            existing_item = next((i for i in existing_items if i.id == item_id), None)
            if existing_item:
                for field in existing_item._meta.fields:
                    field_name = field.name
                    if field_name in item_data:
                        setattr(existing_item, field_name, item_data[field_name])
                existing_item.updated_by = current_user
                existing_item.save()
            else:
                existing_item = MonthlyScheduleDayHoursDetails.objects.create(
                    monthly_schedule=instance, created_by=current_user, **item_data
                )
            for existing_item in existing_items:
                if existing_item.id not in payload_ids:
                    existing_item.is_deleted = True
                    existing_item.updated_by = current_user
                    existing_item.save()
        return instance

class GrowerProfileUpdateSerializer(serializers.ModelSerializer):
    """ Grower Profile Update  Serializer """
    image_base64 = serializers.CharField(write_only=True,required=False)
    class Meta:
        model = GrowerProfile
        exclude=('is_deleted','created_at','updated_at',)
    def update(self,instance,validated_data):
        
        
        image_base64_data = validated_data.get('image_base64', None)
       
        if image_base64_data:
            image_data = base64.b64decode(image_base64_data)
            instance.photo.save(f"{instance.name}_grower_image.png", ContentFile(image_data))
       
        instance.save()
        return super().update(instance, validated_data)       
class AggregatorProfileUpdateSerializer(serializers.ModelSerializer):
    """ Aggregator Profile Update  Serializer """
    image_base64 = serializers.CharField(write_only=True,required=False)
    class Meta:
        model = AggregatorProfile
        exclude=('is_deleted','created_at','updated_at',)
    def update(self,instance,validated_data):
        
        
        image_base64_data = validated_data.get('image_base64', None)
        print("image data",image_base64_data)
        if image_base64_data:
            image_data = base64.b64decode(image_base64_data)
            instance.user_file.save(f"{instance.name}_aggregator_image.png", ContentFile(image_data))
       
        instance.save()
        return super().update(instance, validated_data)    
class BlfProfileUpdateSerializer(serializers.ModelSerializer):
    """ Blf Profile Update  Serializer """
    image_base64 = serializers.CharField(write_only=True,required=False)
    class Meta:
        model = BlfProfile
        exclude=('is_deleted','created_at','updated_at',)        
    def update(self,instance,validated_data):
        
        
        image_base64_data = validated_data.get('image_base64', None)
       
        if image_base64_data:
            image_data = base64.b64decode(image_base64_data)
            instance.user_file.save(f"{instance.entity_unit}_blf_image.png", ContentFile(image_data))
       
        instance.save()
        return super().update(instance, validated_data)           
class SupplyDetailsSerializer(serializers.Serializer):
    consumer_name = serializers.SerializerMethodField()
    consumer_id = serializers.SerializerMethodField()
    vehicle_number = serializers.SerializerMethodField()
    vehicle_name = serializers.SerializerMethodField()
    total_supply_quantity = serializers.SerializerMethodField()
    total_collected_quantity = serializers.SerializerMethodField()
    date_of_supply = serializers.DateField()
    supply_to = serializers.CharField()
    supply_challan_id = serializers.CharField()

    def get_consumer_name(self, obj):
        return obj['supply_management'].consumer.name or obj['supply_management'].consumer.entity_unit 

    def get_consumer_id(self, obj):
        return obj['supply_management'].consumer.id

    def get_vehicle_number(self, obj):
        return obj['supply_management'].alloted_vehicle.vehicle_number

    def get_vehicle_name(self, obj):
        return obj['supply_management'].alloted_vehicle.vehicle_name

    def get_total_supply_quantity(self, obj):
        return obj['supply_management'].quantity

    def get_total_collected_quantity(self, obj):
        return obj['total_collected_quantity']

    class Meta:
        fields = ('is_deleted','created_at','updated_at',) 


class KhataBookGetSerializer(serializers.ModelSerializer):
    """ Khata Book Serializer"""
    plot_name = serializers.ReadOnlyField(source='plot.name')
    grower_name = serializers.ReadOnlyField(source='grower.name')
    grower_user_name = serializers.ReadOnlyField(source='grower.user.username')
    # vehicle_number_name = serializers.ReadOnlyField(source='vehicle_number.vehicle_number')
    vehicle_number_name=serializers.SerializerMethodField()
    receipt_no= serializers.CharField(default="NA")
    class Meta:
        model = CollectionFromGrower
        fields = '__all__'
    def get_vehicle_number_name(self, obj):
        return obj.vehicle_number.vehicle_number if obj.vehicle_number else ''    