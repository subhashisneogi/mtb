from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse
from django.db.models import Q
from django.http import JsonResponse
from django.db.models.functions import Coalesce
from django.db.models import Sum, Count, Value
from django.template.loader import render_to_string
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.contrib.auth import get_user_model
User = get_user_model()
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView, UpdateView, CreateView
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.paginator import Paginator , EmptyPage, PageNotAnInteger
import openpyxl
from django.http import HttpResponse
from openpyxl.utils import get_column_letter
from django.db import transaction
from django.http import HttpResponse
from datetime import datetime
from master.common import CommonMixin
from .models import *
from .forms import *
from accounts.forms import *
from gardens_managment.models import *
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, IsAuthenticatedOrReadOnly, AllowAny
from django.core.paginator import Paginator
from knox.auth import TokenAuthentication
from weighment_supply.models import *
from master.utils import *
from django.template import loader
from django.utils import timezone
import pytz
from master.decorators import *
from django.template.loader import get_template 
from .helpers import *
import datetime
import requests
import pandas as pd
import fuzzymatcher
from django.db.models import Q
import math
import numpy as np
import requests 

@permission_required_admin
def users_profile_list(request, usertype_slug):
    """ users list Superadmin """
    

    if not request.GET._mutable:
        request.GET._mutable = True
    resp = UserProfileAPIView().get(request)
    _list = list(resp.data['results'])
    count['data_list'] = _list

    context={}
    return CommonMixin.render(request, 'profile/user_list.html', context)








