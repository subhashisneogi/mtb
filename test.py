
class PlantMachineryLogBookCumulative2APIView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        fields = request.query_params.get('fields')
        all_records = request.query_params.get('all')
        order_by = request.query_params.get('order_by', '-id')

        if not fields:
            raise APIException({'request_status': 0, 'msg': 'fields is required'})

        try:
            fields = json.loads(fields)
        except json.JSONDecodeError:
            raise APIException({'request_status': 0, 'msg': 'Invalid JSON format for fields'})

        search = custom_filters(request, {}, ['fields'])

        # ----------------------------------
        # WINDOW EXPRESSIONS
        # ----------------------------------
        window_annotations = {}
        aggregate_annotations = {}

        for field, operation in fields.items():
            if operation == 'first_value':
                window_annotations[f'{field}_first'] = Window(
                    expression=FirstValue(field),
                    partition_by=[F('plant_machinery_machine_id')],
                    order_by=F('log_book_date').asc(),
                )

            elif operation == 'last_value':
                window_annotations[f'{field}_last'] = Window(
                    expression=LastValue(field),
                    partition_by=[F('plant_machinery_machine_id')],
                    order_by=F('log_book_date').asc(),
                )

            elif operation == 'aggregate':
                window_annotations[field] = Window(
                    expression=Coalesce(
                        Sum(field), Value(0), output_field=FloatField()
                    ),
                    partition_by=[F('plant_machinery_machine_id')],
                )

            elif operation == 'average':
                window_annotations[field] = Window(
                    expression=Coalesce(
                        Avg(field), Value(0), output_field=FloatField()
                    ),
                    partition_by=[F('plant_machinery_machine_id')],
                )

        # ----------------------------------
        # ROW NUMBER (KEY FIX)
        # ----------------------------------
        qs = (
            PlantMachineryLogBook.cmobjects
            .filter(*search)
            .select_related('plant_machinery_machine')
            .annotate(
                rn=Window(
                    expression=RowNumber(),
                    partition_by=[F('plant_machinery_machine_id')],
                    order_by=F('log_book_date').desc(),
                ),
                **window_annotations
            )
            .filter(rn=1)   # 👈 ONE ROW PER MACHINE
            .values(
                'plant_machinery_machine__id',
                'plant_machinery_machine__machine_number',
                'plant_machinery_machine__equipment_description',
                'plant_machinery_machine__registration_no',
                'plant_machinery_machine__plant_machinery_group__machine_type',
                'project',
                *window_annotations.keys(),
            )
            .order_by(*order_by.split(','))
        )

        # ----------------------------------
        # RESPONSE
        # ----------------------------------
        if all_records == 'true':
            return Response({'results': list(qs)})

        paginator = Paginator(
            qs,
            int(request.query_params.get('page_size', settings.MIN_PAGE_SIZE))
        )
        page = paginator.get_page(request.query_params.get('page', 1))

        return Response({
            'count': paginator.count,
            'next': page.next_page_number() if page.has_next() else None,
            'previous': page.previous_page_number() if page.has_previous() else None,
            'results': list(page),
        })



class PlantMachineryLogBookCumulative2APIView001(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        fields = request.query_params.get('fields')
        all_records = request.query_params.get('all')
        order_by = request.query_params.get('order_by', '-id')

        if not fields:
            raise APIException({'request_status': 0, 'msg': 'fields is required'})

        try:
            fields = json.loads(fields)
        except json.JSONDecodeError:
            raise APIException({'request_status': 0, 'msg': 'Invalid JSON format for fields'})

        search = custom_filters(request, {}, ['fields'])

        qs = (
            PlantMachineryLogBook.cmobjects
            .filter(*search)
            .select_related('plant_machinery_machine')
        )

        # ----------------------------
        # Aggregations (FAST)
        # ----------------------------
        annotations = {
            'first_date': Min('log_book_date'),
            'last_date': Max('log_book_date'),
        }

        for field, operation in fields.items():
            if operation == 'aggregate':
                annotations[field] = Coalesce(Sum(field), Value(0), output_field=FloatField())
            elif operation == 'average':
                annotations[field] = Coalesce(Avg(field), Value(0), output_field=FloatField())

        base = (
            qs.values(
                'plant_machinery_machine__id',
                'plant_machinery_machine__machine_number',
                'plant_machinery_machine__equipment_description',
                'plant_machinery_machine__registration_no',
                'plant_machinery_machine__plant_machinery_group__machine_type',
                'project',
            )
            .annotate(**annotations)
        )

        # ----------------------------
        # Fetch first & last values (INDEXED)
        # ----------------------------
        first_map = {}
        last_map = {}

        first_rows = (
            PlantMachineryLogBook.cmobjects
            .filter(*search)
            .values('plant_machinery_machine_id')
            .annotate(first_date=Min('log_book_date'))
        )

        last_rows = (
            PlantMachineryLogBook.cmobjects
            .filter(*search)
            .values('plant_machinery_machine_id')
            .annotate(last_date=Max('log_book_date'))
        )

        if 'start_hrs' in fields:
            for r in first_rows:
                first_map[r['plant_machinery_machine_id']] = (
                    PlantMachineryLogBook.cmobjects
                    .filter(
                        plant_machinery_machine_id=r['plant_machinery_machine_id'],
                        log_book_date=r['first_date']
                    )
                    .values_list('start_hrs', flat=True)
                    .first()
                )

            for r in last_rows:
                last_map[r['plant_machinery_machine_id']] = (
                    PlantMachineryLogBook.cmobjects
                    .filter(
                        plant_machinery_machine_id=r['plant_machinery_machine_id'],
                        log_book_date=r['last_date']
                    )
                    .values_list('start_hrs', flat=True)
                    .first()
                )

        # ----------------------------
        # Merge (small dataset)
        # ----------------------------
        result = []
        for row in base:
            mid = row['plant_machinery_machine__id']
            if 'start_hrs' in fields:
                row['start_hrs_first'] = first_map.get(mid)
                row['start_hrs_last'] = last_map.get(mid)
            result.append(row)

        if all_records == 'true':
            return Response({'results': result})

        paginator = Paginator(result, int(request.query_params.get('page_size', settings.MIN_PAGE_SIZE)))
        page = paginator.get_page(request.query_params.get('page', 1))

        return Response({
            'count': paginator.count,
            'next': page.next_page_number() if page.has_next() else None,
            'previous': page.previous_page_number() if page.has_previous() else None,
            'results': list(page),
        })

class PlantMachineryLogBookCumulative2APIView001(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        fields = request.query_params.get('fields')
        all_records = request.query_params.get('all')
        order_by = request.query_params.get('order_by', '-id')

        if not fields:
            raise APIException({'request_status': 0, 'msg': 'fields is required'})

        try:
            fields = json.loads(fields)
        except json.JSONDecodeError:
            raise APIException({'request_status': 0, 'msg': 'Invalid JSON for fields'})

        search = custom_filters(request, {}, ['fields'])

        base_qs = (
            PlantMachineryLogBook.cmobjects
            .filter(*search)
            .select_related('plant_machinery_machine')
        )

        # ----------------------------------
        # STEP 1: SUBQUERIES FOR WINDOW DATA
        # ----------------------------------
        subquery_annotations = {}

        for field, operation in fields.items():
            if operation == 'first_value':
                subquery_annotations[f'{field}_first'] = Subquery(
                    PlantMachineryLogBook.cmobjects
                    .filter(
                        plant_machinery_machine_id=OuterRef('plant_machinery_machine_id')
                    )
                    .order_by('log_book_date')
                    .values(field)[:1]
                )

            elif operation == 'last_value':
                subquery_annotations[f'{field}_last'] = Subquery(
                    PlantMachineryLogBook.cmobjects
                    .filter(
                        plant_machinery_machine_id=OuterRef('plant_machinery_machine_id')
                    )
                    .order_by('-log_book_date')
                    .values(field)[:1]
                )

        # ----------------------------------
        # STEP 2: AGGREGATIONS
        # ----------------------------------
        aggregate_annotations = {}

        for field, operation in fields.items():
            if operation == 'aggregate':
                aggregate_annotations[field] = Coalesce(
                    Sum(field), Value(0), output_field=FloatField()
                )
            elif operation == 'average':
                aggregate_annotations[field] = Coalesce(
                    Avg(field), Value(0), output_field=FloatField()
                )

        # ----------------------------------
        # STEP 3: FINAL QUERY
        # ----------------------------------
        result = (
            base_qs
            .values(
                'plant_machinery_machine__id',
                'plant_machinery_machine__machine_number',
                'plant_machinery_machine__equipment_description',
                'plant_machinery_machine__registration_no',
                'plant_machinery_machine__plant_machinery_group__machine_type',
                'project',
            )
            .annotate(**aggregate_annotations)
            .annotate(**subquery_annotations)
            .order_by(*order_by.split(','))
        )

        # ----------------------------------
        # STEP 4: RESPONSE
        # ----------------------------------
        if all_records == 'true':
            return Response({'results': list(result)})

        page_size = int(request.query_params.get('page_size', settings.MIN_PAGE_SIZE))
        paginator = Paginator(result, page_size)
        page = paginator.get_page(request.query_params.get('page', 1))

        return Response({
            'count': paginator.count,
            'next': page.next_page_number() if page.has_next() else None,
            'previous': page.previous_page_number() if page.has_previous() else None,
            'results': list(page),
        })



class PlantMachineryLogBookCumulative2APIView001old(APIView):
    """
    API to fetch cumulative or starting values based on machine.
    """
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        fields = request.query_params.get('fields')
        all_records = request.query_params.get('all')
        order_by = request.query_params.get('order_by', '-id')

        if not fields:
            raise APIException({'request_status': 0, 'msg': 'fields parameter is required'})

        try:
            fields = json.loads(fields)
        except json.JSONDecodeError:
            raise APIException({'request_status': 0, 'msg': "Invalid JSON format for fields."})

        search = custom_filters(request, {}, ['fields'])

        # -------------------------------
        # STEP 1: Base queryset
        # -------------------------------
        base_qs = (
            PlantMachineryLogBook.cmobjects
            .select_related('plant_machinery_machine')
            .filter(*search)
        )

        # -------------------------------
        # STEP 2: Window functions
        # -------------------------------
        window_annotations = {}
        aggregate_annotations = {}

        for field, operation in fields.items():
            if operation == 'first_value':
                window_annotations[f'{field}_first'] = Window(
                    expression=FirstValue(field),
                    partition_by=[F('plant_machinery_machine_id')],
                    order_by=F('log_book_date').asc()
                )

            elif operation == 'last_value':
                window_annotations[f'{field}_last'] = Window(
                    expression=LastValue(field),
                    partition_by=[F('plant_machinery_machine_id')],
                    order_by=F('log_book_date').asc()
                )

            elif operation == 'aggregate':
                aggregate_annotations[field] = Coalesce(
                    Sum(field), Value(0), output_field=FloatField()
                )

            elif operation == 'average':
                aggregate_annotations[field] = Coalesce(
                    Avg(field), Value(0), output_field=FloatField()
                )

        qs_with_window = base_qs.annotate(**window_annotations)

        # -------------------------------
        # STEP 3: Final aggregation
        # -------------------------------
        result = (
            qs_with_window
            .values(
                'plant_machinery_machine__id',
                'plant_machinery_machine__machine_number',
                'plant_machinery_machine__equipment_description',
                'plant_machinery_machine__registration_no',
                'plant_machinery_machine__plant_machinery_group__machine_type',
                'project',
                *window_annotations.keys()
            )
            .annotate(**aggregate_annotations)
            .order_by(*str(order_by).split(','))
        )

        # -------------------------------
        # STEP 4: Response
        # -------------------------------
        if all_records == 'true':
            return Response({'results': list(result)})

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

