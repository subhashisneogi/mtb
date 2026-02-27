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
    tender = models.ForeignKey(TenderMaster, related_name='wbs_list_tender', on_delete=models.CASCADE,
                              null=True, blank=True)
    parent = models.ForeignKey('self', related_name='wbs_list_parent', on_delete=models.CASCADE,
                              null=True, blank=True)
    uom = models.ForeignKey(UnitOfMesurement, related_name='wbs_list_uom', on_delete=models.CASCADE,
                              null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    priority = models.CharField(max_length=255,null=True, blank=True)
    short_name = models.CharField(max_length=255,null=True, blank=True)
    opening_done_quantity = models.FloatField(default=0)
    opening_undone_quantity = models.FloatField(default=0)
    tender_quantity = models.CharField(max_length=255,null=True, blank=True)
    budgeted_quantity = models.FloatField(default=0)
    ra_bill_rate = models.FloatField(default=0)
    escalation_type = models.CharField(max_length=255,null=True, blank=True)
    escalation_per = models.FloatField(default=0)
    bidding_type = models.CharField(max_length=255,null=True, blank=True)
    bidding_per = models.FloatField(default=0)
    rate = models.CharField(max_length=255,null=True, blank=True)
    cost = models.CharField(max_length=255,null=True, blank=True)
    manual_rate = models.FloatField(default=0)
    manual_cost = models.FloatField(default=0)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    duration = models.FloatField(default=0)
    replicate_from = models.CharField(max_length=255,null=True, blank=True)
    total_labour = models.CharField(max_length=255,null=True, blank=True)
    total_material = models.CharField(max_length=255,null=True, blank=True)
    total_machinery = models.CharField(max_length=255,null=True, blank=True)
    total_overheads = models.CharField(max_length=255,null=True, blank=True)
    root = models.ForeignKey('self', null=True, blank=True, related_name='root_node', on_delete=models.CASCADE)

    def clean(self):
        # if self.boq is None and self.tender is None and self.planning_tender is None:
        #     raise ValidationError("Either boq or planning_tender must be specified, but not both.")
        # elif self.boq is not None and self.tender is not None and self.planning_tender is not None:
        #     raise ValidationError("Both boq and planning_tender cannot be specified simultaneously.")

        # Check if more than one field is specified
        specified_fields = [self.boq, self.tender, self.planning_tender]
        specified_count = sum(1 for field in specified_fields if field is not None)

        if specified_count == 0:
            raise ValidationError("Either boq or tender or planning_tender must be specified.")
        elif specified_count > 1:
            raise ValidationError("Only one of boq, tender, or planning_tender can be specified.")

        super().clean()

    def save(self, *args, **kwargs):
        self.full_clean()
        if not self.manual_rate:
            self.manual_rate = 0
        if not self.budgeted_quantity:
            self.budgeted_quantity = 0
        if self.manual_rate != 0 and self.budgeted_quantity != 0:
            self.manual_cost = float(self.manual_rate)*float(self.budgeted_quantity)
        else:
            self.manual_cost = 0 
        if self.parent:
            self.root = self.parent.root if self.parent.root else self.parent
            super().save(*args, **kwargs)
        else:
            self.root = None   
            super().save(*args, **kwargs)
            if self.root is None:
                self.root = self
                super().save(update_fields=['root'])

    def __str__(self):
        # return str(self.wbs) + " (" + str(self.category) + ") " + str(self.parent)
        return str(self.wbs)

    class Meta:
        unique_together = ('organization','tender','boq','wbs',)
        db_table = "boq_wbs"