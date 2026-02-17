
def to_python_value(value):
    if isinstance(value, np.ndarray):
        return value.item() if value.size > 0 else None
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, pd.Timestamp):
        return value.date()
    return value


class PaymentMasterImportAPIView(APIView):
    """
    API for bulk import of PaymentMaster 
    """
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        try:
            with transaction.atomic():

                count_data = {'add': 0, 'edit': 0}

                organization_id = request.query_params.get('organization_id')
                project_id = request.query_params.get('project_id')
                site_id = request.query_params.get('site_id')
                store_id = request.query_params.get('store_id')
                file_name = request.data.get('file_name')
                field_map = request.data.get('field_map', {})

                if not all([organization_id, project_id, site_id, file_name]):
                    raise APIException("Required parameters missing")

                file_path = os.path.join('media/excel', file_name)

                if not os.path.exists(file_path):
                    raise APIException("File not found")

                sheet_xlsx = pd.read_excel(file_path)

                if sheet_xlsx.empty:
                    raise APIException("Empty file")

                sheet_xlsx = sheet_xlsx.fillna("").applymap(
                    lambda x: x.strip() if isinstance(x, str) else x
                )

                def get_value(row, key):
                    column = field_map.get(key)
                    if not column:
                        return None
                    value = row.get(column)
                    return to_python_value(value)

                def handle_date(value):
                    if not value:
                        return None
                    return pd.to_datetime(value, errors='coerce').date()

                def handle_float(value, default=0.0):
                    if not value:
                        return default
                    try:
                        return float(value)
                    except:
                        return default

                def handle_str(value):
                    if not value:
                        return None
                    return str(value).strip()

                def format_choice_field(value, choices):
                    if not value:
                        return None
                    value_str = str(value).strip().lower()
                    choice_map = {c[0].lower(): c[0] for c in choices}
                    return choice_map.get(value_str)

                # Convert queryset to set (safe membership check)
                pending_request_code_list = set(
                    PaymentMaster.cmobjects.filter(
                        status='pending',
                        organization_id=organization_id,
                        store_id=store_id,
                        project_id=project_id,
                        site_id=site_id,
                    ).annotate(
                        request_code_lower=Lower('request_code')
                    ).values_list('request_code_lower', flat=True)
                )

                error_list = []

                for index, row in sheet_xlsx.iterrows():

                    request_code = get_value(row, 'request_code')
                    request_code = str(request_code).strip() if request_code else ''

                    if request_code != '' and request_code.lower() not in pending_request_code_list:
                        error_list.append(
                            f"Row {index+2}: {request_code} not in pending status"
                        )
                        continue

                    vendor_id = get_value(row, 'vendor_id')
                    vendor_id = int(vendor_id) if vendor_id else None

                    cst_id = get_value(row, 'cst_id')
                    cst_id = int(cst_id) if cst_id else None

                    purchase_order_id = get_value(row, 'purchase_order_id')
                    purchase_order_id = int(purchase_order_id) if purchase_order_id else None

                    payment_through = format_choice_field(
                        get_value(row, 'payment_through'),
                        PaymentMaster.PAYMENT_THROUGH_CHOICE
                    ) or 'Non-CST'

                    data = {
                        'vendor_id': vendor_id,
                        'cst_id': cst_id,
                        'cst_no': handle_str(get_value(row, 'cst_no')) if payment_through == 'Non-CST' else None,
                        'remarks': get_value(row, 'remarks'),
                        'amount': float(handle_float(get_value(row, 'amount'), 0.0)),
                        'purpose': get_value(row, 'purpose'),
                        'payment_against': format_choice_field(
                            get_value(row, 'payment_against') or 'PO',
                            PaymentMaster.PAYMENT_AGAINST_CHOICE
                        ) or 'PO',
                        'payment_no': get_value(row, 'payment_no'),
                        'purchase_order_id': purchase_order_id,
                        'date': handle_date(get_value(row, 'date')),
                        'payment_through': payment_through,
                        'is_advance_payment': format_choice_field(
                            get_value(row, 'is_advance_payment'),
                            PaymentMaster.ADVANCE_PAYMENT_CHOICE
                        ),
                    }

                    instance, created = PaymentMaster.cmobjects.update_or_create(
                        organization_id=organization_id,
                        store_id=store_id,
                        project_id=project_id,
                        site_id=site_id,
                        request_code=request_code,
                        latest=True,
                        defaults=data
                    )

                    if created:
                        instance.created_by_id = request.user.id
                        count_data['add'] += 1
                    else:
                        instance.updated_by_id = request.user.id
                        count_data['edit'] += 1

                    instance.save()

                return Response({
                    "results": count_data,
                    "errors": error_list,
                    "msg": "Successfully imported",
                    "request_status": 1
                }, status=status.HTTP_201_CREATED)

        except Exception as e:
            raise APIException(str(e))


class PlantMachineryLogBookCumulative2APIView(APIView):
    """
    API to fetch cumulative or starting values based on machine.
    """
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    def get(self, request):
        fields = request.query_params.get('fields', None)
        all_data = request.query_params.get('all', None)
        order_by = request.query_params.get('order_by', '-id')
        if fields:
            try:
                fields = json.loads(fields)
            except json.JSONDecodeError:
                raise APIException(
                    {'request_status': 0, 'msg': "Invalid JSON format for fields."}
                )
        else:
            fields = {}
        aggregation_fields = {}
        for field, operation in fields.items():
            exp = None
            if operation == 'aggregate':
                exp = Coalesce(
                    Sum(field),
                    Value(0),
                    output_field=FloatField()
                )
            elif operation == 'average':
                exp = Coalesce(
                    Avg(field),
                    Value(0),
                    output_field=FloatField()
                )
            elif operation == 'first_value':
                exp = Window(
                    expression=FirstValue(field),
                    partition_by=[F('plant_machinery_machine__id')],
                    order_by=F('log_book_date').asc()
                )
            elif operation == 'last_value':
                exp = Window(
                    expression=FirstValue(field),
                    partition_by=[F('plant_machinery_machine__id')],
                    order_by=F('log_book_date').desc()
                )
            if exp is not None:
                aggregation_fields[f"{field}_calculated"] = exp
        search = custom_filters(request, {}, ['fields'])
        queryset = PlantMachineryLogBook.cmobjects.filter(*search)
        if aggregation_fields:
            queryset = queryset.annotate(**aggregation_fields)
        queryset = queryset.values(
            'plant_machinery_machine__id',
            'plant_machinery_machine__machine_number',
            'plant_machinery_machine__equipment_description',
            'plant_machinery_machine__registration_no',
            'plant_machinery_machine__plant_machinery_group__machine_type',
            'project',
            *aggregation_fields.keys()
        )
        queryset = queryset.distinct().order_by(
            *str(order_by).split(",")
        )
        if all_data == 'true':
            return Response({'results': list(queryset)})

        page_size = int(request.query_params.get("page_size", settings.MIN_PAGE_SIZE))
        paginator = Paginator(queryset, page_size)
        page_number = request.query_params.get("page", 1)
        page = paginator.get_page(page_number)

        return Response(
            {
                "count": paginator.count,
                "next": page.next_page_number() if page.has_next() else None,
                "previous": page.previous_page_number() if page.has_previous() else None,
                "results": list(page),
            }
        )