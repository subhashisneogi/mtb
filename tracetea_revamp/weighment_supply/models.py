from django.db import models
from time import timezone
from datetime import datetime
from django.contrib.auth import get_user_model
User = get_user_model()
from vehicle_management.models import *
from user_profile.aggregator_api_models import *
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



class BlfSupplier(models.Model):
    aggregator = models.ForeignKey(AggregatorProfile, on_delete=models.CASCADE, related_name="blf_aggregator_supplier", null=True, blank=True)
    supplier_type = models.CharField(max_length=150, blank=True, null=True)
    blf = models.ManyToManyField(BlfProfile, related_name="blfs_aggregators_supplier", null=True, blank=True)
    grower = models.ForeignKey(AggregatorProfile, on_delete=models.CASCADE, related_name="blf_grower_supplier", null=True, blank=True)



class WeighmentSupply(BaseAbstractStructure) :
    """ Weighment & Supply Details Model"""

    supply_option = (
        ('By hand', 'By hand'),
        ('By Non motorised 2/3 wheelers vehicle', 'By Non motorised 2/3 wheelers vehicle'),
        ('Motorised 2 wheelers vehicle', 'Motorised 2 wheelers vehicle'),
        ('Motorised 3 / 4 wheelers vehicle', 'Motorised 3 / 4 wheelers vehicle'),
    )
    
    supplier_option = (
        ('aggregator', 'aggregator'),
        ('grower', 'grower'),
    )

    supplier_type = models.CharField(max_length=150, choices=supplier_option, blank=True, null=True)#supply type
    supplier = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name="supplier_user", blank=True, null=True)
    supply_challan = models.ForeignKey(SupplyManagement, related_name='supply_challan_id_supply_management', on_delete=models.DO_NOTHING, blank=True, null=True)
    mode_of_supply = models.CharField(max_length=150, choices=supply_option, blank=True, null=True)
    supply_date = models.DateField(auto_now_add= False, blank=True,null=True)
    vehicle_no =  models.ForeignKey(VehicleManagement, related_name='weighment_vehicle_id', on_delete=models.DO_NOTHING, blank=True, null=True)
    total_gross_weight_kg = models.FloatField(blank=True,null=True, validators=[MinValueValidator(0)], help_text="Kg") 
    phone_regex = RegexValidator(regex=r'^\+?1?\d{6,10}$', message="Not a valid Mobile Number")
    mobile_number = models.CharField(validators=[phone_regex],max_length=17, blank=True, null=True)
    weighment_txn_id = models.CharField(max_length=300,blank=True, null=True, unique=True)
    is_processed=models.BooleanField(default=False) # Weightment un-processed txn id for leaf receipt View
    is_leaf_rejected = models.BooleanField(default=False)
    is_supplier_exit_proceed = models.BooleanField(default=False)
    
    def __str__(self):
        return str(self.weighment_txn_id)  



    

