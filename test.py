#models.py
class WBSList(BaseAbstractStructure):
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
    budgeted_quantity = models.FloatField(default=0)
    rate = models.CharField(max_length=255,null=True, blank=True)
    uom = models.ForeignKey(UnitOfMesurement, related_name='wbs_list_uom', on_delete=models.CASCADE,
                              null=True, blank=True)
    total_labour = models.CharField(max_length=255,null=True, blank=True)
    total_material = models.CharField(max_length=255,null=True, blank=True)
    total_machinery = models.CharField(max_length=255,null=True, blank=True)
    total_overheads = models.CharField(max_length=255,null=True, blank=True)
    root = models.ForeignKey('self', related_name='root_node', on_delete=models.CASCADE,null=True, blank=True)

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
@receiver(pre_save, sender=WBSList)
def wbs_validate_unique(sender, instance, **kwargs):
    if not instance.organization_id or not instance.boq_id or not instance.boq_code:
        return
    root_id = instance.root_id or (instance.root.pk if instance.root else None)
    if not root_id:
        return
    qs = WBSList.cmobjects.filter(organization_id=instance.organization_id,boq_id=instance.boq_id,root_id=root_id,boq_code=instance.boq_code)
    if instance.pk:
        qs = qs.exclude(pk=instance.pk)
    if qs.exists():
        raise APIException({
            'request_status': 0,
            'msg': f"WBS: BOQ Code {instance.boq_code} must be unique per BOQ"
        })

@receiver(post_save, sender=WBSList)
def handle_wbs_chainage(sender, instance, created, **kwargs):
    change_lmpi_data(instance.id,instance.budgeted_quantity)
    if not instance.boq:
        return
    if created and instance.parent is None:
        BOQChainage.objects.get_or_create(organization=instance.organization,boq=instance.boq,wbs=instance,
            defaults={"name": f"CH-{instance.boq.id}-{instance.pk}","start": 0,"end": 1})
    if instance.parent and instance.root:
        parent_chainage = BOQChainage.cmobjects.filter(boq=instance.boq, wbs=instance.root).first()
        if not parent_chainage:
            return
        if created:
            auto_value = generate_chainage_code(instance)
            BOQChainageExecutiveSummeryData.objects.get_or_create(organization=instance.organization,boq=instance.boq,wbs=instance,type="C", value__isnull=True, 
                defaults={"value": auto_value,"form": parent_chainage})
        if instance.budgeted_quantity:
            qty_obj, created_q = BOQChainageExecutiveSummeryData.objects.get_or_create(
                organization=instance.organization,boq=instance.boq,wbs=instance,type="Q",defaults={"value": instance.budgeted_quantity,"form": parent_chainage,})
            if not created_q:
                qty_obj.value = instance.budgeted_quantity
                qty_obj.save(update_fields=["value"])

#views.py
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
                    "items_created": 0,
                    "items_updated": 0,
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

                required_columns = [field_map["boq_code"], field_map["boq_no"], field_map["wbs"]]
                for col in required_columns:
                    if col not in df.columns:
                        raise APIException(f"Missing required column in Excel: {col}")

                df = df.where(pd.notnull(df), None)
                df = df.apply(lambda col: col.map(lambda x: x.strip() if isinstance(x, str) else x))
                for num_field in ["rate", "budgeted_quantity"]:
                    if num_field in field_map:
                        df[field_map[num_field]] = pd.to_numeric(df[field_map[num_field]], errors="coerce")

                def process_str(x):
                    if isinstance(x, str):
                        return x.lower().strip().replace(" ", "")
                    return x
                
                def get_parent_code(code):
                    if not code:
                        return None
                    code = str(code).strip()
                    if "." in code:
                        return ".".join(code.split(".")[:-1])
                    return None
                 
                existing_wbs_qs = WBSList.objects.filter(
                    organization_id=organization_id, boq_id=boq_id
                ).values("id", "boq_code")
                existing_wbs_map = {str(obj["boq_code"]).strip(): obj["id"] for obj in existing_wbs_qs if obj["boq_code"]}
                uom_list = pd.DataFrame(
                    UnitOfMesurement.cmobjects.filter(organization_id=organization_id).values("id", "formal_name", "symbol")
                )
                uom_list = uom_list.fillna(np.nan).replace([np.nan], [None])
                uom_list["symbol"] = uom_list["symbol"].map(lambda x: process_str(x))
                def check_uom(row):
                    if "uom" in field_map:
                        uom_value = row.get(field_map["uom"])
                        if uom_value:
                            symbol = process_str(uom_value)
                            match = uom_list.loc[uom_list["symbol"] == symbol]
                            if not match.empty:
                                return int(match.iloc[0]["id"])
                    return None

                df["uom_id"] = df.apply(check_uom, axis=1)
                created_map = {}
                df = df.replace([np.nan], [None])
                check_root = WBSList.cmobjects.filter(root_id=wbs_list_id, parent__isnull=False).first()
                print("DYWGDYWVYVV")
                for index, row in df.iterrows():
                    row_index = index + 2
                    boq_code = row.get(field_map["boq_code"])
                    boq_no = row.get(field_map["boq_no"])
                    wbs_name = row.get(field_map["wbs"])
                    
                    
                    if not boq_code or not boq_no or not wbs_name:
                        errors.append(f"Row {row_index}: boq_code, boq_no, and Particulars are required")
                        count_data["errors"] += 1
                        continue
                    boq_code = str(boq_code).strip()
                    if not re.fullmatch(r"\d+(?:\.\d+)*", boq_code):
                        errors.append(f"Row {row_index}: BOQ code must be format like - 1, 1.1, 1.2 etc.")
                        count_data["errors"] += 1
                        continue
  
                    if boq_code in existing_wbs_map:
                        wbs_id = existing_wbs_map[boq_code]
                        duplicate = WBSList.cmobjects.filter(
                            boq_id=boq_id, boq_code=boq_code, root_id=wbs_list_id
                        ).exclude(id=wbs_id).exists()
                    else:
                        duplicate = WBSList.cmobjects.filter(
                            boq_id=boq_id, boq_code=boq_code, root_id=wbs_list_id
                        ).exists()
                    if duplicate:
                        errors.append(f"Row {row_index}: BOQ code - {boq_code} must be unique per BOQ")
                        count_data["errors"] += 1
                        continue

                    quantity = row.get(field_map.get("budgeted_quantity"))
                    rate = row.get(field_map.get("rate"))

                    parent_id = wbs_list_id
                    parent_code = get_parent_code(boq_code)
                    if parent_code:
                        if parent_code in created_map:
                            parent_id = created_map[parent_code]
                        elif parent_code in existing_wbs_map:
                            parent_id = existing_wbs_map[parent_code]
                    data = {
                        "organization_id": organization_id,
                        "boq_id": boq_id,
                        "parent_id": parent_id,
                        "uom_id": None if pd.isna(row["uom_id"]) else row["uom_id"],
                        "boq_code": boq_code,
                        "boq_no": boq_no,
                        "wbs": wbs_name,
                        "rate": float(rate) if rate and not pd.isna(rate) else 0,
                        "budgeted_quantity": float(quantity) if quantity and not pd.isna(quantity) else 0,
                        "total_labour": row.get(field_map.get("total_labour")),
                        "total_material": row.get(field_map.get("total_material")),
                        "total_machinery": row.get(field_map.get("total_machinery")),
                        "total_overheads": row.get(field_map.get("total_overheads")),
                    }
                    if boq_code in existing_wbs_map and check_root:
                        wbs_id = existing_wbs_map[boq_code]
                        WBSList.cmobjects.filter(pk=wbs_id, organization_id=organization_id).update(
                            updated_by_id=request.user.id, **data
                        )
                        created_map[boq_code] = wbs_id
                        if quantity:
                            BOQChainageExecutiveSummeryData.cmobjects.filter(organization_id=organization_id,boq_id=boq_id, 
                                            wbs_id=wbs_id, type="Q").update(value=quantity)
                        count_data["items_updated"] += 1
                    else:
                        instance = WBSList.objects.create(created_by_id=request.user.id, **data)
                        created_map[boq_code] = instance.id
                        count_data["items_created"] += 1
                    print("boq_code", boq_code)
                    print("existing_wbs_map", existing_wbs_map)
                    # if boq_code in existing_wbs_map:
                    #     wbs_id = existing_wbs_map[boq_code]
                    #     wbs_qs = WBSList.cmobjects.filter(
                    #         pk=wbs_id,
                    #         organization_id=organization_id,
                    #         boq_id=boq_id,
                    #         root_id=wbs_list_id,
                    #         parent__isnull=False
                    #     )
                    #     print("wbs_qs####", wbs_qs)
                    #     if wbs_qs.exists():
                    #         wbs_qs.update(updated_by_id=request.user.id, **data)
                    #         created_map[boq_code] = wbs_id
                    #         if quantity:
                    #             BOQChainageExecutiveSummeryData.cmobjects.update_or_create(
                    #                 organization_id=organization_id,
                    #                 boq_id=boq_id,
                    #                 wbs_id=wbs_id,
                    #                 type="Q",
                    #                 defaults={"value": data["budgeted_quantity"]}
                    #             )
                    #         count_data["items_updated"] += 1
                    #     else:
                    #         instance = WBSList.objects.create(created_by_id=request.user.id, **data)
                    #         created_map[boq_code] = instance.id
                    #         count_data["items_created"] += 1

                return Response(
                    {
                        "data": count_data,
                        "errors": errors,
                        "msg": "BOQ WBS import completed successfully.",
                        "status": status.HTTP_201_CREATED,
                        "request_status": 1,
                    }
                )
        # except Exception as e:
        #     error_message = str(e.args[0]) if e.args else str(e)
        #     print(e)
        #     raise APIException({'request_status': 0, 'msg': error_message})


here logic is WBSList data update and create is handle by 
pk=wbs_id, organization_id=organization_id, root_id=wbs_list_id
each root_id can not take the duplicate boq_code

excel data is import for each  wbs_list id which  parent__isnull=False  
please write proper complete optimized way  code
avoid query inside the loop
