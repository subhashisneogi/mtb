from rest_framework import serializers
from django.contrib.auth.models import *
from rest_framework.exceptions import APIException
from django.contrib.auth import authenticate

from django.contrib import auth
from rest_framework.exceptions import AuthenticationFailed
""" Reset password and send link with token"""
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import smart_str, force_str, smart_bytes, DjangoUnicodeDecodeError
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from .models import *
from rest_framework import status
from django.db.models import Q
from gardens_managment.models import Plot,Gardens
from user_profile.aggregator_api_models import *
from user_profile.blf_api_models import *
from chemical_data.models import *
from weighment_supply.models import *
from leaf_receipt.models import *
from user_profile.grower_api_models import *
from user_profile.serializers import GrowerProfileSerializer
from django.core.files.base import ContentFile
import base64
from master.helper import get_details_from_instance

import six
import uuid
from django.core.files.base import ContentFile
from user_profile.helpers import *


class FarmersAggreementFormsSignatureUploadSerializer(serializers.ModelSerializer):
    farmer_signature_file_base64 = serializers.CharField(write_only=True)
    
    class Meta:
        model = FarmersAggreementForms
        fields = ['grower', 'place', 'date', 'farmer_signature_file_base64']

    def create(self, validated_data):
        farmer_signature_file_base64 = validated_data.pop('farmer_signature_file_base64')
        
        # Decode the base64 file
        format, imgstr = farmer_signature_file_base64.split(';base64,') 
        ext = format.split('/')[-1]
        farmer_signature_file = ContentFile(base64.b64decode(imgstr), name=f"{uuid.uuid4()}.{ext}")
        
        # Create the instance with the decoded file
        farmers_agreement_form = FarmersAggreementForms.objects.create(
            farmer_signature_file=farmer_signature_file,
            **validated_data
        )
        return farmers_agreement_form



class MapAreaLandDetailsSerializer(serializers.ModelSerializer):
    map_area_name_details = serializers.SerializerMethodField()
    class Meta:
        model = MapAreaLandDetails
        fields = '__all__'

    def get_map_area_name_details(self, instance):
        """
        Return details of the related MapAreaNameMaster for this land detail.
        """
        if instance.map_area_name:
            return {
                "id": instance.map_area_name.id,
                "name": instance.map_area_name.name
            }
        return None


class MapAreaNameMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = MapAreaNameMaster
        fields = ['id', 'name', 'slug']

class MapAreaMasterSerializer(serializers.ModelSerializer):
    map_area_land_details = MapAreaLandDetailsSerializer(many=True, read_only=True)
    class Meta:
        model = MapAreaMaster
        fields = '__all__'

    def create(self, validated_data):
        request = self.context.get('request')
        grower_id = request.data.get('grower')
        file_data = request.data.get('file_data')
        mime_type = request.data.get('mime_type')
        is_digital_upload = request.data.get('is_digital_upload', False)

        if grower_id:
            validated_data['grower_id'] = grower_id

        instance = MapAreaMaster.objects.create(**validated_data)
        # Handle file upload
        if file_data:
            # try:
                attachment_content = process_attachments({
                    'mime_type': mime_type,
                    'file_data': file_data
                })
                uploaded_file = attachment_content
                if is_digital_upload:
                    instance.digital_map_image = uploaded_file
                    instance.is_digital_upload = True
                else:
                    instance.pdf_map_image = uploaded_file
                    instance.is_image_upload = True
                instance.map_image = uploaded_file
                instance.save()

            # except Exception as e:
            #     raise serializers.ValidationError({
            #         "file_data": f"File upload failed: {str(e)}"
            #     })

        # Create related MapAreaLandDetails
        MapAreaLandDetails.objects.create(
            grower_id=grower_id,
            map_area_master=instance,
            map_area_name_id=request.data.get('map_area_name'),
            total_areas=request.data.get('total_area'),
            coordinate=request.data.get('coordinate'),
        )
        return instance
    
    def update(self, instance, validated_data):
        request = self.context.get('request')
        grower_id = request.data.get('grower')
        file_data = request.data.get('file_data')
        mime_type = request.data.get('mime_type')
        is_digital_upload = request.data.get('is_digital_upload', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if grower_id:
            instance.grower_id = grower_id
        if file_data:
            try:
                attachment_content = process_attachments({
                    'mime_type': mime_type,
                    'file_data': file_data
                })
                uploaded_file = attachment_content
                if is_digital_upload:
                    instance.digital_map_image = uploaded_file
                    instance.is_digital_upload = True
                else:
                    instance.pdf_map_image = uploaded_file
                    instance.is_image_upload = True
                instance.map_image = uploaded_file
            except Exception as e:
                raise serializers.ValidationError({
                    "file_data": f"File upload failed: {str(e)}"
                })
        instance.save()

        # Update or create related MapAreaLandDetails
        map_area_name_id = request.data.get('map_area_name')
        total_areas = request.data.get('total_area')
        coordinate = request.data.get('coordinate')
        if map_area_name_id:
            land_detail, created = MapAreaLandDetails.objects.update_or_create(
                map_area_master=instance,
                map_area_name_id=map_area_name_id,
                defaults={
                    "grower_id": grower_id,
                    "total_areas": total_areas,
                    "coordinate": coordinate,
                }
            )
        return instance
class FarmersAggreementMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = FarmersAggreementMaster
        fields = '__all__'

# class FarmersAggreementFormsGetSerializer(serializers.ModelSerializer):
#     grower= serializers.SerializerMethodField(read_only=True)
#     class Meta:
#         model = FarmersAggreementForms
#         fields = '__all__'        

#     def get_grower(self, obj):
#         details = obj.grower
#         grower = GrowerProfileSerializer(details, context=self.context).data
#         return grower   

   

class FarmersAggreementFormsSerializer(serializers.ModelSerializer):
    farmer_signature_file_base64 = serializers.CharField(write_only=True, required=False)
    blf_grade_official_signature_file_base64 = serializers.CharField(write_only=True, required=False)
    grower_details= serializers.SerializerMethodField()
    class Meta:
        model = FarmersAggreementForms
        fields = '__all__'

    def get_grower_details(self, instance):
        return get_details_from_instance(instance.grower,)

    def create(self, validated_data):
        farmer_signature_file_base64 = validated_data.pop('farmer_signature_file_base64', None)
        blf_grade_official_signature_file_base64 = validated_data.pop('blf_grade_official_signature_file_base64', None)
        grower_id = validated_data['grower_id']
        print(grower_id)
        # Fetch grower's username
        grower = GrowerProfile.objects.filter(id=grower_id).first()
        if grower:
            grower_user_name = grower.user.username if grower else "farmer_signature"
        else:
            grower_user_name='farmer_signature'
        if farmer_signature_file_base64:
            farmer_signature_file_data = base64.b64decode(farmer_signature_file_base64)
            validated_data['farmer_signature_file'] = ContentFile(farmer_signature_file_data, f'{grower_user_name}_signature.png')

        if blf_grade_official_signature_file_base64:
            blf_signature_file_data = base64.b64decode(blf_grade_official_signature_file_base64)
            validated_data['blf_grade_official_signature_file'] = ContentFile(blf_signature_file_data, f'{grower_user_name}_signature.png')

        return super().create(validated_data)

    def update(self, instance, validated_data):
        farmer_signature_file_base64 = validated_data.pop('farmer_signature_file_base64', None)
        blf_grade_official_signature_file_base64 = validated_data.pop('blf_grade_official_signature_file_base64', None)
        grower_id = validated_data.get('grower_id', instance.grower_id)

        # Fetch grower's username
        grower = GrowerProfile.objects.filter(id=grower_id).first()
        grower_user_name = grower.user.username if grower else "farmer_signature"

        if farmer_signature_file_base64:
            farmer_signature_file_data = base64.b64decode(farmer_signature_file_base64)
            instance.farmer_signature_file.save(f'{grower_user_name}_signature.png', ContentFile(farmer_signature_file_data), save=False)

        if blf_grade_official_signature_file_base64:
            blf_signature_file_data = base64.b64decode(blf_grade_official_signature_file_base64)
            instance.blf_grade_official_signature_file.save(f'{grower_user_name}_signature.png', ContentFile(blf_signature_file_data), save=False)

        return super().update(instance, validated_data)