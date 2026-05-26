import json
import pandas as pd

from django.conf import settings
from django.core.paginator import Paginator
from django.db.models import (
    Q, F, Value, Count, Sum, FloatField, OuterRef, Subquery, JSONField, Aggregate
)
from django.db.models.functions import Coalesce, JSONObject
from django.http import HttpResponse

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import APIException


class JSONArrayAgg(Aggregate):
    function = "JSON_ARRAYAGG"
    template = "%(function)s(%(expressions)s ORDER BY %(ordering)s)"
    output_field = JSONField()

    def __init__(self, expression, ordering="total_amount ASC", **extra):
        super().__init__(
            expression,
            ordering=ordering,
            **extra
        )


class MRToPOReportNewAPIView22(APIView):

    def get(self, request, format=None):
        try:
            order_by = request.query_params.get('order_by', '-id')
            all_data = request.query_params.get('all', None)
            is_export = request.query_params.get('is_export', 'false')

            search = {}

            temp = check_store_site(request)

            if 'site__in' in temp:
                search['material_request__site__in'] = temp['site__in']

            if 'store__in' in temp:
                search['material_request__store__in'] = temp['store__in']

            search = custom_filters(request, search, ['return_fields'])

            data_list = MaterialRequestMasterItems.cmobjects.select_related(
                'organization',
                'material_request',
                'material_request__site',
                'requested_material',
                'requested_material__unit_of_mesurement',
                'requested_material__material_type'
            ).prefetch_related(
                'procurement_material_indent_item_request',
                'procurement_material_indent_item_request__indent',
                'procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item',
                'procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__rfq_vendors',
                'procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__procurement_cst_item_rfq_vendor_item',
                'procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__procurement_cst_item_rfq_vendor_item__cst',
                'procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__procurement_cst_item_rfq_vendor_item__procurement_purchase_order_item_cst_item',
                'procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__procurement_cst_item_rfq_vendor_item__procurement_purchase_order_item_cst_item__purchase_order',
                'procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__procurement_cst_item_rfq_vendor_item__procurement_purchase_order_item_cst_item__purchase_order__vendor',
                'procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__procurement_cst_item_rfq_vendor_item__procurement_purchase_order_item_cst_item__procurement_grn_item_purchase_order_item',
            ).filter(
                Q(
                    Q(procurement_material_indent_item_request__isnull=True) |
                    Q(
                        procurement_material_indent_item_request__is_deleted=False,
                        procurement_material_indent_item_request__indent__is_deleted=False
                    )
                ),
                Q(
                    Q(procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__isnull=True) |
                    Q(
                        procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__is_deleted=False,
                        procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__rfq_vendors__is_deleted=False,
                        procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__rfq_vendors__is_archived=False
                    )
                ),
                Q(
                    Q(procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__procurement_cst_item_rfq_vendor_item__isnull=True) |
                    Q(
                        procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__procurement_cst_item_rfq_vendor_item__is_deleted=False,
                        procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__procurement_cst_item_rfq_vendor_item__cst__is_deleted=False,
                        procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__procurement_cst_item_rfq_vendor_item__cst__latest=True
                    )
                ),
                Q(
                    Q(procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__procurement_cst_item_rfq_vendor_item__procurement_purchase_order_item_cst_item__isnull=True) |
                    Q(
                        procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__procurement_cst_item_rfq_vendor_item__procurement_purchase_order_item_cst_item__is_deleted=False,
                        procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__procurement_cst_item_rfq_vendor_item__procurement_purchase_order_item_cst_item__purchase_order__is_deleted=False
                    )
                ),
                Q(
                    Q(procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__procurement_cst_item_rfq_vendor_item__procurement_purchase_order_item_cst_item__procurement_grn_item_purchase_order_item__isnull=True) |
                    Q(
                        procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__procurement_cst_item_rfq_vendor_item__procurement_purchase_order_item_cst_item__procurement_grn_item_purchase_order_item__is_deleted=False,
                        procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__procurement_cst_item_rfq_vendor_item__procurement_purchase_order_item_cst_item__procurement_grn_item_purchase_order_item__grn__is_deleted=False
                    )
                ),
            ).values(
                'id',
                'material_request__request_code',
                'material_request__date',
                'material_request__site__name',
                'status',
                'requested_material',
                'requested_material__material_code',
                'requested_material__sap_code',
                'requested_material__material_name',
                'requested_material__unit_of_mesurement__symbol',
                'requested_material__material_type__name',
                'approved_by_date',
                'quantity_unit',
                'sanctioned_quantity',

                'procurement_material_indent_item_request',
                'procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item',
                'procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__procurement_cst_item_rfq_vendor_item',
                'procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__procurement_cst_item_rfq_vendor_item__procurement_purchase_order_item_cst_item',
                'procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__procurement_cst_item_rfq_vendor_item__procurement_purchase_order_item_cst_item__procurement_grn_item_purchase_order_item',
            ).distinct().annotate(

                indent__request_code=F('procurement_material_indent_item_request__indent__request_code'),
                indent__date=F('procurement_material_indent_item_request__indent__date'),
                indent__status=F('procurement_material_indent_item_request__status'),
                indent__quantity=Coalesce(
                    F('procurement_material_indent_item_request__quantity'),
                    Value(0),
                    output_field=FloatField()
                ),
                indent__sanctioned_quantity=Coalesce(
                    F('procurement_material_indent_item_request__sanctioned_quantity'),
                    Value(0),
                    output_field=FloatField()
                ),
                indent__approved_by_date=F('procurement_material_indent_item_request__approved_by_date'),

                rfq_vendors__request_code=F(
                    'procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__rfq_vendors__request_code'
                ),
                rfq_vendors__date=F(
                    'procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__rfq_vendors__date'
                ),

                quotation__count=Subquery(
                    QuotationItems.cmobjects.filter(
                        quotation__latest=True,
                        indent_item_id=OuterRef('procurement_material_indent_item_request')
                    ).values('indent_item').annotate(
                        value=Count('id', distinct=True)
                    ).values('value')[:1]
                ),

                cst__request_code=F(
                    'procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__procurement_cst_item_rfq_vendor_item__cst__request_code'
                ),
                cst__version=F(
                    'procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__procurement_cst_item_rfq_vendor_item__cst__version'
                ),
                cst__status=F(
                    'procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__procurement_cst_item_rfq_vendor_item__cst__status'
                ),
                cst__current_stage=F(
                    'procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__procurement_cst_item_rfq_vendor_item__cst__current_stage'
                ),
                cst__date=F(
                    'procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__procurement_cst_item_rfq_vendor_item__cst__date'
                ),

                purchase_order__request_code=F(
                    'procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__procurement_cst_item_rfq_vendor_item__procurement_purchase_order_item_cst_item__purchase_order__request_code'
                ),
                purchase_order__vendor__vendor_name=F(
                    'procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__procurement_cst_item_rfq_vendor_item__procurement_purchase_order_item_cst_item__purchase_order__vendor__vendor_name'
                ),
                purchase_order__date=F(
                    'procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__procurement_cst_item_rfq_vendor_item__procurement_purchase_order_item_cst_item__purchase_order__date'
                ),
                purchase_order__status=F(
                    'procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__procurement_cst_item_rfq_vendor_item__procurement_purchase_order_item_cst_item__purchase_order__status'
                ),
                purchase_order__quantity=Coalesce(
                    F('procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__procurement_cst_item_rfq_vendor_item__procurement_purchase_order_item_cst_item__quantity'),
                    Value(0),
                    output_field=FloatField()
                ),
                purchase_order__rate=Coalesce(
                    F('procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__procurement_cst_item_rfq_vendor_item__procurement_purchase_order_item_cst_item__rate'),
                    Value(0),
                    output_field=FloatField()
                ),
                purchase_order__total_amount=Coalesce(
                    F('procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__procurement_cst_item_rfq_vendor_item__procurement_purchase_order_item_cst_item__total_amount'),
                    Value(0),
                    output_field=FloatField()
                ),
                purchase_order__tax_amount=Coalesce(
                    (
                        F('procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__procurement_cst_item_rfq_vendor_item__procurement_purchase_order_item_cst_item__excise_tax_amount') +
                        F('procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__procurement_cst_item_rfq_vendor_item__procurement_purchase_order_item_cst_item__tax_amount') +
                        F('procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__procurement_cst_item_rfq_vendor_item__procurement_purchase_order_item_cst_item__sgst_amount') +
                        F('procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__procurement_cst_item_rfq_vendor_item__procurement_purchase_order_item_cst_item__cgst_amount') +
                        F('procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__procurement_cst_item_rfq_vendor_item__procurement_purchase_order_item_cst_item__igst_amount') +
                        F('procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__procurement_cst_item_rfq_vendor_item__procurement_purchase_order_item_cst_item__utgst_amount')
                    ),
                    Value(0),
                    output_field=FloatField()
                ),
                purchase_order__approved_by_date=F(
                    'procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__procurement_cst_item_rfq_vendor_item__procurement_purchase_order_item_cst_item__purchase_order__approved_by_date'
                ),
                purchase_order__sap_code=F(
                    'procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__procurement_cst_item_rfq_vendor_item__procurement_purchase_order_item_cst_item__purchase_order__sap_code'
                ),

                grn__received_quantity=Coalesce(
                    Sum(
                        'procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__procurement_cst_item_rfq_vendor_item__procurement_purchase_order_item_cst_item__procurement_grn_item_purchase_order_item__quantity'
                    ),
                    Value(0),
                    output_field=FloatField()
                ),

                purchase_order__freight=Coalesce(
                    Sum(
                        Subquery(
                            PurchaseOrderExpenseDetails.cmobjects.filter(
                                expense_head__name='Freight',
                                purchase_order_id=OuterRef(
                                    'procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__procurement_cst_item_rfq_vendor_item__procurement_purchase_order_item_cst_item__purchase_order'
                                )
                            ).values('purchase_order').annotate(
                                value=Sum('total_expense_amount')
                            ).values('value')[:1]
                        )
                    ),
                    Value(0),
                    output_field=FloatField()
                ),

                quotation_details_list=Subquery(
                    QuotationItems.cmobjects.filter(
                        quotation__latest=True,
                        quotation__rfq_vendor_id=OuterRef(
                            'procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__procurement_cst_item_rfq_vendor_item__cst__rfq_vendor_id'
                        ),
                        indent_item_id=OuterRef('procurement_material_indent_item_request')
                    )
                    .values('indent_item')
                    .annotate(
                        quotation_data=JSONArrayAgg(
                            JSONObject(
                                quotation_id=F('quotation_id'),
                                vendor__name=F('quotation__vendor__vendor_name'),
                                vendor__code=F('quotation__vendor__vendor_code'),
                                date=F('quotation__date'),
                                request_code=F('quotation__request_code'),
                                latest=F('quotation__latest'),

                                cst_qty=Coalesce(F('quantity'), Value(0), output_field=FloatField()),
                                basic_rate=Coalesce(F('rate'), Value(0), output_field=FloatField()),
                                freight=Coalesce(F('freight'), Value(0), output_field=FloatField()),
                                tax_amount=Coalesce(F('tax_amount'), Value(0), output_field=FloatField()),
                                total_amount=Coalesce(F('total_amount'), Value(0), output_field=FloatField()),
                            ),
                            ordering='total_amount ASC'
                        )
                    )
                    .values('quotation_data')[:1],
                    output_field=JSONField()
                ),

            ).filter(*search)

            data_list = data_list.distinct().order_by(*str(order_by).split(","))

            if all_data == 'true' and is_export == 'true':

                export_data = []

                for index, item in enumerate(data_list, start=1):

                    mr_date = item.get('material_request__date')
                    po_date = item.get('purchase_order__date')

                    lead_time_days = ''
                    if mr_date and po_date:
                        try:
                            lead_time_days = (po_date - mr_date).days
                        except Exception:
                            lead_time_days = ''

                    balance_po_qty = (
                        float(item.get('purchase_order__quantity') or 0) -
                        float(item.get('grn__received_quantity') or 0)
                    )

                    row = {
                        'Sl. No.': index,
                        'Project Name': item.get('material_request__site__name'),
                        'MR No.': item.get('material_request__request_code'),
                        'MR Date': item.get('material_request__date'),
                        'MR Approved Date': item.get('approved_by_date'),
                        'MR Status': item.get('status'),

                        'Indent No.': item.get('indent__request_code'),
                        'Indent Date': item.get('indent__date'),
                        'Indent Approved Date': item.get('indent__approved_by_date'),
                        'Indent Status': item.get('indent__status'),

                        'RFQ No.': item.get('rfq_vendors__request_code'),
                        'RFQ Date': item.get('rfq_vendors__date'),

                        'CST No.': item.get('cst__request_code'),
                        'CST Dt': item.get('cst__date'),
                    }

                    quotation_list = item.get('quotation_details_list') or []

                    if isinstance(quotation_list, str):
                        try:
                            quotation_list = json.loads(quotation_list)
                        except Exception:
                            quotation_list = []

                    quotation_list = sorted(
                        quotation_list,
                        key=lambda x: float(x.get('total_amount') or 0)
                    )

                    for q_index in range(1, 6):
                        quotation = quotation_list[q_index - 1] if len(quotation_list) >= q_index else {}

                        row[f'L{q_index} SAP Code'] = quotation.get('vendor__code')
                        row[f'L{q_index} Name'] = quotation.get('vendor__name')
                        row[f'L{q_index} Quotation No.'] = quotation.get('request_code')
                        row[f'L{q_index} Quotation Date.'] = quotation.get('date')
                        row[f'L{q_index} CST Qty'] = quotation.get('cst_qty')
                        row[f'L{q_index} Basic Rate'] = quotation.get('basic_rate')
                        row[f'L{q_index} Freight'] = quotation.get('freight')
                        row[f'L{q_index} Tax'] = quotation.get('tax_amount')
                        row[f'L{q_index} Amount'] = quotation.get('total_amount')

                    row.update({
                        'PO No.': item.get('purchase_order__request_code'),
                        'SAP PO No.': item.get('purchase_order__sap_code'),
                        'PO Date': item.get('purchase_order__date'),
                        'PO Status': item.get('purchase_order__status'),
                        'PO Approved Date': item.get('purchase_order__approved_by_date'),
                        'Vendor Name': item.get('purchase_order__vendor__vendor_name'),

                        'Item Group': item.get('requested_material__material_type__name'),
                        'Material SAP Code': item.get('requested_material__sap_code'),
                        'Item Name': item.get('requested_material__material_name'),
                        'UOM': item.get('requested_material__unit_of_mesurement__symbol'),

                        'MR Qty': item.get('quantity_unit'),
                        'Indent Qty': item.get('indent__quantity'),
                        'Sanctioned Qty': item.get('sanctioned_quantity'),
                        'PO Qty': item.get('purchase_order__quantity'),
                        'Basic Rate': item.get('purchase_order__rate'),
                        'Freight': item.get('purchase_order__freight'),
                        'Tax': item.get('purchase_order__tax_amount'),
                        'Amount': item.get('purchase_order__total_amount'),
                        'GRN Qty': item.get('grn__received_quantity'),
                        'Balance PO Qty': balance_po_qty,
                        'Lead Time (MR to PO)\nDays': lead_time_days,
                    })

                    export_data.append(row)

                df = pd.DataFrame(export_data)

                response = HttpResponse(
                    content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
                response['Content-Disposition'] = 'attachment; filename="MR_TO_PO_CST_DUMP.xlsx"'

                with pd.ExcelWriter(response, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='Sheet1')

                return response

            if all_data == 'true':
                return Response({'results': data_list})

            page_size = int(request.query_params.get('page_size', settings.MIN_PAGE_SIZE))
            paginator = Paginator(data_list, page_size)
            page_number = request.query_params.get('page', 1)
            page = paginator.get_page(page_number)

            return Response({
                'count': paginator.count,
                'next': page.next_page_number() if page.has_next() else None,
                'previous': page.previous_page_number() if page.has_previous() else None,
                'results': {
                    'Data': page.object_list,
                },
            })

        except Exception as e:
            raise APIException({
                'request_status': 0,
                'msg': str(e)
            })