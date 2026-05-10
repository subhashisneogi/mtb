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
from django.template.loader import render_to_string
import pdfkit
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
import logging
from urllib.parse import urlparse 

def get_details_from_instance(instance,extras=[],type="list"):  
    res = [] if type == 'list' else None
    try:
        if instance:
            if instance.__class__.__name__ == 'ManyRelatedManager':
                temp_instances = instance.all()
                for temp_instance in temp_instances:
                    res.append(get_details_from_instance(temp_instance,[],'dict'))
            else:
                flag = True
                # result = {field.name:field.value_from_object(instance) if field.value_from_object(instance)
                #            is not None else None for field in instance._meta.fields}
                # result = model_to_dict(instance)
                result = {}
                for field in instance._meta.fields:
                    try:
                        field_value = field.value_from_object(instance)
                        if (isinstance(field, models.FileField) or isinstance(field, models.ImageField)):
                            result[field.name] = field_value.url if field_value else None
                        elif isinstance(field, models.ForeignKey):
                            result[field.name] = field_value
                            result[field.name + "_id"] = field_value
                        else:
                            result[field.name] = field_value
                    except ValueError:
                        result[field.name] = None
                if 'is_deleted' in result and result['is_deleted']:
                    flag = False
                if flag:
                    for extra in extras:
                        result[extra+'_details'] = get_details_from_instance(getattr(instance,extra))
                    if type == 'list':
                        res.append(result)
                    else:
                        res = result
        else:
            res = None
    except Exception as e:
        print(e)
    return res