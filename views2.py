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


# @receiver(post_save, sender=WBSList)
# def signal_update_wbs_list(sender, instance, created, **kwargs):
#     change_lmpi_data(instance.id,instance.budgeted_quantity)
#     if instance.boq and created:
#         if instance.parent is None:
#             BOQChainage.objects.get_or_create(boq=instance.boq, wbs=instance, organization=instance.organization, defaults={
#                 "name": f"CH-{instance.boq.id}-{instance.pk}",  "start": 0,"end": 1,})
#         elif instance.parent:
#             parent_chainage_id = BOQChainage.cmobjects.filter(boq=instance.boq, wbs=instance.root_id).values_list('id', flat=True).first()
#             auto_value = generate_chainage_code(instance)
#             print("parent_chainage_id ###", parent_chainage_id)
#             BOQChainageExecutiveSummeryData.objects.get_or_create(boq=instance.boq, wbs=instance, value__isnull=True,  
#                 defaults={"organization": instance.organization, "type": "C", "value": auto_value, 'form_id' : parent_chainage_id})
	

