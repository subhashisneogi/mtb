from django.db import models
from time import timezone
from datetime import datetime
from django.contrib.auth import get_user_model
User = get_user_model()
from user_profile.models import *
from invoicing.models import *
from django.db.models import Max, Value
from django.db.models.functions import Coalesce
from django.db.models import CharField


class CustomManager(models.Manager):
    def get_queryset(self):
        return super(__class__, self).get_queryset().filter(is_deleted=False)
    

class BaseAbstractStructure(models.Model):
    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.DO_NOTHING, blank=True, null=True, related_name='+')
    updated_by = models.ForeignKey(User, on_delete=models.DO_NOTHING, blank=True, null=True, related_name='+')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = models.Manager()
    cmobjects = CustomManager()

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.updated_at = datetime.now()
        super(__class__, self).save(*args, **kwargs)


class Packaging(BaseAbstractStructure):
    dispatch_option=(
        ('Direct Sale', 'Direct Sale'),
        ('Forward Contract', 'Forward Contract'),
        ('Auction', ' Auction'),
    )
    invoice_no = models.ForeignKey(Invoice, related_name="lot_batch_range", on_delete=models.CASCADE)
    type_of_dispatch = models.CharField(max_length=150, choices=dispatch_option, null=True, blank=True)
    consignee = models.CharField(max_length=150, null=True, blank=True)
    warehouse = models.ForeignKey(WarehouseManagement, related_name="packaging_warehouse", on_delete=models.DO_NOTHING, null=True, blank=True)
    is_auction = models.BooleanField(default=False)

    def __str__(self):
        return str(self.invoice_no)
    
    def save(self, *args, **kwargs):
        if self.type_of_dispatch == "Auction":
            self.is_auction = True
        else:
            self.is_auction = False

        super(Packaging, self).save(*args, **kwargs)
    

    

