class BDDepartmentMasterSerializer(serializers.ModelSerializer):
    """
    Serializer for BD Department Master with nested details
    """
    concerened_details = BDMasterConcerenedDetailsSerializer(
        many=True, required=False,
        source="bd_master_concerened_details_bd_master",
    )
    department_progress = BDMasterDepartmentProgressSerializer(
        many=True, required=False,
        source="bd_master_department_progress_bd_master",
    )
    competitors = BDMasterCompetitorsSerializer(
        many=True, required=False,
        source="bd_master_competitors_bd_master",
    )
    visit_details = BDMasterVisitDetailsSerializer(
        many=True, required=False,
        source="bd_master_visit_details_bd_master",
    )
    attachments = BDMasterAttachmentsSerializer(
        many=True, required=False,
        source="bd_master_attachments_bd_master",
    )
    sector_details = serializers.SerializerMethodField()
    state_details  = serializers.SerializerMethodField()
    city_details   = serializers.SerializerMethodField()

    def get_state_details(self, instance):
        return get_details_from_instance(instance.state, type='dict')

    def get_city_details(self, instance):
        return get_details_from_instance(instance.city)

    def get_sector_details(self, instance):
        return get_details_from_instance(instance.tender_sector)

    @transaction.atomic
    def create(self, validated_data):
        concerened_details_data  = validated_data.pop('bd_master_concerened_details_bd_master', [])
        department_progress_data = validated_data.pop('bd_master_department_progress_bd_master', [])
        competitors_data         = validated_data.pop('bd_master_competitors_bd_master', [])
        visit_details_data       = validated_data.pop('bd_master_visit_details_bd_master', [])

        bd_master    = BDMaster.objects.create(**validated_data)
        current_user = bd_master.created_by if bd_master.created_by else None

        for concerened_data in concerened_details_data:
            clean = {k: v for k, v in concerened_data.items()
                     if k not in ('organization', 'bd_master', 'created_by', 'updated_by', 'id')}
            BDMasterConcerenedDetails.objects.create(
                organization=bd_master.organization,
                bd_master=bd_master,
                created_by=current_user,
                **clean,
            )

        for progress_data in department_progress_data:
            clean = {k: v for k, v in progress_data.items()
                     if k not in ('organization', 'bd_master', 'created_by', 'updated_by', 'id')}
            BDMasterDepartmentProgress.objects.create(
                organization=bd_master.organization,
                bd_master=bd_master,
                created_by=current_user,
                **clean,
            )

        for competitor_data in competitors_data:
            clean = {k: v for k, v in competitor_data.items()
                     if k not in ('organization', 'bd_master', 'created_by', 'updated_by', 'id')}
            BDMasterCompetitors.objects.create(
                organization=bd_master.organization,
                bd_master=bd_master,
                created_by=current_user,
                **clean,
            )

        for visit_data in visit_details_data:
            clean = {k: v for k, v in visit_data.items()
                     if k not in ('organization', 'bd_master', 'created_by', 'updated_by', 'id')}
            BDMasterVisitDetails.objects.create(
                organization=bd_master.organization,
                bd_master=bd_master,
                created_by=current_user,
                **clean,
            )

        bd_master.save()
        return bd_master

    @transaction.atomic
    def update(self, instance, validated_data):
        # Update base fields
        for field in instance._meta.fields:
            field_name = field.name
            if field_name in validated_data:
                setattr(instance, field_name, validated_data[field_name])

        current_user = instance.updated_by if instance.updated_by else None

        # Handle concerened details
        concerened_details_data = validated_data.get('bd_master_concerened_details_bd_master', None)
        if concerened_details_data is not None:
            existing_concerened_details = instance.bd_master_concerened_details_bd_master.filter(is_deleted=False)
            for item_data in concerened_details_data:
                item_id       = item_data.get('id')
                existing_item = next((item for item in existing_concerened_details if item.id == item_id), None)
                if not existing_item:
                    clean = {k: v for k, v in item_data.items()
                             if k not in ('organization', 'bd_master', 'created_by', 'updated_by', 'id')}
                    BDMasterConcerenedDetails.objects.create(
                        organization=instance.organization,
                        bd_master=instance,
                        created_by=current_user,
                        **clean,
                    )
                else:
                    for field in existing_item._meta.fields:
                        field_name = field.name
                        if field_name in item_data and field_name not in ('organization', 'bd_master', 'created_by'):
                            setattr(existing_item, field_name, item_data[field_name])
                    existing_item.updated_by = current_user
                    existing_item.save()
            for existing_item in existing_concerened_details:
                if existing_item.id not in [i.get('id') for i in concerened_details_data]:
                    existing_item.is_deleted = True
                    existing_item.updated_by = current_user
                    existing_item.save()

        # Handle department progress
        department_progress_data = validated_data.get('bd_master_department_progress_bd_master', None)
        if department_progress_data is not None:
            existing_department_progress = instance.bd_master_department_progress_bd_master.filter(is_deleted=False)
            for item_data in department_progress_data:
                item_id       = item_data.get('id')
                existing_item = next((item for item in existing_department_progress if item.id == item_id), None)
                if not existing_item:
                    clean = {k: v for k, v in item_data.items()
                             if k not in ('organization', 'bd_master', 'created_by', 'updated_by', 'id')}
                    BDMasterDepartmentProgress.objects.create(
                        organization=instance.organization,
                        bd_master=instance,
                        created_by=current_user,
                        **clean,
                    )
                else:
                    for field in existing_item._meta.fields:
                        field_name = field.name
                        if field_name in item_data and field_name not in ('organization', 'bd_master', 'created_by'):
                            setattr(existing_item, field_name, item_data[field_name])
                    existing_item.updated_by = current_user
                    existing_item.save()
            for existing_item in existing_department_progress:
                if existing_item.id not in [i.get('id') for i in department_progress_data]:
                    existing_item.is_deleted = True
                    existing_item.updated_by = current_user
                    existing_item.save()

        # Handle competitors
        competitors_data = validated_data.get('bd_master_competitors_bd_master', None)
        if competitors_data is not None:
            existing_competitors = instance.bd_master_competitors_bd_master.filter(is_deleted=False)
            for item_data in competitors_data:
                item_id       = item_data.get('id')
                existing_item = next((item for item in existing_competitors if item.id == item_id), None)
                if not existing_item:
                    clean = {k: v for k, v in item_data.items()
                             if k not in ('organization', 'bd_master', 'created_by', 'updated_by', 'id')}
                    BDMasterCompetitors.objects.create(
                        organization=instance.organization,
                        bd_master=instance,
                        created_by=current_user,
                        **clean,
                    )
                else:
                    for field in existing_item._meta.fields:
                        field_name = field.name
                        if field_name in item_data and field_name not in ('organization', 'bd_master', 'created_by'):
                            setattr(existing_item, field_name, item_data[field_name])
                    existing_item.updated_by = current_user
                    existing_item.save()
            for existing_item in existing_competitors:
                if existing_item.id not in [i.get('id') for i in competitors_data]:
                    existing_item.is_deleted = True
                    existing_item.updated_by = current_user
                    existing_item.save()

        # Handle visit details
        visit_details_data = validated_data.get('bd_master_visit_details_bd_master', None)
        if visit_details_data is not None:
            existing_visit_details = instance.bd_master_visit_details_bd_master.filter(is_deleted=False)
            for item_data in visit_details_data:
                item_id       = item_data.get('id')
                existing_item = next((item for item in existing_visit_details if item.id == item_id), None)
                if not existing_item:
                    clean = {k: v for k, v in item_data.items()
                             if k not in ('organization', 'bd_master', 'created_by', 'updated_by', 'id')}
                    BDMasterVisitDetails.objects.create(
                        organization=instance.organization,
                        bd_master=instance,
                        created_by=current_user,
                        **clean,
                    )
                else:
                    for field in existing_item._meta.fields:
                        field_name = field.name
                        if field_name in item_data and field_name not in ('organization', 'bd_master', 'created_by'):
                            setattr(existing_item, field_name, item_data[field_name])
                    existing_item.updated_by = current_user
                    existing_item.save()
            for existing_item in existing_visit_details:
                if existing_item.id not in [i.get('id') for i in visit_details_data]:
                    existing_item.is_deleted = True
                    existing_item.updated_by = current_user
                    existing_item.save()

        instance.save()
        return instance

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['concerened_details']  = representation.pop('concerened_details', [])
        representation['department_progress'] = representation.pop('department_progress', [])
        representation['competitors']         = representation.pop('competitors', [])
        representation['visit_details']       = representation.pop('visit_details', [])
        return representation

    class Meta:
        model  = BDMaster
        fields = '__all__'
        read_only_fields = ['id']
        list_serializer_class = CommonFilterListSerializer


### without "id"
class BDDepartmentMasterSerializer(serializers.ModelSerializer):
    """
    Serializer for BD Department Master with nested details
    """
    concerened_details = BDMasterConcerenedDetailsSerializer(
        many=True, required=False,
        source="bd_master_concerened_details_bd_master",
    )
    department_progress = BDMasterDepartmentProgressSerializer(
        many=True, required=False,
        source="bd_master_department_progress_bd_master",
    )
    competitors = BDMasterCompetitorsSerializer(
        many=True, required=False,
        source="bd_master_competitors_bd_master",
    )
    visit_details = BDMasterVisitDetailsSerializer(
        many=True, required=False,
        source="bd_master_visit_details_bd_master",
    )
    attachments = BDMasterAttachmentsSerializer(
        many=True, required=False,
        source="bd_master_attachments_bd_master",
    )
    sector_details = serializers.SerializerMethodField()
    state_details  = serializers.SerializerMethodField()
    city_details   = serializers.SerializerMethodField()

    def get_state_details(self, instance):
        return get_details_from_instance(instance.state, type='dict')

    def get_city_details(self, instance):
        return get_details_from_instance(instance.city)

    def get_sector_details(self, instance):
        return get_details_from_instance(instance.tender_sector)

    @transaction.atomic
    def create(self, validated_data):
        concerened_details_data  = validated_data.pop('bd_master_concerened_details_bd_master', [])
        department_progress_data = validated_data.pop('bd_master_department_progress_bd_master', [])
        competitors_data         = validated_data.pop('bd_master_competitors_bd_master', [])
        visit_details_data       = validated_data.pop('bd_master_visit_details_bd_master', [])

        bd_master    = BDMaster.objects.create(**validated_data)
        current_user = bd_master.created_by if bd_master.created_by else None

        for item_data in concerened_details_data:
            clean = {k: v for k, v in item_data.items()
                     if k not in ('organization', 'bd_master', 'created_by', 'updated_by', 'id')}
            BDMasterConcerenedDetails.objects.create(
                organization=bd_master.organization,
                bd_master=bd_master,
                created_by=current_user,
                **clean,
            )

        for item_data in department_progress_data:
            clean = {k: v for k, v in item_data.items()
                     if k not in ('organization', 'bd_master', 'created_by', 'updated_by', 'id')}
            BDMasterDepartmentProgress.objects.create(
                organization=bd_master.organization,
                bd_master=bd_master,
                created_by=current_user,
                **clean,
            )

        for item_data in competitors_data:
            clean = {k: v for k, v in item_data.items()
                     if k not in ('organization', 'bd_master', 'created_by', 'updated_by', 'id')}
            BDMasterCompetitors.objects.create(
                organization=bd_master.organization,
                bd_master=bd_master,
                created_by=current_user,
                **clean,
            )

        for item_data in visit_details_data:
            clean = {k: v for k, v in item_data.items()
                     if k not in ('organization', 'bd_master', 'created_by', 'updated_by', 'id')}
            BDMasterVisitDetails.objects.create(
                organization=bd_master.organization,
                bd_master=bd_master,
                created_by=current_user,
                **clean,
            )

        bd_master.save()
        return bd_master

    @transaction.atomic
    def update(self, instance, validated_data):
        # Update base fields
        for field in instance._meta.fields:
            field_name = field.name
            if field_name in validated_data:
                setattr(instance, field_name, validated_data[field_name])

        current_user = instance.updated_by if instance.updated_by else None

        # Handle concerened details
        concerened_details_data = validated_data.get('bd_master_concerened_details_bd_master', None)
        if concerened_details_data is not None:
            instance.bd_master_concerened_details_bd_master.filter(is_deleted=False).update(
                is_deleted=True,
                updated_by=current_user,
            )
            for item_data in concerened_details_data:
                clean = {k: v for k, v in item_data.items()
                         if k not in ('organization', 'bd_master', 'created_by', 'updated_by', 'id')}
                BDMasterConcerenedDetails.objects.create(
                    organization=instance.organization,
                    bd_master=instance,
                    created_by=current_user,
                    **clean,
                )

        # Handle department progress
        department_progress_data = validated_data.get('bd_master_department_progress_bd_master', None)
        if department_progress_data is not None:
            instance.bd_master_department_progress_bd_master.filter(is_deleted=False).update(
                is_deleted=True,
                updated_by=current_user,
            )
            for item_data in department_progress_data:
                clean = {k: v for k, v in item_data.items()
                         if k not in ('organization', 'bd_master', 'created_by', 'updated_by', 'id')}
                BDMasterDepartmentProgress.objects.create(
                    organization=instance.organization,
                    bd_master=instance,
                    created_by=current_user,
                    **clean,
                )

        # Handle competitors
        competitors_data = validated_data.get('bd_master_competitors_bd_master', None)
        if competitors_data is not None:
            instance.bd_master_competitors_bd_master.filter(is_deleted=False).update(
                is_deleted=True,
                updated_by=current_user,
            )
            for item_data in competitors_data:
                clean = {k: v for k, v in item_data.items()
                         if k not in ('organization', 'bd_master', 'created_by', 'updated_by', 'id')}
                BDMasterCompetitors.objects.create(
                    organization=instance.organization,
                    bd_master=instance,
                    created_by=current_user,
                    **clean,
                )

        # Handle visit details
        visit_details_data = validated_data.get('bd_master_visit_details_bd_master', None)
        if visit_details_data is not None:
            instance.bd_master_visit_details_bd_master.filter(is_deleted=False).update(
                is_deleted=True,
                updated_by=current_user,
            )
            for item_data in visit_details_data:
                clean = {k: v for k, v in item_data.items()
                         if k not in ('organization', 'bd_master', 'created_by', 'updated_by', 'id')}
                BDMasterVisitDetails.objects.create(
                    organization=instance.organization,
                    bd_master=instance,
                    created_by=current_user,
                    **clean,
                )

        instance.save()
        return instance

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['concerened_details']  = representation.pop('concerened_details', [])
        representation['department_progress'] = representation.pop('department_progress', [])
        representation['competitors']         = representation.pop('competitors', [])
        representation['visit_details']       = representation.pop('visit_details', [])
        return representation

    class Meta:
        model  = BDMaster
        fields = '__all__'
        read_only_fields = ['id']
        list_serializer_class = CommonFilterListSerializer
