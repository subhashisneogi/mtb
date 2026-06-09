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
