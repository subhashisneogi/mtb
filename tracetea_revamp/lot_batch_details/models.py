from django.db import models
from time import timezone
from datetime import datetime
from django.contrib.auth import get_user_model
User = get_user_model()
from tea_production.models import *
from user_profile.models import *
from django.db.models.functions import Concat
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



class LotBatchDetails(BaseAbstractStructure):
    lot_batch_no = models.CharField(max_length=200, unique=False)
    lot_batch_date = models.DateField(auto_now_add= False, blank=True,null=True)
    grade = models.ForeignKey(TeaGradeDetails, related_name='grade_lot', on_delete=models.DO_NOTHING, blank=True, null=True)
    bag_sl_no_from = models.IntegerField(max_length=150, blank=True, null=True, validators=[MinValueValidator(0)], unique=True)
    sl_no_to = models.IntegerField(max_length=150, blank=True, null=True, validators=[MinValueValidator(0)], unique=True)
    bag_sl_no_range = models.CharField(max_length=150, unique=False,  blank=True, null=True)
    bag_weight_kg = models.CharField(max_length=150, blank=True, null=True)
    mark = models.ForeignKey(BlfTeaProduction, on_delete=models.DO_NOTHING, related_name="lot_batch_mark", blank=True, null=True)
    
    def __str__(self):
        return str(self.lot_batch_no)  
    
    def save(self, *args, **kwargs):
        if self.bag_sl_no_from and self.sl_no_to:
            self.bag_sl_no_range = str(self.bag_sl_no_from) + "-" + str(self.sl_no_to)

            # BagSlNoRange.objects.update_or_create(pk=self.pk, defaults={'lot_batch_no_id': self.id, 'bag_sl_no_range': self.bag_sl_no_range})
        
        super(LotBatchDetails, self).save(*args, **kwargs)


class BagSlNoRange(models.Model):

    lot_batch_no = models.ForeignKey(LotBatchDetails, related_name="lot_batch_range", on_delete=models.DO_NOTHING, null=True, blank=True)
    bag_sl_no_range = models.CharField(max_length=150, unique=False,  blank=True, null=True)

    def __str__(self):
        return str(self.bag_sl_no_range)  
