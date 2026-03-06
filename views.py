class BOQWBSImportAPIView(APIView):
    """
    Optimized BOQ WBS Import API
    """

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):

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
            field_map = request.data.get("field_map")

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

            df = df.where(pd.notnull(df), None)

            required_columns = [
                field_map["boq_code"],
                field_map["boq_no"],
                field_map["wbs"]
            ]

            for col in required_columns:
                if col not in df.columns:
                    raise APIException(f"Missing required column: {col}")

            df = df.apply(lambda col: col.map(lambda x: x.strip() if isinstance(x, str) else x))

            def get_parent_code(code):

                if not code:
                    return None

                code = str(code).strip()

                if "." in code:
                    return ".".join(code.split(".")[:-1])

                return None

            # -------------------------------
            # PRELOAD EXISTING WBS
            # -------------------------------

            existing_wbs = WBSList.cmobjects.filter(
                organization_id=organization_id,
                boq_id=boq_id,
                root_id=wbs_list_id
            ).values("id", "boq_code")

            existing_wbs_map = {
                str(i["boq_code"]).strip(): i["id"]
                for i in existing_wbs if i["boq_code"]
            }

            # -------------------------------
            # PRELOAD UOM
            # -------------------------------

            uom_list = UnitOfMesurement.cmobjects.filter(
                organization_id=organization_id
            ).values("id", "symbol")

            uom_map = {
                str(i["symbol"]).lower().strip(): i["id"]
                for i in uom_list if i["symbol"]
            }

            created_map = {}

            create_list = []
            update_list = []

            # -------------------------------
            # PROCESS EXCEL
            # -------------------------------

            for index, row in df.iterrows():

                row_index = index + 2

                boq_code = row.get(field_map["boq_code"])
                boq_no = row.get(field_map["boq_no"])
                wbs_name = row.get(field_map["wbs"])

                if not boq_code or not boq_no or not wbs_name:

                    errors.append(
                        f"Row {row_index}: boq_code, boq_no and wbs required"
                    )

                    count_data["errors"] += 1
                    continue

                boq_code = str(boq_code).strip()

                if not re.fullmatch(r"\d+(\.\d+)*", boq_code):

                    errors.append(
                        f"Row {row_index}: invalid BOQ code format"
                    )

                    count_data["errors"] += 1
                    continue

                parent_id = wbs_list_id

                parent_code = get_parent_code(boq_code)

                if parent_code:

                    if parent_code in created_map:
                        parent_id = created_map[parent_code]

                    elif parent_code in existing_wbs_map:
                        parent_id = existing_wbs_map[parent_code]

                quantity = row.get(field_map.get("budgeted_quantity"))
                rate = row.get(field_map.get("rate"))

                uom_value = row.get(field_map.get("uom"))

                uom_id = None

                if uom_value:
                    symbol = str(uom_value).lower().strip()
                    uom_id = uom_map.get(symbol)

                record_data = {

                    "organization_id": organization_id,
                    "boq_id": boq_id,
                    "root_id": wbs_list_id,
                    "parent_id": parent_id,

                    "boq_code": boq_code,
                    "boq_no": boq_no,
                    "wbs": wbs_name,

                    "uom_id": uom_id,

                    "rate": float(rate) if rate else 0,
                    "budgeted_quantity": float(quantity) if quantity else 0,

                    "total_labour": row.get(field_map.get("total_labour")),
                    "total_material": row.get(field_map.get("total_material")),
                    "total_machinery": row.get(field_map.get("total_machinery")),
                    "total_overheads": row.get(field_map.get("total_overheads")),
                }

                # -------------------------------
                # UPDATE
                # -------------------------------

                if boq_code in existing_wbs_map:

                    wbs_id = existing_wbs_map[boq_code]

                    update_list.append(
                        WBSList(
                            id=wbs_id,
                            updated_by_id=request.user.id,
                            **record_data
                        )
                    )

                    created_map[boq_code] = wbs_id

                    count_data["items_updated"] += 1

                # -------------------------------
                # CREATE
                # -------------------------------

                else:

                    obj = WBSList(
                        created_by_id=request.user.id,
                        **record_data
                    )

                    create_list.append(obj)

                    created_map[boq_code] = obj

                    count_data["items_created"] += 1

            # -------------------------------
            # BULK CREATE
            # -------------------------------

            if create_list:

                created_objs = WBSList.objects.bulk_create(
                    create_list,
                    batch_size=500
                )

                for obj in created_objs:
                    created_map[obj.boq_code] = obj.id

            # -------------------------------
            # BULK UPDATE
            # -------------------------------

            if update_list:

                WBSList.objects.bulk_update(
                    update_list,
                    [
                        "parent",
                        "boq_code",
                        "boq_no",
                        "wbs",
                        "uom",
                        "rate",
                        "budgeted_quantity",
                        "total_labour",
                        "total_material",
                        "total_machinery",
                        "total_overheads",
                    ],
                    batch_size=500
                )

            return Response(
                {
                    "data": count_data,
                    "errors": errors,
                    "msg": "BOQ WBS import completed successfully",
                    "request_status": 1,
                },
                status=status.HTTP_201_CREATED
            )
