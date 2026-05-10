from rest_framework import serializers
from django.contrib.auth.models import *
from rest_framework.exceptions import APIException
from django.contrib.auth import authenticate
from django.contrib import auth
from rest_framework.exceptions import AuthenticationFailed
from rest_framework import status

from .models import *
from user_profile.models import *

class LoginFailedException(APIException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = {"msg": "Please check the username and password"}
    default_code = "login_failed"

class AccountDisabledException(APIException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = {"msg":"The account has been disabled!"}
    default_code = "account_disabled"

class LoginSerializer(serializers.Serializer):
    """ Login serializer @ vivek """
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        user = authenticate(
            username=data['username'],
            password=data['password'],
            active_check=True
        )
        if user is not None:
            if user.is_active:
                return user
            else:
                raise AccountDisabledException()
        else:
            raise LoginFailedException()

# class LoginSerializer(serializers.Serializer):
#     """ Login serializer @ vivek"""
#     username = serializers.CharField()
#     password = serializers.CharField()

#     def validate(self, data):
#         user = authenticate(username=data['username'],password=data['password'],active_check=True)
#         if user is not None:
#             print("check")
#             if user.is_active == True:
#                 return user
#             else:
#                 raise serializers.ValidationError({ 'msg': 'The account has been disabled!'},code='authorization')
#         else:
#             raise serializers.ValidationError({ 'msg': 'Please check the username and password'}, code='authorization')

class SetNewPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(min_length=3, max_length=50, write_only=True)
    confirm_password = serializers.CharField(min_length=3, max_length=50, write_only=True)
    user_id = serializers.IntegerField(write_only=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({'msg': "Passwords do not match"})
        return attrs
    
    def save(self, **kwargs):
        user_id = self.validated_data['user_id']
        password = self.validated_data['new_password']
        try:
            user = User.objects.get(id=user_id)
            user.set_password(password)
            user.save()
            return user
        except User.DoesNotExist:
            raise serializers.ValidationError({'msg': 'User not found'})

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    confirm_password = serializers.CharField(required=True)