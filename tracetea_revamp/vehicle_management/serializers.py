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
from rest_framework.exceptions import ValidationError
class VehicleManagementSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleManagement
        fields = '__all__'

    def is_valid(self, raise_exception=False):
        """
        Override is_valid to flatten error messages.
        """
        valid = super().is_valid(raise_exception=False)
        if not valid and raise_exception:
            errors = self.errors
            first_error = next(
                (msg if isinstance(msg, str) else msg[0])
                for msg in errors.values()
            )
            
            raise ValidationError({"msg": first_error, "request_status": 0})
        return valid