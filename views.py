    def post(self, request):
        """
        Bulk Create & Update
        """
        request_data = request.data if isinstance(request.data, list) else [request.data]
        results = {"success": [], "errors": []}
        with transaction.atomic():
            try:
                payload_ids = [data.get("id") for data in request_data if "id" in data]

                survey_id = request_data[0].get("survey")
                existing_items = BDDepartmentMaster.objects.filter(survey=survey_id)
                existing_ids = list(existing_items.values_list("id", flat=True))

                ids_to_delete = set(existing_ids) - set(payload_ids)
                if ids_to_delete:
                    BDDepartmentMaster.cmobjects.filter(id__in=ids_to_delete).update(
                        is_deleted=True,   
                        updated_by=request.user.id
                    )
                for data in request_data:
                    serializer = None
                    if 'id' in data:
                        instance = BDDepartmentMaster.cmobjects.filter(pk=data['id']).first()
                        data['updated_by'] = request.user.id
                        serializer = BDMasterSerializer(instance, data=data, partial=True, context={'request': request})
                    else:
                        data['created_by'] = request.user.id
                        serializer = BDMasterSerializer(data=data, context={'request': request})
                    if serializer.is_valid():
                        serializer.save()
                        results["success"].append({
                            "data": serializer.data,
                            "msg": "Successfully created"
                        })
                    else:
                        results["errors"].append({
                            "data": data,
                            "error": serializer.errors,
                            "msg": "Validation failed"
                        })
            except Exception as e:
                results["errors"].append({
                    "error": str(e),
                    "msg": "Something went wrong. If the problem persists, please contact support."
                })
        return Response({
            'results': results,
            'status': status.HTTP_201_CREATED,
            "request_status": 1
        })  
#serializers
class TenderMasterNewSurveyMasterConstructionMaterialsSerializer(serializers.ModelSerializer):
    """
    Serializer for Construction Materials with nested supplier details and attachments
    """
    supplier_details = TenderMasterNewSurveyMasterConstructionMaterialsSupplierDetailsSerializer(many=True, required=False, source="survey_construction_materials_supplier_details")
    # attachments = TenderMasterNewSurveyMasterConstructionMaterialsAttachmentsSerializer(
    #     many=True, required=False, source="survey_construction_materials_attachments"
    # )
    @transaction.atomic
    def create(self, validated_data):
        supplier_details_data = validated_data.pop('survey_construction_materials_supplier_details', [])
        # attachments_data = validated_data.pop('survey_construction_materials_attachments', [])

        construction_materials = TenderMasterNewSurveyMasterConstructionMaterials.objects.create(**validated_data)
        current_user = construction_materials.created_by if construction_materials.created_by else None

        # for attachment in attachments_data:
        #     try:
        #         TenderMasterNewSurveyMasterConstructionMaterialsAttachments.objects.create(
        #             construction_materials=construction_materials,
        #             attachment=process_attachments(attachment),
        #             file_data="",
        #             mime_type=attachment.get('mime_type'),
        #             attachment_name=attachment.get('attachment_name'),
        #             remarks=attachment.get('remarks'),
        #             created_by=current_user,
        #         )
        #     except Exception as e:
        #         print(f"Attachment creation exception: {e}")

        # Create supplier details
        for supplier in supplier_details_data:
            TenderMasterNewSurveyMasterConstructionMaterialsSupplierDetails.objects.create(
                construction_materials=construction_materials,
                created_by=current_user,
                **supplier
            )
        return construction_materials

    @transaction.atomic
    def update(self, instance, validated_data):
        # Update base fields
        for field in instance._meta.fields:
            field_name = field.name
            if field_name in validated_data:
                setattr(instance, field_name, validated_data[field_name])

        current_user = instance.updated_by if instance.updated_by else None

        # Handle attachments
        # attachments_data = validated_data.get('survey_construction_materials_attachments', [])
        # existing_attachments = instance.survey_construction_materials_attachments.filter(is_deleted=False)
        
        # for attachment in attachments_data:
        #     attachment_id = attachment.get('id')
        #     temp_attach_data = process_attachments(attachment)
        #     existing_attachment = next((a for a in existing_attachments if a.id == attachment_id), None)

        #     if not existing_attachment:
        #         try:
        #             TenderMasterNewSurveyMasterConstructionMaterialsAttachments.objects.create(
        #                 construction_materials=instance,
        #                 attachment=temp_attach_data,
        #                 file_data="",
        #                 mime_type=attachment.get('mime_type'),
        #                 attachment_name=attachment.get('attachment_name'),
        #                 remarks=attachment.get('remarks'),
        #                 created_by=current_user
        #             )
        #         except Exception as e:
        #             print(f"Attachment update exception: {e}")
        #     else:
        #         if temp_attach_data:
        #             existing_attachment.attachment = temp_attach_data
        #         existing_attachment.attachment_name = attachment.get('attachment_name')
        #         existing_attachment.mime_type = attachment.get('mime_type')
        #         existing_attachment.remarks = attachment.get('remarks')
        #         existing_attachment.updated_by = current_user
        #         existing_attachment.save()

        # Handle supplier details
        supplier_details_data = validated_data.get('survey_construction_materials_supplier_details', [])
        existing_suppliers = instance.survey_construction_materials_supplier_details.filter(is_deleted=False)

        for item_data in supplier_details_data:
            item_id = item_data.get('id')
            existing_item = next((item for item in existing_suppliers if item.id == item_id), None)
            print(existing_item)
            if not existing_item:
                existing_item = TenderMasterNewSurveyMasterConstructionMaterialsSupplierDetails.objects.create(construction_materials=instance, created_by=current_user, **item_data)
            else:
                for field in existing_item._meta.fields:
                    field_name = field.name
                    if field_name in item_data:
                        setattr(existing_item, field_name, item_data[field_name])
                setattr(existing_item, 'updated_by', current_user)
                existing_item.save()

        # Mark deleted suppliers
        for existing_supplier in existing_suppliers:
            if existing_supplier.id not in [s.get('id') for s in supplier_details_data]:
                existing_supplier.is_deleted = True
                existing_supplier.updated_by = current_user
                existing_supplier.save()
        instance.save()
        return instance

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # representation['attachments'] = representation.pop('attachments', [])
        supplier_details_data = representation.pop('supplier_details', [])
        representation['supplier_details'] = supplier_details_data
        return representation
    class Meta:
        model = TenderMasterNewSurveyMasterConstructionMaterials
        fields = '__all__'
        list_serializer_class = CommonFilterListSerializer


