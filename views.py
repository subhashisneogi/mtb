@receiver(post_save, sender=WBSList)
def handle_wbs_chainage(sender, instance, created, **kwargs):

    change_lmpi_data(instance.id, instance.budgeted_quantity)

    if not instance.boq:
        return

    # Root WBS chainage creation
    if created and instance.parent is None:
        BOQChainage.objects.get_or_create(
            organization=instance.organization,
            boq=instance.boq,
            wbs=instance,
            defaults={
                "name": f"CH-{instance.boq.id}-{instance.pk}",
                "start": 0,
                "end": 1
            }
        )

    # Child WBS logic
    if instance.parent and instance.root:

        parent_chainage = BOQChainage.cmobjects.filter(
            boq=instance.boq,
            wbs=instance.root
        ).first()

        if not parent_chainage:
            return

        # Create chainage code only on create
        if created:
            auto_value = generate_chainage_code(instance)

            BOQChainageExecutiveSummeryData.objects.get_or_create(
                organization=instance.organization,
                boq=instance.boq,
                wbs=instance,
                type="C",
                defaults={
                    "value": auto_value,
                    "form": parent_chainage
                }
            )

        # Handle Quantity (Q type) for BOTH create and update
        if instance.budgeted_quantity is not None:

            qty_obj, created_q = BOQChainageExecutiveSummeryData.objects.get_or_create(
                organization=instance.organization,
                boq=instance.boq,
                wbs=instance,
                type="Q",
                defaults={
                    "value": instance.budgeted_quantity,
                    "form": parent_chainage
                }
            )

            # If already exists then update value
            if not created_q:
                if qty_obj.value != str(instance.budgeted_quantity):
                    qty_obj.value = instance.budgeted_quantity
                    qty_obj.save(update_fields=["value"])
    

class BOQWBSImportAPIView(APIView):
    """
    BOQ WBS Import API
    """
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):

        try:
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

                required_columns = [
                    field_map["boq_code"],
                    field_map["boq_no"],
                    field_map["wbs"]
                ]

                for col in required_columns:
                    if col not in df.columns:
                        raise APIException(f"Missing required column in Excel: {col}")

                df = df.where(pd.notnull(df), None)

                df = df.apply(lambda col: col.map(lambda x: x.strip() if isinstance(x, str) else x))

                for num_field in ["rate", "budgeted_quantity"]:
                    if num_field in field_map:
                        df[field_map[num_field]] = pd.to_numeric(
                            df[field_map[num_field]], errors="coerce"
                        )

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

                # Fetch existing WBS records once
                existing_wbs_qs = WBSList.objects.filter(
                    organization_id=organization_id,
                    boq_id=boq_id,
                    root_id=wbs_list_id
                ).values("id", "boq_code")

                existing_wbs_map = {
                    str(obj["boq_code"]).strip(): obj["id"]
                    for obj in existing_wbs_qs if obj["boq_code"]
                }

                # Track duplicates inside Excel
                excel_code_map = {}

                # Fetch UOM list
                uom_list = pd.DataFrame(
                    UnitOfMesurement.cmobjects.filter(
                        organization_id=organization_id
                    ).values("id", "formal_name", "symbol")
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

                for index, row in df.iterrows():

                    row_index = index + 2

                    boq_code = row.get(field_map["boq_code"])
                    boq_no = row.get(field_map["boq_no"])
                    wbs_name = row.get(field_map["wbs"])

                    if not boq_code or not boq_no or not wbs_name:
                        errors.append(
                            f"Row {row_index}: boq_code, boq_no and WBS name are required"
                        )
                        count_data["errors"] += 1
                        continue

                    boq_code = str(boq_code).strip()

                    if not re.fullmatch(r"\d+(?:\.\d+)*", boq_code):
                        errors.append(
                            f"Row {row_index}: BOQ code must be format like 1, 1.1, 1.2"
                        )
                        count_data["errors"] += 1
                        continue

                    # Excel duplicate validation
                    if boq_code in excel_code_map:
                        first_row = excel_code_map[boq_code]
                        errors.append(
                            f"Row {row_index}: BOQ code '{boq_code}' already used in Row {first_row}"
                        )
                        count_data["errors"] += 1
                        continue
                    else:
                        excel_code_map[boq_code] = row_index

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

                    existing_id = existing_wbs_map.get(boq_code)

                    if existing_id:

                        WBSList.cmobjects.filter(
                            pk=existing_id,
                            organization_id=organization_id
                        ).update(
                            updated_by_id=request.user.id,
                            **data
                        )

                        created_map[boq_code] = existing_id
                        count_data["items_updated"] += 1

                    else:

                        instance = WBSList.objects.create(
                            created_by_id=request.user.id,
                            **data
                        )

                        created_map[boq_code] = instance.id
                        existing_wbs_map[boq_code] = instance.id
                        count_data["items_created"] += 1

                return Response(
                    {
                        "data": count_data,
                        "errors": errors,
                        "msg": "BOQ WBS import completed successfully.",
                        "status": status.HTTP_201_CREATED,
                        "request_status": 1,
                    }
                )

        except Exception as e:

            error_message = str(e.args[0]) if e.args else str(e)
            print(e)

            raise APIException({
                "request_status": 0,
                "msg": error_message
            })


