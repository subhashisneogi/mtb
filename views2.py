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