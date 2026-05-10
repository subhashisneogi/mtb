from django.db import models
# Create your models here.
import sys

import datetime

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

from .validators import *
from vehicle_management.models import *
from chemical_data.models import *

from gardens_managment.models import *
# from gardens_managment.models import Gardens

# Create your models here.
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


class CollectionFromGrower(BaseAbstractStructure):
     
    """ Collection From Grower Model created by aggregator """   
    vehicle_option = (
        ('Yes', 'Yes'),
        ('No', 'No'),
    ) 
    record_option = (
        ('Yes', 'Yes'),
        ('No', 'No'),
    )
    
    grower= models.ForeignKey(GrowerProfile, related_name='available_grower_id', on_delete=models.DO_NOTHING, blank=True, null=True)
    date=models.DateField(auto_now_add= False, blank=True,null=True)
    vehicle_option=models.CharField(max_length=100, choices=vehicle_option, blank=True, null=True)
    vehicle_number=models.ForeignKey(VehicleManagement, related_name='available_vehicle_number',on_delete=models.DO_NOTHING, blank=True, null=True)  
    quantity = models.CharField(max_length=200,blank=True, null=True)
    keep_record=models.CharField(max_length=100, choices=record_option, blank=True, null=True)
    rate= models.CharField(max_length=200,blank=True, null=True)
    plot= models.ForeignKey(Plot, related_name='available_plot_id',on_delete=models.DO_NOTHING, blank=True, null=True)
    division = models.ForeignKey(Division, related_name='division_collection_from_grower', on_delete=models.DO_NOTHING, blank=True, null=True)
    latitude=models.DecimalField('latitude',max_digits=30,decimal_places=20, blank=True, null=True)
    longitude=models.DecimalField('longitude',max_digits=30,decimal_places=20, blank=True, null=True)
    receipt_no= models.CharField(max_length=300,blank=True, null=True, unique=True)
    is_complete=models.BooleanField(default=False)
    def __str__(self):
        return str(self.grower) 

class Labour(BaseAbstractStructure):
    """ Labour Model created by grower and aggregator(app), from app and BLF (Web) """
    type_option = (
        ('Permanent', 'Permanent'),
        ('Temporary', 'Temporary'),
    ) 
    gender_option = (
        ('Male', 'Male'),
        ('Female', 'Female'),
    ) 
    grower = models.ForeignKey(GrowerProfile, related_name="for_grower_labour", blank=True, null=True, on_delete=models.CASCADE)
    aggregator = models.ForeignKey(AggregatorProfile, related_name="aggregator_labour", blank=True, null=True, on_delete=models.CASCADE)
    blf = models.ForeignKey(BlfProfile, related_name="blf_labour", blank=True, null=True, on_delete=models.CASCADE)
    name = models.CharField(max_length=200,blank=True, null=True)
    type=models.CharField(max_length=100, choices=type_option, blank=True, null=True)   
    gender=models.CharField(max_length=100, choices=gender_option, blank=True, null=True)
    age = models.IntegerField(blank=True, null=True, validators=[MinValueValidator(0)])    
    def __str__(self):
        return str(self.name)
    
class PluckingData(BaseAbstractStructure):
    """ Plucking Data Model created by grower and aggregator """
    grower= models.ForeignKey(GrowerProfile, related_name='grower_id_pluckingdata', on_delete=models.CASCADE, blank=True, null=True)
    date=models.DateField(auto_now_add= False, blank=True,null=True)
    start_time=models.TimeField(auto_now_add= False, blank=True,null=True)
    end_time=models.TimeField(auto_now_add= False, blank=True,null=True) 
    labour= models.ForeignKey(Labour, related_name='labour_id', on_delete=models.CASCADE, blank=True, null=True)
    labours= models.ManyToManyField(Labour, related_name='labour_ids', blank=True, null=True)
    division = models.ForeignKey(Division, related_name='division_id', on_delete=models.CASCADE, blank=True, null=True)
    plot= models.ForeignKey(Plot, related_name='plot_id_pluckingdata',on_delete=models.CASCADE, blank=True, null=True)
    area_plucked=models.CharField(max_length=200, blank=True, null=True)
    quantity_plucked= models.CharField(max_length=200,blank=True, null=True)
    plucking_time =  models.CharField(max_length=200,blank=True, null=True)
    
    def __str__(self):
        return str(self.created_by)    

    def save(self, *args, **kwargs):
        if self.start_time and self.end_time:
            starttime = str(self.start_time)
            endtime = str(self.end_time)
            time1 = datetime.strptime(starttime,'%H:%M:%S')
            time2 = datetime.strptime(endtime,'%H:%M:%S')
            difference = time2-time1
            self.plucking_time = difference
        super(PluckingData, self).save(*args, **kwargs)
        
class CollectionFromAggregator(BaseAbstractStructure):
    
    """ Collection From Grower Model created by Aggregator
       
    """   
    vehicle_option = (
        ('Yes', 'Yes'),
        ('No', 'No'),
    ) 
    record_option = (
        ('Yes', 'Yes'),
        ('No', 'No'),
    )
    aggregator= models.ForeignKey(AggregatorProfile, related_name='available_aggregator_collection_id', on_delete=models.DO_NOTHING, blank=True, null=True)
    date=models.DateField(auto_now_add= False, blank=True,null=True)
    vehicle_option=models.CharField(max_length=100, choices=vehicle_option, blank=True, null=True)
    vehicle_number=models.ForeignKey(VehicleManagement, related_name='available_vehicle_number_aggregator',on_delete=models.DO_NOTHING, blank=True, null=True)  
    quantity = models.CharField(max_length=200,blank=True, null=True)
    keep_record=models.CharField(max_length=100, choices=record_option, blank=True, null=True)
    rate= models.CharField(max_length=200,blank=True, null=True)
    plot= models.ForeignKey(Plot, related_name='available_plot_id_aggregator',on_delete=models.DO_NOTHING, blank=True, null=True)
    division = models.ForeignKey(Division, related_name='division_collection_from_aggregator', on_delete=models.DO_NOTHING, blank=True, null=True)
    latitude=models.DecimalField('latitude',max_digits=30,decimal_places=20, blank=True, null=True)
    longitude=models.DecimalField('longitude',max_digits=30,decimal_places=20, blank=True, null=True)
    receipt_no= models.CharField(max_length=300,blank=True, null=True, unique=True)
    is_complete=models.BooleanField(default=False)

    def __str__(self):
        return str(self.aggregator)    

class SupplyManagement(BaseAbstractStructure):
    """ Supply to factory/aggregator from (aggregator or grower)model """
    vehicle_option = (
        ('Yes', 'Yes'),
        ('No', 'No'),
    )
    supply_option = (
        ('Factory', 'Factory'),
        ('Aggregator', 'Aggregator'),
    )
    supply_to=models.CharField(max_length=100, choices=supply_option, blank=True, null=True)
    consumer=models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name="consumer_supply_management", blank=True, null=True)
    vehicle_option=models.CharField(max_length=100, choices=vehicle_option, blank=True, null=True)
    date_of_supply=models.DateField(auto_now_add= False, blank=True,null=True)
    alloted_vehicle=models.ForeignKey(VehicleManagement, related_name='vehicle_number_alloted',on_delete=models.DO_NOTHING, blank=True, null=True)  
    gross_leaf = models.CharField(max_length=200,blank=True, null=True)
    supply_challan_id = models.CharField(max_length=300,blank=True, null=True, unique=True)
    ##for grower to factory supply fields
    quantity=models.CharField(max_length=200,blank=True, null=True) 
    supply_bag_id=models.CharField(max_length=200,blank=True,null=True)
    driver_name=models.CharField(max_length=200,blank=True, null=True)
    phone_regex = RegexValidator(regex=r'^\+?1?\d{6,12}$', message="Not a valid Mobile Number")
    mobile_number = models.CharField(validators=[phone_regex],max_length=17,blank=True, null=True)
    is_weighment_proceed = models.BooleanField(default=False)
    def __str__(self):
        return str(self.supply_challan_id)
    
class GrowerDetailsSupply(BaseAbstractStructure):
    """ Supply to Grower Supply Model  """   
    
    supply = models.ForeignKey(SupplyManagement, on_delete=models.CASCADE, related_name="supply_id", null=True, blank=True)
    grower= models.ForeignKey(GrowerProfile, related_name='collected_grower_id_supply', on_delete=models.DO_NOTHING, blank=True, null=True)
    collected_quantity = models.CharField(max_length=200,blank=True, null=True)
    collected_date= models.DateField(auto_now_add= False, blank=True,null=True)
    collected_time= models.TimeField(auto_now_add= False, blank=True,null=True)
    supply_quantity = models.CharField(max_length=200,blank=True, null=True)
    collected_quantity_vehicle= models.CharField(max_length=200,blank=True, null=True)#collected quantity during vehicle selection and automatic collected data are entered
        
    def __str__(self):
        return str(self.supply)
    