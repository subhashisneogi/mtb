
path('procurement-mrtopo-report-new/', views.MRToPOReportNewAPIView.as_view()),
from django.db.models import Aggregate, JSONField
from django.db.models.functions import JSONObject

from django.db.models import Aggregate, JSONField
from django.db.models.functions import JSONObject
from django.db.models.expressions import Func
class JSONArrayAgg(Aggregate):
    function = "JSON_ARRAYAGG"
    output_field = JSONField()


class JSONArrayAgg(Aggregate):
    function = "JSON_ARRAYAGG"
    output_field = JSONField()

class MRToPOReportNewAPIView(APIView):
    
    def get(self, request, format=None):
        try:
            order_by = self.request.query_params.get('order_by', '-id')
            all = self.request.query_params.get('all', None)
            # return_fields = self.request.query_params.get('return_fields', None)
            search = {}
            temp = check_store_site(request)
            if 'site__in' in temp:
                search['material_request__site__in'] = temp['site__in']
            if 'store__in' in temp:
                search['material_request__store__in'] = temp['store__in']
            search = custom_filters(self.request, search, ['return_fields'])

            data_list = MaterialRequestMasterItems.cmobjects.select_related(
                'organization','material_request','requested_material','requested_material__unit_of_mesurement','requested_material__material_type'
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
                Q(Q(procurement_material_indent_item_request__isnull=True)|Q(Q(procurement_material_indent_item_request__is_deleted=False)&Q(procurement_material_indent_item_request__indent__is_deleted=False))),
                Q(Q(procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__isnull=True)|Q(Q(procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__is_deleted=False)&Q(procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__rfq_vendors__is_deleted=False)&Q(procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__rfq_vendors__is_archived=False))),
                Q(Q(procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__procurement_cst_item_rfq_vendor_item__isnull=True)|Q(Q(procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__procurement_cst_item_rfq_vendor_item__is_deleted=False)&Q(procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__procurement_cst_item_rfq_vendor_item__cst__is_deleted=False)&Q(procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__procurement_cst_item_rfq_vendor_item__cst__latest=True))),
                Q(Q(procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__procurement_cst_item_rfq_vendor_item__procurement_purchase_order_item_cst_item__isnull=True)|Q(Q(procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__procurement_cst_item_rfq_vendor_item__procurement_purchase_order_item_cst_item__is_deleted=False)&Q(procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__procurement_cst_item_rfq_vendor_item__procurement_purchase_order_item_cst_item__purchase_order__is_deleted=False))),
                Q(Q(procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__procurement_cst_item_rfq_vendor_item__procurement_purchase_order_item_cst_item__procurement_grn_item_purchase_order_item__isnull=True)|Q(Q(procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__procurement_cst_item_rfq_vendor_item__procurement_purchase_order_item_cst_item__procurement_grn_item_purchase_order_item__is_deleted=False)&Q(procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__procurement_cst_item_rfq_vendor_item__procurement_purchase_order_item_cst_item__procurement_grn_item_purchase_order_item__grn__is_deleted=False))),
            ).values(
                'id','material_request__request_code','material_request__date','status','requested_material', 'requested_material__material_code', 'requested_material__sap_code', 'requested_material__material_name', 'requested_material__unit_of_mesurement__symbol', 'requested_material__material_type__name','approved_by_date','quantity_unit','sanctioned_quantity',
                'procurement_material_indent_item_request',
                'procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item',
                'procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__procurement_cst_item_rfq_vendor_item',
                'procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__procurement_cst_item_rfq_vendor_item__procurement_purchase_order_item_cst_item',
                'procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__procurement_cst_item_rfq_vendor_item__procurement_purchase_order_item_cst_item__procurement_grn_item_purchase_order_item',
            ).distinct().annotate(
                indent__request_code = F('procurement_material_indent_item_request__indent__request_code'),
                indent__date = F('procurement_material_indent_item_request__indent__date'),
                indent__status = F('procurement_material_indent_item_request__status'),
                indent__quantity = Coalesce(('procurement_material_indent_item_request__quantity'), Value(0), output_field=FloatField()),
                indent__sanctioned_quantity = Coalesce(('procurement_material_indent_item_request__sanctioned_quantity'), Value(0), output_field=FloatField()),
                indent__approved_by_date = F('procurement_material_indent_item_request__approved_by_date'),
                
                rfq_vendors__request_code = F('procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__rfq_vendors__request_code'),
                rfq_vendors__date = F('procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__rfq_vendors__date'),

                quotation__count = Subquery(
                    QuotationItems.cmobjects.filter(
                        quotation__latest=True,
                        indent_item_id=OuterRef('procurement_material_indent_item_request')).values('indent_item').annotate(
                            value=Count('id', distinct=True)
                        ).values('value')
                ),
                cst__request_code = F('procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__procurement_cst_item_rfq_vendor_item__cst__request_code'),
                cst__version = F('procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__procurement_cst_item_rfq_vendor_item__cst__version'),
                cst__status = F('procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__procurement_cst_item_rfq_vendor_item__cst__status'),
                cst__current_stage = F('procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__procurement_cst_item_rfq_vendor_item__cst__current_stage'),
                cst__date = F('procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__procurement_cst_item_rfq_vendor_item__cst__date'),
                cst_rfq_vendor_id = F('procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__procurement_cst_item_rfq_vendor_item__cst__rfq_vendor_id'),

                purchase_order__request_code = F('procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__procurement_cst_item_rfq_vendor_item__procurement_purchase_order_item_cst_item__purchase_order__request_code'),
                purchase_order__vendor__vendor_name = F('procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__procurement_cst_item_rfq_vendor_item__procurement_purchase_order_item_cst_item__purchase_order__vendor__vendor_name'),
                purchase_order__date = F('procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__procurement_cst_item_rfq_vendor_item__procurement_purchase_order_item_cst_item__purchase_order__date'),
                purchase_order__status = F('procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__procurement_cst_item_rfq_vendor_item__procurement_purchase_order_item_cst_item__purchase_order__status'),
                purchase_order__quantity = Coalesce(('procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__procurement_cst_item_rfq_vendor_item__procurement_purchase_order_item_cst_item__quantity'), Value(0), output_field=FloatField()),
                purchase_order__rate = Coalesce(('procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__procurement_cst_item_rfq_vendor_item__procurement_purchase_order_item_cst_item__rate'), Value(0), output_field=FloatField()),
                purchase_order__total_amount = Coalesce(('procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__procurement_cst_item_rfq_vendor_item__procurement_purchase_order_item_cst_item__total_amount'), Value(0), output_field=FloatField()),
                purchase_order__tax_amount = Coalesce((
                    F('procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__procurement_cst_item_rfq_vendor_item__procurement_purchase_order_item_cst_item__excise_tax_amount')+
                    F('procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__procurement_cst_item_rfq_vendor_item__procurement_purchase_order_item_cst_item__tax_amount')+
                    F('procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__procurement_cst_item_rfq_vendor_item__procurement_purchase_order_item_cst_item__sgst_amount')+
                    F('procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__procurement_cst_item_rfq_vendor_item__procurement_purchase_order_item_cst_item__cgst_amount')+
                    F('procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__procurement_cst_item_rfq_vendor_item__procurement_purchase_order_item_cst_item__igst_amount')+
                    F('procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__procurement_cst_item_rfq_vendor_item__procurement_purchase_order_item_cst_item__utgst_amount')
                ), Value(0), output_field=FloatField()),
                purchase_order__approved_by_date = F('procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__procurement_cst_item_rfq_vendor_item__procurement_purchase_order_item_cst_item__purchase_order__approved_by_date'),
                purchase_order__sap_code = F('procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__procurement_cst_item_rfq_vendor_item__procurement_purchase_order_item_cst_item__purchase_order__sap_code'),
                purchase_order__final_release_date_from_sap = F('procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__procurement_cst_item_rfq_vendor_item__procurement_purchase_order_item_cst_item__purchase_order__final_release_date_from_sap'),
                grn__received_quantity = Coalesce(Sum('procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__procurement_cst_item_rfq_vendor_item__procurement_purchase_order_item_cst_item__procurement_grn_item_purchase_order_item__quantity'), Value(0), output_field=FloatField()),
                balance_po_remarks = Subquery(
                    BalancePORemarks.cmobjects.filter(
                        Q(Q(material_request_item_id=OuterRef('pk')) | Q(material_request_item__isnull=True)),
                        Q(Q(indent_item_id=OuterRef('procurement_material_indent_item_request')) | Q(indent_item__isnull=True)),
                        Q(Q(rfq_vendor_item_id=OuterRef('procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item')) | Q(rfq_vendor_item__isnull=True)),
                        Q(Q(cst_item_id=OuterRef('procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__procurement_cst_item_rfq_vendor_item')) | Q(cst_item__isnull=True)),
                        Q(Q(purchase_order_item_id=OuterRef('procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__procurement_cst_item_rfq_vendor_item__procurement_purchase_order_item_cst_item')) | Q(purchase_order_item__isnull=True)),
                        ).values('material_request_item','indent_item','rfq_vendor_item','enquiry_at_once_item','cst_item','purchase_order_item').annotate(
                            balance_po_remarks_all=GroupConcat('balance_po_remarks', distinct=True)
                        ).values('balance_po_remarks_all')
                ),
                purchase_order__freight = Coalesce(Sum(Subquery(
                    PurchaseOrderExpenseDetails.cmobjects.filter(
                        expense_head__name='Freight',
                        purchase_order_id=OuterRef('procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__procurement_cst_item_rfq_vendor_item__procurement_purchase_order_item_cst_item__purchase_order'),
                        ).values('purchase_order').annotate(
                            value=Sum('total_expense_amount')
                        ).values('value')
                )), Value(0), output_field=FloatField()),                
                rfq_vendors__status = Value(''),

                quotation_details_list=Subquery(
                    Quotation.cmobjects.filter(
                        organization_id=1,
                        latest=True,
                        rfq_vendor_id=OuterRef(
                            'procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__procurement_cst_item_rfq_vendor_item__cst__rfq_vendor_id'
                        )
                    )
                    .order_by('total_amount')
                    .values('rfq_vendor_id')
                    .annotate(
                        quotation_data=JSONArrayAgg(
                            JSONObject(
                                id=F('id'),
                                vendor__name=F('vendor__vendor_name'),
                                vendor__code=F('vendor__vendor_code'),
                                date=F('date'),
                                request_code=F('request_code'),
                                latest=F('latest'),
                                total_amount=F('total_amount'),
                            )
                        )
                    )
                    .values('quotation_data')[:1],
                    output_field=JSONField()
                ),

                # payment_master__payment_no = Subquery(
                #     PaymentMaster.cmobjects.filter(
                #         cst_id=OuterRef('procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__procurement_cst_item_rfq_vendor_item__cst_id')
                #     ).values('cst_id')
                #     .annotate(payment_nos=GroupConcat('payment_no', distinct=True, separator=','))
                #     .values('payment_nos')
                # ),
            ).filter(*search) 
            # if return_fields:
            #     data_list = data_list.values(*str(return_fields).split(","))
            data_list = data_list.distinct().order_by(*str(order_by).split(","))

            if all == 'true':
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
            error_message = str(e)
            raise APIException({'request_status': 0, 'msg': error_message})
