from django.db.models import Max, IntegerField, Value
from django.db.models.functions import Cast
from django.db.models import Func

class SubstringIndex(Func):
    function = "SUBSTRING_INDEX"
    arity = 3

def generate_chainage_code(instance):
    """
    Generate hierarchical chainage code
    """
    BASE_CODE = "CG-01-CP"
    if not instance.parent:
        return BASE_CODE
    parent_exec = BOQChainageExecutiveSummeryData.cmobjects.filter(wbs=instance.parent,boq=instance.boq,type="C").values("value").first()
    parent_code = parent_exec["value"] if parent_exec else BASE_CODE
    prefix = f"{parent_code}-"
    max_seq = BOQChainageExecutiveSummeryData.cmobjects.filter(boq=instance.boq,type="C",value__startswith=prefix ).annotate(
        seq=Cast(
            SubstringIndex("value", Value("-"), Value(-1)),
            IntegerField()
        )
    ).aggregate(max_seq=Max("seq"))["max_seq"]
    next_number = (max_seq or 0) + 1
    return f"{prefix}{str(next_number).zfill(2)}"

@receiver(pre_save, sender=WBSList)
def wbs_validate_unique(sender, instance, **kwargs):
    if instance.parent and instance.parent.boq_id != instance.boq_id:
        raise APIException({
            "request_status": 0,
            "msg": "Parent WBS must belong to the same BOQ as the current WBS."
        })
    if not instance.organization_id or not instance.boq_id or not instance.boq_code:
        return
    root_id = instance.root_id or (instance.root.pk if instance.root else None)
    if not root_id:
        return
    qs = WBSList.cmobjects.filter(
        organization_id=instance.organization_id,
        boq_id=instance.boq_id,
        root_id=root_id,
        boq_code=instance.boq_code
    )
    if instance.pk:
        qs = qs.exclude(pk=instance.pk)
    if qs.exists():
        raise APIException({"request_status": 0,"msg": f"WBS: BOQ Code {instance.boq_code} must be unique per BOQ"})

@receiver(post_save, sender=WBSList)
def handle_wbs_chainage(sender, instance, created, **kwargs):
    change_lmpi_data(instance.id, instance.budgeted_quantity)
    if not instance.boq:
        return
    if created and instance.parent is None:
        BOQChainage.objects.get_or_create(organization=instance.organization,boq=instance.boq,wbs=instance,
            defaults={
                "name": f"CH-{instance.boq.id}-{instance.pk}",
                "start": 0,
                "end": 1
            }
        )
    if instance.parent and instance.root:
        parent_chainage = BOQChainage.cmobjects.filter(
            boq=instance.boq,
            wbs=instance.root
        ).first()
        if not parent_chainage:
            return
        if created:
            auto_value = generate_chainage_code(instance)
            BOQChainageExecutiveSummeryData.objects.get_or_create(organization=instance.organization,boq=instance.boq,wbs=instance,type="C",
                defaults={
                    "value": auto_value,
                    "form": parent_chainage
                }
            )
        if instance.budgeted_quantity > 0:
            qty_obj, created_q = BOQChainageExecutiveSummeryData.objects.get_or_create(organization=instance.organization,boq=instance.boq,wbs=instance,
                type="Q",
                defaults={
                    "value": instance.budgeted_quantity,
                    "form": parent_chainage
                }
            )
            if not created_q:
                if qty_obj.value != str(instance.budgeted_quantity):
                    qty_obj.value = instance.budgeted_quantity
                    qty_obj.save(update_fields=["value"])
