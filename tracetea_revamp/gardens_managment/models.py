
from django.db import models
# Create your models here.
import datetime
import sys
from unittest.util import _MAX_LENGTH
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.core.validators import RegexValidator
from django.utils.text import gettext_lazy as _
from django.db.models import Avg, Value
from django.db.models.functions import Coalesce
from django.dispatch import receiver
from django.contrib.auth import get_user_model
User = get_user_model()
from master.models import *
from user_profile.models import *



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
    


class LandType(models.Model):

    name = models.CharField(max_length=150, blank=True, null=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.name)

class Gardens(BaseAbstractStructure):
    # Gardens model for Grower
    grower = models.ForeignKey(GrowerProfile, on_delete=models.CASCADE, related_name="gardens_grower", null=True, blank=True)
    estate = models.ForeignKey(EstateProfile, on_delete=models.CASCADE, related_name="estate_gardens", null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="gardens_user", null=True, blank=True )
    land_type = models.ForeignKey(LandType, on_delete=models.CASCADE, related_name="gardens_landtype", null=True, blank=True)
    name = models.CharField(max_length=150, null=True, blank=True)
    production_area = models.CharField(max_length=150, null=True, blank=True )
    estate_total_area = models.CharField(max_length=150, null=True, blank=True )
    is_division = models.BooleanField(default=False)
    is_plot = models.BooleanField(default=True)
    import_id = models.IntegerField(blank=True, null=True)
    is_import = models.BooleanField(default=False)
    
    def __str__(self):
        return str(self.name)

    def save(self, *args, **kwargs):

        if self.is_division == True:
            self.is_plot = False
        elif self.is_division == False:
            self.is_plot = True

        super(Gardens, self).save(*args, **kwargs)



class EstateGardens(BaseAbstractStructure):
    # Estate Gardens model for Grower
    estate = models.ForeignKey(EstateProfile, on_delete=models.CASCADE, related_name="estates_gardens",)
    land_type = models.ForeignKey(LandType, on_delete=models.CASCADE, related_name="estate_gardens_landtype", null=True, blank=True)
    name = models.CharField(max_length=150, null=True, blank=True )
    production_area = models.CharField(max_length=150, null=True, blank=True )
    is_division = models.BooleanField(default=False)
    is_plot = models.BooleanField(default=True)

    def __str__(self):
        return str(self.name)
    
    def save(self, *args, **kwargs):
        if self.is_division == True:
            self.is_plot = False
        elif self.is_division == False:
            self.is_plot = True

        super(EstateGardens, self).save(*args, **kwargs)


class Plot(models.Model):
    garden = models.ForeignKey(Gardens, on_delete=models.CASCADE, related_name="garden_plot")
    name = models.CharField(max_length=150, null=True, blank=True )
    plot_area = models.CharField(max_length=150, null=True, blank=True )
    plot_status = models.BooleanField(default=True)
    # created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return str(self.name)
    
    def save(self, *args, **kwargs):
        from .models import Gardens

        gardern_details = Gardens.objects.filter(pk=self.garden_id).first()

        if gardern_details.is_division == True:
            self.plot_status = False
            self.is_delete = True
        elif gardern_details.is_plot == False:
            self.plot_status = True

        super(Plot, self).save(*args, **kwargs)



class Division(models.Model):
    garden = models.ForeignKey(Gardens, on_delete=models.CASCADE, related_name="garden_division")
    name = models.CharField(max_length=150, null=True, blank=True )

    def __str__(self):
        return str(self.name)

    # def total_section_area(self):
    #     """
    #     Calculate and return the total section area for this division.
    #     """
    #     sections = Section.objects.filter(division=self)
    #     if sections:
    #         total_area = sections.aggregate(models.Sum('section_area'))['section_area__sum'] or 0
    #         return total_area



class Section(models.Model):
    garden = models.ForeignKey(Gardens, on_delete=models.CASCADE, related_name="garden_section", null=True, blank=True)
    division = models.ForeignKey(Division, on_delete=models.CASCADE, related_name="garden_division_section")
    name = models.CharField(max_length=150, null=True, blank=True )
    section_area = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return str(self.name)

    # def get_total_area(self):
    #     """
    #     Get Stock Sold Quantity
    #     """
    #     area = UserProducts.objects.filter(product=self).aggregate(
    #             the_sum=Coalesce(Sum('product_quantity'), Value(0)))['the_sum']
    #     Opening_qty = self.total_quantity	
    #     total_quantity = Opening_qty - pre_quantity
    #     return total_quantity