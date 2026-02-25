#models.py
class WBSList(BaseAbstractStructure):
    """
    List for WBS for Tender/BOQ
    """
    CATEGORY = (
        ('highway', 'Highway'),
        ('structure', 'Structure'),
        ('volumetric', 'Volumetric'),
        ('others', 'Others'),
    )
    organization = models.ForeignKey(Organization, related_name='wbs_list_organization', on_delete=models.CASCADE)
    category = models.CharField(max_length=100, choices=CATEGORY, default='highway')
    by_order = models.IntegerField(default=1)
    after_this = models.ForeignKey('self', related_name="+", on_delete=models.CASCADE, null=True, blank=True)
    boq_code = models.CharField(max_length=255,null=True, blank=True)
    boq_no = models.CharField(max_length=255,null=True, blank=True)
    #wbs = models.ForeignKey(TenderWBSKeyScopes, related_name='wbs_list_wbs_key_scopes', on_delete=models.DO_NOTHING)
    wbs = models.CharField(max_length=255)
    planning_tender = models.ForeignKey(PlanningTender, related_name='boq_planning_tender', on_delete=models.CASCADE, null=True, blank=True)
    boq = models.ForeignKey(BOQ, related_name='wbs_list_boq', on_delete=models.CASCADE,
                             null=True, blank=True)
    tender = models.ForeignKey(TenderMasterNew, related_name='wbs_list_tender', on_delete=models.CASCADE,
                              null=True, blank=True)
    parent = models.ForeignKey('self', related_name='wbs_list_parent', on_delete=models.CASCADE,
                              null=True, blank=True)
    uom = models.ForeignKey(UnitOfMesurement, related_name='wbs_list_uom', on_delete=models.CASCADE,
                              null=True, blank=True)
    
class BOQChainage(BaseAbstractStructure):
    organization = models.ForeignKey(Organization, related_name='+', on_delete=models.CASCADE)
    planning_tender = models.ForeignKey(PlanningTender, related_name='boq_chainage_planning_tender', on_delete=models.CASCADE, null=True, blank=True)
    boq = models.ForeignKey(BOQ, related_name='+',on_delete=models.CASCADE, null=True, blank=True)
    wbs = models.ForeignKey(WBSList, related_name='+',on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    start = models.FloatField(blank=True, null=True, default=0)
    end = models.FloatField(blank=True, null=True, default=0)
    chainage_value = models.FloatField(blank=True, null=True, default=0)

    def save(self, *args, **kwargs):
        self.full_clean()
        if not self.start:
            self.start = 0.
        if not self.end:
            self.end = 0.
        self.chainage_value = float(self.end)-float(self.start)
        super().save(*args, **kwargs)

class BOQChainageExecutiveSummeryData(BaseAbstractStructure):
    organization = models.ForeignKey(Organization, related_name='+', on_delete=models.CASCADE)
    planning_tender = models.ForeignKey(PlanningTender, related_name='boq_chainage_executive_planning_tender', on_delete=models.CASCADE, null=True, blank=True)
    boq = models.ForeignKey(BOQ, related_name='+',on_delete=models.CASCADE, null=True, blank=True)
    wbs = models.ForeignKey(WBSList, related_name='+',on_delete=models.CASCADE, null=True, blank=True)
    form = models.ForeignKey(BOQChainage, related_name='+',on_delete=models.CASCADE, blank=True, null=True)
    value = models.CharField(max_length=200, blank=True, null=True)
    type = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return str(self.value) + " (" + str(self.type) + ") "

    class Meta:
        db_table = "boq_chainage_executivesummery"


#signals.py
@receiver(post_save, sender=WBSList)
def signal_update_wbs_list(sender, instance, created, **kwargs):
    print("in signal WBSList")
    if instance:
        change_lmpi_data(instance.id,instance.budgeted_quantity)
    if instance.boq and created:
        if instance.parent is None:
            BOQChainage.objects.get_or_create(boq=instance.boq, wbs=instance, organization=instance.organization, defaults={
                "name": f"CH-{instance.boq.id}-{instance.pk}",  "start": 0,"end": 1,})
        elif instance.parent:
            parent_chainage_id = BOQChainage.cmobjects.filter(boq=instance.boq, wbs=instance.parent).values_list('id', flat=True).first()
            auto_value = generate_chainage_code(instance)
            print("parent_chainage_id ###", parent_chainage_id)
            BOQChainageExecutiveSummeryData.objects.get_or_create(boq=instance.boq, wbs=instance, value__isnull=True,  
                defaults={"organization": instance.organization, "type": "C", "value": auto_value, 'form_id' : parent_chainage_id})
	


here have the BOQChainage which WBSList have parent is null
and to get the BOQChainage instance which have multiple child WBSList
one parent WBSList can have the multiple chiled WBSList 	
