from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction

@receiver(post_save, sender=SupplyManagement)
def generate_supply_challan_code(sender, instance, created, **kwargs):
    if not created or instance.supply_challan_id:
        return

    # Get region
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

    with transaction.atomic():

        # 🔒 LOCK rows to prevent race condition
        last_record = (
            SupplyManagement.objects
            .select_for_update()
            .filter(supply_challan_id__startswith=prefix)
            .order_by('-id')
            .first()
        )

        if last_record and last_record.supply_challan_id:
            last_number = int(last_record.supply_challan_id.replace(prefix, ""))
            next_number = last_number + 1
        else:
            next_number = 1

        challan_id = f"{prefix}{str(next_number).zfill(2)}"

        # Update without triggering signal again
        SupplyManagement.objects.filter(id=instance.id).update(
            supply_challan_id=challan_id
        )
