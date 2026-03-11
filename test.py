class TenderMasterNewSurveyMaster(BaseAbstractStructure):
    organization = models.ForeignKey(Organization,related_name='organization_tender_survey',on_delete=models.CASCADE,null=True,blank=TenderSubSector)
    tender = models.ForeignKey(TenderMasterNew,related_name='tender_master_new_survey', on_delete=models.CASCADE,null=True,blank=True)
    date = models.DateField(null=True, blank=True)
    visited_by = models.CharField(max_length=250, null=True, blank=True)
    project_details_remarks = models.TextField(null=True, blank=True)
    client_remarks = models.TextField(null=True, blank=True)
    nature_of_contract_remarks = models.TextField(null=True, blank=True)
    users = models.ManyToManyField("administrations.PmsUser", null=True, blank=True)


class TenderMasterNewSurveyMasterAPIView(APIView):
    def post(self, request):
        request.data['created_by'] = request.user.id
        serializer = TenderMasterNewSurveyMasterSerializer(data=request.data, context={'request': request})
        users = self.request.data.get('users', [])
        existing_record = RFQVendorsMailList.cmobjects.filter(rfq_vendors_id=id).values_list('vendor_id',flat=True)
        users = list(set(users) - set(existing_record))
        if serializer.is_valid():
            try:
                obj = serializer.save()
                send_assign_users_email(users, serializer.data)
            except Exception as e:
                error_message = str(e.args[0]) if e.args else str(e)
                raise APIException({'request_status': 0, 'msg': error_message})
            return Response(
                {'results': {
                    'Data': serializer.data,
                },
                    'msg': 'Successfully created',
                    'status': status.HTTP_201_CREATED,
                    "request_status": 1})
        raise APIException({'request_status': 0, 'msg': serializer.errors})
    def put(self, request):
        method = self.request.query_params.get('method', None)
        organization_id = self.request.query_params.get('organization', None)
        id = self.request.query_params.get('id', None)
        request.data['updated_by'] = request.user.id
        details = TenderMasterNewSurveyMaster.cmobjects.filter(pk=id).first()
        with transaction.atomic():
            if method.lower() == 'edit':
                if TenderMasterNewSurveyMaster.cmobjects.filter(pk=id, organization_id=organization_id).exists():
                    details = TenderMasterNewSurveyMaster.cmobjects.filter(pk=id).first()
                    serializer = TenderMasterNewSurveyMasterSerializer(details, data=request.data,
                                                          context={'request': request})
                    if serializer.is_valid():
                        try:
                            obj = serializer.save()
                        except Exception as e:
                            error_message = str(e.args[0]) if e.args else str(e)
                            raise APIException({'request_status': 0, 'msg': error_message})

                        return Response({'results': {
                            'Data': serializer.data,
                        },
                            'msg': "Successfully updated",
                            'status': status.HTTP_202_ACCEPTED,
                            "request_status": 1})
                    raise APIException({'request_status': 0, 'msg': serializer.errors})
                else:
                    raise APIException({'request_status': 1, 'msg': "Something went wrong"})
                

#here I want to implement if new users is added then email functins will trigger
for both post and put properly standard way


def send_assign_survey_users_email(users, data):
    """Tender Site Survey users assigned Email Triggered """
    if not users or not data:
        return
    context={}
    context['current_datetime'] = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    context['user'] = f"{user.first_name} {user.last_name}"
    subject = f"Tender Survey Checklist Update – Verification Required"
    to_users_list = list(UserWiseModulePermissions.cmobjects.filter(
        module_item__unique_id__in=['tender-survey-approver'],
        level_permission=True,
    ).values_list('user_id',flat=True))
    cc_users_list = list(UserWiseModulePermissions.cmobjects.filter(
        module_item__unique_id__in=['tender-survey-submit-cc'],
        level_permission=True,
    ).values_list('user_id',flat=True))
    trigger_notifications(action='TENDER-SURVEY-ASSIGNED-USERS', subject=subject, user_list=to_users_list, cc_user_list=cc_users_list, context=context)

