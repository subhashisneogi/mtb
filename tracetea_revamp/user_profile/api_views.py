
from django.contrib import messages
from django.urls import reverse
from django.db.models import Q
from django.http import JsonResponse, HttpResponse
from django.db.models.functions import Coalesce
from django.db.models import Sum, Count, Value
from django.template.loader import render_to_string
from django.http import HttpResponseRedirect
from django.contrib.auth import get_user_model
User = get_user_model()
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponse
from datetime import datetime
from master.common import CommonMixin
from .models import *
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
from xhtml2pdf import pisa   
from .helpers import *
import datetime
from user_profile.serializers import *
### REVAMAP API VIEW
class FarmDiaryLabourAPIView(APIView):
	""" Farmdiary Labour API View """
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
			list_data = Labour.cmobjects.filter(id=id).first()
			serializer = LabourSerializer(list_data)
			return Response(serializer.data)
		list_data = Labour.cmobjects.filter(*search).order_by(*str(order_by).split(","))
		if all == 'true':
			serializer = LabourSerializer(list_data, many=True)
			return Response({'results': serializer.data})
		page_size = int(request.query_params.get('page_size', settings.MIN_PAGE_SIZE))
		paginator = Paginator(list_data, page_size)
		page_number = self.request.query_params.get('page', 1)
		page = paginator.get_page(page_number)
		serializer = LabourSerializer(page, many=True)
		return Response({
			'count': paginator.count,
			'next': page.next_page_number() if page.has_next() else None,
			'previous': page.previous_page_number() if page.has_previous() else None,
			'results': serializer.data,
		})
	
	def post(self, request):
		request.data['created_by'] = request.user.id
		serializer = LabourSerializer(data=request.data, context={'request': request})
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
		raise APIException({'request_status': 0, 'msg': serializer.errors})
	def put(self, request):
		method = self.request.query_params.get('method', None)
		id = self.request.query_params.get('id', None)
		details = Labour.cmobjects.filter(pk=id).first()
		request.data['updated_by'] = request.user.id
		with transaction.atomic():
			if method.lower() == 'edit':
				if Labour.cmobjects.filter(pk=id).exists():
					details = Labour.cmobjects.filter(pk=id).first()
					serializer = LabourSerializer(details, data=request.data,
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
					raise APIException({'request_status': 0, 'msg': serializer.errors})
				else:
					raise APIException({'request_status': 1, 'msg': "Something went wrong"})
				
			elif method.lower() == 'delete':
				if Labour.cmobjects.filter(pk=id).exists():
					details = Labour.cmobjects.get(pk=id)
					details.is_deleted = True
					details.save()
					return Response({'results': {
						'details': Labour.cmobjects.filter(pk=id).values(),
					},
						'msg': 'Successfully deleted',
						"request_status": 1})
				else:
					raise APIException({'request_status': 1, 'msg': "Something went wrong"})
				
class FarmDiaryPluckingDataAPIView(APIView):
	""" Farmdiary PluckingData API View """
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
			list_data = PluckingData.cmobjects.filter(id=id).first()
			serializer = PluckingDataSerializer(list_data)
			return Response(serializer.data)
		list_data = PluckingData.cmobjects.filter(*search).order_by(*str(order_by).split(","))
		if all == 'true':
			serializer = PluckingDataSerializer(list_data, many=True)
			return Response({'results': serializer.data})
		page_size = int(request.query_params.get('page_size', settings.MIN_PAGE_SIZE))
		paginator = Paginator(list_data, page_size)
		page_number = self.request.query_params.get('page', 1)
		page = paginator.get_page(page_number)
		serializer = PluckingDataSerializer(page, many=True)
		return Response({
			'count': paginator.count,
			'next': page.next_page_number() if page.has_next() else None,
			'previous': page.previous_page_number() if page.has_previous() else None,
			'results': serializer.data,
		})
	
	def post(self, request):
		request.data['created_by'] = request.user.id
		serializer = PluckingDataSerializer(data=request.data, context={'request': request})
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
		raise APIException({'request_status': 0, 'msg': serializer.errors})
	def put(self, request):
		method = self.request.query_params.get('method', None)
		id = self.request.query_params.get('id', None)
		details = PluckingData.cmobjects.filter(pk=id).first()
		request.data['updated_by'] = request.user.id
		with transaction.atomic():
			if method.lower() == 'edit':
				if PluckingData.cmobjects.filter(pk=id).exists():
					details = PluckingData.cmobjects.filter(pk=id).first()
					serializer = PluckingDataSerializer(details, data=request.data,
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
					raise APIException({'request_status': 0, 'msg': serializer.errors})
				else:
					raise APIException({'request_status': 1, 'msg': "Something went wrong"})
				
			elif method.lower() == 'delete':
				if PluckingData.cmobjects.filter(pk=id).exists():
					details = PluckingData.cmobjects.get(pk=id)
					details.is_deleted = True
					details.save()
					return Response({'results': {
						'details': PluckingData.cmobjects.filter(pk=id).values(),
					},
						'msg': 'Successfully deleted',
						"request_status": 1})
				else:
					raise APIException({'request_status': 1, 'msg': "Something went wrong"})