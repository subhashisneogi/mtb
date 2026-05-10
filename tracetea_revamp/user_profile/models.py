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
from .validators import *
from django.contrib.auth.models import AbstractUser
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


# from django.contrib.auth.models import AbstractUser

# class User(BaseAbstractStructure):
#    created_by = models.ForeignKey(User, on_delete=models.DO_NOTHING, blank=True, null=True, related_name='+')

class ProfileType(models.Model):
    """ Trace Tea Profile Type Model @vivek"""    
    name=models.CharField(max_length=200, unique=True)
    slug = models.SlugField(
        max_length=255, unique=True, null=True, blank=True)
    def __str__(self):
             return self.name
    def save(self, *args, **kwargs):
        """
        Save Funtion to Slugify The Slug Field
        """
        self.slug = slugify(self.name)
        super(ProfileType, self).save(*args, **kwargs)

# PROFILE MODEL
class Profile(BaseAbstractStructure):
    """
    Profile Model
    """
    full_name = models.TextField(blank=True, null=True)
    user_type = models.ForeignKey(ProfileType,related_name='profile_type',on_delete=models.DO_NOTHING, blank=True, null=True)
    user = models.OneToOneField(User, related_name='profile', on_delete=models.CASCADE, blank=True, null=True)
    trustea_id = models.CharField(max_length=250, blank=True, null=True, unique=True)
    email = models.EmailField(max_length=250, blank=True, null=True)
    phone_regex = RegexValidator(regex=r'^\+?1?\d{6,10}$', message="Not a valid Mobile Number")
    phone_no = models.CharField(validators=[phone_regex], max_length=17, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    region=models.ForeignKey(Region,related_name='profile_region',on_delete=models.DO_NOTHING, blank=True, null=True)
    state=models.ForeignKey(State,related_name='profile_state',on_delete=models.DO_NOTHING, blank=True, null=True)
    district=models.ForeignKey(District,related_name='profile_district',on_delete=models.DO_NOTHING, blank=True, null=True)
    is_allow_otp_login = models.BooleanField(default=True)

    def __str__(self):
        return str(self.user)

class UserOTP(BaseAbstractStructure):
    user = models.ForeignKey(User, related_name='+', on_delete=models.CASCADE,blank=True, null=True)
    otp_secret = models.CharField(max_length=200)
    expiry = models.DateTimeField(blank=True,null=True)
    is_used = models.BooleanField(default=False)

#################   BLF PROFILE SECTION ###################
class BlfProfile(BaseAbstractStructure):
    """Trace Tea Blf Model @vivek"""
    EASY_WEIGHT_SYSTEM_OPTION = (
        ('Enable', 'Enable'),
        ('Disable', 'Disable'),
    ) 
    profile_type= models.ForeignKey(ProfileType, related_name='profile_type_blf',\
                                    on_delete=models.CASCADE, blank=True, null=True)    
    user = models.OneToOneField(User, related_name='profile_id_blf', \
                                  on_delete=models.CASCADE, blank=True, null=True)
    email= models.EmailField(max_length=70, unique=False, null=True, blank=True)
    tcms_unit_id = models.CharField(max_length=255, null=True, blank=True)
    tcmo_no = models.CharField(max_length=255,blank=True, null=True)
    entity_name = models.CharField(max_length=255, null=True, blank=True)
    entity_unit = models.CharField(max_length=255, null=True, blank=True)
    certificate_no=models.CharField(max_length=255,blank=True,null=True)
    region=models.ForeignKey(Region,related_name='profile_blf_region',on_delete=models.DO_NOTHING, blank=True, null=True)
    state=models.ForeignKey(State,related_name='profile_blf_state',on_delete=models.DO_NOTHING, blank=True, null=True)
    district=models.ForeignKey(District,related_name='profile_blf_district',on_delete=models.DO_NOTHING, blank=True, null=True)
    address=models.TextField(null=True, blank=True) 
    phone_regex = RegexValidator(regex=r'^\+?1?\d{6,10}$', message="Not a valid Mobile Number")
    mobile_number = models.CharField(validators=[phone_regex],max_length=17,blank=True, null=True) # validators should be a list

    # contact info
    ho_contact_person=models.CharField(max_length=255,blank=True,null=True)
    ho_contact_number=models.CharField(max_length=10,blank=True,null=True, validators=[phone_regex],)
    ho_contact_email= models.EmailField(max_length=255, unique=False, null=True, blank=True)
    garden_contact_person=models.CharField(max_length=300,blank=True,null=True)
    garden_contact_number=models.CharField(max_length=10,blank=True,null=True, validators=[phone_regex],)
    garden_contact_email= models.EmailField(max_length=255, unique=False,blank=True,null=True)
    manager_contact_person=models.CharField(max_length=300,blank=True,null=True)
    manager_contact_number=models.CharField(max_length=10,blank=True,null=True, validators=[phone_regex],)
    manager_contact_email= models.EmailField(unique=False, blank=True,null=True)
    trust_tea_officer_contact_person=models.CharField(max_length=300,blank=True,null=True)
    trust_tea_officer_contact_number=models.CharField(max_length=10,blank=True,null=True, validators=[phone_regex],)
    trust_tea_officer_contact_email= models.EmailField(max_length=255, unique=False, blank=True,null=True )
    data_operator_contact_person=models.CharField(max_length=255,blank=True,null=True)
    data_operator_contact_number=models.CharField(max_length=10,blank=True,null=True, validators=[phone_regex],)
    data_operator_contact_email= models.EmailField(max_length=255, unique=False,null=True,blank=True)

    easy_weight_system = models.CharField(max_length=100, choices=EASY_WEIGHT_SYSTEM_OPTION, null=True,blank=True )
    # factory info
    factory_details_likely_production=models.CharField(max_length=255, blank=True,null=True)

    factory_details_other_certificate=models.CharField(max_length=255,blank=True,null=True)
    ownership_details_managing_company=models.CharField(max_length=255,blank=True,null=True)
    ownership_details_name_of_tea_company=models.CharField(max_length=255,blank=True,null=True)
    ownership_details_email=models.CharField(max_length=255, unique=False, null=True,blank=True)
    voter_id=models.CharField(max_length=100, blank=True,null=True, unique=True) 
    aadhar_no=models.CharField(max_length=100,blank=True,null=True)
    user_file=models.FileField(
        upload_to='user_profile_estate/file',null=True,blank=True, help_text='file', validators=[validate_image_file_extension])
    is_active = models.BooleanField(default=True)
    otp= models.CharField(max_length = 9, blank = True, null= True)
    otp_created_at=models.DateTimeField(blank=True,null=True)
    is_tcms_user = models.BooleanField(default=False)

    def __str__(self):
        # return str(self.entity_unit) + " - " + "[" + str(self.user) + "]"
        return str(self.user)
    
    def save(self, *args, **kwargs):
        """ image file resize @Subhashis"""
        if self.user_file:
            temp_image = Image.open(self.user_file).convert('RGB')
            output_io_stream = BytesIO()
            temp_resized_image = temp_image.resize((200, 200))
            temp_resized_image.save(
                output_io_stream, format='JPEG', quality=60)
            output_io_stream.seek(0)
            self.user_file = InMemoryUploadedFile(output_io_stream,
                                                    'ImageField', "%s.jpg" % self.user_file.name.split('.')[0], 'image/jpeg', sys.getsizeof(output_io_stream), None)

        super(BlfProfile, self).save(*args, **kwargs)


    
class BlfTroughDetails(models.Model):

    LEAF_TYPE = (
        ('OWN LEAF', 'OWN LEAF'),
        ('BOUGHT LEAF', 'BOUGHT LEAF'),
    )   
    user_profile_blf =models.ForeignKey(BlfProfile, related_name='blf_trough_details',\
                                    on_delete=models.CASCADE, blank=True, null=True)
    capacity_qty=models.CharField(blank=True,null=True, max_length=200)
    size_width=models.CharField(blank=True,null=True,max_length=200)
    size_height=models.CharField(blank=True,null=True,max_length=200)
    name=models.CharField(max_length=200,blank=True,null=True)
    leaf_type=models.CharField(max_length=40, choices=LEAF_TYPE, blank=True,null=True)

    def __str__(self):
        return str(self.name)


class BlfTeaProduction(models.Model):     

    blf = models.ForeignKey(BlfProfile, related_name="tea_productions_blf", 
                    on_delete=models.CASCADE, blank=True, null=True)
    tea_type=models.ForeignKey(TeaType, related_name='tea_type_blf', on_delete=models.CASCADE, 
                blank=True, null=True )
    tea_grade=models.ForeignKey(TeaGradeDetails, related_name='tea_type_grade_productions_blf', 
                    on_delete=models.CASCADE, blank=True, null=True)
    marks= models.CharField(max_length=200, blank=True, null=True)
    quantity=models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return str(self.marks) 

class BlfFactoryDetailsMarks(models.Model):

    name = models.CharField(max_length=100, blank=True, null=True)
    blf = models.ForeignKey(BlfProfile, on_delete=models.CASCADE, related_name="blf_factory_details_marks", null=True, blank=True)
    
    def __str__(self):
        return str(self.name) 

class BlfFactoryMarks(models.Model):

    name = models.CharField(max_length=100, blank=True, null=True)
    blf = models.ForeignKey(BlfProfile, on_delete=models.CASCADE, related_name="blf_factorys_marks", null=True, blank=True)

    def __str__(self):
        return str(self.name)





#####################  Aggregators Profile Section ###########

class AggregatorType(BaseAbstractStructure):
     
    """ Aggregator Type Model Trace Tea @Vivek """   
    name=models.CharField(max_length=200,blank=True,null=True)

    def __str__(self):
        return str(self.name) 


class AggregatorProfile(BaseAbstractStructure):
    """Trace Tea User Profile Aggregator Model @vivek"""
    
    aggregator_option = (
        ('Lead Farmer', 'Lead Farmer'),
        ('Aggregator', 'Aggregator'),
        ('SHG', 'SHG'),
        ('Cooperative', 'Cooperative')
    ) 
    
    profile_type= models.ForeignKey(ProfileType, related_name='profile_type_aggregator',on_delete=models.CASCADE, blank=True, null=True)
    user = models.OneToOneField(User, related_name='profile_id_aggregator', on_delete=models.CASCADE)
    is_tcms_user = models.BooleanField(default=False)
    tcms_supplier_code = models.CharField(max_length=250, blank=True,null=True)
    username=models.CharField(max_length=200, blank=True,null=True)
    password=models.CharField(max_length=200, blank=True,null=True)
    name = models.CharField(max_length=200, blank=True,null=True)
    region=models.ForeignKey(Region,related_name='profile_aggregator_region',on_delete=models.DO_NOTHING, blank=True, null=True)
    state=models.ForeignKey(State,related_name='profile_aggregator_state',on_delete=models.DO_NOTHING, blank=True, null=True)
    district=models.ForeignKey(District,related_name='profile_aggregator_district',on_delete=models.DO_NOTHING, blank=True, null=True)
    email= models.EmailField(max_length=70, unique=False, null=True,blank=True)
    associated_entity=models.ManyToManyField(BlfProfile,related_name='profile_aggregator_entity', blank=True, null=True)
    associated_aggregator=models.ManyToManyField('self', related_name='profile_associated_agent', blank=True, null=True)
    phone_regex = RegexValidator(regex=r'^\+?1?\d{6,10}$', message="Not a valid Mobile Number")
    mobile_number = models.CharField(validators=[phone_regex],max_length=17,blank=True, null=True) # validators should be a list
    # aggregator_type=models.ForeignKey(AggregatorType, related_name='aggregator_type_aggregator',on_delete=models.CASCADE, blank=True, null=True)
    aggregator_type=models.CharField(max_length=100, choices=aggregator_option, blank=True, null=True)

   
    address=models.TextField(blank=True, null=True)
    gstin_no=models.CharField(max_length=100,blank=True,null=True)
    user_file=models.FileField(
        upload_to='user_profile_aggregator/image',null=True,blank=True, help_text='file',validators=[validate_image_file_extension])
    is_active = models.BooleanField(default=True)
    otp= models.CharField(max_length = 9, blank = True, null= True)
    voter_id=models.CharField(max_length=100, blank=True,null=True, unique=True) 
    aadhar_no=models.CharField(max_length=100,blank=True,null=True)
    otp_created_at=models.DateTimeField(blank=True,null=True)
    is_import_users =  models.BooleanField(default=False)

    def __str__(self):
        return str(self.name) + " - " + "[" +str(self.user) + "]"
    
    def save(self, *args, **kwargs):
        """ image file resize """
        if self.user_file:
            temp_image = Image.open(self.user_file).convert('RGB')
            output_io_stream = BytesIO()
            temp_resized_image = temp_image.resize((200, 200))
            temp_resized_image.save(
                output_io_stream, format='JPEG', quality=60)
            output_io_stream.seek(0)
            self.user_file = InMemoryUploadedFile(output_io_stream,
                                                    'ImageField', "%s.jpg" % self.user_file.name.split('.')[0], 'image/jpeg', sys.getsizeof(output_io_stream), None)

        super(AggregatorProfile, self).save(*args, **kwargs)
    
class GrowerType(BaseAbstractStructure):
     
    """ Grower Type Model Trace Tea @vivek""" 

    name=models.CharField(max_length=200,blank=True,null=True)
    def __str__(self):
        return self.name 

class GrowerProfile(BaseAbstractStructure):
    """Trace Tea User Profile Model @vivek"""
    GENDER_TYPE = (
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    )
    ID_PROOF_TYPE = (
        ('AADHAR CARD', 'AADHAR CARD'),
        ('VOTER ID', 'VOTER ID'),   
        ('TBOI CARD', 'TBOI CARD'),
        ('RC ID', 'RC ID'),   
        ('DL ID', 'DL'),   
        ('Other', 'Other'),
    )
    grower_option = (
        ('STG', 'STG'),
        ('LTG', 'LTG'),
        ('Member Of SHG', 'Member Of SHG'),
        ('Others', 'Others'),
        ('INDIVIDUAL', 'INDIVIDUAL'),
    ) 
    profile_type= models.ForeignKey(ProfileType, related_name='profile_type_grower',on_delete=models.CASCADE, blank=True, null=True)
    user = models.OneToOneField(User, related_name='profile_id_grower', on_delete=models.CASCADE,blank=True, null=True)
    is_tcms_user = models.BooleanField(default=False)
    tcms_supplier_code = models.CharField(max_length=250, blank=True,null=True)
    grower_type=models.CharField(max_length=100, choices=grower_option, blank=True, null=True)
    # username=models.CharField(max_length=200, blank=True,null=True)
    # password=models.CharField(max_length=200, blank=True,null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    age=models.IntegerField(blank=True,null=True)
    gender= models.CharField(max_length=15,choices=GENDER_TYPE, blank=True,null=True)
    date_of_birth=models.DateField(auto_now_add= False, blank=True,null=True)
    region=models.ForeignKey(Region,related_name='profile_grower_region',on_delete=models.DO_NOTHING, blank=True, null=True)
    state=models.ForeignKey(State,related_name='profile_grower_state',on_delete=models.DO_NOTHING, blank=True, null=True)
    district=models.ForeignKey(District,related_name='profile_grower_district',on_delete=models.DO_NOTHING, blank=True, null=True)
    email= models.EmailField(max_length=255, unique=False, null=True,blank=True)
    village_or_town=models.CharField(max_length=255, blank=True,null=True)
    address=models.TextField(blank=True,null=True)
    phone_regex = RegexValidator(regex=r'^\+?1?\d{6,10}$', message="Not a valid Mobile Number")
    mobile_number = models.CharField(validators=[phone_regex],max_length=17,blank=True, null=True) # validators should be a list
    associated_aggregator=models.ManyToManyField(AggregatorProfile, \
                                                 related_name='profile_associated_aggregator', blank=True, null=True)
    associated_entity=models.ManyToManyField(BlfProfile,related_name='grower_associated_entity', blank=True, null=True)
    certificate_no=models.CharField(max_length=200,blank=True,null=True)
    postoffice=models.CharField(max_length=200,blank=True,null=True)
    pincode=models.CharField(
        max_length=6,
        validators=[RegexValidator('^[0-9]{6}$', _('Invalid postal code'))],blank=True,null=True
    )
    voter_id=models.CharField(max_length=250, blank=True,null=True, unique=True) 
    aadhar_no=models.CharField(max_length=250,blank=True,null=True)
    driving_licence_no=models.CharField(max_length=250,blank=True,null=True)
    ration_card_no=models.CharField(max_length=250,blank=True,null=True)
    pan_no = models.CharField(max_length=250,blank=True,null=True)
    trustea_id=models.CharField(max_length=255,blank=True,null=True)#autogenerated
    existing_trust_tea_id=models.CharField(max_length=100,blank=True,null=True)
    associated_unit=models.ForeignKey(AssociatedUnit, related_name='profile_grower_asso_unit',on_delete=models.CASCADE, blank=True, null=True)
    # associated_grower=models.ForeignKey(AssociatedEntity,related_name='profile_associated_grower',on_delete=models.CASCADE, blank=True, null=True)
    father_name=models.CharField(max_length=300,blank=True,null=True)
    tea_board_id=models.CharField(max_length=100, blank=True,null=True)
    total_male_worker=models.IntegerField(blank=True,null=True)
    total_female_worker=models.IntegerField(blank=True,null=True)
    estimated_production_of_green_tea=models.CharField(max_length=150, blank=True,null=True)
    estimated_production_of_made_tea=models.CharField(max_length=150, blank=True,null=True)
    id_proof_type=models.CharField(max_length=50,choices=ID_PROOF_TYPE, blank=True,null=True)
    id_proof_file=models.FileField(
        upload_to='user_profile_grower/ID',null=True,blank=True, help_text='file')
    additional_information=models.TextField(null=True,blank=True)#In case of Type = LTG, this field is mandatory
    photo = models.FileField(
        upload_to='user_profile_grower/image',null=True,blank=True,help_text='file', validators=[validate_image_file_extension])
    is_active = models.BooleanField(default=True)
    garden_name = models.CharField(max_length=255, null=True, blank=True ) #fields added only for export template
    production_area = models.CharField(max_length=255, null=True, blank=True ) #fields added only for export template
    otp= models.CharField(max_length = 9, blank = True, null= True)  
    otp_created_at=models.DateTimeField(blank=True,null=True)
    poi_type = models.CharField(max_length=255, null=True, blank=True )
    poi_id = models.CharField(max_length=255, null=True, blank=True )

    def __str__(self):
        return str(self.user)
    
    def save(self, *args, **kwargs):
        import datetime
        if self.photo and not getattr(self.photo, "_committed", True):
            temp_image = Image.open(self.photo).convert('RGB')
            output_io_stream = BytesIO()
            temp_resized_image = temp_image.resize((200, 200))
            temp_resized_image.save(
                output_io_stream, format='JPEG', quality=60)
            output_io_stream.seek(0)
            self.photo = InMemoryUploadedFile(output_io_stream,
                                                    'ImageField', "%s.jpg" % self.photo.name.split('.')[0], 'image/jpeg', sys.getsizeof(output_io_stream), None)
        super(GrowerProfile, self).save(*args, **kwargs)
    
class ShgCooperativeType(BaseAbstractStructure):
     
    """ ShgCooperative Type Model Trace Tea @Vivek """   
    name=models.CharField(max_length=200,blank=True,null=True)

    def __str__(self):
        return str(self.name)
    
class ShgCooperativeProfile(BaseAbstractStructure):
    """Trace Tea User Profile Shg or cooperative Model @vivek"""

    profile_type= models.ForeignKey(ProfileType, related_name='profile_type_shg_cooperative',\
                                    on_delete=models.CASCADE, blank=True, null=True)
    email= models.EmailField(max_length=70, unique=False, null=True, blank=True)
    user= models.OneToOneField(User, related_name='profile_id_shg_cooperative', \
                                  on_delete=models.CASCADE)
    name = models.CharField(max_length=200,blank=True,null=True)
    phone_regex = RegexValidator(regex=r'^\+?1?\d{6,10}$', message="Not a valid Mobile Number")
    mobile_number = models.CharField(validators=[phone_regex],max_length=17,blank=True, null=True) # validators should be a list
    shg_cooperative_type=models.ForeignKey(ShgCooperativeType, related_name='shg_type',on_delete=models.CASCADE, blank=True, null=True)
    region=models.ForeignKey(Region,related_name='profile_shg_cooperative_region',on_delete=models.DO_NOTHING, blank=True, null=True)
    state=models.ForeignKey(State,related_name='profile_shg_cooperative_state',on_delete=models.DO_NOTHING, blank=True, null=True)
    district=models.ForeignKey(District,related_name='profile_shg_cooperative_district',on_delete=models.DO_NOTHING, blank=True, null=True)
    address=models.TextField(blank=True,null=True)    
    total_no_members=models.IntegerField(blank=True,null=True)
    no_of_associated_non_member=models.IntegerField(blank=True,null=True)
    govt_registration_no=models.CharField(max_length=100,blank=True,null=True)
    trustea_id=models.CharField(max_length=100,blank=True,null=True)#autogenerated
    user_file=models.FileField(
        upload_to='user_profile_shg_cooperative/file',null=True,blank=True, help_text='file',validators=[validate_image_file_extension])
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return str(self.user) + "-" +str(self.user.id)
    
    def save(self, *args, **kwargs):
        """ image file resize """
        if self.user_file:
            temp_image = Image.open(self.user_file).convert('RGB')
            output_io_stream = BytesIO()
            temp_resized_image = temp_image.resize((200, 200))
            temp_resized_image.save(
                output_io_stream, format='JPEG', quality=60)
            output_io_stream.seek(0)
            self.user_file = InMemoryUploadedFile(output_io_stream,
                                                    'ImageField', "%s.jpg" % self.user_file.name.split('.')[0], 'image/jpeg', sys.getsizeof(output_io_stream), None)

        super(ShgCooperativeProfile, self).save(*args, **kwargs)
    

class AdvisoryProfile(BaseAbstractStructure):
    """Trace Tea User Profile Advisory User Model @vivek"""

    profile_type= models.ForeignKey(ProfileType, related_name='profile_type_advisory_user',\
                                    on_delete=models.CASCADE, blank=True, null=True)
    user = models.OneToOneField(User, related_name='profile_id_advisory_user', \
                                  on_delete=models.CASCADE)
    name = models.CharField(max_length=200,blank=True,null=True)
    email= models.EmailField(max_length=70, unique=False, null=True,blank=True)

    phone_regex = RegexValidator(regex=r'^\+?1?\d{6,10}$', message="Not a valid Mobile Number")
    mobile_number = models.CharField(validators=[phone_regex],max_length=17,blank=True, null=True) # validators should be a list
    region=models.ForeignKey(Region,related_name='profile_advisory_user_region',on_delete=models.DO_NOTHING, blank=True, null=True)
    state=models.ForeignKey(State,related_name='profile_advisory_user_state',on_delete=models.DO_NOTHING, blank=True, null=True)
    district=models.ForeignKey(District,related_name='profile_advisory_user_district',on_delete=models.DO_NOTHING, blank=True, null=True)
    # address=models.TextField()     
    organization_name=models.CharField(max_length=300,null=True,blank=True)
    expert_name=models.CharField(max_length=300,null=True,blank=True)
    user_file=models.FileField(
        upload_to='user_profile_advisory_user/Image',null=True,blank=True,help_text='file',validators=[validate_image_file_extension])
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return str(self.user) + "-" +str(self.user.id)
    
    def save(self, *args, **kwargs):
        """ image file resize """
        if self.user_file:
            temp_image = Image.open(self.user_file).convert('RGB')
            output_io_stream = BytesIO()
            temp_resized_image = temp_image.resize((200, 200))
            temp_resized_image.save(
                output_io_stream, format='JPEG', quality=60)
            output_io_stream.seek(0)
            self.user_file = InMemoryUploadedFile(output_io_stream,
                                                    'ImageField', "%s.jpg" % self.user_file.name.split('.')[0], 'image/jpeg', sys.getsizeof(output_io_stream), None)

        super(AdvisoryProfile, self).save(*args, **kwargs)


class ConsigneeProfile(BaseAbstractStructure):
    """Trace Tea User Profile Consignee Model @vivek"""

    profile_type= models.ForeignKey(ProfileType, related_name='profile_type_consignee',\
                                    on_delete=models.CASCADE, blank=True, null=True)
    user = models.OneToOneField(User, related_name='profile_id_consignee', \
                                  on_delete=models.CASCADE)
    organization_name=models.CharField(max_length=300,null=True,blank=True)
    email= models.EmailField(max_length=70, unique=False, null=True,blank=True)
    phone_regex = RegexValidator(regex=r'^\+?1?\d{6,10}$', message="Not a valid Mobile Number")
    mobile_number = models.CharField(validators=[phone_regex],max_length=17,blank=True, null=True) # validators should be a list
    buyer_name=models.CharField(max_length=300,blank=True,null=True)
    region=models.ForeignKey(Region,related_name='profile_consignee_region',on_delete=models.DO_NOTHING, blank=True, null=True)  
    user_file=models.FileField(
        upload_to='user_profile_consignee/file',null=True,blank=True, help_text='file', validators=[validate_image_file_extension])
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return str(self.user) + "-" +str(self.user.id)
    
    def save(self, *args, **kwargs):
        """ image file resize """
        if self.user_file:
            temp_image = Image.open(self.user_file).convert('RGB')
            output_io_stream = BytesIO()
            temp_resized_image = temp_image.resize((200, 200))
            temp_resized_image.save(
                output_io_stream, format='JPEG', quality=60)
            output_io_stream.seek(0)
            self.user_file = InMemoryUploadedFile(output_io_stream,
                                                    'ImageField', "%s.jpg" % self.user_file.name.split('.')[0], 'image/jpeg', sys.getsizeof(output_io_stream), None)

        super(ConsigneeProfile, self).save(*args, **kwargs)
 

####################### ESTATE MODELS ###########################
class EstateProfile(BaseAbstractStructure):
    """Trace Tea User Profile Estate Model """

    TCMS_FETCH_OPTION = (
            ('YES', 'YES'),
            ('NO', 'NO'),  
        )
    
    EASY_WEIGHT_SYSTEM_OPTION = (
        ('Enable', 'Enable'),
        ('Disable', 'Disable'),
    ) 

    profile_type= models.ForeignKey(ProfileType, related_name='profile_type_estate',\
                                    on_delete=models.CASCADE, blank=True, null=True)    
    user = models.OneToOneField(User, related_name='profile_id_estate', \
                                  on_delete=models.CASCADE, blank=True, null=True)
    email= models.EmailField(max_length=70, unique=False, null=True, blank=True)
    # entity sec
    is_fetch_from_tcms = models.CharField(max_length=100, choices=TCMS_FETCH_OPTION, null=True, blank=True)
    api_entity_name = models.CharField(max_length=100, null=True, blank=True)
    api_entity_unit = models.CharField(max_length=100, null=True, blank=True)
    entity_name = models.CharField(max_length=100, null=True, blank=True)
    entity_unit = models.CharField(max_length=100, null=True, blank=True)
    certificate_no=models.CharField(max_length=300,blank=True,null=True)
    region=models.ForeignKey(Region,related_name='profile_estate_region',on_delete=models.DO_NOTHING, blank=True, null=True)
    state=models.ForeignKey(State,related_name='profile_estate_state',on_delete=models.DO_NOTHING, blank=True, null=True)
    district=models.ForeignKey(District,related_name='profile_estate_district',on_delete=models.DO_NOTHING, blank=True, null=True)
    address=models.TextField(null=True, blank=True) 
    phone_regex = RegexValidator(regex=r'^\+?1?\d{6,10}$', message="Not a valid Mobile Number")
    # contact info
    ho_contact_person=models.CharField(max_length=300,blank=True,null=True)
    ho_contact_number=models.CharField(max_length=10,blank=True,null=True, validators=[phone_regex],)
    ho_contact_email= models.EmailField(max_length=70, unique=False, null=True, blank=True)
    garden_contact_person=models.CharField(max_length=300,blank=True,null=True)
    garden_contact_number=models.CharField(max_length=10,blank=True,null=True, validators=[phone_regex],)
    garden_contact_email= models.EmailField(max_length=70, unique=False,blank=True,null=True)
    manager_contact_person=models.CharField(max_length=300,blank=True,null=True)
    manager_contact_number=models.CharField(max_length=10,blank=True,null=True, validators=[phone_regex],)
    manager_contact_email= models.EmailField(unique=False, blank=True,null=True)
    trust_tea_officer_contact_person=models.CharField(max_length=300,blank=True,null=True)
    trust_tea_officer_contact_number=models.CharField(max_length=10,blank=True,null=True, validators=[phone_regex],)
    trust_tea_officer_contact_email= models.EmailField(max_length=70, unique=False, blank=True,null=True )
    data_operator_contact_person=models.CharField(max_length=300,blank=True,null=True)
    data_operator_contact_number=models.CharField(max_length=10,blank=True,null=True, validators=[phone_regex],)
    data_operator_contact_email= models.EmailField(max_length=255, unique=False,null=True,blank=True)
    easy_weight_system = models.CharField(max_length=100, choices=EASY_WEIGHT_SYSTEM_OPTION, null=True,blank=True )
    # factory info
    factory_details_likely_production=models.FloatField( blank=True,null=True)
    factory_details_other_certificate=models.CharField(max_length=255,blank=True,null=True)
    ownership_details_managing_company=models.CharField(max_length=255,blank=True,null=True)
    ownership_details_name_of_tea_company=models.CharField(max_length=255,blank=True,null=True)
    ownership_details_email=models.CharField(max_length=255, unique=False, null=True,blank=True)
    # 3rd party
    third_party_easy_weight_system = models.BooleanField(default=False)
    # Cultivation Management
    total_male_worker=models.IntegerField(blank=True,null=True)
    total_female_worker=models.IntegerField(blank=True,null=True)
    estimated_production_of_green_leaves=models.CharField(max_length=255, blank=True,null=True)
    estimated_production_of_made_tea=models.CharField(max_length=255, blank=True,null=True)
    user_file=models.FileField(
        upload_to='user_profile_estate/file',null=True,blank=True, help_text='file', validators=[validate_image_file_extension])
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return str(self.user) + "-" + str(self.user_id)
     
    def save(self, *args, **kwargs):
        """ image file resize @Subhashis"""
        if self.user_file:
            temp_image = Image.open(self.user_file).convert('RGB')
            output_io_stream = BytesIO()
            temp_resized_image = temp_image.resize((200, 200))
            temp_resized_image.save(
                output_io_stream, format='JPEG', quality=60)
            output_io_stream.seek(0)
            self.user_file = InMemoryUploadedFile(output_io_stream,
                                                    'ImageField', "%s.jpg" % self.user_file.name.split('.')[0], 'image/jpeg', sys.getsizeof(output_io_stream), None)

        super(EstateProfile, self).save(*args, **kwargs)



class FactoryDetailsMarks(models.Model):

    name = models.CharField(max_length=100, blank=True, null=True)
    estate = models.ForeignKey(EstateProfile, on_delete=models.CASCADE, related_name="estate_factory_marks", null=True, blank=True)
    
    def __str__(self):
        return str(self.name) 
   

class EstateTeaProduction(models.Model):     

    estate = models.ForeignKey(EstateProfile, related_name="tea_production_estate", 
                    on_delete=models.CASCADE, blank=True, null=True)
    tea_type=models.ForeignKey(TeaType, related_name='tea_type', on_delete=models.CASCADE, 
                blank=True, null=True )
    tea_grade=models.ForeignKey(TeaGradeDetails, related_name='tea_type_grade_production', 
                    on_delete=models.CASCADE, blank=True, null=True)
    marks= models.CharField(max_length=200, blank=True,null=True)
    quantity=models.CharField(max_length=200, blank=True, null=True)





class EstateProductionTeaType(models.Model):

    estate = models.ForeignKey(EstateProfile, related_name="estate_production_tea_type", on_delete=models.CASCADE, blank=True, null=True)
    tea_type = models.ForeignKey(TeaType, related_name='estate_tea_type', on_delete=models.CASCADE, 
                blank=True, null=True )

    tea_grade=models.ForeignKey(TeaGradeDetails, related_name='estate_tea_type_grade_production', 
                    on_delete=models.CASCADE, blank=True, null=True)
    marks= models.CharField(max_length=200, blank=True,null=True)
    quantity=models.CharField(max_length=200, blank=True, null=True)




class TroughDetailsEstate(models.Model): 
    """ Trough Details X User Profile Estate Model Trace Tea """

    LEAF_TYPE = (
        ('OWN LEAF', 'OWN LEAF'),
        ('BOUGHT LEAF', 'BOUGHT LEAF'),  
    )
    user_profile_estate =models.ForeignKey(EstateProfile, related_name='user_profile_trough_details_estate',\
                                    on_delete=models.CASCADE, blank=True, null=True)
    capacity_qty=models.CharField(blank=True,null=True, max_length=100)
    size_width=models.CharField(blank=True,null=True,max_length=100)
    size_height=models.CharField(blank=True,null=True,max_length=100)
    name=models.CharField(max_length=200,blank=True,null=True)
    leaf_type=models.CharField(max_length=40,choices=LEAF_TYPE,blank=True,null=True)

    def __str__(self):
        return str(self.name)    
    


    

# QR CODE MODELS

class GrowerQrCode(models.Model):

    grower = models.ForeignKey(GrowerProfile, related_name="grower_qr", on_delete=models.CASCADE,blank=True,null=True)
    name = models.CharField(max_length=100,blank=True,null=True)
    image=models.ImageField(upload_to='qrcode',blank=True,null=True)
    
    # def save(self,*args,**kwargs):
    #     from django.template import Template, Context

    #     # grower_text="Grower ID : " + str(self.grower) + "\n" + "Name : " + str(self.name) + "\n" + "Profile Image Url : " + str(self.profile_image.url)
    #     grower_text= "Grower ID : " + str(self.grower) + "\n" + "Name : " + str(self.name) 
    #     # grower_text= self.name
    #     qrcode_img=qrcode.make(grower_text)
    #     canvas=Image.new("RGB", (900,900),"white")
    #     draw=ImageDraw.Draw(canvas)
    #     canvas.paste(qrcode_img)
    #     buffer=BytesIO()
    #     canvas.save(buffer,"PNG")
    #     self.image.save(f'image{random.randint(0,9999)}',File(buffer),save=False)
    #     canvas.close()
    #     super().save(*args,**kwargs)




class AggregatorQrCode(models.Model):

    aggregator = models.ForeignKey(AggregatorProfile, related_name="aggregator_qr_code", on_delete=models.CASCADE,blank=True,null=True)
    name = models.CharField(max_length=100,blank=True,null=True)
    image=models.ImageField(upload_to='qrcode',blank=True,null=True)
    
    # def save(self,*args,**kwargs):
    #     from django.template import Template, Context

    #     details = AggregatorProfile.objects.filter(id=self.aggregator_id).first()

    #     # image="http://127.0.0.1:8000/" + str(self.profile_image.url)
    #     # grower_text = "<h2> Grower ID : " + str(self.grower) + "</h2><br><h4> Name : " + str(self.name) + "</h4><br><p> Profile Image :</p><br><img src=" + str(image) +">"
        
    #     # grower_text="Grower ID : " + str(self.grower) + "\n" + "Name : " + str(self.name) + "\n" + "Profile Image Url : " + str(self.profile_image.url)
    #     grower_text= "Grower ID : " + str(details) + "\n" + "Name : " + str(self.name) 
    #     # grower_text= self.name
    #     qrcode_img=qrcode.make(grower_text)
    #     canvas=Image.new("RGB", (900,900),"white")
    #     draw=ImageDraw.Draw(canvas)
    #     canvas.paste(qrcode_img)
    #     buffer=BytesIO()
    #     canvas.save(buffer,"PNG")
    #     self.image.save(f'image{random.randint(0,9999)}',File(buffer),save=False)
    #     canvas.close()
    #     super().save(*args,**kwargs)




# ESTATE TROUGH DETAILS MODEL 

class FactoryTroughDetails(models.Model):
    """ Estate Trough Details Factory Model """

    user = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name="user_trough_factorty", null=True, blank=True)
    estate = models.ForeignKey(EstateProfile, on_delete=models.DO_NOTHING, related_name="estate_trough_factorty", null=True, blank=True)
    
    name=models.CharField(max_length=200,blank=True,null=True)
    def __str__(self):
        return str(self.name)

class EstateTroughDetails(models.Model):

    LEAF_TYPE = (
        ('OWN LEAF', 'OWN LEAF'),
        ('BOUGHT LEAF', 'BOUGHT LEAF'),
    )   
    factory =models.ForeignKey(FactoryTroughDetails, related_name='estate_trough_details_factory',\
                                    on_delete=models.CASCADE, blank=True, null=True)
    estate =models.ForeignKey(BlfProfile, related_name='estate_trough_details',\
                                    on_delete=models.CASCADE, blank=True, null=True)
    capacity_qty=models.CharField(blank=True,null=True, max_length=200)
    size_width=models.CharField(blank=True,null=True,max_length=200)
    size_height=models.CharField(blank=True,null=True,max_length=200)
    name=models.CharField(max_length=200,blank=True,null=True)
    leaf_type=models.CharField(max_length=40, choices=LEAF_TYPE, blank=True,null=True)

    def __str__(self):
        return str(self.name)
    



# BLF ASSOCIATED USERS
class BlfAssociatedUsers(models.Model):

    blf =models.ForeignKey(BlfProfile, related_name='blf',\
                                    on_delete=models.CASCADE, blank=True, null=True)
    grower =models.ForeignKey(GrowerProfile, related_name='blf_associated_growers',\
                                    on_delete=models.CASCADE, blank=True, null=True)
    aggregator =models.ForeignKey(AggregatorProfile, related_name='blf_associated_aggregators',\
                                    on_delete=models.CASCADE, blank=True, null=True)
    
    

class BlfofficialSignature(BaseAbstractStructure):
    blf= models.ForeignKey(BlfProfile, related_name='blf_signature', on_delete=models.DO_NOTHING, blank=True, null=True)
    blf_grade_official_signature_file = models.FileField(
        upload_to='BLF/signature',
        null=True,
        blank=True,
        help_text='file',
        validators=[validate_signature_file_extension]
    )
    date = models.DateField(auto_now=True, null=True, blank=True)

    def __str__(self):
        return str(self.blf)
    

class UserFileUpload(models.Model):
    """ users File Upload  """
    file_name = models.CharField(max_length=255, null=True, blank=True)
    file = models.FileField(upload_to='excel',null=True,blank=True,)
    def __str__(self):
        return self.file_name
    
class UserProfileAttachments(BaseAbstractStructure):
    """
    Profile ID Attachments
    """
    DOC_TYPE = (
        ('id_proof', 'ID Proff'),
        ('profile_image', 'Profile Image'),   
    )
    ID_PROOF_TYPE = (
        ('AADHAR_CARD', 'AADHAR CARD'),
        ('VOTER_ID', 'VOTER ID'),   
        ('TBOI_CARD', 'TBOI CARD'),
        ('RC_ID', 'RC ID'),   
        ('DL_ID', 'DL'),   
        ('Other', 'Other'),
    )
    grower = models.ForeignKey(GrowerProfile, related_name='grower_proof_id_attachments', 
                                on_delete=models.CASCADE, blank=True, null=True)
    doc_type = models.CharField(max_length=250, choices=DOC_TYPE, default='id_proof', null=True, blank=True)
    attachment_name = models.CharField(max_length=250, choices=ID_PROOF_TYPE, default="", null=True, blank=True)
    attachment = models.FileField(upload_to='users/profile/ID', null=True, blank=True)
    mime_type = models.CharField(max_length=200, null=True, blank=True)
    file_data = models.TextField(null=True, blank=True)
    doc_no =  models.CharField(max_length=250, null=True, blank=True)
    class Meta:
        db_table = "user_profile_attachments"
