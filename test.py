#html
{% load custom_filters %}
{% load custom_template_filters %}
<div class="email-container">
    <p>Date: {{ date }}</p>
    <p>Hi,</p>
    <p>
        This is a reminder that the Bank Guarantees&nbsp;(BGs) for the following Tenders are due for withdrawal from the authorities.
    </p>
        <table class="borderTable">
        <thead>
            <tr>
                <th>Sl No</th>
                <th>Tender Id</th>
                <th>Organisation</th>
                <th>Work Description</th>
                <th>BG Value</th>
                <th>Financial Open Date</th>
                <th>Rank</th>
                <th>Pending Since(Today-Financial Open Date)</th>
                <th>BG Submission Address</th>
            </tr>
        </thead>
        <tbody>
            {% for item in data %}
            <tr>
                <td>{{ forloop.counter }}</td>
                <td>{{ item.tender_id|default:"" }}</td>
                <td>{{ item.tender_organization__employee_name|default:"" }}</td>
                <td>{{ item.proposed_tender|default:"" }}</td>
                <td>{{ item.bg_value|default:"" }}</td>
                <td>{{ item.financial_bid_open_date|str_to_date:"%d-%m-%Y" }}</td>
                <td>{{ item.rank_value|default:"" }}</td>
                <td>{{ item.pending_since_days }}</td>
                <td>{{ item.emd_deposition_location|default:"" }}</td>
            </tr>
            {% endfor %}
            </tbody>
    </table>
    <p>Please ensure timely action.</p>
    <div class="footer">
        <p style="color: #333333;">Thank you for your support.</p>
        <div class="signature">
            <p style="color: #333333;">Regards,</p>
            <p style="color: #333333;">
                <strong>Team Shyam Infra</strong>
            </p>
        </div>
    </div>
</div>

#views

class TenderMonitoringPendingEMDEmailTriggerAPIView(APIView):
    permission_classes = (AllowAny,)
    def get(self, request):
        """
        Monitoring of pending EMDs, if no action taken, every 31 days after Financial Bid Open Date
        """
        current_date = datetime.now().date()
        pending_since_date = current_date - timedelta(days=31)
        rank_subquery = TenderMasterNewWinLossAnalysis.cmobjects.filter(
            tender=OuterRef('pk')).values('rank')[:1]
        tender_data = TenderMasterNew.cmobjects.annotate(
            pending_since_days=ExpressionWrapper(
                (F('financial_bid_open_date') - Now()) / timedelta(days=1),
                output_field=IntegerField()
            ),
            rank_value=Subquery(rank_subquery, output_field=IntegerField())
            ).filter(status__in=['win', 'loss', 'canceled'],financial_bid_open_date__lte=pending_since_date).values(
            'id','tender_id','financial_bid_open_date','emd_amount','emd_type','emd_deposition_location','emd_validity_date',
            'emd_checked_by_account','pending_since_days', 'tender_organization__employee_name', 'proposed_tender', 'bg_value', 'rank_value')

        to_users_list = list(UserWiseModulePermissions.cmobjects.filter(
                module_item__unique_id__in=['tender-pending-emds-to'],
                level_permission=True,
            ).values_list('user_id', flat=True))
        cc_users_list = list(UserWiseModulePermissions.cmobjects.filter(
                module_item__unique_id__in=['tender-pending-emds-cc'],
                level_permission=True,
            ).values_list('user_id', flat=True))
        context = {}
        if tender_data:
            subject = "List of pending EMDs with details for follow-up"
            context = {
                "date": current_date.strftime('%d-%m-%Y'),
                "data": list(tender_data),
            }
            trigger_notifications(
                action='TENDER-AUTO-PENDING-EMDS',
                subject=subject,
                user_list=to_users_list,
                cc_user_list=cc_users_list,
                context=context
            )
        return Response(context)


please write proper code to calculate the 
pending_since_days = today_date - financial_bid_open_date
