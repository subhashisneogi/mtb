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
