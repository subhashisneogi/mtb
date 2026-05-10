from colorama import Back, Style
from django.db import transaction
from django.db.models import Sum, Q, Subquery, OuterRef, Case, When, F, Max, IntegerField, FloatField, ExpressionWrapper, Func, Value, CharField
from django.db.models.functions import Concat
from rest_framework.exceptions import APIException
from django.template import Template, Context
from django.forms.models import model_to_dict
from datetime import datetime, time
from functools import reduce
import operator
import pandas as pd
import numpy as np
from django.db.models import Q
import pprint
import requests
import urllib3
from urllib.parse import quote
from rest_framework.test import APIRequestFactory
from django.http import QueryDict
from knox.models import AuthToken
from requests.auth import HTTPBasicAuth
from decimal import ROUND_HALF_UP
import mimetypes
from datetime import date, timedelta
from rest_framework.serializers import ModelSerializer
from django.apps import apps
import importlib
from .serializers import *
from .models import *
from django.http import HttpResponse
from django.shortcuts import redirect
from django.contrib import messages
from django.utils.http import url_has_allowed_host_and_scheme
from django.template.loader import render_to_string
import pdfkit
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
import logging
from urllib.parse import urlparse 
import mimetypes
import urllib3
import uuid

from django.db import connection
from django.db.models import CharField, Expression, Value
from django.db.models.functions import Cast, Replace
from django_mysql.models import GroupConcat as StringAggCustom
from collections import Counter


def get_api_exception_message(exception, default_message="Something went wrong."):
    detail = getattr(exception, "detail", None)
    if isinstance(detail, dict):
        msg = detail.get("msg") or detail.get("detail") or detail.get("message")
        if msg:
            return str(msg)
    if isinstance(detail, (list, tuple)) and detail:
        return str(detail[0])
    if detail:
        return str(detail)
    return str(exception) if str(exception) else default_message


def soft_delete_instance_for_web(request, instance, redirect_url, success_message="Data Deleted Successfully", not_found_message="Data not found."):
    if not instance:
        messages.error(request, not_found_message)
        return redirect(redirect_url)

    if not hasattr(instance, "is_deleted"):
        messages.error(request, "This record cannot be deleted safely.")
        return redirect(redirect_url)

    try:
        instance.is_deleted = True
        update_fields = ["is_deleted"]
        if any(field.name == "updated_at" for field in instance._meta.fields):
            update_fields.append("updated_at")
        instance.save(update_fields=update_fields)
    except APIException as exception:
        messages.error(request, get_api_exception_message(exception))
    except Exception as exception:
        messages.error(request, str(exception) if str(exception) else "Something went wrong.")
    else:
        messages.success(request, success_message)

    return redirect(redirect_url)


def get_safe_next_url(request, default_url):
    next_url = request.GET.get("next") or request.POST.get("next")
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        return next_url
    return default_url


def process_filters(filter_name, filter_value):
    resp = Q()
    if filter_value == 'true':
        filter_value = True
    if filter_value == 'false':
        filter_value = False
    if filter_name.endswith('__isblank'):
        filter_name = filter_name.replace('__isblank','__exact')
        filter_value = ''
    if filter_name.endswith('__in') and not isinstance(filter_value,list):
        filter_value = filter_value.split(',')
    elif filter_name.startswith('compare__'):
        filter_value = F(filter_value)
        filter_name = filter_name.replace('compare__', '')
    if filter_name.startswith('exclude__'):
        resp = ~Q(**{filter_name.replace('exclude__', ''):filter_value})
    else:
        resp = Q(**{filter_name:filter_value})
    return resp

def process_filters_response(search):
    search_updated = []
    for filter_name, filter_value in search.items():
        search_list = Q()
        if '__or__' in filter_name:
            search_processed = []
            filter_name_list = filter_name.split('__or__')
            filter_value_list = filter_value.split('__or__')
            for index in range(len(filter_name_list)):
                search_processed.append(process_filters(filter_name_list[index],filter_value_list[index]))
            search_list = reduce(operator.or_,search_processed)
        else:
            search_list = process_filters(filter_name,filter_value)
        search_updated.append(search_list)
    return search_updated


def custom_web_filters(request, search: dict, extras: list, parent=None):
    valid_filters = ['id', 'all', 'page_size', 'page', 'order_by', 'hideLoader', 'order', 'my_debug']
    valid_filters = valid_filters+extras
    # print(Back.CYAN,"*"*100)
    # print("query_params -> ",request.query_params)
    # print("search -> ",search)
    # print('extras ->', extras)
    # print("valid_filters -> ",valid_filters)
    for filter_name, filter_value in request.GET.items():
        if filter_name not in valid_filters and filter_value:
            search[f'{filter_name}'] = filter_value
    if parent:
        search = {f'{parent}__{key}': value for key, value in search.items()}
    search_updated = process_filters_response(search)
    # print("search -> ",search)
    # print("search_updated -> ",search_updated)
    # print("*"*100,Style.RESET_ALL)
    return search_updated

def custom_filters(request, search: dict, extras: list, parent=None):
    valid_filters = ['id', 'all', 'page_size', 'page', 'order_by', 'hideLoader', 'order', 'my_debug']
    valid_filters = valid_filters+extras
    # print(Back.CYAN,"*"*100)
    # print("query_params -> ",request.query_params)
    # print("search -> ",search)
    # print('extras ->', extras)
    # print("valid_filters -> ",valid_filters)
    for filter_name, filter_value in request.query_params.items():
        if filter_name not in valid_filters and filter_value:
            search[f'{filter_name}'] = filter_value
    if parent:
        search = {f'{parent}__{key}': value for key, value in search.items()}
    search_updated = process_filters_response(search)
    # print("search -> ",search)
    # print("search_updated -> ",search_updated)
    # print("*"*100,Style.RESET_ALL)
    return search_updated

def process_attachments(file_data):
    mime_type = file_data.get('mime_type', None)
    file_content = file_data.get('file_data', None)
    raw_file_name = file_data.get('raw_file_name', None)
    try:
        if file_content:
            attachment_content = base64.b64decode(file_content)
            file_name = raw_file_name if raw_file_name else f"{uuid.uuid4().hex}"
            mime_type_obj = MimeTypes.objects.filter(mime_type=mime_type).first()
            if not mime_type_obj:
                file_extension = mimetypes.guess_extension(mime_type)
            else:
                file_extension=mime_type_obj.file_extension
            file_extension = file_extension if file_extension else '.bin'
            file_name_with_extension = f"{file_name}{file_extension}"
            return ContentFile(attachment_content, name=file_name_with_extension)
        else:
            None
    except Exception as e:
        print(Back.MAGENTA, f"Exception while adding new attachments: {str(e)}", Style.RESET_ALL)

def wrap_f_with_cast(expression, output_field):
    if isinstance(expression, Func):
        # For Function objects like Concat, use source_expressions
        if hasattr(expression, 'source_expressions'):
            new_sources = []
            for child in expression.source_expressions:
                new_sources.append(wrap_f_with_cast(child, output_field))
            expression.source_expressions = new_sources
        return expression
    elif isinstance(expression, Expression):
        # For other expressions, check for children
        if hasattr(expression, 'children'):
            new_children = []
            for child in expression.children:
                new_children.append(wrap_f_with_cast(child, output_field))
            expression.children = new_children
        return expression
    else:
        return Cast(expression, output_field=output_field)
class GroupConcat(StringAggCustom):
    def __init__(self, expression, **extra):
        # Set the default delimiter and output field
        delimiter = ', '
        output_field = extra.pop('output_field', CharField())
        if connection.vendor == 'postgresql' and 'ordering' in extra:
            extra.pop("ordering")
            if not isinstance(expression, Expression):
                extra['order_by'] = expression
                extra.pop("distinct")
        expression = Replace(
            Cast(wrap_f_with_cast(expression, CharField()), output_field=CharField()),
            Value(','),
            Value('&#44;')
        )
        super().__init__(
            expression, 
            delimiter=delimiter, 
            separator=delimiter, 
            output_field=output_field, 
            **extra
        )
