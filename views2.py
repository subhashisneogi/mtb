from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from rest_framework.exceptions import APIException


# -----------------------------
# VALIDATION SIGNAL
# -----------------------------
@receiver(pre_save, sender=WBSList)
def validate_unique_wbs(sender, instance, **kwargs):

    if not instance.organization_id or not instance.boq_id:
        return

    qs = WBSList.cmobjects.filter(
        organization_id=instance.organization_id,
        boq_id=instance.boq_id,
        wbs=instance.wbs
    )

    if instance.pk:
        qs = qs.exclude(pk=instance.pk)

    if qs.exists():
        raise APIException({
            "request_status": 0,
            "msg": "WBS must be unique per BOQ."
        })


# -----------------------------
# MAIN SIGNAL
# -----------------------------
@receiver(post_save, sender=WBSList)
def handle_wbs_chainage(sender, instance, created, **kwargs):

    if not instance.boq:
        return

    # -----------------------------
    # ROOT WBS (Create Chainage)
    # -----------------------------
    if created and instance.parent is None:

        BOQChainage.objects.get_or_create(
            organization=instance.organization,
            boq=instance.boq,
            wbs=instance,
            defaults={
                "name": f"CH-{instance.boq.id}-{instance.pk}",
                "start": 0,
                "end": 1
            }
        )

    # -----------------------------
    # CHILD WBS
    # -----------------------------
    if instance.parent and instance.root:

        parent_chainage = BOQChainage.cmobjects.filter(
            boq=instance.boq,
            wbs=instance.root
        ).first()

        if not parent_chainage:
            return

        # --------------------------------
        # CREATE CODE VALUE (Only CREATE)
        # --------------------------------
        if created:

            auto_value = generate_chainage_code(instance)

            BOQChainageExecutiveSummeryData.objects.get_or_create(
                organization=instance.organization,
                boq=instance.boq,
                wbs=instance,
                type="C",
                defaults={
                    "value": auto_value,
                    "form": parent_chainage
                }
            )

        # --------------------------------
        # QUANTITY VALUE (CREATE + UPDATE)
        # --------------------------------
        if instance.budgeted_quantity:

            qty_obj, created_q = BOQChainageExecutiveSummeryData.objects.get_or_create(
                organization=instance.organization,
                boq=instance.boq,
                wbs=instance,
                type="Q",
                defaults={
                    "value": instance.budgeted_quantity,
                    "form": parent_chainage
                }
            )

            # update value if already exists
            if not created_q:
                qty_obj.value = instance.budgeted_quantity
                qty_obj.save(update_fields=["value"])
