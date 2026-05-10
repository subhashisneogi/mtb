from django.db import models
from time import timezone
from datetime import datetime
from django.contrib.auth import get_user_model
User = get_user_model()

from lot_batch_details.models import *


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


class Invoice(BaseAbstractStructure):
    invoice_no = models.CharField(max_length=200, unique=True)
    invoice_date = models.DateField(auto_now_add= False, blank=True,null=True)
    is_packaged = models.BooleanField(default=False)
    
    def __str__(self):
        return str(self.invoice_no)
    
class BatchList(models.Model):
    invoice_no = models.ForeignKey(Invoice, related_name="batchlist_invoice_no", on_delete=models.CASCADE, blank=True, null=True)
    lot_batch = models.ForeignKey(LotBatchDetails, related_name="batchlist_lot_no", on_delete=models.CASCADE, blank=True, null=True, unique=False)
    bag_no_range = models.CharField(max_length=150, blank=True, null=True, unique=False )
        
    def __str__(self):
        return str(self.lot_batch)
    

    
    