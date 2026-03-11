from datetime import datetime, timedelta

class TenderMonitoringPendingEMDEmailTriggerAPIView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        """
        Monitoring of pending EMDs, if no action taken, every 31 days after Financial Bid Open Date
        """

        current_date = datetime.now().date()
        pending_since_date = current_date - timedelta(days=31)

        tender_data = TenderMasterNew.cmobjects.filter(
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
            'emd_checked_by_account'
        )

        to_users_list = list(
            UserWiseModulePermissions.cmobjects.filter(
                module_item__unique_id__in=['tender-pending-emds-to'],
                level_permission=True,
            ).values_list('user_id', flat=True)
        )

        cc_users_list = list(
            UserWiseModulePermissions.cmobjects.filter(
                module_item__unique_id__in=['tender-pending-emds-cc'],
                level_permission=True,
            ).values_list('user_id', flat=True)
        )

        context = {}

        if to_users_list and tender_data:

            subject = "List of pending EMDs with details for follow-up"

            context = {
                "date": current_date.strftime('%d-%m-%Y'),
                "data": list(tender_data),
                "pending_since_foD_date": pending_since_date.strftime('%d-%m-%Y'),
            }

            trigger_notifications(
                action='TENDER-AUTO-PENDING-EMDS',
                subject=subject,
                user_list=to_users_list,
                cc_user_list=cc_users_list,
                context=context
            )

        return Response(context)
