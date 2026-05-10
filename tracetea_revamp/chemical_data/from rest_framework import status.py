from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import MapAreaMaster, MapAreaLandDetails
from .serializers import MapAreaDetailsSerializer

class MapAreaImageUploadAPIView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        grower_id = request.data.get('grower_id')
        map_image_base64 = request.data.get('map_image')
        water_source = request.data.get('water_source')
        land_near_by = request.data.get('land_near_by')
        map_details = request.data.get('map_details', [])

        logged_user_details = Profile.objects.filter(user_id=request.user.id).first()
        logged_user_type = str(logged_user_details.user_type.name)

        aggregator_details, grower_details, blf_details = None, None, None
        blf_details = BlfProfile.objects.filter(user_id=request.user.id).first()

        if logged_user_type == "aggregator":
            aggregator_details = AggregatorProfile.objects.filter(user_id=request.user.id).first()

        if grower_id:
            grower_details = GrowerProfile.objects.filter(id=grower_id).first()

        if logged_user_type == 'blf':
            blf_details = BlfProfile.objects.filter(user_id=request.user.id).first()

        # Convert base64 image to Django File if provided
        map_image_file = None
        if map_image_base64:
            try:
                decoded_data = base64.b64decode(map_image_base64)
                map_image_file = ContentFile(decoded_data, name=f'{grower_details}-map-image.png')
            except Exception as e:
                return Response({'status': status.HTTP_400_BAD_REQUEST, 'request_status': 0, 'msg': 'Invalid base64 image'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                map_area_master = MapAreaMaster(
                    grower_id=grower_details,
                    water_source=water_source,
                    land_near_by=land_near_by,
                    is_image_upload=False,
                    is_digital_upload=False,
                    map_image=map_image_file
                )
                map_area_master.save()

                for detail in map_details:
                    map_area_id = detail.get('map_area_id')
                    total_area = detail.get('total_area')

                    map_area_name = MapAreaNameMaster.objects.filter(id=map_area_id).first()
                    if not map_area_name:
                        return Response({'msg': 'Map area name not found'}, status=status.HTTP_404_NOT_FOUND)

                    map_area_land_details = MapAreaLandDetails(
                        grower_id=grower_details,
                        map_area_name=map_area_name,
                        total_areas=float(total_area),
                        water_source=water_source,
                        land_near_by=land_near_by,
                        blf_id=blf_details.id if blf_details else None,
                        aggregator_id=aggregator_details.id if aggregator_details else None,
                        map_image=map_image_file
                    )
                    map_area_land_details.save()

                serializer = MapAreaDetailsSerializer(map_area_land_details)
                return Response({'results': {'Data': request.data}, 'msg': 'Map Area Details Created Successfully',
                                'status': status.HTTP_201_CREATED, 'request_status': 1})
        except Exception as e:
            return Response({'status': status.HTTP_400_BAD_REQUEST, 'request_status': 0, 'msg': str(e)}, status=status.HTTP_400_BAD_REQUEST)