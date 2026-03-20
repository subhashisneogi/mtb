#models
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
    quantity=models.FloatField(max_length=200,blank=True, null=True) 
    supply_bag_id=models.CharField(max_length=200,blank=True,null=True)
    driver_name=models.CharField(max_length=200,blank=True, null=True)
    phone_regex = RegexValidator(regex=r'^\+?1?\d{6,12}$', message="Not a valid Mobile Number")
    mobile_number = models.CharField(validators=[phone_regex],max_length=17,blank=True, null=True)
    is_weighment_proceed = models.BooleanField(default=False)
    def __str__(self):
        return str(self.supply_challan_id)
#signals
@receiver(post_save, sender=SupplyManagement)
def generate_supply_challan_code(sender, instance, created, **kwargs):
    print("HBFEGFEYFEFVYEFY #############")
    if not created:
        return
    # Get region code from aggregator or grower profile
    agg_supplier_details = AggregatorProfile.cmobjects.filter(user_id=instance.created_by_id).first()
    grower_supplier_details = GrowerProfile.cmobjects.filter(user_id=instance.created_by_id).first()
    if agg_supplier_details and agg_supplier_details.region:
        region_code = agg_supplier_details.region.region_id
    elif grower_supplier_details and grower_supplier_details.region:
        region_code = grower_supplier_details.region.region_id
    else:
        region_code = ""
    # Use username for stability
    user_code = instance.created_by.username.upper()
    prefix = f"CH{region_code}{user_code}"
    print("prefix ##", prefix)
    with transaction.atomic():
        last_challan = SupplyManagement.objects.filter(supply_challan_id__contains="CH"+str(region_code) + str(request.user).upper(),\
        created_by_id=request.user.id).last()
        # Calculate the next supply_challan_id
        if last_challan and last_challan.supply_challan_id.startswith("CH"+str(region_code) + str(request.user).upper()):
            # Extract the numeric part and increment it
            numeric_part_index = len("CH" + str(region_code) + str(request.user).upper())
            
            numeric_part = int(last_challan.supply_challan_id[numeric_part_index:]) + 1    
            next_challan_id = f"CH{region_code}{str(request.user).upper()}{numeric_part:0>2d}"
        else:
            # Handle the case when there are no existing supply_challan_id values
            next_challan_id = f"CH{region_code}{str(request.user).upper()}01"
        # Set the new supply_challan_id
        created.supply_challan_id = next_challan_id


please write the proper way to generate the supply_challan_id when created 
now challan_id is not created


