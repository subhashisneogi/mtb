from django.db.models.signals import post_save, pre_save, pre_delete
from django.db import transaction
from django.db.models import F,Func
from django.dispatch import receiver
from .models import *
from .serializers import *
from .helpers import *
import random
import time
from django.db.models import Max
from django.db.models.functions import Substr, Length, Cast
from django.db.models import Max, IntegerField, Sum, FloatField
from django.db.models.functions import Substr, Length, Cast
from django.db import transaction
from rest_framework.exceptions import APIException

@receiver(pre_save)
def delete_check(sender, instance, **kwargs):
    # print(sender._meta.app_label)
    # print(sender._meta.model_name)
    # print(sender._meta.object_name)
    if hasattr(sender, '_meta'):
        if not sender._meta.app_label in ['accounts']:
            if hasattr(instance, 'is_deleted') and instance.is_deleted:
                links = sender._meta.related_objects
                total_count = 0
                for relation in links:
                    if not relation.related_model._meta.object_name.startswith(sender._meta.object_name):
                        # print(relation.related_model._meta.object_name)
                        search = { relation.field.name: instance.id,'is_deleted': False}
                        total_count += relation.related_model.objects.filter(**search).count()
                if total_count > 0:
                    raise APIException({'request_status': 0, 'msg': 'This record is linked with other active records. Please unlink first.'})

@receiver(pre_save, sender=SupplyManagement)
def validate_quantity(sender, instance, **kwargs):
    tot_quantity_plucked = (
        PluckingData.cmobjects
        .filter(created_by=instance.created_by, quantity_plucked__isnull=False)
        .annotate(qty_float=Cast('quantity_plucked', FloatField())) 
        .aggregate(total_qty=Sum('qty_float'))                    
    )["total_qty"] or 0.0
    try:
        gross_leaf_value = float(instance.gross_leaf) if instance.gross_leaf else 0.0
    except ValueError:
        raise APIException({
            'request_status': 0,
            'msg': "Gross leaf must be a numeric value."
        })
    if tot_quantity_plucked and gross_leaf_value > tot_quantity_plucked:
        raise APIException({
            'request_status': 0,
            'msg': f"Quantity: Gross leaf should be less than {tot_quantity_plucked}."
        })
    if instance.alloted_vehicle:
        vehicle = VehicleManagement.cmobjects.filter(id=instance.alloted_vehicle.id).first()
        if not vehicle:
            raise APIException({'request_status': 0, 'msg': "Vehicle does not exist."})
        if not instance.pk and vehicle.is_available == False:
            raise APIException({'request_status': 0, 'msg': "Vehicle is already booked."})
        if instance.pk:
            existing = SupplyManagement.cmobjects.filter(pk=instance.pk).first()
            if existing and existing.alloted_vehicle == instance.alloted_vehicle:
                return
            if vehicle.is_available == False:
                raise APIException({'request_status': 0, 'msg': "Vehicle is already booked."})
            
# @receiver(post_save, sender=SupplyManagement)
# def generate_supply_challan_code(sender, instance, created, **kwargs):
#     agg_supplier = AggregatorProfile.cmobjects.filter(user_id=instance.created_by_id).first()
#     grower_supplier = GrowerProfile.cmobjects.filter(user_id=instance.created_by_id).first()
#     if agg_supplier and agg_supplier.region:
#         region_code = agg_supplier.region.region_id
#     elif grower_supplier and grower_supplier.region:
#         region_code = grower_supplier.region.region_id
#     else:
#         region_code = ""
#     user_code = instance.created_by.username.upper()
#     prefix = f"CH{region_code}{user_code}"
#     with transaction.atomic():
#         if created:
#             last_record = SupplyManagement.cmobjects.select_for_update().filter(supply_challan_id__startswith=prefix).order_by('-id').first()
#             if last_record and last_record.supply_challan_id:
#                 last_number = int(last_record.supply_challan_id.replace(prefix, ""))
#                 next_number = last_number + 1
#             else:
#                 next_number = 1
#             challan_id = f"{prefix}{str(next_number).zfill(2)}"
#             SupplyManagement.cmobjects.filter(id=instance.id).update(supply_challan_id=challan_id)
#             if instance.alloted_vehicle:
#                 VehicleManagement.objects.filter(id=instance.alloted_vehicle.id).update(is_available=False)
#         if instance.alloted_vehicle and VehicleManagement.cmobjects.filter(id=instance.alloted_vehicle.id,is_available=True).exists():
#             VehicleManagement.objects.filter(id=instance.alloted_vehicle.id).update(is_available=False)

@receiver(post_save, sender=SupplyManagement)
def generate_supply_challan_code(sender, instance, created, **kwargs):
    agg_supplier = AggregatorProfile.cmobjects.filter(user_id=instance.created_by_id).first()
    grower_supplier = GrowerProfile.cmobjects.filter(user_id=instance.created_by_id).first()
    if agg_supplier and agg_supplier.region:
        region_code = agg_supplier.region.region_id
    elif grower_supplier and grower_supplier.region:
        region_code = grower_supplier.region.region_id
    else:
        region_code = ""
    user_code = instance.created_by.username.upper()
    prefix = f"CH{region_code}{user_code}"
    if created:
        with transaction.atomic():
            last_record = (
                SupplyManagement.cmobjects
                .select_for_update()
                .filter(supply_challan_id__startswith=prefix)
                .order_by('-id')
                .first()
            )
            if last_record and last_record.supply_challan_id:
                last_number = int(last_record.supply_challan_id[len(prefix):])
                next_number = last_number + 1
            else:
                next_number = 1

            challan_id = f"{prefix}{str(next_number).zfill(2)}"

            # Ensure uniqueness at DB level
            SupplyManagement.cmobjects.filter(id=instance.id).update(supply_challan_id=challan_id)

            if instance.alloted_vehicle:
                VehicleManagement.objects.filter(id=instance.alloted_vehicle.id).update(is_available=False)

@receiver(post_save, sender=GrowerProfile)
def common_profile_details_update(sender, instance, **kwargs):
    Profile.objects.update_or_create(
        user=instance.user,
        defaults={
            'full_name': instance.name,
            'user_type': instance.profile_type,
            'phone_no': instance.mobile_number,
            'region': instance.region,
            'state': instance.state,
            'district': instance.district,
            'address': instance.address,
            'trustea_id': instance.tea_board_id,
        }
    )

@receiver(post_save, sender=AggregatorProfile)
def common_profile_details_update(sender, instance, **kwargs):
    Profile.objects.update_or_create(
        user=instance.user,
        defaults={
            'full_name': instance.name,
            'user_type': instance.profile_type,
            'phone_no': instance.mobile_number,
        }
    )

@receiver(post_save, sender=BlfProfile)
def common_profile_details_update(sender, instance, **kwargs):
    Profile.objects.update_or_create(
        user=instance.user,
        defaults={
            'full_name': instance.entity_unit,
            'user_type': instance.profile_type,
            'phone_no': instance.mobile_number,
            'region': instance.region,
            'state': instance.state,
            'district': instance.district,
        }
    )


