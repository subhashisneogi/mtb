from django.shortcuts import render
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
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, IsAuthenticatedOrReadOnly, AllowAny
from django.core.paginator import Paginator
from knox.auth import TokenAuthentication
from django.db import transaction
from rest_framework import status
from rest_framework.exceptions import APIException
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import smart_str, force_str, smart_bytes, DjangoUnicodeDecodeError
from django.db import transaction
from django.db.models import Q
from master.common import CommonMixin
from .models import *
from master.forms import *
from accounts.forms import *
# Create your views here.
from accounts.models import *
from accounts.serializers import *
import collections
from django.contrib.auth import authenticate, login 
from knox.auth import TokenAuthentication
from rest_framework import permissions
from knox.models import AuthToken
#from AuthTokenSerializer import *
from knox.views import LoginView as KnoxLoginView
from user_profile.models import *
from user_profile.serializers import *
from .serializers import *
from .forms import VehicleManagementForm
from user_profile.helpers import *

# Create your views here.
def _is_ajax_request(request):
    return request.headers.get('x-requested-with') == 'XMLHttpRequest'


def _vehicle_list_url(request):
    query = request.GET.copy()
    query.pop('next', None)
    url = reverse('vehicle_management:vehicle_list')
    if query.urlencode():
        return f"{url}?{query.urlencode()}"
    return url


def _vehicle_queryset(search_query):
    queryset = VehicleManagement.cmobjects.select_related(
        'created_by',
        'created_by__profile',
        'created_by__profile__user_type',
    ).order_by('-id')
    if search_query:
        queryset = queryset.filter(
            Q(vehicle_number__icontains=search_query) |
            Q(vehicle_type__icontains=search_query) |
            Q(mobile_number__icontains=search_query) |
            Q(created_by__username__icontains=search_query) |
            Q(created_by__profile__user_type__name__icontains=search_query)
        )
    return queryset


@login_required
def vehicle_list(request):
    search_query = request.GET.get('q', '').strip()
    queryset = _vehicle_queryset(search_query)
    paginator = Paginator(queryset, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'vehicle_list': page_obj.object_list,
        'page_obj': page_obj,
        'paginator': paginator,
        'is_paginated': page_obj.has_other_pages(),
        'search_query': search_query,
        'list_url': reverse('vehicle_management:vehicle_list'),
        'current_list_url': _vehicle_list_url(request),
    }

    if _is_ajax_request(request):
        return CommonMixin.render(request, 'vehicle/_vehicle_table.html', context)
    return CommonMixin.render(request, 'vehicle/vehicle_list.html', context)


@login_required
def vehicle_create(request):
    default_url = reverse('vehicle_management:vehicle_list')
    next_url = get_safe_next_url(request, default_url)

    if request.method == 'POST':
        form = VehicleManagementForm(request.POST)
        if form.is_valid():
            vehicle = form.save(commit=False)
            vehicle.created_by = request.user
            vehicle.updated_by = request.user
            vehicle.save()
            messages.success(request, 'Vehicle Created Successfully')
            return redirect(next_url)
    else:
        form = VehicleManagementForm()

    return CommonMixin.render(request, 'vehicle/vehicle_form.html', {
        'form': form,
        'next_url': next_url,
        'is_create': True,
    })


@login_required
def vehicle_edit(request, id):
    vehicle = VehicleManagement.cmobjects.select_related(
        'created_by',
        'created_by__profile',
        'created_by__profile__user_type',
    ).filter(id=id).first()
    default_url = reverse('vehicle_management:vehicle_list')
    next_url = get_safe_next_url(request, default_url)

    if not vehicle:
        messages.error(request, 'Vehicle data not found.')
        return redirect(next_url)

    if request.method == 'POST':
        form = VehicleManagementForm(request.POST, instance=vehicle)
        if form.is_valid():
            vehicle = form.save(commit=False)
            vehicle.updated_by = request.user
            vehicle.save()
            messages.success(request, 'Vehicle Updated Successfully')
            return redirect(next_url)
    else:
        form = VehicleManagementForm(instance=vehicle)

    return CommonMixin.render(request, 'vehicle/vehicle_form.html', {
        'form': form,
        'vehicle': vehicle,
        'next_url': next_url,
        'is_create': False,
    })


@login_required
def vehicle_view(request, id):
    vehicle = VehicleManagement.cmobjects.select_related(
        'created_by',
        'created_by__profile',
        'created_by__profile__user_type',
    ).filter(id=id).first()
    next_url = get_safe_next_url(request, reverse('vehicle_management:vehicle_list'))

    if not vehicle:
        messages.error(request, 'Vehicle data not found.')
        return redirect(next_url)

    return render(request, 'vehicle/vehicle_view.html', {
        'vehicle': vehicle,
        'next_url': next_url,
    })


@login_required
def vehicle_delete(request, id):
    next_url = get_safe_next_url(request, reverse('vehicle_management:vehicle_list'))
    vehicle = VehicleManagement.cmobjects.filter(id=id).first()
    return soft_delete_instance_for_web(
        request,
        vehicle,
        next_url,
        success_message='Vehicle Deleted Successfully',
        not_found_message='Vehicle data not found.',
    )


class VehicleManagementAPIView(APIView):
    """ Vehicle Management View"""
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    def get(self, request):
        id = self.request.query_params.get('id', None)
        all = self.request.query_params.get('all', None)
        order_by = self.request.query_params.get('order_by', '-id')
        search = {}
        search['created_by'] = request.user
        search = custom_filters(self.request, search, [])
        if id:
            list_data = VehicleManagement.cmobjects.filter(id=id).first()
            serializer = VehicleManagementSerializer(list_data)
            return Response(serializer.data)
        list_data = VehicleManagement.cmobjects.filter(*search).order_by(*str(order_by).split(","))
        if all == 'true':
            serializer = VehicleManagementSerializer(list_data, many=True)
            return Response({'results': serializer.data})
        page_size = int(request.query_params.get('page_size', settings.MIN_PAGE_SIZE))
        paginator = Paginator(list_data, page_size)
        page_number = self.request.query_params.get('page', 1)
        page = paginator.get_page(page_number)
        serializer = VehicleManagementSerializer(page, many=True)
        return Response({
            'count': paginator.count,
            'next': page.next_page_number() if page.has_next() else None,
            'previous': page.previous_page_number() if page.has_previous() else None,
            'results': serializer.data,
        })
    def post(self, request):
        request.data['created_by'] = request.user.id
        serializer = VehicleManagementSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            try:
                serializer.save()
            except Exception as e:
                error_message = str(e.args[0]) if e.args else str(e)
                raise APIException({'request_status': 0, 'msg': error_message})
            return Response(
                {'results': {
                    'Data': serializer.data,
                },
                    'msg': 'Successfully created',
                    'status': status.HTTP_201_CREATED,
                    "request_status": 1})
        else:
            error_message = next(iter(serializer.errors.values()))[0]
            raise APIException({
                "request_status": 0,
                "msg": error_message
            })
        raise APIException({'request_status': 0, 'msg': serializer.errors})
    def put(self, request):
        method = self.request.query_params.get('method', None)
        id = self.request.query_params.get('id', None)
        details = Labour.cmobjects.filter(pk=id).first()
        request.data['updated_by'] = request.user.id
        with transaction.atomic():
            if method.lower() == 'edit':
                if VehicleManagement.cmobjects.filter(pk=id).exists():
                    details = VehicleManagement.cmobjects.filter(pk=id).first()
                    serializer = VehicleManagementSerializer(details, data=request.data,
                                                            context={'request': request})
                    if serializer.is_valid():
                        try:
                            serializer.save()
                        except Exception as e:
                            error_message = str(e.args[0]) if e.args else str(e)
                            raise APIException({'request_status': 0, 'msg': error_message})

                        return Response({'results': {
                            'Data': serializer.data,
                        },
                            'msg': "Successfully updated",
                            'status': status.HTTP_202_ACCEPTED,
                            "request_status": 1})
                    else:
                        error_message = next(iter(serializer.errors.values()))[0]
                        raise APIException({
                            "request_status": 0,
                            "msg": error_message
                        })


                    raise APIException({'request_status': 0, 'msg': serializer.errors})
                else:
                    raise APIException({'request_status': 1, 'msg': "Something went wrong"})
                
            elif method.lower() == 'delete':
                if VehicleManagement.cmobjects.filter(pk=id).exists():
                    details = VehicleManagement.cmobjects.get(pk=id)
                    details.is_deleted = True
                    details.save()
                    return Response({'results': {
                        'details': VehicleManagement.cmobjects.filter(pk=id).values(),
                    },
                        'msg': 'Successfully deleted',
                        "request_status": 1})
                else:
                    raise APIException({'request_status': 1, 'msg': "Something went wrong"})

class VehicleAvailabilityAPIView(APIView):

    def put(self, request, *args, **kwargs):
        """ Edit and Delete Vehicle API View"""
        try:    
            id = self.request.query_params.get('id', None)
            with transaction.atomic():
                available = request.data.get('available', None)
                	
                vehicle_details = VehicleManagement.cmobjects.filter(pk=id).first()
                if not vehicle_details:
                    return Response({'results': [],
                                    'msg': "Selected Vehicle  Details Does'nt exists!",
                                    "request_status": 0}, status=status.HTTP_404_NOT_FOUND)
                update=VehicleManagement.cmobjects.filter(id=id).update(is_available=available,updated_by=request.user )
                # vehicle_details = VehicleManagement.cmobjects.get(pk=id)
                # serializer = VehicleManagementSerializer(
                #         vehicle_details, data=request.dat             
                # if serializer.is_valid():
                # 	serializer.save()
                return Response({'results':{
                                        # 'Data':serializer.data,
                                        'Data':VehicleManagement.objects.filter(pk=id).values(),
                                        },
                                        'msg': 'Vehicle Details Updated SuccessFully',
                                        'status':status.HTTP_202_ACCEPTED,
                                        "request_status": 1})	
        except Exception as e:
            raise serializers.ValidationError({'status': status.HTTP_400_BAD_REQUEST,'request_status': 0, 'msg': e},code='authorization')    
