def generate_chainage_code(instance):
    """
    Generate hierarchical chainage code for BOQChainageExecutiveSummeryData
    """

    BASE_CODE = "CG-01-CP"

    # If no parent → base level
    if not instance.parent:
        return BASE_CODE

    # If has parent → get parent executive code
    parent_exec = BOQChainageExecutiveSummeryData.objects.filter(
        wbs=instance.parent,
        type="C"
    ).first()

    if parent_exec:
        parent_code = parent_exec.value
    else:
        parent_code = BASE_CODE

    # Find existing children count
    existing_children = BOQChainageExecutiveSummeryData.objects.filter(
        wbs__parent=instance.parent,
        type="C"
    ).count()

    next_number = str(existing_children + 1).zfill(2)

    return f"{parent_code}-{next_number}"


from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import WBSList, BOQChainage, BOQChainageExecutiveSummeryData
from .utils import generate_chainage_code


@receiver(post_save, sender=WBSList)
def signal_update_wbs_list(sender, instance, created, **kwargs):

    if not created:
        return

    print("Signal triggered for WBSList")

    if not instance.boq:
        return

    # CASE 1 → If Parent is NULL → Create BOQChainage
    if instance.parent is None:

        BOQChainage.objects.get_or_create(
            boq=instance.boq,
            wbs=instance,
            defaults={
                "organization": instance.organization,
                "planning_tender": instance.planning_tender,
                "name": "STEP-1",
                "start": 0,
                "end": 0,
            }
        )

    # CASE 2 → If Parent Exists → Create Executive Summary Data
    else:

        auto_value = generate_chainage_code(instance)

        BOQChainageExecutiveSummeryData.objects.get_or_create(
            boq=instance.boq,
            wbs=instance,
            form=None,
            defaults={
                "organization": instance.organization,
                "planning_tender": instance.planning_tender,
                "type": "C",
                "value": auto_value,
            }
        )




