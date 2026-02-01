
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

