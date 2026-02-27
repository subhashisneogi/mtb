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


class BOQWBSImportAPIView(APIView):
    """
    Optimized BOQ WBS Import API
    """
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    def post(self, request, *args, **kwargs):
        # try:
            with transaction.atomic():
                count_data = {
                    "wbs_add": 0,
                    "wbs_edit": 0,
                    "errors": 0,
                }
                errors = []
                organization_id = request.query_params.get("organization_id")
                boq_id = request.query_params.get("boq_id")
                wbs_list_id = request.query_params.get("wbs_list_id")
                if not organization_id or not boq_id or not wbs_list_id:
                    raise APIException("organization_id, boq_id, wbs_list_id are required.")
                file_name = request.data.get("file_name")
                field_map = request.data.get("field_map", {})
                if not file_name:
                    raise APIException("file_name is required.")
                if not field_map:
                    raise APIException("field_map is required.")
                file_path = os.path.join("media/excel/", file_name)
                if not os.path.exists(file_path):
                    raise APIException("Excel file not found.")
                df = pd.read_excel(file_path)
                if df.empty:
                    raise APIException("Excel file is empty.")
                required_columns = list(field_map.values())
                for col in required_columns:
                    if col not in df.columns:
                        raise APIException(f"Missing column in Excel: {col}")
                df = df.where(pd.notnull(df), None)
                df = df.apply(lambda col: col.map(lambda x: x.strip() if isinstance(x, str) else x))
                df[field_map["rate"]] = pd.to_numeric(
                    df[field_map["rate"]], errors="coerce"
                )
                df[field_map["budgeted_quantity"]] = pd.to_numeric(
                    df[field_map["budgeted_quantity"]], errors="coerce"
                )
                def get_parent_code(code):
                    if not code:
                        return None
                    code = str(code).strip()
                    if "." in code:
                        return ".".join(code.split(".")[:-1])
                    return None
                existing_wbs_qs = WBSList.objects.filter(
                    organization_id=organization_id,
                    boq_id=boq_id
                ).values("id", "boq_code")
                existing_wbs_map = {
                    str(obj["boq_code"]).strip(): obj["id"]
                    for obj in existing_wbs_qs
                    if obj["boq_code"]
                }
                created_map = {}
                for index, row in df.iterrows():
                    row_index = index + 2  # Excel row number
                    boq_code = row.get(field_map["boq_code"])
                    wbs_name = row.get(field_map["wbs"])
                    rate = row.get(field_map["rate"])
                    quantity = row.get(field_map["budgeted_quantity"])
                    if not wbs_name:
                        continue
                    boq_code = str(boq_code).strip() if boq_code else None
                    # Validate Rate
                    if rate is None or pd.isna(rate):
                        errors.append(f"Row {row_index}: Basic Rate must be numeric")
                        count_data["errors"] += 1
                        continue

                    if float(rate) <= 0:
                        errors.append(f"Row {row_index}: Basic Rate should be greater than 0")
                        count_data["errors"] += 1
                        continue
                    # Validate Quantity
                    if quantity is None or pd.isna(quantity):
                        errors.append(f"Row {row_index}: Quantity must be numeric")
                        count_data["errors"] += 1
                        continue
                    if float(quantity) <= 0:
                        errors.append(f"Row {row_index}: Quantity should be greater than 0")
                        count_data["errors"] += 1
                        continue

                    parent_id = wbs_list_id
                    parent_code = get_parent_code(boq_code)

                    if parent_code:
                        if parent_code in created_map:
                            parent_id = created_map[parent_code]
                        elif parent_code in existing_wbs_map:
                            parent_id = existing_wbs_map[parent_code]

                    record_data = {
                        "organization_id": organization_id,
                        "boq_id": boq_id,
                        "parent_id": parent_id,
                        "boq_code": boq_code,
                        "boq_no": row.get(field_map["boq_no"]),
                        "wbs": wbs_name,
                        "rate": float(rate),
                        "budgeted_quantity": float(quantity),
                    }

                    if boq_code in existing_wbs_map:
                        WBSList.objects.filter(
                            pk=existing_wbs_map[boq_code]
                        ).update(
                            updated_by_id=request.user.id,
                            **record_data
                        )
                        created_map[boq_code] = existing_wbs_map[boq_code]
                        count_data["wbs_edit"] += 1
                    else:
                        instance = WBSList.objects.create(
                            created_by_id=request.user.id,
                            **record_data
                        )
                        created_map[boq_code] = instance.id
                        count_data["wbs_add"] += 1

                return Response({
                    "results": {
                        "data": count_data,
                        "errors": errors
                    },
                    "msg": "BOQ WBS import completed successfully.",
                    "status": status.HTTP_201_CREATED,
                    "request_status": 1
                })

        # except Exception as e:
        #     raise APIException({
        #         "request_status": 0,
        #         "msg": str(e)
        #     })