from django.db.models import (
    Sum, Avg, FloatField, Value, F, Window
)
from django.db.models.functions import (
    Coalesce, FirstValue, LastValue
)
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import APIException
from django.core.paginator import Paginator
from django.conf import settings
import json

class PlantMachineryLogBookCumulative3APIView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    def get(self, request):
        fields = request.query_params.get('fields', None)
        all = request.query_params.get('all', None)
        order_by = request.query_params.get('order_by', '-id')
        if not fields:
            raise APIException({'request_status': 0, 'msg': "Require fields."})
        try:
            fields = json.loads(fields)
        except json.JSONDecodeError:
            raise APIException({'request_status': 0, 'msg': "Invalid JSON format for fields."})
        window_annotations = {}
        aggregation_fields = {}
        for field, operation in fields.items():
            if operation == 'aggregate':
                aggregation_fields[field] = Coalesce(Sum(field), Value(0), output_field=FloatField())
            elif operation == 'average':
                aggregation_fields[field] = Coalesce(Avg(field), Value(0), output_field=FloatField())
            elif operation == 'first_value':
                window_annotations[f"{field}_first"] = Window(
                    expression=FirstValue(F(field)),
                    partition_by=[F('plant_machinery_machine__id')],
                    order_by=F('log_book_date').asc()
                )
            elif operation == 'last_value':
                window_annotations[f"{field}_last"] = Window(
                    expression=LastValue(F(field)),
                    partition_by=[F('plant_machinery_machine__id')],
                    order_by=F('log_book_date').asc()
                )
        search = custom_filters(request, {}, ['fields'])
        result = PlantMachineryLogBook.cmobjects.filter(*search).values(
            'plant_machinery_machine__id',
            'plant_machinery_machine__machine_number',
            'plant_machinery_machine__equipment_description',
            'plant_machinery_machine__registration_no',
            'plant_machinery_machine__plant_machinery_group__machine_type',
            'project',
        ).annotate(**aggregation_fields).annotate(**window_annotations).distinct().order_by(*str(order_by).split(","))
        
        print("aggregation_fields ###", aggregation_fields.keys())
        print("window_annotations ###", window_annotations.keys())

        if all == 'true':
            return Response({'results': result})
        page_size = int(request.query_params.get("page_size", settings.MIN_PAGE_SIZE))
        paginator = Paginator(result, page_size)
        page_number = request.query_params.get("page", 1)
        page = paginator.get_page(page_number)

        return Response({
            "count": paginator.count,
            "next": page.next_page_number() if page.has_next() else None,
            "previous": page.previous_page_number() if page.has_previous() else None,
            "results": list(page),
        })

class PlantMachineryLogBookCumulative2APIViewBack(APIView):
    """
    Optimized API to fetch cumulative / first / last values
    machine-wise with GROUP BY support (MySQL strict mode safe).
    """

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request):

        fields_param = request.query_params.get("fields", None)
        fetch_all = request.query_params.get("all", None)
        order_by = request.query_params.get("order_by", "-plant_machinery_machine__id")

        if not fields_param:
            raise APIException({
                "request_status": 0,
                "msg": "fields parameter is required."
            })

        # Parse JSON
        try:
            fields = json.loads(fields_param)
        except json.JSONDecodeError:
            raise APIException({
                "request_status": 0,
                "msg": "Invalid JSON format for fields."
            })

        # Apply custom filters first (VERY IMPORTANT)
        search = custom_filters(request, {}, ["fields"])

        base_queryset = PlantMachineryLogBook.cmobjects.filter(*search)

        aggregation_fields = {}

        for field, operation in fields.items():

            annotation_name = f"{operation}_{field}"

            if operation == "aggregate":

                aggregation_fields[annotation_name] = Coalesce(
                    Sum(field),
                    Value(0),
                    output_field=FloatField()
                )

            elif operation == "average":

                aggregation_fields[annotation_name] = Coalesce(
                    Avg(field),
                    Value(0),
                    output_field=FloatField()
                )

            elif operation == "first_value":

                subquery = PlantMachineryLogBook.cmobjects.filter(
                    plant_machinery_machine=OuterRef("plant_machinery_machine"),
                    *search
                ).order_by("log_book_date").values(field)[:1]

                aggregation_fields[annotation_name] = Subquery(subquery)

            elif operation == "last_value":

                subquery = PlantMachineryLogBook.cmobjects.filter(
                    plant_machinery_machine=OuterRef("plant_machinery_machine"),
                    *search
                ).order_by("-log_book_date").values(field)[:1]

                aggregation_fields[annotation_name] = Subquery(subquery)

            else:
                raise APIException({
                    "request_status": 0,
                    "msg": f"Unsupported operation: {operation}"
                })

        # 🔥 Final grouped query (exact structure preserved)
        result = base_queryset.values(
            "plant_machinery_machine__id",
            "plant_machinery_machine__machine_number",
            "plant_machinery_machine__equipment_description",
            "plant_machinery_machine__registration_no",
            "plant_machinery_machine__plant_machinery_group__machine_type",
            "project",
        ).annotate(
            **aggregation_fields
        ).order_by(
            *str(order_by).split(",")
        )

        # If all data requested
        if fetch_all == "true":
            return Response({
                "results": list(result)
            })

        # Pagination
        page_size = int(
            request.query_params.get(
                "page_size",
                settings.MIN_PAGE_SIZE
            )
        )

        paginator = Paginator(result, page_size)
        page_number = request.query_params.get("page", 1)
        page = paginator.get_page(page_number)

        return Response({
            "count": paginator.count,
            "next": page.next_page_number() if page.has_next() else None,
            "previous": page.previous_page_number() if page.has_previous() else None,
            "results": list(page),
        })

indexes = [
    models.Index(
        fields=["plant_machinery_machine", "log_book_date"]
    ),
]






class PaymentMasterImportAPIView(APIView):
    """
    API for bulk import of PaymentMaster 
    """
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                count_data = {
                    'add': 0,
                    'edit': 0,
                }
                organization_id = self.request.query_params.get('organization_id', None)
                project_id = self.request.query_params.get('project_id', None)
                site_id = self.request.query_params.get('site_id', None)
                store_id = self.request.query_params.get('store_id', None)
                file_name = request.data.get('file_name', None)
                field_map = request.data.get('field_map', {})

                if not all([organization_id, project_id, site_id, file_name]):
                    raise APIException({'request_status': 0, 'msg': "Organization ID, Project ID,Site ID or file name not provided"})

                file_path = os.path.join('media/excel', file_name)
                if not os.path.exists(file_path):
                    raise APIException("File not found")

                sheet_xlsx = pd.read_excel(file_path)
                if sheet_xlsx.empty:
                    raise APIException({'request_status': 0, 'msg': 'Empty file'})

                sheet_xlsx = sheet_xlsx.fillna("").applymap(lambda x: x.strip() if isinstance(x, str) else x)
                def get_value(row, key):
                    return row.get(field_map.get(key)) or None
                def handle_date(value, default=None):
                    if pd.isna(value) or value == "":
                        return default
                    try:
                        return pd.to_datetime(value, errors='coerce').date()
                    except Exception as e:
                        return default

                def handle_float(value, default=0.0):
                    if pd.isna(value) or value == "":
                        return default
                    try:
                        return float(value)
                    except (ValueError, TypeError):
                        return default
                def handle_str(value):
                    if pd.isna(value) or value is None:
                        return None
                    if isinstance(value, float) and value.is_integer():
                        return str(int(value))
                    return str(value).strip()
                # def format_choice_field(value, choices):
                #     if not value:
                #         return None
                #     value = str(value).strip()
                #     valid_choices = [choice[0] for choice in choices]
                #     return value if value in valid_choices else None
                def format_choice_field(value, choices):
                    if not value:
                        return None
                    value_str = str(value).strip().lower()
                    choice_map = {str(choice[0]).strip().lower(): choice[0] for choice in choices}
                    return choice_map.get(value_str) 
                def process_str(x):
                    if isinstance(x, str):
                        x = x.lower().strip().replace(' ', '')
                    return x
                vendor_list = pd.DataFrame(VendorMasterV2.cmobjects.filter(
                    organization_id=organization_id
                ).annotate(pms_code = Concat(Value('pms-'), Cast(F('pk'), CharField()), output_field=CharField())).values('id', 'vendor_code','vendor_name','pms_code').distinct())
                vendor_search = {
                    'quotation__rfq_vendor_id': OuterRef('rfq_vendor_id'),
                    'quotation__is_deleted': False,
                    'quotation__latest': True,
                    'is_selected_by_cst':True,
                }
                cst_list = pd.DataFrame(CST.cmobjects.annotate(
                    l1_vendors_ids = Subquery(
                        QuotationItems.cmobjects.filter(**vendor_search).values('quotation__rfq_vendor').annotate(value=GroupConcat('quotation__vendor__pk',distinct=True)).values('value')
                    ),
                    request_code_lower=Lower('request_code')
                    ).filter(
                        organization_id=organization_id,
                        latest=True,
                        store_id=store_id,
                        project_id=project_id,
                        site_id=site_id,
                        l1_vendors_ids__isnull = False
                    ).values('id', 'request_code','l1_vendors_ids','request_code_lower').distinct())
                po_list = pd.DataFrame(PurchaseOrder.cmobjects.annotate(
                    request_code_lower=Lower('request_code')
                    ).filter(
                        organization_id=organization_id,
                        latest=True,
                        store_id=store_id,
                        project_id=project_id,
                        site_id=site_id,
                        vendor__isnull = False
                    ).values('id', 'request_code','vendor_id','request_code_lower').distinct())
                pending_request_code_list = PaymentMaster.cmobjects.filter(status='pending',
                    organization_id=organization_id,
                    store_id=store_id,
                    project_id=project_id,
                    site_id=site_id,
                    ).annotate(request_code_lower=Lower('request_code')).values_list('request_code_lower',flat=True).distinct()
                
                payment_no_list = pd.DataFrame(PaymentMaster.cmobjects.filter(
                        organization_id=organization_id,
                        store_id=store_id,
                        project_id=project_id,
                        site_id=site_id,
                    ).values('id', 'payment_no','vendor_id',).distinct())
                
                sheet_xlsx = sheet_xlsx.fillna(np.nan).replace([np.nan], [None])
                vendor_list = vendor_list.fillna(np.nan).replace([np.nan], [None])
                vendor_list = vendor_list.applymap(lambda x: process_str(x))
                vendor_list = vendor_list.replace([np.nan], [None])
                cst_list = cst_list.fillna(np.nan).replace([np.nan], [None])
                cst_list = cst_list.applymap(lambda x: process_str(x))
                cst_list = cst_list.replace([np.nan], [None])
                po_list = po_list.fillna(np.nan).replace([np.nan], [None])
                po_list = po_list.applymap(lambda x: process_str(x))
                po_list = po_list.replace([np.nan], [None])

                payment_no_list = payment_no_list.fillna(np.nan).replace([np.nan], [None])
                payment_no_list = payment_no_list.applymap(lambda x: process_str(x))
                payment_no_list = payment_no_list.replace([np.nan], [None])                

                def get_payment_through(row):
                    value = get_value(row, 'payment_through') or 'Non-CST'
                    return format_choice_field(value, PaymentMaster.PAYMENT_THROUGH_CHOICE) or 'Non-CST' 
                
                def check_vendor(row):
                    vendor_code = row.get(field_map.get('vendor'))
                    if vendor_code and 'vendor_code' in vendor_list and 'pms_code' in vendor_list:
                        vendor_code_str = process_str(str(vendor_code))
                        temp = list(vendor_list.loc[(vendor_list['vendor_code'] == vendor_code_str) | 
                                (vendor_list['pms_code'] == vendor_code_str)
                            ]['id'].items()
                        )
                        if len(temp) > 0:
                            return temp[0][1]
                    return None
              
                def check_cst(row):
                    payment_through = row.get('payment_through_value')
                    cst_request_code = row.get(field_map.get('cst_no'))
                    vendor_id = row.get('vendor_id')
                    if (payment_through == 'CST' and cst_request_code and vendor_id and 'request_code_lower' in cst_list):
                        cst_request_code_str = process_str(str(cst_request_code))
                        temp = list(
                            cst_list.loc[
                                cst_list['request_code_lower'] == cst_request_code_str
                            ][['id', 'l1_vendors_ids']].iterrows()
                        )
                        if len(temp) > 0:
                            l1_vendors_ids = temp[0][1]['l1_vendors_ids']
                            l1_vendor_list = [int(x.strip()) for x in str(l1_vendors_ids).split(',') if x.strip().isdigit()]
                            if int(vendor_id) in l1_vendor_list:
                                return temp[0][1]['id']
                    return None
                def check_po(row):
                    po_request_code = row.get(field_map.get('purchase_order'))
                    vendor_id = row.get('vendor_id')
                    if (po_request_code and vendor_id and 'request_code_lower' in po_list):
                        po_request_code_str = process_str(str(po_request_code))
                        temp = list(po_list.loc[(po_list['request_code_lower'] == po_request_code_str) & 
                            (po_list['vendor_id'] == vendor_id)
                            ]['id'].items()
                        )
                        if len(temp) > 0:
                            return temp[0][1]
                    return None 
                
                def check_payment_no(row):
                    payment_no = row.get(field_map.get('payment_no'))
                    vendor_id = row.get('vendor_id')

                    if payment_no and vendor_id and 'payment_no' in payment_no_list.columns:
                        payment_no_str = process_str(str(payment_no))

                        temp = list(
                            payment_no_list.loc[
                                (payment_no_list['payment_no'] == payment_no_str) &
                                (payment_no_list['vendor_id'] == vendor_id)
                            ]['id'].items()
                        )

                        if len(temp) > 0:
                            return True
                    return False


                for column in field_map.values():
                    if column not in sheet_xlsx.columns:
                        sheet_xlsx[column] = np.nan
                sheet_xlsx['payment_through_value'] = sheet_xlsx.apply(lambda row: get_payment_through(row), axis=1)
                sheet_xlsx['vendor_id'] = sheet_xlsx.apply(lambda row: check_vendor(row), axis=1)
                sheet_xlsx['cst_id'] = sheet_xlsx.apply(lambda row: check_cst(row), axis=1)
                sheet_xlsx['purchase_order_id'] = sheet_xlsx.apply(lambda row: check_po(row), axis=1)
                sheet_xlsx['payment_no'] = sheet_xlsx.apply(lambda row: check_payment_no(row), axis=1)

                sheet_xlsx = sheet_xlsx.replace([np.nan], [None])
                error_list = []
                for index, row in sheet_xlsx.iterrows():
                    payment_through = sheet_xlsx.at[index, 'payment_through_value']
                    vendor_id = sheet_xlsx.at[index, 'vendor_id']
                    cst_id= sheet_xlsx.at[index, 'cst_id']
                    purchase_order_id= sheet_xlsx.at[index, 'purchase_order_id']
                    request_code = get_value(row, 'request_code') or ''
                    skip = False
                    
                    payment_no_duplicate = sheet_xlsx.at[index, 'payment_no']
                    payment_no_value = get_value(row, 'payment_no')

                    if payment_no_duplicate:
                        error_list.append(
                            f"Row {index + 2}: Payment No '{payment_no_value}' already exists for this vendor"
                        )
                        skip = True


                    if request_code and str(request_code).lower() not in pending_request_code_list :
                        error_list.append(f"Row {index + 2}:{request_code}' is not in pending status")
                        skip = True   
                    if payment_through == 'CST' and not cst_id:
                        error_list.append(f"Row {index+2}: Not a valid CST tag")
                        skip = True 
                    if get_value(row, 'purchase_order') and not purchase_order_id:
                        error_list.append(f"Row {index+2}: Not a valid PO tag")
                        skip = True     
                    if not vendor_id:
                        error_list.append(f"Row {index+2}: Not a valid vendor")
                        skip = True
                    if skip:
                        continue
                    data = {
                        'vendor_id': vendor_id,
                        'cst_id': cst_id,
                        'cst_no': handle_str(get_value(row, 'cst_no')) if payment_through == 'Non-CST' else None,
                        'remarks': get_value(row, 'remarks'),
                        'amount': handle_float(get_value(row, 'amount'), 0.0),
                        'purpose': get_value(row, 'purpose'),
                        'payment_against': format_choice_field(get_value(row, 'payment_against') or 'PO', PaymentMaster.PAYMENT_AGAINST_CHOICE) or 'PO',
                        'payment_no': get_value(row, 'payment_no'),
                        'purchase_order_id':purchase_order_id,
                        'date': handle_date(get_value(row, 'date'), None),
                        'payment_through': payment_through,
                        'is_advance_payment': format_choice_field(get_value(row, 'is_advance_payment') or None, PaymentMaster.ADVANCE_PAYMENT_CHOICE) or None,


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
                    else:
                        instance.updated_by_id = request.user.id
                    instance.save()    
                    count_data['add' if created else 'edit'] += 1
                   
                return Response({
                    'results': {'Data': count_data},
                    'errors': error_list,
                    'msg': 'Successfully imported',
                    
                    'status': status.HTTP_201_CREATED,
                    "request_status": 1
                })
        except Exception as e:
            error_message = str(e.args[0]) if e.args else str(e)
            raise APIException({'request_status': 0, 'msg': error_message})       
        

class PlantMachineryLogBookCumulative3APIView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request):

        fields = request.query_params.get('fields')
        all_data = request.query_params.get('all')
        order_by = request.query_params.get('order_by', 'plant_machinery_machine__id')

        if not fields:
            raise APIException({'request_status': 0, 'msg': 'Require fields'})

        try:
            fields = json.loads(fields)
        except Exception:
            raise APIException({'request_status': 0, 'msg': 'Invalid JSON for fields'})

        # -----------------------------------
        # Containers
        # -----------------------------------
        aggregation_fields = {}
        window_annotations = {}
        window_fields = []   # 👈 IMPORTANT

        # -----------------------------------
        # Build dynamic annotations
        # -----------------------------------
        for field, operation in fields.items():

            # ---------- AGGREGATE ----------
            if operation == 'aggregate':
                aggregation_fields[field] = Coalesce(
                    Sum(field),
                    Value(0),
                    output_field=FloatField()
                )

            # ---------- AVERAGE ----------
            elif operation == 'average':
                aggregation_fields[field] = Coalesce(
                    Avg(field),
                    Value(0),
                    output_field=FloatField()
                )

            # ---------- FIRST VALUE ----------
            elif operation == 'first_value':
                alias = f"{field}_first"
                window_annotations[alias] = Window(
                    expression=FirstValue(F(field)),
                    partition_by=[F('plant_machinery_machine_id')],
                    order_by=F('log_book_date').asc()
                )
                window_fields.append(alias)

            # ---------- LAST VALUE ----------
            elif operation == 'last_value':
                alias = f"{field}_last"
                window_annotations[alias] = Window(
                    expression=LastValue(F(field)),
                    partition_by=[F('plant_machinery_machine_id')],
                    order_by=F('log_book_date').asc()
                )
                window_fields.append(alias)

        # -----------------------------------
        # Filters (project, date range, etc.)
        # -----------------------------------
        search = custom_filters(request, {}, ['fields'])

        # -----------------------------------
        # Base fields (GROUP BY)
        # -----------------------------------
        base_values = [
            'plant_machinery_machine__id',
            'plant_machinery_machine__machine_number',
            'plant_machinery_machine__equipment_description',
            'plant_machinery_machine__registration_no',
            'plant_machinery_machine__plant_machinery_group__machine_type',
            'project',
        ]

        # -----------------------------------
        # FINAL QUERY (Single SQL)
        # -----------------------------------
        queryset = (
            PlantMachineryLogBook.cmobjects
            .filter(*search)
            .annotate(**window_annotations)
            .values(*base_values, *window_fields)   # 👈 window fields INCLUDED
            .annotate(**aggregation_fields)
            .order_by(*str(order_by).split(','))
        )

        # -----------------------------------
        # OPTIONAL: Rename window fields
        # (Clean API response)
        # -----------------------------------
        queryset = queryset.annotate(
            start_kms=F('start_kms_first'),
            close_kms=F('close_kms_last'),
            start_hrs=F('start_hrs_first'),
            close_hrs=F('close_hrs_last'),
            from_chainage=F('from_chainage_first'),
            to_chainage=F('to_chainage_last'),
        )

        # -----------------------------------
        # Response
        # -----------------------------------
        if all_data == 'true':
            return Response({'results': list(queryset)})

        page_size = int(request.query_params.get('page_size', settings.MIN_PAGE_SIZE))
        paginator = Paginator(queryset, page_size)
        page = paginator.get_page(request.query_params.get('page', 1))

        return Response({
            'count': paginator.count,
            'next': page.next_page_number() if page.has_next() else None,
            'previous': page.previous_page_number() if page.has_previous() else None,
            'results': list(page),
        })
