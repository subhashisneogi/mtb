from django.db import models
# Create your models here.
import sys
from unittest.util import _MAX_LENGTH
from PIL import Image
import os
from io import BytesIO

from django.core.validators import URLValidator, RegexValidator
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.core.validators import RegexValidator
from django.utils.text import gettext_lazy as _
from django.utils.text import slugify
from django.dispatch import receiver
from django.contrib.auth import get_user_model
User = get_user_model()
from ckeditor_uploader.fields import RichTextUploadingField

import qrcode
from PIL import ImageDraw
from io import BytesIO
from django.core.files import File
import random

from phonenumber_field.modelfields import PhoneNumberField

from django.core.validators import MaxValueValidator, MinValueValidator

from django.core.validators import MaxValueValidator, MinValueValidator
from master.models import *
from tea_production.models import *
from user_profile.models import *
from gardens_managment.models import Plot,Gardens
from .validators import *
from vehicle_management.models import *
from chemical_data.models import *
from weighment_supply.models import *
class CustomManager(models.Manager):
    def get_queryset(self):
        return super(__class__, self).get_queryset().filter(is_deleted=False)
    

class BaseAbstractStructure(models.Model):
    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.DO_NOTHING, blank=True, null=True, related_name='+')
    updated_by = models.ForeignKey(User, on_delete=models.DO_NOTHING, blank=True, null=True, related_name='+')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_verify = models.BooleanField(default=False)

    objects = models.Manager()
    cmobjects = CustomManager()

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.updated_at = datetime.now()
        super(__class__, self).save(*args, **kwargs)



class SupplierExit(BaseAbstractStructure):
    """ 
        Supplier exit Model,
        Created by BLF
    """
    released_option = (
        ('Yes', 'Yes'),
    ) 
    weighment_txn= models.ForeignKey(WeighmentSupply, related_name='available_weighment_id', on_delete=models.DO_NOTHING, blank=True, null=True)
    unloaded_vehicle_weight= models.FloatField(blank=True,  null=True, validators=[MinValueValidator(0)], help_text="Kg")
    date_of_supply = models.DateField(auto_now_add= False, blank=True,null=True)
    is_released=models.CharField(max_length=100, choices=released_option, blank=True, null=True)
    net_supplied_qty=models.FloatField(blank=True, null=True, validators=[MinValueValidator(0)], help_text="Kg") # Total net Leaf weight 


    def __str__(self):
        return str(self.weighment_txn) 
    
    