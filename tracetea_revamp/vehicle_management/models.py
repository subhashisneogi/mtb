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
from PIL import ImageDraw
from io import BytesIO
from django.core.files import File
import random
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db.models import Q
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
class VehicleManagement(BaseAbstractStructure): 
    """ Vehicle Management @Vivek """   
    vehicle_option = (
        ('owned', 'owned'),
        ('hired', 'hired'),
    ) 
    vehicle_type=models.CharField(max_length=100, choices=vehicle_option, blank=True, null=True)
    vehicle_number=models.CharField(max_length=200,blank=True,null=True)
    phone_regex = RegexValidator(regex=r'^\+?1?\d{6,10}$', message="Not a valid Mobile Number")
    mobile_number = models.CharField(validators=[phone_regex],max_length=17,blank=True, null=True)
    is_available=models.BooleanField(default=True) # If False then vehicle booked, If true vehicle available
    def __str__(self):
        return str(self.vehicle_number)     
    def clean(self):
        if not self.is_deleted and self.vehicle_number:
            exists = VehicleManagement.objects.filter(
                vehicle_number=self.vehicle_number,
                is_deleted=False
            ).exclude(pk=self.pk).exists()
            if exists:
                raise ValidationError('Vehicle number already exists.')
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    