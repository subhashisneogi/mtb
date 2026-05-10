from django.db import models
from time import timezone
from datetime import datetime
from django.contrib.auth import get_user_model
User = get_user_model()

from user_profile.models import *
from collection_center.models import *
# from month.models import MonthField
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

    objects = models.Manager()
    cmobjects = CustomManager()

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.updated_at = datetime.now()
        super(__class__, self).save(*args, **kwargs)



class EasyWeightMaster(BaseAbstractStructure):
    """ Easy Weight master Model"""
    collection_center = models.ForeignKey(CollectionCenter, on_delete=models.DO_NOTHING, related_name="easy_weight_collection_center", null=True, blank=True)
    tracetea_id= models.ForeignKey(User, on_delete=models.DO_NOTHING, blank=True, null=True, related_name='easy_weight_user')
    member_no=models.CharField(max_length=200,null=True,blank=True)
    member_name=models.CharField(max_length=200,null=True,blank=True)
    phone_regex = RegexValidator(regex=r'^\+?1?\d{6,12}$', message="Not a valid Mobile Number")
    mobile_number = models.CharField(validators=[phone_regex],max_length=17,blank=True, null=True)
    # month_year=models.DateField(auto_now_add= False, blank=True,null=True)
   
    month_year=models.CharField(max_length=200,null=True,blank=True)
    # month=models.CharField(max_length=200,null=True,blank=True)
    # year=models.CharField(max_length=200,null=True,blank=True)
    total_weight =models.CharField(max_length=200,null=True,blank=True)
    rate_gl=models.CharField(max_length=200,null=True,blank=True)
    total_value = models.CharField(max_length=200,null=True,blank=True)
    rate_tf = models.CharField(max_length=200,null=True,blank=True)
    tft=models.CharField(max_length=200,null=True,blank=True)
    ss=models.CharField(max_length=200,null=True,blank=True)
    rate_fa=models.CharField(max_length=200,null=True,blank=True)
    fa=models.CharField(max_length=200,null=True,blank=True)
    manure=models.CharField(max_length=200,null=True,blank=True)
    kadhi=models.CharField(max_length=200,null=True,blank=True)
    gl_adv=models.CharField(max_length=200,null=True,blank=True)
    hort=models.CharField(max_length=200,null=True,blank=True)
    mbf=models.CharField(max_length=200,null=True,blank=True)
    roud_off_net=models.CharField(max_length=200,null=True,blank=True)
    total_ded=models.CharField(max_length=200,null=True,blank=True)
    net_payable=models.CharField(max_length=200,null=True,blank=True)
    cb=models.CharField(max_length=200,null=True,blank=True)
    ob=models.CharField(max_length=200,null=True,blank=True)
    payment_rcpt_no=models.CharField(max_length=200,null=True,blank=True)
    payment_date=models.DateField(auto_now_add= False, blank=True,null=True)

    def __str__(self):
        return str(self.tracetea_id) + "," + str(self.month_year)
    
    # def save(self, *args, **kwargs):
    #     if self.month_year:
    #         self.month = str(self.month_year.month)
    #         self.year = str(self.month_year.month)
    #         super(EasyWeightMaster, self).save(*args, **kwargs)

class EasyWeightWt(BaseAbstractStructure):
     
    """ Easy Weight WT model  """   
 
    easy_weight= models.ForeignKey(EasyWeightMaster, related_name='wt_easy_weight_master', on_delete=models.CASCADE, blank=True, null=True)
    wt=models.CharField(max_length=200, blank=True, null=True)
    value=models.CharField(max_length=200, blank=True, null=True)

   

    def __str__(self):
        return str(self.easy_weight)        
class EasyWeightAdv(BaseAbstractStructure):
     
    """ Easy Weight ADV model  """   
 
    easy_weight= models.ForeignKey(EasyWeightMaster, related_name='adv_easy_weight_master', on_delete=models.CASCADE, blank=True, null=True)
    adv=models.CharField(max_length=200, blank=True, null=True)
    value=models.CharField(max_length=200, blank=True, null=True)

   

    def __str__(self):
        return str(self.easy_weight)   
class EasyWeightGwt(BaseAbstractStructure):
     
    """ Easy Weight GWT model  """   
 
    easy_weight= models.ForeignKey(EasyWeightMaster, related_name='gwt_easy_weight_master', on_delete=models.CASCADE, blank=True, null=True)
    gwt=models.CharField(max_length=200, blank=True, null=True)
    value=models.CharField(max_length=200, blank=True, null=True)

   

    def __str__(self):
        return str(self.easy_weight)           

class EasyWeightMisc(BaseAbstractStructure):
     
    """ Easy Weight Misc model  """   
 
    easy_weight= models.ForeignKey(EasyWeightMaster, related_name='misc_easy_weight_master', on_delete=models.CASCADE, blank=True, null=True)
    misc=models.CharField(max_length=200, blank=True, null=True)
    value=models.CharField(max_length=200, blank=True, null=True)

   

    def __str__(self):
        return str(self.easy_weight)     