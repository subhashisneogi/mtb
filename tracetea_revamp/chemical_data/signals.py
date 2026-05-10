
from django.db.models.signals import pre_save
from django.dispatch import receiver
from rest_framework.exceptions import APIException
from .models import UseOfChemical
from django.core.exceptions import ValidationError

@receiver(pre_save, sender=UseOfChemical)
def chemical_data_validation(sender, instance, **kwargs):
    if all([instance.created_by, instance.date, instance.chemical, instance.labour, instance.plot]):
        qs = UseOfChemical.cmobjects.filter(
            date=instance.date,
            chemical=instance.chemical,
            labour=instance.labour,
            plot=instance.plot,
            created_by=instance.created_by,
        )
        if instance.pk:
            qs = qs.exclude(pk=instance.pk)
        if qs.exists():
            raise APIException("This chemical has already been recorded for the selected Date, Labour, and Plot")

