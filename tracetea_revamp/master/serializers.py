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


class RegionSerializer(serializers.ModelSerializer):
    """ Region Model Serializer @vivek"""

    class Meta:
        model = Region
        fields = '__all__'


class AndroidVersionSerializer(serializers.ModelSerializer):
    """ AndroidVersion Model Serializer @vivek"""

    class Meta:
        model = AndroidVersion
        fields = '__all__'