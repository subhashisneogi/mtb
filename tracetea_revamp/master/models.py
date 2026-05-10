from django.db import models
from time import timezone
from datetime import datetime
from django.contrib.auth import get_user_model
User = get_user_model()
from django.core.exceptions import ValidationError
from tea_production.models import *
from django.utils import timezone
from ckeditor_uploader.fields import RichTextUploadingField

class CustomManager(models.Manager):
    def get_queryset(self):
        return super(__class__, self).get_queryset().filter(is_deleted=False)
    
class BaseAbstractStructure(models.Model):
    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.DO_NOTHING, blank=True, null=True, related_name='+')
    updated_by = models.ForeignKey(User, on_delete=models.DO_NOTHING, blank=True, null=True, related_name='+')

    objects = models.Manager()
    cmobjects = CustomManager()

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        # self.updated_at = datetime.datetime.now()
        super(__class__, self).save(*args, **kwargs)





class State(models.Model):
    """ States Model Trust Tea"""
    # region_name=models.ForeignKey('Region',related_name='region_name',on_delete=models.CASCADE)
    state_id=models.IntegerField(null=True,blank=True)
    name=models.CharField('name',max_length=100)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
    def __str__(self):
        return self.name

class District(models.Model):
        """ District Model Trust Tea"""
        state=models.ForeignKey('State',related_name='state_name_city',on_delete=models.CASCADE )
        district_id =models.IntegerField(null=True,blank=True)
        name= models.CharField('name',max_length=100)  
        created_at = models.DateTimeField(auto_now_add=True)
        updated_at = models.DateTimeField(auto_now=True)
        is_deleted = models.BooleanField(default=False)
        def __str__(self):
             return self.name
       
class Region(BaseAbstractStructure):
        """ Region Model PMS """
        region_id=models.IntegerField(null=True,blank=True)
        region_name= models.CharField('region_name',max_length=100) 
        abbrevation= models.CharField('abbrevation',max_length=100)  
        state= models.ManyToManyField(State, related_name='state_name_region',blank=True,null=True)
    #   district= models.ManyToManyField(District,related_name='district_name_region',blank=True,null=True)
        is_deleted = models.BooleanField(default=False)
        created_at = models.DateTimeField(auto_now_add=True)
        updated_at = models.DateTimeField(auto_now=True)
        created_by = models.ForeignKey(User, related_name='created_by_user_region', on_delete=models.CASCADE, blank=True, null=True)

        objects = models.Manager()
        cmobjects = CustomManager()

        def __str__(self):
              return self.region_name


        def save(self, *args, **kwargs):
            self.updated_at = datetime.now()
            super(__class__, self).save(*args, **kwargs)       

class AssociatedEntity(models.Model):
        """ Associated Entity Model Trust Tea"""
        region=models.ForeignKey('Region',related_name='entity_region',on_delete=models.CASCADE )
        name= models.CharField('name',max_length=100)  
        created_at = models.DateTimeField(auto_now_add=True)
        updated_at = models.DateTimeField(auto_now=True)
        is_deleted = models.BooleanField(default=False)
        created_by = models.ForeignKey(User, related_name='created_by_user_entity', on_delete=models.CASCADE, blank=True, null=True)

        def __str__(self):
             return self.name  

class AssociatedUnit(models.Model):
        """ Associated Unit Model Trust Tea"""
        name= models.CharField('name',max_length=100)  

        def __str__(self):
             return self.name

class WarehouseType(models.Model):
     
    """ Chemical Type Model Trace Tea @vivek"""   
    name=models.CharField(max_length=200,blank=True,null=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, related_name='created_by_user_warehouse_type', on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return self.name 
    

class WarehouseManagement(models.Model):
     
    """ Chemical Type Model Trace Tea @vivek"""   
    warehouse_type= models.ForeignKey(WarehouseType, related_name='warehouse_type_trusttea',on_delete=models.CASCADE, blank=True, null=True)
    name = models.CharField(max_length=200, blank=True,null=True)
    address=models.TextField(blank=True,null=True)

    is_deleted = models.BooleanField(default=False)                                                                                                                                                                                                                                 
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, related_name='created_by_user_warehouse_management', on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return self.name 


   
# Period Select Model
class PeriodSelected(models.Model):
    """
    Period selected by a user
    """
    user = models.OneToOneField(User, related_name="auth_user_period", on_delete=models.CASCADE)
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(default=timezone.now)

    def __str__(self):
        return str(self.user.username) + " [From " + str(self.start_date) + " To " + str(self.end_date) + "]"

    def clean(self):
        if self.start_date > self.end_date:
            raise ValidationError({
                'start_date': ["Start Date cannot be greater than End Date"],
                'end_date': ["End Date cannot be earlier than Start Date"]
            })
        


class PrivacyPolicy(models.Model):
    """
    Terms and Condition Model
    """
    sample = models.CharField(max_length=200)
    text = RichTextUploadingField(
        blank=True, null=True, config_name='special')

    class Meta:
        app_label = 'master'

    def __str__(self):
        return self.sample




class AndroidVersion(models.Model):
    """ Android Version Table """
    version_name = models.CharField(max_length=200)

    class Meta:
        app_label = 'master'

    def __str__(self):
        return self.version_name
    
class MimeTypes(BaseAbstractStructure):
    mime_type = models.CharField(max_length=200, null=True, blank=True)
    file_extension = models.CharField(max_length=200, null=True, blank=True)
    class Meta:
        db_table = "mime_type"