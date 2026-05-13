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
from weighment_supply.models import WeighmentSupply
from leaf_receipt.models import LeafManagement, LeafCollection
from user_profile.blf_api_models import SupplierExit

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
                        search = {relation.field.name: instance.id}
                        if any(field.name == 'is_deleted' for field in relation.related_model._meta.fields):
                            search['is_deleted'] = False
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


def _next_weighment_txn_id():
    last_txn = (
        WeighmentSupply.objects
        .select_for_update()
        .filter(weighment_txn_id__startswith="TXN")
        .order_by("-id")
        .first()
    )
    if not last_txn or not last_txn.weighment_txn_id:
        next_number = 1
    else:
        try:
            next_number = int(last_txn.weighment_txn_id.replace("TXN", "")) + 1
        except ValueError:
            next_number = last_txn.id + 1
    txn_id = f"TXN{next_number:09d}"
    while WeighmentSupply.objects.filter(weighment_txn_id=txn_id).exists():
        next_number += 1
        txn_id = f"TXN{next_number:09d}"
    return txn_id


@receiver(post_save, sender=WeighmentSupply)
def generate_weighment_txn_id(sender, instance, created, **kwargs):
    if not created or instance.weighment_txn_id:
        return
    with transaction.atomic():
        txn_id = _next_weighment_txn_id()
        WeighmentSupply.objects.filter(pk=instance.pk).update(weighment_txn_id=txn_id)
        instance.weighment_txn_id = txn_id


@receiver(post_save, sender=WeighmentSupply)
def mark_supply_challan_weighment_proceeded(sender, instance, created, **kwargs):
    if created and instance.supply_challan_id:
        SupplyManagement.objects.filter(pk=instance.supply_challan_id).update(is_weighment_proceed=True)


@receiver(post_save, sender=LeafManagement)
def mark_weighment_leaf_processed(sender, instance, created, **kwargs):
    if created and instance.weighment_txn_id:
        WeighmentSupply.objects.filter(pk=instance.weighment_txn_id).update(is_processed=True)


@receiver(post_save, sender=SupplierExit)
def mark_weighment_supplier_exit_proceeded(sender, instance, created, **kwargs):
    if created and instance.weighment_txn_id:
        WeighmentSupply.objects.filter(pk=instance.weighment_txn_id).update(is_supplier_exit_proceed=True)


def _supplier_profile_for_weighment(weighment):
    if str(weighment.supplier_type).lower() == "aggregator":
        return AggregatorProfile.cmobjects.filter(user_id=weighment.supplier_id).first()
    if str(weighment.supplier_type).lower() == "grower":
        return GrowerProfile.cmobjects.filter(user_id=weighment.supplier_id).first()
    return None


def _create_leaf_collection_for_challan_process(weighment, leaf_receipt, supplier_exit, request_user):
    supplier_profile = _supplier_profile_for_weighment(weighment)
    if not supplier_profile:
        return None
    collection_kwargs = {
        "leaf_receipt_id": leaf_receipt,
        "suppler_exit_id": supplier_exit,
        "weighment_supply_id": weighment,
        "supply_id": weighment.supply_challan,
        "supplier_id": weighment.supplier_id,
        "nt_wght": supplier_exit.net_supplied_qty,
        "collection_date": weighment.supply_challan.date_of_supply if weighment.supply_challan else weighment.supply_date,
        "supplier_type": weighment.supplier_type,
        "supply_date": weighment.supply_challan.date_of_supply if weighment.supply_challan else weighment.supply_date,
        "created_by_id": request_user.id,
    }
    if str(weighment.supplier_type).lower() == "aggregator":
        collection_kwargs["aggregator_id"] = supplier_profile.id
    elif str(weighment.supplier_type).lower() == "grower":
        collection_kwargs["grower_id"] = supplier_profile.id
        plucking_details = PluckingData.cmobjects.filter(grower_id=supplier_profile.id).first()
        if plucking_details:
            collection_kwargs["plucking_data_id"] = plucking_details.id
    return LeafCollection.objects.create(**collection_kwargs)


def create_challan_process_records(data, request_user):
    supplier_id = data.get("supplier")
    if not supplier_id:
        raise APIException({"request_status": 0, "msg": "supplier is required"})
    supplier = User.objects.filter(pk=supplier_id).first()
    if not supplier:
        raise APIException({"request_status": 0, "msg": "Supplier does not exist"})

    total_gross_weight = float(data.get("total_gross_weight_kg") or 0)
    unloaded_vehicle_weight = float(data.get("unloaded_vehicle_weight") or 0)
    deduction = float(data.get("deduction") or 0)
    if unloaded_vehicle_weight > total_gross_weight:
        raise APIException({
            "request_status": 0,
            "msg": "unloaded vehicle weight not be more than total gross during weighment supply",
        })

    with transaction.atomic():
        txn_id = _next_weighment_txn_id()
        weighment_serializer = WeighmentSupplySerializer(data={
            "supplier": supplier_id,
            "supplier_type": data.get("supplier_type"),
            "supply_date": data.get("supply_date"),
            "total_gross_weight_kg": data.get("total_gross_weight_kg"),
            "tare_weight_kg": data.get("tare_weight_kg"),
            "mobile_number": data.get("mobile_number"),
            "mode_of_supply": data.get("mode_of_supply") or "Motorised 3 / 4 wheelers vehicle",
            "vehicle_no": data.get("vehicle_no") or data.get("vehicle_no_id") or None,
            "supply_challan": data.get("supply_challan") or data.get("challan_id") or None,
            "weighment_txn_id": txn_id,
        })
        weighment_serializer.is_valid(raise_exception=True)
        weighment = weighment_serializer.save(created_by=request_user)

        leaf_serializer = LeafReceiptSerializer(data={
            "weighment_txn": weighment.pk,
            "supply_date": data.get("supply_date"),
            "deduction": data.get("deduction"),
            "final_leaf_count": data.get("final_leaf_count"),
            "net_leaf_weight": data.get("net_leaf_weight"),
            "rate": data.get("rate"),
            "quality_standard": data.get("quality_standard"),
            "acknowledge_status": data.get("acknowledge_status"),
            "payment_record_option": data.get("payment_record_option") or data.get("keep_payment_record"),
        })
        leaf_serializer.is_valid(raise_exception=True)
        leaf_receipt = leaf_serializer.save(created_by=request_user)

        supplier_exit_serializer = SupplierExitSerializer(data={
            "weighment_txn": weighment.pk,
            "unloaded_vehicle_weight": data.get("unloaded_vehicle_weight"),
            "date_of_supply": data.get("supply_date"),
            "is_released": data.get("is_released"),
        })
        supplier_exit_serializer.is_valid(raise_exception=True)
        supplier_exit = supplier_exit_serializer.save(created_by=request_user)
        net_leaf_weight = total_gross_weight - unloaded_vehicle_weight
        moisture_deduction = net_leaf_weight * (deduction / 100)
        supplier_exit.net_supplied_qty = round(net_leaf_weight - moisture_deduction, 2)
        supplier_exit.save(update_fields=["net_supplied_qty", "updated_at"])
        is_leaf_rejected = str(leaf_receipt.acknowledge_status).lower() == "rejected"
        WeighmentSupply.objects.filter(pk=weighment.pk).update(
            is_processed=True,
            is_supplier_exit_proceed=True,
            is_leaf_rejected=is_leaf_rejected,
        )

        if weighment.vehicle_no and str(supplier_exit.is_released).lower() == "yes":
            VehicleManagement.objects.filter(pk=weighment.vehicle_no_id).update(is_available=True)
            CollectionFromGrower.objects.filter(vehicle_number=weighment.vehicle_no).update(is_complete=True)

        leaf_collection = _create_leaf_collection_for_challan_process(
            weighment=weighment,
            leaf_receipt=leaf_receipt,
            supplier_exit=supplier_exit,
            request_user=request_user,
        )
        weighment.is_processed = True
        weighment.is_supplier_exit_proceed = True
        weighment.is_leaf_rejected = is_leaf_rejected

    return {
        "weighment": weighment,
        "leaf_receipt": leaf_receipt,
        "supplier_exit": supplier_exit,
        "leaf_collection": leaf_collection,
    }


def _recalculate_supplier_exit(weighment, leaf_receipt, supplier_exit):
    total_gross_weight = float(weighment.total_gross_weight_kg or 0)
    unloaded_vehicle_weight = float(supplier_exit.unloaded_vehicle_weight or 0)
    deduction = float(leaf_receipt.deduction or 0)
    if unloaded_vehicle_weight > total_gross_weight:
        raise APIException({
            "request_status": 0,
            "msg": "unloaded vehicle weight not be more than total gross during weighment supply",
        })
    net_leaf_weight = total_gross_weight - unloaded_vehicle_weight
    moisture_deduction = net_leaf_weight * (deduction / 100)
    supplier_exit.net_supplied_qty = round(net_leaf_weight - moisture_deduction, 2)


def update_challan_process_records(weighment_id, data, request_user):
    weighment = WeighmentSupply.cmobjects.filter(pk=weighment_id).first()
    if not weighment:
        raise APIException({"request_status": 0, "msg": "Challan process record not found"})

    leaf_receipt = LeafManagement.cmobjects.filter(weighment_txn=weighment).order_by("-id").first()
    supplier_exit = SupplierExit.cmobjects.filter(weighment_txn=weighment).order_by("-id").first()
    if not leaf_receipt or not supplier_exit:
        raise APIException({"request_status": 0, "msg": "Linked leaf receipt or supplier exit record not found"})

    with transaction.atomic():
        weighment_data = {}
        for field in [
            "supplier_type", "supplier", "supply_date", "total_gross_weight_kg",
            "tare_weight_kg", "mobile_number", "mode_of_supply",
        ]:
            if field in data:
                weighment_data[field] = data.get(field)
        if "vehicle_no" in data or "vehicle_no_id" in data:
            weighment_data["vehicle_no"] = data.get("vehicle_no") or data.get("vehicle_no_id")
        if "supply_challan" in data or "challan_id" in data:
            weighment_data["supply_challan"] = data.get("supply_challan") or data.get("challan_id")
        if weighment_data:
            weighment_serializer = WeighmentSupplySerializer(weighment, data=weighment_data, partial=True)
            weighment_serializer.is_valid(raise_exception=True)
            weighment = weighment_serializer.save(updated_by=request_user)

        leaf_data = {}
        for field in [
            "supply_date", "deduction", "final_leaf_count", "net_leaf_weight",
            "rate", "quality_standard", "acknowledge_status", "payment_record_option",
        ]:
            if field in data:
                leaf_data[field] = data.get(field)
        if "keep_payment_record" in data:
            leaf_data["payment_record_option"] = data.get("keep_payment_record")
        if leaf_data:
            leaf_serializer = LeafReceiptSerializer(leaf_receipt, data=leaf_data, partial=True)
            leaf_serializer.is_valid(raise_exception=True)
            leaf_receipt = leaf_serializer.save()

        supplier_exit_data = {}
        if "unloaded_vehicle_weight" in data:
            supplier_exit_data["unloaded_vehicle_weight"] = data.get("unloaded_vehicle_weight")
        if "is_released" in data:
            supplier_exit_data["is_released"] = data.get("is_released")
        if "supply_date" in data:
            supplier_exit_data["date_of_supply"] = data.get("supply_date")
        if supplier_exit_data:
            supplier_exit_serializer = SupplierExitSerializer(supplier_exit, data=supplier_exit_data, partial=True)
            supplier_exit_serializer.is_valid(raise_exception=True)
            supplier_exit = supplier_exit_serializer.save(updated_by=request_user)
        _recalculate_supplier_exit(weighment, leaf_receipt, supplier_exit)
        supplier_exit.save(update_fields=[
            "unloaded_vehicle_weight", "is_released", "date_of_supply",
            "net_supplied_qty", "updated_by", "updated_at",
        ])

        WeighmentSupply.objects.filter(pk=weighment.pk).update(
            is_processed=True,
            is_supplier_exit_proceed=True,
            is_leaf_rejected=str(leaf_receipt.acknowledge_status).lower() == "rejected",
        )
        if weighment.vehicle_no and str(supplier_exit.is_released).lower() == "yes":
            VehicleManagement.objects.filter(pk=weighment.vehicle_no_id).update(is_available=True)
            CollectionFromGrower.objects.filter(vehicle_number=weighment.vehicle_no).update(is_complete=True)

        LeafCollection.objects.filter(weighment_supply_id=weighment).delete()
        leaf_collection = _create_leaf_collection_for_challan_process(
            weighment=weighment,
            leaf_receipt=leaf_receipt,
            supplier_exit=supplier_exit,
            request_user=request_user,
        )
        weighment.refresh_from_db()

    return {
        "weighment": weighment,
        "leaf_receipt": leaf_receipt,
        "supplier_exit": supplier_exit,
        "leaf_collection": leaf_collection,
    }


def delete_challan_process_records(weighment_id, request_user):
    weighment = WeighmentSupply.cmobjects.filter(pk=weighment_id).first()
    if not weighment:
        raise APIException({"request_status": 0, "msg": "Challan process record not found"})
    with transaction.atomic():
        LeafCollection.objects.filter(weighment_supply_id=weighment).delete()
        LeafManagement.cmobjects.filter(weighment_txn=weighment).update(is_deleted=True)
        SupplierExit.cmobjects.filter(weighment_txn=weighment).update(is_deleted=True, updated_by=request_user)
        weighment.is_deleted = True
        weighment.updated_by = request_user
        weighment.save()
    return weighment

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
