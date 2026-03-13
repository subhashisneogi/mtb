from django.db.models import F, IntegerField, ExpressionWrapper, Subquery, OuterRef
from django.db.models.functions import Now, TruncDate
from datetime import timedelta, datetime

class TenderMonitoringPendingEMDEmailTriggerAPIView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):

        current_date = datetime.now().date()
        pending_since_date = current_date - timedelta(days=31)

        rank_subquery = TenderMasterNewWinLossAnalysis.cmobjects.filter(
            tender=OuterRef('pk')
        ).values('rank')[:1]

        tender_data = TenderMasterNew.cmobjects.annotate(

            pending_since_days=ExpressionWrapper(
                TruncDate(Now()) - F('financial_bid_open_date'),
                output_field=IntegerField()
            ),

            rank_value=Subquery(rank_subquery, output_field=IntegerField())

        ).filter(
            status__in=['win', 'loss', 'canceled'],
            financial_bid_open_date__lte=pending_since_date
        ).values(
            'id',
            'tender_id',
            'financial_bid_open_date',
            'emd_amount',
            'emd_type',
            'emd_deposition_location',
            'emd_validity_date',
            'emd_checked_by_account',
            'pending_since_days',
            'tender_organization__employee_name',
            'proposed_tender',
            'bg_value',
            'rank_value'
        )
