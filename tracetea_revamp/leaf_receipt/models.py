from django.db import models

# Create your models here.
from django.db import models
from time import timezone
from datetime import datetime
from django.contrib.auth import get_user_model
User = get_user_model()
from weighment_supply.models import *
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db.models.signals import post_save
from user_profile.blf_api_models import SupplierExit

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


class LeafManagement(models.Model):
    """ Leaf receipt Model Trace Tea @vivek, changes made by subhashis"""   
    ACKNOWLEDGE_STATUS = (
        ('Received', 'Received'),
        ('Rejected', 'Rejected'),
    )
    PAYMENT_RECORD_OPTION = (
        ('Yes', 'Yes'),
        ('No', 'No'),
    )
    QUALITY_STANDARD = (
        ('A', 'A'),
        ('A+', 'A+'),   
        ('B', 'B'),
        ('B+', 'B+'),
        ('C', 'C'),
        ('C+', 'C+'),
        ('D+', 'D+'),
        ('D', 'D'),
    )
    
    weighment_txn= models.ForeignKey(WeighmentSupply, related_name='weignment_supply_txn_id',on_delete=models.CASCADE, blank=True, null=True)
    deduction = models.FloatField( blank=True,null=True, validators=[MinValueValidator(0), MaxValueValidator(100)], help_text = "(%)")
    final_leaf_count=models.FloatField(blank=True,null=True, validators=[MinValueValidator(0), MaxValueValidator(100)], help_text = "(%)")
    acknowledge_status=models.CharField(max_length=50,choices=ACKNOWLEDGE_STATUS, blank=True,null=True)
    quality_standard=models.CharField(max_length=50,choices=QUALITY_STANDARD, blank=True,null=True)
    payment_record_option=models.CharField(max_length=50,choices=PAYMENT_RECORD_OPTION, blank=True,null=True)
    rate=models.CharField(max_length=200,blank=True,null=True)
    supply_date = models.DateField(auto_now_add=False,blank=True,null=True)
    net_leaf_weight = models.FloatField(blank=True, null=True, help_text = "(Kg)", validators=[MinValueValidator(0)])
    is_complete = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, related_name='created_by_user_leaf_receipt', on_delete=models.CASCADE, blank=True, null=True)
    
    objects = models.Manager()
    cmobjects = CustomManager()

    def __str__(self):
        return str(self.weighment_txn)


class LeafCollection(models.Model):
    """ Leaf collection Model """
    leaf_receipt_id= models.ForeignKey(LeafManagement, on_delete=models.CASCADE, related_name="leaf_receipt_collection", blank=True,null=True)
    weighment_supply_id = models.ForeignKey(WeighmentSupply, on_delete=models.CASCADE, related_name="weighment_collection", blank=True,null=True)
    supply_id = models.ForeignKey(SupplyManagement, on_delete=models.CASCADE, related_name="supplymanagment_collection", blank=True,null=True)
    suppler_exit_id = models.ForeignKey(SupplierExit, on_delete=models.CASCADE, related_name="supplier_exit_collection", blank=True,null=True)
    supplier_type = models.CharField(max_length=150, blank=True,null=True)
    supplier = models.ForeignKey(User, related_name="users_leafcollect", on_delete=models.CASCADE, blank=True,null=True)
    nt_wght = models.FloatField(blank=True, null=True, help_text = "(Kg)", validators=[MinValueValidator(0)]) # total net weight sum of leaf collect 
    aggregator = models.ForeignKey(AggregatorProfile, related_name="aggregators_leafcollect", on_delete=models.CASCADE, blank=True,null=True )
    grower = models.ForeignKey(GrowerProfile, related_name="grower_leafcollect", on_delete=models.CASCADE, blank=True,null=True )
    grower_plot = models.ForeignKey(Plot, related_name="grower_plot_leafcollect", on_delete=models.CASCADE, blank=True,null=True)
    grower_garden = models.ForeignKey(Gardens, related_name="grower_garden_leafcollect", on_delete=models.CASCADE, blank=True,null=True)
    plucking_data = models.ForeignKey(PluckingData, related_name="plucking_data_leafcollect", on_delete=models.CASCADE, blank=True,null=True)
    collection_date = models.DateField(auto_now_add=False,blank=True,null=True)
    supply_date = models.DateField(auto_now_add=False,blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.DO_NOTHING, blank=True, null=True, related_name='+')
    
    def __str__(self):
        return str(self.weighment_supply_id)



# @receiver(post_save, sender=LeafManagement)
# def on_model_create(sender, instance, created, **kwargs):
#     if created:
#         new_object_id = instance.id
#         LeafCollection.objects.update_or_create(leaf_receipt_id=instance)