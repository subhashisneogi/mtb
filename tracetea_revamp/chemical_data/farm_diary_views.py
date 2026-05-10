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
from django.shortcuts import get_object_or_404
from django.db import transaction
from user_profile.grower_api_models import *
from master.common import CommonMixin
from .models import *
from .forms import *
from knox.auth import TokenAuthentication
from rest_framework import permissions
from knox.models import AuthToken
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, IsAuthenticatedOrReadOnly, AllowAny
from django.core.paginator import Paginator
from knox.auth import TokenAuthentication
from django.db import transaction
from rest_framework import status
from rest_framework.exceptions import APIException
from .serializers import *
# from reportlab.lib.pagesizes import letter
# from reportlab.pdfgen import canvas
from user_profile.helpers import *
from django.core.files.storage import FileSystemStorage
from master.decorators import *
import json
import calendar
import pdfkit


def _farm_diary_has_data(grower_id, date_from=None, date_to=None):
	date_filter = {}
	created_filter = {}
	if date_from and date_to:
		date_filter = {'date__range': [date_from, date_to]}
		created_filter = {'created_at__date__range': [date_from, date_to]}
	return (
		UseOfChemical.cmobjects.filter(grower_id=grower_id, **date_filter).exists()
		or PluckingData.cmobjects.filter(grower_id=grower_id, **date_filter).exists()
		or Labour.cmobjects.filter(grower_id=grower_id, **created_filter).exists()
		or MonthlySchedule.cmobjects.filter(grower_id=grower_id, **created_filter).exists()
	)


def _month_week_count(year_value, month_name):
	try:
		year_number = int(year_value)
		month_number = list(calendar.month_name).index(month_name)
	except (ValueError, TypeError):
		return 0
	weeks = calendar.Calendar(firstweekday=calendar.MONDAY).monthdayscalendar(year_number, month_number)
	return len(weeks)


def _month_week_day_limits(year_value, month_name):
	try:
		year_number = int(year_value)
		month_number = list(calendar.month_name).index(month_name)
	except (ValueError, TypeError):
		return []
	weeks = calendar.Calendar(firstweekday=calendar.MONDAY).monthdayscalendar(year_number, month_number)
	return [len([day for day in week if day]) for week in weeks]


def _month_day_count(year_value, month_name):
	try:
		year_number = int(year_value)
		month_number = list(calendar.month_name).index(month_name)
	except (ValueError, TypeError):
		return 0
	return calendar.monthrange(year_number, month_number)[1]


def _get_grower_by_url_pk(grower_pk):
	query = Q(user_id=grower_pk)
	if str(grower_pk).isdigit():
		query |= Q(pk=grower_pk)
	return GrowerProfile.cmobjects.filter(query).select_related('user').first()

@login_required
def farmdiary_user_list(request):
	blf_details = BlfProfile.objects.filter(user_id=request.user.id).first()
	query = request.GET.get('q', '').strip()
	sort = request.GET.get('sort', 'id')
	direction = request.GET.get('dir', 'desc')
	sort_map = {
		'id': 'id',
		'tracetea_id': 'user__username',
		'grower_name': 'name',
		'mobile': 'mobile_number',
	}
	order_field = sort_map.get(sort, 'id')
	if direction == 'desc':
		order_field = '-' + order_field
	user_details = Profile.objects.filter(user_id=request.user.id).first()
	logged_user_type = str(user_details.user_type) if user_details else ''
	associated_grower=GrowerProfile.objects.filter().order_by('-id')
	if logged_user_type == "blf" and blf_details:
		gr = blf_details.grower_associated_entity.select_related('user').prefetch_related('associated_aggregator').all()
		ar = AggregatorProfile.objects.filter(associated_entity=blf_details).order_by('-id')
	else:
		gr = GrowerProfile.cmobjects.select_related('user').prefetch_related('associated_aggregator').all()
		ar = AggregatorProfile.objects.none()
	if query:
		gr = gr.filter(
			Q(user__username__icontains=query) |
			Q(name__icontains=query) |
			Q(mobile_number__icontains=query) |
			Q(associated_aggregator__name__icontains=query)
		).distinct()
	gr = gr.order_by(order_field)
	
	page = request.GET.get('page', 1)
	paginator = Paginator(gr, 10)
	try:
		gr = paginator.page(page)
	except PageNotAnInteger:
		gr = paginator.page(1)
	except EmptyPage:
		gr = paginator.page(paginator.num_pages)

	context ={
		'associated_grower_list' : gr,
		'blf_details' : blf_details,
		'associated_ar_list' : ar,
		'search_query': query,
		'sort': sort,
		'dir': direction,
		'next_dir': 'asc' if direction == 'desc' else 'desc',
	}
	if request.headers.get('x-requested-with') == 'XMLHttpRequest':
		html = render_to_string('farm_diary/_farmdiary_user_table.html', context, request=request)
		return JsonResponse({'html': html})
	return CommonMixin.render(request, 'farm_diary/farmdiary_user_list.html', context)





def search_as_gr_list(request):

	query = request.GET.get('grower')

	print("wsbwhbw", query)
	
	if query:
		result = GrowerProfile.objects.filter(user_id=query)
	else:
		result = GrowerProfile.objects.none()

	# print(GrowerProfile.objects.filter(user_id=query).first())

	# page = request.GET.get('page', 1)
	# paginator = Paginator(result, 10)
	# try:
	# 	gr = paginator.page(page)
	# except PageNotAnInteger:
	# 	gr = paginator.page(1)
	# except EmptyPage:
	# 	gr = paginator.page(paginator.num_pages)

	blf_details = BlfProfile.objects.filter(user_id=request.user.id).first()
	associated_grower=GrowerProfile.objects.filter().order_by('-id')
	gr = GrowerProfile.objects.filter(associated_entity=blf_details).order_by('-id')

	ar = AggregatorProfile.objects.filter(associated_entity=blf_details).order_by('-id')
	page = request.GET.get('page', 1)
	paginator = Paginator(result, 10)
	try:
		result = paginator.page(page)
	except PageNotAnInteger:
		result = paginator.page(1)
	except EmptyPage:
		result = paginator.page(paginator.num_pages)

	context ={
		'associated_grower_list' : result,
		'blf_details' : blf_details,
		'associated_ar_list' : ar,
		'search_query': query or '',
	}


	return CommonMixin.render(request, 'farm_diary/farmdiary_user_list.html', context)



class FarmdiaryUserList(LoginRequiredMixin, CommonMixin, ListView):
	"""
	STG FARM DIARY Users List View
	"""
	model = GrowerProfile
	context_object_name = 'farmdiary_user_list'
	template_name = 'farm_diary/farmdiary_user_list.html'
	paginate_by = 5

	def get(self, request, *args, **kwargs):
		# try:
		# 	if not self.request.user.is_superuser:
		# 		messages.error(self.request, 'You have no permission to access the requested resource!')
		# 		return redirect(reverse('index'))
		# except AttributeError as error:
		# 	messages.error(self.request, 'You have no permission to access the requested resource!')
		# 	return redirect(reverse('index'))

		return super().get(request, *args, **kwargs)

	def get_queryset(self, *args, **kwargs):
		qs = super().get_queryset(*args, **kwargs)
		blf_details = BlfProfile.objects.filter(user_id=self.request.user.id).first()
		grower=self.request.GET.get('grower')
		# if grower:
		# 	return qs.filter(grower__name__icontains=grower)
		
		return GrowerProfile.objects.filter(associated_entity=blf_details).order_by('-id')

	def get_context_data(self, **kwargs):	
		context = super().get_context_data(**kwargs)
		
		return context
	

@login_required
def chemical_type_list(request, grower_pk):
	domain = request.get_host()
	chemical_type_list = ChemicalType.objects.all().order_by('id')
	grower_details = GrowerProfile.cmobjects.filter(user_id=grower_pk).first()
	diary_links = []
	diary_links.append({
		"title": "Map Of The Land",
		"url": reverse('chemical_data:farm_diary_map_create', kwargs={'grower_pk': grower_pk}),
		"icon": "fa-map",
		"class": "farm-diary-tile-blue",
	})
	type_style_map = {
		1: ("fa-seedling", "farm-diary-tile-green"),
		2: ("fa-leaf", "farm-diary-tile-red"),
		3: ("fa-shield-alt", "farm-diary-tile-yellow"),
		5: ("fa-bug", "farm-diary-tile-gray"),
	}
	for item in chemical_type_list:
		if item.name and item.name.lower() in ["herbicides", "insecticides & fungicides", "acaricides"]:
			continue
		icon, css_class = type_style_map.get(item.pk, ("fa-flask", "farm-diary-tile-green"))
		diary_links.append({
			"title": item.name,
			"url": reverse('chemical_data:chemical_view_list', kwargs={'grower_pk': grower_pk, 'chemical_type': item.id}),
			"icon": icon,
			"class": css_class,
		})
	diary_links.append({
		"title": "Chemical Data",
		"url": reverse('chemical_data:chemical_view_list', kwargs={'grower_pk': grower_pk, 'chemical_type': 0}),
		"icon": "fa-flask",
		"class": "farm-diary-tile-cyan",
	})
	diary_links.extend([
		{"title": "Plucking Data", "url": reverse('chemical_data:plucking_data_view_list', kwargs={'grower_pk': grower_pk}), "icon": "fa-hand-paper", "class": "farm-diary-tile-green"},
		{"title": "Labour List Entry", "url": reverse('chemical_data:farmdiary_labour_list', kwargs={'grower_pk': grower_pk}), "icon": "fa-users", "class": "farm-diary-tile-red"},
		{"title": "Monthly Schedule Of Work", "url": reverse('chemical_data:farmdiary_monthly_shedule_list', kwargs={'grower_pk': grower_pk}), "icon": "fa-calendar-alt", "class": "farm-diary-tile-blue"},
		{"title": "Forms And Registration", "url": reverse('chemical_data:farmers_aggreements_forms_list', kwargs={'grower_pk': grower_pk}), "icon": "fa-file-signature", "class": "farm-diary-tile-cyan"},
	])
	context = {
		"domain" : domain,
		'chemical_type_list' : chemical_type_list,
		'grower_pk' : grower_pk,
		"grower_details" : grower_details,
		"diary_links": diary_links,
		"has_download_data": _farm_diary_has_data(grower_details.id) if grower_details else False,
	}
	return CommonMixin.render(request, 'farm_diary/chemical_type_list.html', context)


@login_required
def farm_diary_download_available(request, grower_pk):
	grower_details = GrowerProfile.cmobjects.filter(user_id=grower_pk).only('id').first()
	date_from = request.GET.get('date_from', '').strip()
	date_to = request.GET.get('date_to', '').strip()
	if not grower_details or not date_from or not date_to:
		return JsonResponse({'has_data': False})
	return JsonResponse({'has_data': _farm_diary_has_data(grower_details.id, date_from, date_to)})


@login_required
def farm_diary_record_detail(request, record_type, pk):
	item = None
	title = "Farm Diary Details"
	fields = []
	if record_type == "chemical":
		item = UseOfChemical.cmobjects.select_related('grower', 'chemical', 'chemical__chemical_type', 'plot', 'division', 'labour').filter(pk=pk).first()
		title = "Use of Chemical Details"
		if item:
			fields = [
				("Date", item.date.strftime("%d-%m-%Y") if item.date else "NA"),
				("Chemical Type", item.chemical.chemical_type if item.chemical else "NA"),
				("Chemical", item.chemical if item.chemical else "NA"),
				("Plot", item.plot if item.plot else "NA"),
				("Division", item.division if item.division else "NA"),
				("Labour", item.labour if item.labour else "NA"),
				("Quantity", item.quantity if item.quantity else "NA"),
				("Unit", item.unit if item.unit else "NA"),
			]
	elif record_type == "plucking":
		item = PluckingData.cmobjects.select_related('grower', 'plot', 'division', 'labour').prefetch_related('labours').filter(pk=pk).first()
		title = "Plucking Data Details"
		if item:
			labour_names = ", ".join([str(labour) for labour in item.labours.all()])
			fields = [
				("Date", item.date.strftime("%d-%m-%Y") if item.date else "NA"),
				("Start Time", item.start_time if item.start_time else "NA"),
				("End Time", item.end_time if item.end_time else "NA"),
				("Plot", item.plot if item.plot else "NA"),
				("Division", item.division if item.division else "NA"),
				("Area Plucked", item.area_plucked if item.area_plucked else "NA"),
				("Quantity Plucked", item.quantity_plucked if item.quantity_plucked else "NA"),
				("Labours", labour_names or item.labour or "NA"),
			]
	elif record_type == "labour":
		item = Labour.cmobjects.filter(pk=pk).first()
		title = "Labour Details"
		if item:
			fields = [
				("Name", item.name or "NA"),
				("Type", item.type or "NA"),
				("Gender", item.gender or "NA"),
				("Age", item.age if item.age else "NA"),
			]
	elif record_type == "monthly-schedule":
		item = MonthlySchedule.cmobjects.select_related('year').prefetch_related('monthly_schedule_hour_details').filter(pk=pk).first()
		title = "Monthly Schedule Details"
		if item:
			fields = [
				("Year", item.year or "NA"),
				("Month", item.month or "NA"),
				("Total Working Days", item.no_of_working_days if item.no_of_working_days else "NA"),
				("Total Hours", item.total_hours if item.total_hours else "NA"),
				("Hourly Rate", item.hourly_rate if item.hourly_rate else "NA"),
				("Monthly Wages", item.monthly_wages if item.monthly_wages else "NA"),
			]
	if not item:
		messages.error(request, 'Record was not found')
		return redirect(request.META.get('HTTP_REFERER', reverse('chemical_data:farmdiary_user_list')))
	return CommonMixin.render(request, 'farm_diary/farm_diary_record_detail.html', {
		'title': title,
		'fields': fields,
		'item': item,
		'record_type': record_type,
	})



#################################  START USE OF CHEMICAL ############################ 
@login_required
def chemical_view_list(request, grower_pk, chemical_type):
	""" Use Of Chemical Model Data List View   """

	from django.db.models import Sum, F, Case, When, Value, FloatField

	grower_details = GrowerProfile.cmobjects.filter(user_id=grower_pk).first()
	is_unified_chemical = str(chemical_type) in ["0", "chemical"]
	chemical_type_details = None if is_unified_chemical else ChemicalType.objects.filter(pk=chemical_type).first()
	chemical_type_name = "Chemical Data" if is_unified_chemical else str(chemical_type_details)
	gardden_details = Gardens.cmobjects.filter(grower_id=grower_details.id).first()

	use_of_chemical_list = UseOfChemical.cmobjects.filter(grower_id=grower_details.id).select_related(
		'chemical', 'chemical__chemical_type', 'plot', 'division', 'labour'
	)
	if is_unified_chemical:
		use_of_chemical_list = use_of_chemical_list.exclude(chemical__chemical_type__name__iexact="Fertilizer")
	else:
		use_of_chemical_list = use_of_chemical_list.filter(chemical__chemical_type=chemical_type_details)
	start_date = request.GET.get('start_date', '').strip()
	end_date = request.GET.get('end_date', '').strip()
	sort = request.GET.get('sort', 'id')
	direction = request.GET.get('dir', 'desc')
	if start_date:
		use_of_chemical_list = use_of_chemical_list.filter(date__gte=start_date)
	if end_date:
		use_of_chemical_list = use_of_chemical_list.filter(date__lte=end_date)
	sort_map = {
		'id': 'id',
		'date': 'date',
		'name': 'chemical__chemical_name',
		'quantity': 'quantity',
	}
	order_field = sort_map.get(sort, 'id')
	if direction == 'desc':
		order_field = '-' + order_field
	use_of_chemical_list = use_of_chemical_list.order_by(order_field)

	total_plot_area = Plot.objects.filter(garden_id=gardden_details.id).aggregate(Sum('plot_area'))['plot_area__sum'] or 0 if gardden_details else 0


	chemicals_list = []
	page = request.GET.get('page', 1)
	paginator = Paginator(use_of_chemical_list, 10)

	try:
		use_of_chemical_page = paginator.page(page)
	except PageNotAnInteger:
		use_of_chemical_page = paginator.page(1)
	except EmptyPage:
		use_of_chemical_page = paginator.page(paginator.num_pages)

	for item in use_of_chemical_page:
		date = item.date
		name = item.chemical
		plot = item.plot
		division = item.division		
		labour = item.labour
		quantity = item.quantity

		if plot:
			plot_list = Plot.objects.filter(pk=item.plot.pk)
		else:
			plot_list = None

		if division:
			division_list = Division.objects.filter(pk=division.pk)
			total_section_areas = Section.objects.filter(division_id=item.division.pk).aggregate(Sum('section_area'))['section_area__sum'] or 0
		else:
			division_list = None
			total_section_areas = None

		chemical_list_data = {
			"pk" : item.pk,
			"date" : date,
			"name" : name,
			"plot" : plot,
			"division" : division,
			"labour" : labour,
			"quantity" : quantity,
			"total_section_areas" : total_section_areas,
			"plots_list" : plot_list,
			"division_list" : division_list,
		}

		chemicals_list.append(chemical_list_data)


	# print("ALL DATA", type(chemicals_list))


	context = {
		'grower_details': grower_details,
		'chemical_type_details' : chemical_type_details,
		'chemical_type_label' : chemical_type_name,
		'use_of_chemical_list': use_of_chemical_page,
		'grower_pk': grower_pk,
		'total_plot_area': total_plot_area,
		'grower_pk' : grower_pk,
		'chemical_type' : 0 if is_unified_chemical else chemical_type_details.pk,
		'chemical_type_name' : chemical_type_name,
		'gardden_details' : gardden_details,
		'start_date': start_date,
		'end_date': end_date,
		'sort': sort,
		'dir': direction,
		'next_dir': 'asc' if direction == 'desc' else 'desc',
		'is_unified_chemical': is_unified_chemical,

		# result
		"chemicals_list" : chemicals_list,
	}
	if request.headers.get('x-requested-with') == 'XMLHttpRequest':
		html = render_to_string('farm_diary/_chemical_data_table.html', context, request=request)
		return JsonResponse({'html': html})
	return CommonMixin.render(request, 'farm_diary/chemical_type_details.html', context)



class UseOfChemicalCreateView(LoginRequiredMixin, CommonMixin, CreateView):
	"""
	Use Of Chemical Update View for BLF ADMIN
	"""
	model = UseOfChemical
	form_class = UseOfChemicalForm
	template_name = 'farm_diary/use_chemical_edit.html'

	def get(self, request, *args, **kwargs):

		
		return super().get(request, *args, **kwargs)

	def get_success_url(self, **kwargs):
		messages.success(self.request, 'Use Of Chemical Created Successfully')
		return reverse('chemical_data:chemical_view_list', kwargs={'grower_pk': self.kwargs['grower_pk'], 'chemical_type': self.kwargs['chemical_type']} )

	def get_context_data(self, **kwargs):
		context = super(UseOfChemicalCreateView, self).get_context_data(**kwargs)
		context['grower_pk'] = self.kwargs['grower_pk']
		context['chemical_type'] =  self.kwargs['chemical_type']
		context['grower_details'] = GrowerProfile.cmobjects.filter(user_id=self.kwargs['grower_pk']).first()
		is_unified_chemical = str(self.kwargs['chemical_type']) in ["0", "chemical"]
		type_details = None if is_unified_chemical else ChemicalType.objects.filter(pk=self.kwargs['chemical_type']).first()
		context['type_details'] = "Chemical Data" if is_unified_chemical else type_details
		context['chemical_type_id'] = 0 if is_unified_chemical else type_details.pk
		context['type_name'] = "Chemical Data" if is_unified_chemical else str(type_details)
		context['is_unified_chemical'] = is_unified_chemical
		if is_unified_chemical:
			context['chemical_options_json'] = json.dumps(list(
				ChemicalData.objects.exclude(
					chemical_type__name__iexact="Fertilizer"
				).filter(is_deleted=False).values('id', 'chemical_name', 'chemical_type_id').order_by('chemical_name')
			))

		grower_details=GrowerProfile.cmobjects.filter(user_id=self.kwargs['grower_pk']).first()
		context['garden_details'] = Gardens.cmobjects.filter(grower_id=grower_details.id).first()

		# print("garden_details", Gardens.cmobjects.filter(grower_id=grower_details.id).first().id)

		# print(garden_details.is_plot)
		# print(garden_details.is_division)

		# if garden_details.is_plot == True:
		# 	pass
		
		return context

	def get_form_kwargs(self, **kwargs):
		""" Provides keyword arguemnt """
		kwargs = super(UseOfChemicalCreateView, self).get_form_kwargs()
		kwargs['chemical_type_pk'] = self.kwargs['chemical_type']
		kwargs['grower_pk'] = self.kwargs['grower_pk']
		kwargs['request_user'] = self.request.user
		grower_details = GrowerProfile.cmobjects.filter(user_id=self.kwargs['grower_pk']).first()
		kwargs['grower_details_id'] = grower_details.id
		if Gardens.objects.filter(grower_id=grower_details.pk).first():
			garden_details = Gardens.objects.filter(grower_id=grower_details.pk).first()
			kwargs['garden_pk'] = garden_details.pk
		return kwargs
	def form_valid(self, form):
		context = self.get_context_data()
		try:
			with transaction.atomic():
				form.instance.created_by_id = self.request.user.id
				form.instance.grower = GrowerProfile.cmobjects.filter(user_id=self.kwargs['grower_pk']).first()
				self.object = form.save()
		except APIException as e:
			# convert APIException into a form error
			form.add_error(None, str(e))  # non-field error
			return self.form_invalid(form)
		return super().form_valid(form)

class UseOfChemicalUpdateView(LoginRequiredMixin, CommonMixin, UpdateView):
	model = UseOfChemical
	form_class = UseOfChemicalForm
	template_name = 'farm_diary/use_chemical_edit.html'

	def get_object(self, queryset=None):
		use_chemical_details = UseOfChemical.cmobjects.filter(pk=self.kwargs['use_of_chemical_pk'], \
							grower__user_id=self.kwargs['grower_pk']).first()
		return use_chemical_details

	def get_success_url(self, **kwargs):
		messages.success(self.request, 'Use Of Chemical  Updated Successfully')
		chemical_type = self.object.chemical.chemical_type_id if self.object and self.object.chemical_id else 0
		if chemical_type and self.object.chemical.chemical_type.name.lower() != "fertilizer":
			chemical_type = 0
		return reverse('chemical_data:chemical_view_list', kwargs={'grower_pk': self.kwargs['grower_pk'], 'chemical_type': chemical_type} )

	def get_form_kwargs(self, **kwargs):
		""" Provides keyword arguemnt """
		kwargs = super(UseOfChemicalUpdateView, self).get_form_kwargs()
		kwargs['request_user'] = self.request.user
		chemical_details = UseOfChemical.cmobjects.filter(pk=self.kwargs['use_of_chemical_pk'], \
								grower__user_id=self.kwargs['grower_pk']).first()
		
		
		chemical_type_id = chemical_details.chemical.chemical_type.id
		kwargs['chemical_type_pk'] = chemical_type_id
		kwargs['grower_pk'] = self.kwargs['grower_pk']
		grower_details = GrowerProfile.cmobjects.filter(user_id=self.kwargs['grower_pk']).first()
		kwargs['grower_details_id'] = grower_details.id
		if Gardens.objects.filter(grower_id=grower_details.pk).first():
			garden_details = Gardens.objects.filter(grower_id=grower_details.pk).first()
			kwargs['garden_pk'] = garden_details.pk
		return kwargs


	def get_context_data(self, **kwargs):
		context = super(UseOfChemicalUpdateView, self).get_context_data(**kwargs)

		context['chemical_details'] = UseOfChemical.cmobjects.filter(pk=self.kwargs['use_of_chemical_pk'], \
								grower__user_id=self.kwargs['grower_pk']).first()

		context['grower_pk'] = self.kwargs['grower_pk']
		context['grower_details'] = GrowerProfile.cmobjects.filter(user_id=self.kwargs['grower_pk']).first()
		chemical_details = UseOfChemical.cmobjects.filter(pk=self.kwargs['use_of_chemical_pk'], \
								grower__user_id=self.kwargs['grower_pk']).first()
		chemical_type_id = chemical_details.chemical.chemical_type.id
		context['type_details'] = chemical_details.chemical.chemical_type.name
		is_unified_chemical = chemical_details.chemical.chemical_type.name.lower() != "fertilizer"
		context['chemical_type_id'] = 0 if is_unified_chemical else chemical_type_id
		context['chemical_type'] = context['chemical_type_id']
		context['type_details'] = "Chemical Data" if is_unified_chemical else chemical_details.chemical.chemical_type.name
		context['type_name'] = context['type_details']
		context['is_unified_chemical'] = is_unified_chemical
		if is_unified_chemical:
			context['chemical_options_json'] = json.dumps(list(
				ChemicalData.objects.exclude(
					chemical_type__name__iexact="Fertilizer"
				).filter(is_deleted=False).values('id', 'chemical_name', 'chemical_type_id').order_by('chemical_name')
			))

		grower_details=GrowerProfile.cmobjects.filter(user_id=self.kwargs['grower_pk']).first()
		context['garden_details'] = Gardens.cmobjects.filter(grower_id=grower_details.id).first()

		return context
	def form_invalid(self, form):
		for field, errors in form.errors.items():
			for error in errors:
				messages.error(self.request, f"{field}: {error}")
		for error in form.non_field_errors():
			messages.error(self.request, error)
		return super().form_invalid(form)
	def form_valid(self, form):
		try:
			with transaction.atomic():
				form.instance.created_by_id = self.request.user.id
				form.instance.grower = GrowerProfile.cmobjects.filter(user_id=self.kwargs['grower_pk']).first()
				self.object = form.save()
		except APIException as e:
			# Convert signal error into a message
			messages.error(self.request, str(e))
			return self.form_invalid(form)
		return super().form_valid(form)


@login_required
def use_of_chemical_delete(request, grower_pk, use_of_chemical_pk ):
	""" USe of chemical Details Delete view """
	grower_details = GrowerProfile.cmobjects.filter(user_id=grower_pk).first()
	use_of_chemical_details = UseOfChemical.cmobjects.filter(grower_id=grower_details.pk, pk=use_of_chemical_pk).first()
	if use_of_chemical_details:
		use_of_chemical_details.is_deleted = True
		use_of_chemical_details.save()
		messages.success(request, 'Use Of Chemical Deleted Successfully')
	else:
		messages.error(request, 'Use Of Chemical record was not found')
	return redirect(request.META.get('HTTP_REFERER', reverse('chemical_data:chemical_view_list', kwargs={'grower_pk': grower_pk, 'chemical_type': 0})))


######################### Start Plucking DATA ################
@login_required
def farmdiary_plucking_data_list(request, grower_pk):

	# print(request.user.id)

	chemical_type_list = ChemicalType.objects.all().order_by('-id')
	grower_details = GrowerProfile.cmobjects.filter(user_id=grower_pk).first()

	# plucking data list by for which grower and created by respective BLF
	plucking_data_list = PluckingData.cmobjects.filter(
		Q(grower_id=grower_details.id)).select_related('plot', 'division', 'labour').prefetch_related('labours').order_by('-date', '-id')
	start_date = request.GET.get('start_date', '').strip()
	end_date = request.GET.get('end_date', '').strip()
	if start_date:
		plucking_data_list = plucking_data_list.filter(date__gte=start_date)
	if end_date:
		plucking_data_list = plucking_data_list.filter(date__lte=end_date)

	page = request.GET.get('page', 1)
	paginator = Paginator(plucking_data_list, 10)
	try:
		plucking_data_list = paginator.page(page)
	except PageNotAnInteger:
		plucking_data_list = paginator.page(1)
	except EmptyPage:
		plucking_data_list = paginator.page(paginator.num_pages)

	context = {
		'grower_pk' : grower_pk,
		'grower_details' : grower_details,
		'plucking_data_list' : plucking_data_list,
		'start_date': start_date,
		'end_date': end_date,
	}
	if request.headers.get('x-requested-with') == 'XMLHttpRequest':
		return CommonMixin.render(request, 'farm_diary/_plucking_data_table.html', context)

	return CommonMixin.render(request, 'farm_diary/farmdiary_plucking_data_list.html', context)

@login_required
def plucking_data_search(request):
	""" Plucking Data Search View """
	start_date= request.GET.get('start_date')
	end_date= request.GET.get('end_date')
	grower_pk = request.GET.get('grower_pk')
	grower_details=GrowerProfile.cmobjects.filter(user_id=grower_pk).first()
	plucking_data_list = PluckingData.cmobjects.filter(
		grower_id=grower_details.id
	).select_related('plot', 'division', 'labour').prefetch_related('labours').order_by('-date', '-id')
	if start_date and end_date:
		plucking_data_list = plucking_data_list.filter(date__range=(start_date, end_date))

	page = request.GET.get('page', 1)
	paginator = Paginator(plucking_data_list, 10)

	try:
		plucking_data_list = paginator.page(page)
	except PageNotAnInteger:
		plucking_data_list = paginator.page(1)
	except EmptyPage:
		plucking_data_list = paginator.page(paginator.num_pages)

	context = {
		'grower_details' : grower_details,
		'grower_pk' : grower_pk,
		'grower_details' : grower_details,
		'plucking_data_list' : plucking_data_list,
		'start_date': start_date,
		'end_date': end_date,
	}
	return CommonMixin.render(request, 'farm_diary/farmdiary_plucking_data_list.html', context)



class PluckingDataCreateView(LoginRequiredMixin, CommonMixin, CreateView):
	"""
	Use Of Chemical Create View  for BLF ADMIN
	"""
	model = PluckingData
	form_class = PluckingDataForm
	template_name = 'farm_diary/plucking_data_form.html'

	def get(self, request, *args, **kwargs):
		
		return super(PluckingDataCreateView, self).get(request, *args, **kwargs)

	def get_success_url(self, **kwargs):
		messages.success(self.request, 'Plucking Data Updated Successfully')
		return reverse('chemical_data:plucking_data_view_list', kwargs={'grower_pk': self.kwargs['grower_pk']} )

	def get_context_data(self, **kwargs):
		context = super(PluckingDataCreateView, self).get_context_data(**kwargs)
		
		context['grower_pk'] = self.kwargs['grower_pk']
		context['grower_details'] = GrowerProfile.cmobjects.filter(user_id=self.kwargs['grower_pk']).first()
		return context

	def get_form_kwargs(self, **kwargs):
		kwargs = super(PluckingDataCreateView, self).get_form_kwargs()
		grower_details = GrowerProfile.cmobjects.filter(user_id=self.kwargs['grower_pk']).first()
		garden_details = Gardens.objects.filter(grower_id=grower_details.pk).first()
		kwargs['grower_pk'] = self.kwargs['grower_pk']
		kwargs['garden_pk'] = garden_details.pk
		grower_details = GrowerProfile.cmobjects.filter(user_id=self.kwargs['grower_pk']).first()
		kwargs['grower_details_id'] = grower_details.id
		return kwargs

	def form_valid(self, form):
		with transaction.atomic():
			form.instance.created_by_id = self.request.user.id
			grower_details = GrowerProfile.cmobjects.filter(user_id=self.kwargs['grower_pk']).first()
			form.instance.grower_id = grower_details.pk
			self.object = form.save()
		return HttpResponseRedirect(self.get_success_url())



class PluckingDataUpdateView(LoginRequiredMixin, CommonMixin, UpdateView):
	"""
	Use Of Chemical Update View
	"""
	model = PluckingData
	form_class = PluckingDataForm
	template_name = 'farm_diary/plucking_data_form.html'

	def get(self, request, *args, **kwargs):
		
		return super().get(request, *args, **kwargs)

	def get_success_url(self, **kwargs):
		messages.success(self.request, 'Plucking Data Updated Successfully')
		print("grower",self.kwargs['grower_pk'])
		print("chemical",self.kwargs['plucking_data_pk'])
		return reverse('chemical_data:plucking_data_view_list', kwargs={'grower_pk': self.kwargs['grower_pk']} )

	def get_object(self,queryset=None):
		grower_details = GrowerProfile.cmobjects.filter(user_id=self.kwargs['grower_pk']).first()
		plucking_data_details = PluckingData.objects.filter(grower_id=grower_details.id, pk=self.kwargs['plucking_data_pk']).first()
		return plucking_data_details

	def get_form_kwargs(self, **kwargs):
		kwargs = super(PluckingDataUpdateView, self).get_form_kwargs()
		grower_details = GrowerProfile.cmobjects.filter(user_id=self.kwargs['grower_pk']).first()
		garden_details = Gardens.objects.filter(grower_id=grower_details.pk).first()
		kwargs['grower_pk'] = self.kwargs['grower_pk']
		kwargs['garden_pk'] = garden_details.pk
		grower_details = GrowerProfile.cmobjects.filter(user_id=self.kwargs['grower_pk']).first()
		kwargs['grower_details_id'] = grower_details.id
		return kwargs

	def get_context_data(self, **kwargs):
		context = super(PluckingDataUpdateView, self).get_context_data(**kwargs)
		
		context['plucking_data_details'] = self.get_object()
		context['grower_pk'] = self.kwargs['grower_pk']
		context['grower_details'] = GrowerProfile.cmobjects.filter(user_id=self.kwargs['grower_pk']).first()
		return context

	def form_valid(self, form):
		grower_details = GrowerProfile.cmobjects.filter(user_id=self.kwargs['grower_pk']).first()
		with transaction.atomic():
			form.instance.updated_by = self.request.user
			form.instance.grower_id = grower_details.pk
			self.object = form.save()

		return HttpResponseRedirect(self.get_success_url())


def plucking_data_delete(request, plucking_data_pk ):
	""" USe of chemical Details Delete view """
	plucking_details = PluckingData.cmobjects.filter(pk=plucking_data_pk).first()
	if plucking_details:
		plucking_details.is_deleted = True
		plucking_details.save()
		messages.success(request, 'Plucking Data Deleted Successfully')
	else:
		messages.error(request, 'Plucking Data record was not found')
	return redirect(request.META.get('HTTP_REFERER', reverse('chemical_data:farmdiary_user_list')))


######################### END Plucking DATA ################


######################### START LABOUR DATA ################

def farmdiary_labour_list(request, grower_pk):
	growewr_details = GrowerProfile.cmobjects.filter(user_id=grower_pk).first()
	labour_type = request.GET.get('labour_type', '').strip()
	labour_list = Labour.cmobjects.filter(
		Q(grower_id=growewr_details.id)).order_by('-id')
	if labour_type:
		labour_list = labour_list.filter(type=labour_type)

	page = request.GET.get('page', 1)
	paginator = Paginator(labour_list, 10)
	try:
		labour_list = paginator.page(page)
	except PageNotAnInteger:
		labour_list = paginator.page(1)
	except EmptyPage:
		labour_list = paginator.page(paginator.num_pages)

	context = {
		'grower_pk' : grower_pk,
		'growewr_details' : growewr_details,
		'labour_list' : labour_list,
		'labour_type': labour_type,
	}
	if request.headers.get('x-requested-with') == 'XMLHttpRequest':
		return CommonMixin.render(request, 'farm_diary/_labour_table.html', context)
	return CommonMixin.render(request, 'farm_diary/farmdiary_labour_list.html', context)



def labour_data_search(request):
	""" Labour Data Search View """
	labour_type= request.GET.get('labour_type')
	grower_pk = request.GET.get('grower_pk')
	grower_details = GrowerProfile.cmobjects.filter(user_id=grower_pk).first()
	if labour_type:
		labour_data_list = Labour.cmobjects.filter(
			Q(type=labour_type), Q(grower_id=grower_details.id)).order_by('-id')
	else:
		labour_data_list= Labour.cmobjects.filter(
		Q(grower_id=grower_details.id)).order_by('-id')

	page = request.GET.get('page', 1)
	paginator = Paginator(labour_data_list, 10)
	try:
		labour_data_list = paginator.page(page)
	except PageNotAnInteger:
		labour_data_list = paginator.page(1)
	except EmptyPage:
		labour_data_list = paginator.page(paginator.num_pages)

	context = {
		'grower_pk' : grower_pk,
		'growewr_details' : grower_details,
		'labour_list' : labour_data_list,
		"labour_type" : labour_type,
	}
	return CommonMixin.render(request, 'farm_diary/farmdiary_labour_list.html', context)



class LabourDataCreateView(LoginRequiredMixin, CommonMixin, CreateView):
	"""
	Labour Data Create View
	"""
	model = Labour
	form_class = LabourDataForm
	template_name = 'farm_diary/labour_form.html'

	def get(self, request, *args, **kwargs):
		
		return super().get(request, *args, **kwargs)

	def get_success_url(self, **kwargs):
		messages.success(self.request, 'Labour Data Updated Successfully')
		return reverse('chemical_data:farmdiary_labour_list', kwargs={'grower_pk': self.kwargs['grower_pk']} )


	def get_context_data(self, **kwargs):
		context = super(LabourDataCreateView, self).get_context_data(**kwargs)
		context['grower_pk'] = self.kwargs['grower_pk']
		context['grower_details'] = GrowerProfile.cmobjects.filter(user_id=self.kwargs['grower_pk']).first()
		return context

	def form_valid(self, form):
		context = self.get_context_data()	
		grower_details = GrowerProfile.cmobjects.filter(user_id=self.kwargs['grower_pk']).first()

		with transaction.atomic():
			form.instance.created_by_id = self.request.user.id
			form.instance.grower_id = grower_details.id
			self.object = form.save()
			if not form.is_valid():
				# formsets or form is invalid; render the form with error
				return self.render_to_response(context)

		return super(LabourDataCreateView, self).form_valid(form)



class LabourDataUpdateView(LoginRequiredMixin, CommonMixin, UpdateView):
	"""
	Labour Data Update View
	"""
	model = Labour
	form_class = LabourDataForm
	template_name = 'farm_diary/labour_form.html'

	def get(self, request, *args, **kwargs):
		
		return super().get(request, *args, **kwargs)

	def get_success_url(self, **kwargs):
		messages.success(self.request, 'Labour Data Updated Successfully')
		return reverse('chemical_data:farmdiary_labour_list', kwargs={'grower_pk': self.kwargs['grower_pk']} )

	def get_object(self,queryset=None):
		grower_details = GrowerProfile.cmobjects.filter(user_id=self.kwargs['grower_pk']).first()
		labour_data_details = Labour.cmobjects.filter(grower_id=grower_details.id, pk=self.kwargs['labour_pk']).first()
		return labour_data_details

	def get_context_data(self, **kwargs):
		context = super(LabourDataUpdateView, self).get_context_data(**kwargs)
		context['labour_data_details'] = self.get_object()
		context['grower_pk'] = self.kwargs['grower_pk']
		context['grower_details'] = GrowerProfile.cmobjects.filter(user_id=self.kwargs['grower_pk']).first()
		return context

	def form_valid(self, form):
		context = self.get_context_data()	
		with transaction.atomic():
			grower_details = GrowerProfile.cmobjects.filter(user_id=self.kwargs['grower_pk']).first()
			self.created_by_id = self.request.user.id
			self.grower_id = grower_details.id
			
			self.object = form.save()
			if not form.is_valid():
				# formsets or form is invalid; render the form with error
				return self.render_to_response(context)

		return super(LabourDataUpdateView, self).form_valid(form)



def labour_data_delete(request, labour_data_pk ):
	""" USe of chemical Details Delete view """
	labour_details = Labour.cmobjects.filter(pk=labour_data_pk).first()
	if labour_details:
		labour_details.is_deleted = True
		labour_details.save()
		messages.success(request, 'Deleted Successfully')
	else:
		messages.error(request, 'Labour record was not found')
	return redirect(request.META.get('HTTP_REFERER', reverse('chemical_data:farmdiary_user_list')))


######################### END LABOUR DATA ################


######################### START MONTHLT SHEDULE DATA ################

def farmdiary_monthly_shedule_list(request, grower_pk):
	grower_details = _get_grower_by_url_pk(grower_pk)
	if not grower_details:
		messages.error(request, 'Grower was not found')
		return redirect(reverse('chemical_data:farmdiary_user_list'))
	monthly_dhedule_details_list = MonthlySchedule.cmobjects.filter(
		grower_id=grower_details.id
	).select_related('year').prefetch_related('monthly_schedule_hour_details').order_by('-year__year', '-id')
	select_year = request.GET.get('select_year', '').strip()
	if select_year:
		monthly_dhedule_details_list = monthly_dhedule_details_list.filter(year__year=select_year)

	page = request.GET.get('page', 1)
	paginator = Paginator(monthly_dhedule_details_list, 10)
	try:
		monthly_dhedule_details_list = paginator.page(page)
	except PageNotAnInteger:
		monthly_dhedule_details_list = paginator.page(1)
	except EmptyPage:
		monthly_dhedule_details_list = paginator.page(paginator.num_pages)

	context = {
		'grower_pk' : grower_pk,
		'growewr_details' : grower_details,
		'monthly_shedule_list' : monthly_dhedule_details_list,
		'select_year': select_year,
	}
	if request.headers.get('x-requested-with') == 'XMLHttpRequest':
		return CommonMixin.render(request, 'farm_diary/_monthly_schedule_table.html', context)

	return CommonMixin.render(request, 'farm_diary/farmdiary_monthly_shedule_list.html', context)



def monthly_schedule_data_search(request):
	""" monthly schedule Data Search View """
	
	select_year= request.GET.get('select_year', None)
	grower_pk = request.GET.get('grower_pk', None)
	grower_details = GrowerProfile.cmobjects.filter(user_id=grower_pk).first()

	if select_year:
		monthly_shedule_list = MonthlySchedule.cmobjects.filter(year__year=select_year, grower_id=grower_details.id).order_by('-year')
	else:
		monthly_shedule_list = MonthlySchedule.cmobjects.filter(grower_id=grower_details.id).order_by('-year')

	page = request.GET.get('page', 1)
	paginator = Paginator(monthly_shedule_list, 10)
	try:
		monthly_shedule_list = paginator.page(page)
	except PageNotAnInteger:
		monthly_shedule_list = paginator.page(1)
	except EmptyPage:
		monthly_shedule_list = paginator.page(paginator.num_pages)

	context = {
		'monthly_shedule_list' : monthly_shedule_list,
		'grower_pk' : grower_pk,
		'growewr_details' : grower_details,
		'select_year': select_year,
		
	}

	return CommonMixin.render(request, 'farm_diary/farmdiary_monthly_shedule_list.html', context)


class MonthlyScheduleMixin:
	model = MonthlySchedule
	form_class = MonthlyScheduleForm
	template_name = 'farm_diary/monthly_shedule_form.html'

	def get_success_url(self, **kwargs):
		return reverse('chemical_data:farmdiary_monthly_shedule_list', kwargs={'grower_pk': self.kwargs['grower_pk']} )

	def get_grower(self):
		if not hasattr(self, '_grower_details'):
			self._grower_details = _get_grower_by_url_pk(self.kwargs['grower_pk'])
		return self._grower_details

	def get_object(self, queryset=None):
		grower_details = self.get_grower()
		if not grower_details:
			return None
		return MonthlySchedule.cmobjects.filter(
			grower_id=grower_details.id,
			pk=self.kwargs.get('monthly_shedule_pk')
		).prefetch_related('monthly_schedule_hour_details').first()

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['grower_pk'] = self.kwargs['grower_pk']
		context['grower_details'] = self.get_grower()
		schedule = self.object if getattr(self, 'object', None) else None
		if self.request.method == 'POST':
			days = self.request.POST.getlist('week_days[]')
			hours = self.request.POST.getlist('week_hours[]')
			context['day_hour_rows'] = [{'days': d, 'hour': h} for d, h in zip(days, hours)]
		elif schedule and schedule.pk:
			context['day_hour_rows'] = schedule.monthly_schedule_hour_details.all().order_by('id')
		else:
			context['day_hour_rows'] = []
		return context

	def _posted_day_hour_rows(self):
		days = self.request.POST.getlist('week_days[]')
		hours = self.request.POST.getlist('week_hours[]')
		rows = []
		for day_value, hour_value in zip(days, hours):
			if day_value == '' and hour_value == '':
				continue
			try:
				day = int(day_value)
				hour = int(hour_value)
			except (TypeError, ValueError):
				raise ValueError('Days and hours must be valid whole numbers.')
			if day <= 0 or hour <= 0:
				raise ValueError('Days and hours must be greater than zero.')
			rows.append((day, hour))
		return rows

	def form_invalid(self, form):
		for error in form.non_field_errors():
			messages.error(self.request, error)
		for field, errors in form.errors.items():
			if field == '__all__':
				continue
			label = form.fields[field].label if field in form.fields else field
			for error in errors:
				messages.error(self.request, f'{label}: {error}')
		return super().form_invalid(form)

	def form_valid(self, form):
		try:
			rows = self._posted_day_hour_rows()
		except ValueError as error:
			form.add_error(None, str(error))
			return self.form_invalid(form)
		year_value = form.cleaned_data['year'].year if form.cleaned_data.get('year') else None
		month_name = form.cleaned_data.get('month')
		max_rows = _month_week_count(year_value, month_name)
		max_days = _month_day_count(year_value, month_name)
		week_day_limits = _month_week_day_limits(year_value, month_name)
		total_days = sum(row[0] for row in rows)
		total_hours = sum(row[0] * row[1] for row in rows)
		hourly_rate = form.cleaned_data.get('hourly_rate') or 0
		if not rows:
			form.add_error(None, 'Add at least one Days and Hours row.')
			return self.form_invalid(form)
		if max_rows and len(rows) > max_rows:
			form.add_error(None, f'{month_name} {year_value} can have maximum {max_rows} week rows.')
			return self.form_invalid(form)
		for index, row in enumerate(rows):
			week_limit = week_day_limits[index] if index < len(week_day_limits) else 0
			if week_limit and row[0] > week_limit:
				form.add_error(None, f'Week {index + 1} can have maximum {week_limit} days for {month_name} {year_value}.')
				return self.form_invalid(form)
			if row[1] > row[0] * 24:
				form.add_error(None, f'Week {index + 1} hours cannot exceed {row[0] * 24:g} hours for {row[0]:g} days.')
				return self.form_invalid(form)
		if max_days and total_days > max_days:
			form.add_error(None, f'Total working days cannot exceed {max_days} days for {month_name} {year_value}.')
			return self.form_invalid(form)
		grower_details = self.get_grower()
		if not grower_details:
			form.add_error(None, 'Grower was not found.')
			return self.form_invalid(form)
		duplicate_qs = MonthlySchedule.cmobjects.filter(
			grower_id=grower_details.id,
			year=form.cleaned_data.get('year'),
			month=month_name,
		)
		if getattr(self, 'object', None) and self.object.pk:
			duplicate_qs = duplicate_qs.exclude(pk=self.object.pk)
		if duplicate_qs.exists():
			form.add_error(None, 'Monthly Schedule already exists for the selected year and month.')
			return self.form_invalid(form)
		with transaction.atomic():
			form.instance.created_by_id = form.instance.created_by_id or self.request.user.id
			form.instance.updated_by_id = self.request.user.id
			form.instance.grower_id = grower_details.id
			form.instance.no_of_working_days = int(total_days)
			form.instance.total_hours = total_hours
			form.instance.monthly_wages = total_hours * hourly_rate
			self.object = form.save()
			self.object.monthly_schedule_hour_details.all().delete()
			MonthlyScheduleDayHoursDetails.objects.bulk_create([
				MonthlyScheduleDayHoursDetails(
					monthly_schedule=self.object,
					days=day,
					hour=hour,
					created_by_id=self.request.user.id,
					updated_by_id=self.request.user.id,
				)
				for day, hour in rows
			])
		messages.success(self.request, 'Monthly Schedule Saved Successfully')
		return HttpResponseRedirect(self.get_success_url())


class MonthlyScheduleUpdateView(LoginRequiredMixin, CommonMixin, MonthlyScheduleMixin, UpdateView):
	"""Monthly Schedule Update View"""
	pass


class MonthlyScheduleCreateView(LoginRequiredMixin, CommonMixin, MonthlyScheduleMixin, CreateView):
	"""Monthly Schedule Create View"""
	pass


def monthly_schedule_data_delete(request, pk ):
	""" monthly schedule  Delete view """
	monthly_schedule_details = MonthlySchedule.cmobjects.filter(pk=pk).first()
	if monthly_schedule_details:
		monthly_schedule_details.is_deleted = True
		monthly_schedule_details.save()
		messages.success(request, 'Deleted Successfully')
	else:
		messages.error(request, 'Monthly Schedule record was not found')
	return redirect(request.META.get('HTTP_REFERER', reverse('chemical_data:farmdiary_user_list')))


def use_of_chemical_search(request):
	""" Use Of Chemical Data Search View """
	start_date= request.GET.get('start_date')
	end_date= request.GET.get('end_date')
	grower_pk = request.GET.get('grower_pk')
	chemical_type = request.GET.get('chemical_type')

	grower_details=GrowerProfile.cmobjects.filter(user_id=grower_pk).first()
	chemical_type_details = ChemicalType.objects.filter(pk=chemical_type).first()

	if start_date and end_date:
		use_of_chemical_list = UseOfChemical.cmobjects.filter(
			Q(date__range=(start_date, end_date)), 
			Q(grower_id=grower_details.id),
			Q(chemical__chemical_type__name__iexact=chemical_type_details)).order_by('-date')
		
	page = request.GET.get('page', 1)
	paginator = Paginator(use_of_chemical_list, 10)
	try:
		use_of_chemical_list = paginator.page(page)
	except PageNotAnInteger:
		use_of_chemical_list = paginator.page(1)
	except EmptyPage:
		use_of_chemical_list = paginator.page(paginator.num_pages)

	chemical_type_name = str(ChemicalType.objects.filter(pk=chemical_type).first())

	context = {
		'grower_details' : grower_details,
		'chemical_type_details' : chemical_type_details,
		'use_of_chemical_list' : use_of_chemical_list,
		'grower_pk' : grower_pk,
		'chemical_type' : chemical_type,
		'chemical_type_name' : chemical_type_name,
		'start_date': start_date,
		'end_date': end_date,
	}

	return CommonMixin.render(request, 'farm_diary/chemical_type_details.html', context)


######## STG FARM DIARY PDF REPORTS #############
def use_of_chemical_pdf_reports(request):
	""" Generate use of Chemical list PDF """
	from django.http import HttpResponse
	from xhtml2pdf import pisa
	from django.template.loader import get_template

	# Get query parameters from the request
	start_date = request.GET.get('start_date')
	end_date = request.GET.get('end_date')
	grower_pk = request.GET.get('grower_pk')
	chemical_type = request.GET.get('chemical_type')

	# Create a response with PDF content
	response = HttpResponse(content_type='application/pdf')
	response['Content-Disposition'] = f'attachment; filename="use_of_chemical_pdf.pdf"'


    # Generate PDF content here
	grower_details = GrowerProfile.objects.filter(user_id=grower_pk).first()
	chemical_type_details = ChemicalType.objects.filter(pk=chemical_type).first()
	chemical_type_name = str(ChemicalType.objects.filter(pk=chemical_type).first())

	if start_date and end_date:
		use_of_chemical_list = UseOfChemical.cmobjects.filter(
			Q(date__range=(start_date, end_date)),
			Q(grower_id=grower_details.id),
			Q(chemical__chemical_type__name__iexact=chemical_type_details)).order_by('-date')  # Sort in descending order
	else:
		use_of_chemical_list = UseOfChemical.cmobjects.filter(
			Q(grower_id=grower_details.id),
			Q(chemical__chemical_type__name__iexact=chemical_type_details)).order_by('-date')

	context = {
		"start_date" : start_date,
		"use_of_chemical_list" : use_of_chemical_list,
		"grower_pk" : grower_pk,
		"chemical_type" : chemical_type,
		"grower_details" : grower_details,
		"chemical_type_name" : chemical_type_name,
	}
	# Create an HTML template
	template = get_template('reports_pdf/chemical_list_pdf.html')
	html = template.render(context)  # Replace with your template context data

	# Generate PDF
	pisa.CreatePDF(html, dest=response)
	return response


def plucking_data_generate_pdf(request):
	""" Plucking Data generate pdf View """
	from django.http import HttpResponse
	from xhtml2pdf import pisa
	from django.template.loader import get_template
	
	start_date= request.GET.get('start_date')
	end_date= request.GET.get('end_date')
	grower_pk = request.GET.get('grower_pk')

	grower_details=GrowerProfile.cmobjects.filter(user_id=grower_pk).first()

	if start_date and end_date:
		item_list = PluckingData.cmobjects.filter(
			Q(date__range=(start_date, end_date)),
			Q(grower_id=grower_details.id)).order_by('-date')# Sort in descending order
	else:
		item_list = PluckingData.cmobjects.filter(
			Q(grower_id=grower_details.id)).order_by('-date')

	context = {
		'grower_details' : grower_details,
		'grower_pk' : grower_pk,
		'grower_details' : grower_details,
		'plucking_data_list' : item_list,
	}
	
	# Create a response with PDF content
	response = HttpResponse(content_type='application/pdf')
	response['Content-Disposition'] = f'attachment; filename="plucking_data_list_pdf.pdf"'

	# Create an HTML template
	template = get_template('reports_pdf/plucking_data_list_pdf.html')
	html = template.render(context)  # Replace with your template context data

	# Generate PDF
	pisa.CreatePDF(html, dest=response)
	return response


def generate_labour_pdf(request):
	""" Labour Data generate pdf View """
	from django.http import HttpResponse
	from xhtml2pdf import pisa
	from django.template.loader import get_template
	
	labour_type= request.GET.get('labour_type')
	grower_pk = request.GET.get('grower_pk')

	grower_details=GrowerProfile.cmobjects.filter(user_id=grower_pk).first()

	if labour_type:
		item_list = Labour.cmobjects.filter(
			Q(type=labour_type),
			Q(grower_id=grower_details.id)).order_by('-id')# Sort in descending order
	else:
		item_list = Labour.cmobjects.filter(
		Q(grower_id=grower_details.id)).order_by('-id')

	context = {
		'grower_details' : grower_details,
		'grower_pk' : grower_pk,
		'grower_details' : grower_details,
		'labour_list' : item_list,
	}
	
	# Create a response with PDF content
	response = HttpResponse(content_type='application/pdf')
	response['Content-Disposition'] = f'attachment; filename="labour_data_pdf.pdf"'

	# Create an HTML template
	template = get_template('reports_pdf/labour_list_pdf.html')
	html = template.render(context)  # Replace with your template context data

	# Generate PDF
	pisa.CreatePDF(html, dest=response)
	return response



def grower_farmdiary_pdf(request):
	""" Labour Data generate pdf View """
	from django.http import HttpResponse
	from xhtml2pdf import pisa
	from django.template.loader import get_template
	
	grower_pk = request.GET.get('grower_pk')
	grower_details=GrowerProfile.cmobjects.filter(user_id=grower_pk).first()

	# if labour_type:
	# 	item_list = Labour.cmobjects.filter(
	# 		Q(type=labour_type),
	# 		Q(grower_id=grower_details.id)).order_by('-id')# Sort in descending order
	# else:
	# 	item_list = Labour.cmobjects.filter(
	# 	Q(grower_id=grower_details.id)).order_by('-id')

	labour_list = Labour.cmobjects.filter(
		Q(grower_id=grower_details.id)).order_by('-id')
	
	plucking_data_list = PluckingData.cmobjects.filter(
			Q(grower_id=grower_details.id)).order_by('-date')
	
	use_of_fertilizer_list = UseOfChemical.cmobjects.filter(
			Q(grower_id=grower_details.id),
			Q(chemical__chemical_type_id=1)).order_by('-date')
	
	use_of_herbicides_list = UseOfChemical.cmobjects.filter(
			Q(grower_id=grower_details.id),
			Q(chemical__chemical_type_id=2)).order_by('-date')
	
	use_of_insecticides_list = UseOfChemical.cmobjects.filter(
			Q(grower_id=grower_details.id),
			Q(chemical__chemical_type_id=3)).order_by('-date')

	use_of_acaricides_list = UseOfChemical.cmobjects.filter(
			Q(grower_id=grower_details.id),
			Q(chemical__chemical_type_id=5)).order_by('-date')

	monthly_shedule_list = MonthlySchedule.cmobjects.filter(grower_id=grower_details.id).order_by('-year')

	context = {
		'grower_details' : grower_details,
		'grower_pk' : grower_pk,
		'grower_details' : grower_details,
		'labour_list' : labour_list,
		'plucking_data_list' : plucking_data_list,
		"fertilizer_chemical_list" : use_of_fertilizer_list,
		"herbicides_chemical_list" : use_of_herbicides_list,
		"insecticides_chemical_list" : use_of_insecticides_list,
		"acaricides_chemical_list" : use_of_acaricides_list,
		"schedule_list" : monthly_shedule_list,

	}
	
	# Create a response with PDF content
	response = HttpResponse(content_type='application/pdf')
	response['Content-Disposition'] = f'attachment; filename="consolidated_farm_diary.pdf"'

	# Create an HTML template
	template = get_template('consolidate.html')
	html = template.render(context)  # Replace with your template context data

	# Generate PDF
	pisa.CreatePDF(html, dest=response)
	return response




@login_required
def farm_diary_add_map__back(request, grower_pk, map_area):
	
	blf_details = BlfProfile.cmobjects.filter(user=request.user).first()
	grower_details = GrowerProfile.cmobjects.filter(user=grower_pk).first()

	map_area_details = MapAreaNameMaster.cmobjects.filter(slug__icontains=map_area).first()
	check_details_data = MapAreaDetails.cmobjects.filter(map_area_name=map_area_details,\
				grower=grower_details, created_by=request.user).first()
	
	if str(map_area) == "total-land-under-agriculuture":
		map_area_url = "land-under-tea-cultivation"
		back_url = ''
	elif str(map_area) == "land-under-tea-cultivation":
		map_area_url = "area-of-human-settlement"
		back_url = 'total-land-under-agriculuture'

	elif str(map_area) == "area-of-human-settlement":
		map_area_url = "area-under-other-agri-product"
		back_url = 'land-under-tea-cultivation'

	elif str(map_area) == "area-under-other-agri-product":
		map_area_url = "water-source"
		back_url = 'area-of-human-settlement'

	elif str(map_area) == "water-source":
		map_area_url = "land-nearby"
		back_url = 'area-under-other-agri-product'
	else:
		map_area_url = "total-land-under-agriculuture"
		back_url = 'water-source'

	
	if request.method == "POST":
		total_area = request.POST.get('total_area')
		map_area_name = MapAreaNameMaster.cmobjects.filter(slug__icontains=map_area).first()

		coordinates = request.POST.get('coordinates')
		
		if total_area and map_area_name:
			total_area = float(total_area)  # Convert the input to a float if needed
			create_map_area_details = MapAreaDetails(blf_id=blf_details.id, grower=grower_details, map_area_name=map_area_name,\
							total_areas=total_area, created_by_id=request.user.id)
			
			create_map_area_details.save()
			messages.success(request, 'Created Successfully')

			return redirect(reverse('chemical_data:farm_diary_add_map', kwargs={"grower_pk": grower_pk, "map_area": map_area_url }))
			
	context = {
		'grower_pk': grower_pk,
		'map_area': map_area,
		'map_area_details': map_area_details,
		"map_area_back_url" : back_url,
		"check_details_data" : check_details_data,
		"map_area_url" : map_area_url,
	}

	return CommonMixin.render(request, 'farm_diary/farm_diary_add_map.html', context)


import json  # Import json module

@login_required
def farm_diary_add_map(request, grower_pk, map_area):

	blf_details = BlfProfile.cmobjects.filter(user=request.user).first()
	grower_details = GrowerProfile.cmobjects.filter(user=grower_pk).first()
	existing_manual_map = MapAreaMaster.cmobjects.filter(
		grower=grower_details,
		is_image_upload=True,
	).first()
	if existing_manual_map:
		messages.error(request, "Manual map is already uploaded. Digital map creation is disabled for this grower.")
		return redirect(reverse('chemical_data:farm_diary_map_create', kwargs={"grower_pk": grower_pk}))

	map_area_details = MapAreaNameMaster.cmobjects.filter(slug__icontains=map_area).first()

	map_area_master_details = MapAreaMaster.cmobjects.filter(grower=grower_details).first()
	map_land_area_list = MapAreaLandDetails.cmobjects.filter(
		grower=grower_details
	)
	check_details_data = MapAreaLandDetails.cmobjects.filter(
		map_area_name=map_area_details,
		grower=grower_details,
	).first()

	# print("check_details_data Length #########", map_land_area_list_count)
	land_details_data_1 = MapAreaLandDetails.cmobjects.filter(
		map_area_name_id=1,
		grower=grower_details,
	).first()

	land_details_data_2 = MapAreaLandDetails.cmobjects.filter(
		map_area_name_id=2,
		grower=grower_details,
	).first()

	land_details_data_3 = MapAreaLandDetails.cmobjects.filter(
		map_area_name_id=3,
		grower=grower_details,
	).first()

	land_details_data_4 = MapAreaLandDetails.cmobjects.filter(
		map_area_name_id=4,
		grower=grower_details,
	).first()


	# print("map_area_details ======== #######", map_area_details)

	if str(map_area) == "total-land-under-agriculuture":
		map_area_url = "land-under-tea-cultivation"
		back_url = ''

	elif str(map_area) == "land-under-tea-cultivation":
		map_area_url = "area-of-human-settlement"
		back_url = 'total-land-under-agriculuture'

	elif str(map_area) == "area-of-human-settlement":
		map_area_url = "area-under-other-agri-product"
		back_url = 'land-under-tea-cultivation'

	elif str(map_area) == "area-under-other-agri-product":
		map_area_url = "water-source-land-near-by"
		back_url = 'area-of-human-settlement'

	elif str(map_area) == "water-source-land-near-by":
		map_area_url = "total-land-under-agriculuture"
		back_url = 'area-under-other-agri-product'
	else:
		map_area_url = "total-land-under-agriculuture"
		back_url = 'water-source'

	action_type = request.GET.get('action_type')

	if request.GET.get:
		action_type = request.GET.get('action_type')
		edit_area_url = map_area
		print("edit_back_url#############", edit_area_url)


	if request.method == "POST":
		total_area = request.POST.get('total_area')
		land_near_by = request.POST.get('land_near_by')
		water_source = request.POST.get('water_source')
		coordinates = request.POST.get('coordinates')
		map_edit = request.POST.get('edit_map')

		map_area_name = MapAreaNameMaster.cmobjects.filter(slug__icontains=map_area).first()
		map_edit = str(map_edit)

		check_map_area_master_details = MapAreaMaster.cmobjects.filter(grower=grower_details).first()
		print("check_map_area_master_details **", check_map_area_master_details)

		if check_map_area_master_details is None:
			check_map_area_master_details = MapAreaMaster(
				blf=blf_details,
				grower=grower_details,
				is_digital_upload = True,
				created_by=request.user
			).save()
			
		if check_map_area_master_details and land_near_by and water_source:
			check_map_area_master_details.grower=grower_details
			check_map_area_master_details.water_source = water_source
			check_map_area_master_details.land_near_by = land_near_by
			check_map_area_master_details.updated_by = request.user
			check_map_area_master_details.save()
			messages.success(request, 'Created Successfully')
			return redirect(reverse('chemical_data:farm_diary_add_map', kwargs={"grower_pk": grower_pk, "map_area": map_area_url}))

			
		if land_near_by and water_source and check_map_area_master_details is None:

			create_map_area_details = MapAreaMaster(
				blf=blf_details,
				grower=grower_details,
				water_source=water_source,
				land_near_by=land_near_by,
				created_by=request.user
			).save()
			messages.success(request, 'Created Successfully')
			return redirect(reverse('chemical_data:farm_diary_add_map', kwargs={"grower_pk": grower_pk, "map_area": map_area_url}))


		if total_area and map_area_name and coordinates:
			total_area = float(total_area)
			coordinates = json.loads(coordinates)

			create_map_area_details = MapAreaLandDetails(
				grower=grower_details,
				map_area_master= check_map_area_master_details,
				map_area_name=map_area_name,
				total_areas=total_area,
				coordinate=coordinates,
				created_by=request.user
			).save()

			messages.success(request, 'Created Successfully')
			return redirect(reverse('chemical_data:farm_diary_add_map', kwargs={"grower_pk": grower_pk, "map_area": map_area_url}))


		print("map_edit ###################", map_edit)

		if str(map_edit) == "map_edit" and total_area and map_area_name and coordinates:
			total_area = float(total_area)
			coordinates = json.loads(coordinates)


			print(f"coordinates={coordinates}, total_area={total_area}")

			check_details_data.total_areas = total_area
			check_details_data.coordinate = coordinates
			check_details_data.save()
			messages.success(request, 'Updatedd Successfully')
			return redirect(reverse('chemical_data:farm_diary_add_map', kwargs={"grower_pk": grower_pk, "map_area": map_area}))




	context = {
		'grower_pk': grower_pk,
		'map_area': map_area,
		'map_area_details': map_area_details,
		"map_area_back_url": back_url,
		"check_details_data": check_details_data,
		"map_area_url": map_area_url,
		"edit" : action_type,
		"land_details_data_1" : land_details_data_1,
		"land_details_data_2" : land_details_data_2,
		"land_details_data_3" : land_details_data_3,
		"land_details_data_4" : land_details_data_4,
		"map_area_master_details" : map_area_master_details,
		"edit_area_url" : edit_area_url,
		"map_land_area_list_count" : len(map_land_area_list),
		"map_land_area_list" : map_land_area_list,
	}

	return CommonMixin.render(request, 'farm_diary/farm_diary_add_map.html', context)





# EDIT MAP AREA
@login_required
def farm_diary_edit_map(request, grower_pk, map_area):

	blf_details = BlfProfile.cmobjects.filter(user=request.user).first()
	grower_details = GrowerProfile.cmobjects.filter(user=grower_pk).first()
	map_area_details = MapAreaNameMaster.cmobjects.filter(slug__icontains=map_area).first()

	check_details_data = MapAreaLandDetails.cmobjects.filter(
		map_area_name=map_area_details,
		grower=grower_details
	).first()

	back_url = map_area

	print("map_area_back_url ###########", back_url)

	action_type = request.GET.get('action_type')

	if request.method == "POST":
		total_area = request.POST.get('total_area')
		coordinates = request.POST.get('coordinates')
		map_edit = request.POST.get('edit_map')

		print("total_area ###$$$$$$$$$$$$$$$$$$$", total_area)

		map_area_name = MapAreaNameMaster.cmobjects.filter(slug__icontains=map_area).first()

		map_edit = str(map_edit)

		if map_edit and total_area and map_area_name and coordinates:
			total_area = float(total_area)
			coordinates = json.loads(coordinates)

			check_details_data.total_areas = total_area
			check_details_data.coordinate = coordinates
			check_details_data.save()
			messages.success(request, 'Updatedd Successfully')
			return HttpResponseRedirect(request.META.get("HTTP_REFERER"))

		if map_edit and total_area and map_area_name:
			total_area = float(total_area)
			check_details_data.total_areas = total_area
			check_details_data.save()
			messages.success(request, 'Updatedd Successfully')
			return HttpResponseRedirect(request.META.get("HTTP_REFERER"))

	context = {
		'grower_pk': grower_pk,
		'map_area': map_area,
		'map_area_details': map_area_details,
		"map_area_back_url": back_url,
		"check_details_data": check_details_data,
		"edit" : action_type,
	}
	return HttpResponseRedirect(request.META.get("HTTP_REFERER"))




# EDIT TEXT DATA
@login_required
def farm_diary_edit_map_text_data(request, grower_pk, map_area):
	blf_details = BlfProfile.cmobjects.filter(user=request.user).first()
	grower_details = GrowerProfile.cmobjects.filter(user=grower_pk).first()
	map_area_details = MapAreaNameMaster.cmobjects.filter(slug__icontains=map_area).first()

	check_details_data = MapAreaDetails.cmobjects.filter(
		map_area_name=map_area_details,
		grower=grower_details,
		blf=blf_details
	).first()

	if str(map_area) == "total-land-under-agriculuture":
		map_area_url = "land-under-tea-cultivation"
		back_url = ''
	elif str(map_area) == "land-under-tea-cultivation":
		map_area_url = "area-of-human-settlement"
		back_url = 'total-land-under-agriculuture'
	elif str(map_area) == "area-of-human-settlement":
		map_area_url = "area-under-other-agri-product"
		back_url = 'land-under-tea-cultivation'
	elif str(map_area) == "area-under-other-agri-product":
		map_area_url = "water-source"
		back_url = 'area-of-human-settlement'
	elif str(map_area) == "water-source":
		map_area_url = "land-nearby"
		back_url = 'area-under-other-agri-product'
	else:
		map_area_url = "total-land-under-agriculuture"
		back_url = 'water-source'

	action_type = request.GET.get('action_type')

	if request.method == "POST":
		total_area = request.POST.get('total_area')

		total_area = float(total_area)

		check_details_data.total_areas = total_area
		check_details_data.save()
		messages.success(request, 'Updatedd Successfully')
		return redirect(reverse('chemical_data:farm_diary_add_map', kwargs={"grower_pk": grower_pk, "map_area": map_area}))
		
	context = {
		'grower_pk': grower_pk,
		'map_area': map_area,
		'map_area_details': map_area_details,
		"map_area_back_url": back_url,
		"check_details_data": check_details_data,
		"map_area_url": map_area_url,
		"edit" : action_type,
	}
	return CommonMixin.render(request, 'farm_diary/farm_diary_add_map.html', context)




@login_required
def farmers_aggreements_forms_list(request, grower_pk):

	blf_details = BlfProfile.objects.filter(user=request.user).first()
	grower_details = GrowerProfile.objects.filter(user=grower_pk).first()
	froms_list = FarmersAggreementMaster.cmobjects.all()

	final_list = []

	for item in froms_list:
		form_master_name = item.name
		form_master_pk = item.pk
		form_details = FarmersAggreementForms.cmobjects.filter(aggreement_form_title=item.pk, blf=blf_details,\
										 grower=grower_details)
		
		print("form_details ### ****", form_details)

		form_data = {
                'form_master_name': form_master_name,	
				"form_master_pk" : form_master_pk,  
                "form_details" : form_details,
		}
		final_list.append(form_data)


	print("froms_list", froms_list)

	context ={
		"grower_pk" : grower_pk,
		"grower_details" : grower_details,
		"froms_list" : final_list,
	}

	return CommonMixin.render(request, "farm_diary/farmers_aggreements_forms_list.html", context)



@login_required
def farm_diary_mannual_map_create(request, grower_pk):

	blf_details = BlfProfile.cmobjects.filter(user=request.user).first()
	grower_details = GrowerProfile.cmobjects.filter(user_id=grower_pk).first()
	if not grower_details:
		messages.error(request, "Grower not found.")
		return redirect(reverse('chemical_data:farmdiary_user_list'))

	map_area_master_details = MapAreaMaster.cmobjects.filter(grower=grower_details).first()
	total_land_area = MapAreaNameMaster.cmobjects.filter(slug__icontains="total-land-under-agriculuture").first()
	if not total_land_area:
		total_land_area = MapAreaNameMaster.cmobjects.order_by("id").first()
	total_area_details = MapAreaLandDetails.cmobjects.filter(
		grower=grower_details,
		map_area_name=total_land_area,
	).first()

	if request.method == "POST":
		form = ManualMapUploadForm(
			request.POST,
			request.FILES,
			instance=map_area_master_details,
			initial_total_area=total_area_details.total_areas if total_area_details else None,
		)
		if form.is_valid():
			with transaction.atomic():
				map_area_master_details = form.save(commit=False)
				map_area_master_details.blf = blf_details
				map_area_master_details.grower = grower_details
				map_area_master_details.is_image_upload = True
				map_area_master_details.is_digital_upload = False
				map_area_master_details.water_source = ""
				if not map_area_master_details.created_by_id:
					map_area_master_details.created_by = request.user
				map_area_master_details.updated_by = request.user
				map_area_master_details.save()

				if total_land_area:
					map_area_land_details, created = MapAreaLandDetails.cmobjects.get_or_create(
						grower=grower_details,
						map_area_master=map_area_master_details,
						map_area_name=total_land_area,
						defaults={
							"created_by": request.user,
						},
					)
					map_area_land_details.total_areas = form.cleaned_data["total_area"]
					map_area_land_details.updated_by = request.user
					if created:
						map_area_land_details.created_by = request.user
					map_area_land_details.save()

				MapAreaLandDetails.cmobjects.filter(
					grower=grower_details,
					map_area_master=map_area_master_details,
				).exclude(map_area_name=total_land_area).update(is_deleted=True, updated_by=request.user)

			messages.success(request, 'Manual map saved successfully.')
			return redirect(reverse('chemical_data:farm_diary_mannual_map_create', kwargs={"grower_pk": grower_pk}))
		else:
			messages.error(request, "Please correct the errors below.")
	else:
		form = ManualMapUploadForm(
			instance=map_area_master_details,
			initial_total_area=total_area_details.total_areas if total_area_details else None,
		)

	templates_name = "farm_diary/farmers_mannual_map_upload.html"

	context = {
		"blf_details": blf_details,
		"grower_details": grower_details,
		"grower_pk": grower_pk,
		"form": form,
		"map_area_master_details": map_area_master_details,
		"total_area_details": total_area_details,
	}
	return CommonMixin.render(request, templates_name, context)



# Edit

# views.py
from django.db import transaction

@login_required
def farm_diary_manual_map_edit(request, grower_pk):
	blf_details = BlfProfile.objects.filter(user=request.user).first()
	grower_details = GrowerProfile.objects.filter(user_id=grower_pk).first()
	map_area_name_master_list = MapAreaNameMaster.objects.all()
	map_area_master_details = MapAreaMaster.objects.filter(grower=grower_details).first()
	land_details = MapAreaLandDetails.objects.filter(grower=grower_details)

	map_land_area_list = MapAreaLandDetails.objects.filter(grower=grower_details)
	check_details_data = MapAreaLandDetails.objects.filter(grower=grower_details).first()

	land_details_data_1 = MapAreaLandDetails.objects.filter(map_area_name_id=1, grower=grower_details).first()
	land_details_data_2 = MapAreaLandDetails.objects.filter(map_area_name_id=2, grower=grower_details).first()
	land_details_data_3 = MapAreaLandDetails.objects.filter(map_area_name_id=3, grower=grower_details).first()
	land_details_data_4 = MapAreaLandDetails.objects.filter(map_area_name_id=4, grower=grower_details).first()

	if request.method == "POST":
		# Create or update MapAreaMaster
		if map_area_master_details:
			map_image = request.FILES.get('map_image')
			water_source = request.POST.get('water_source')
			land_near_by = request.POST.get('land_near_by')

			if map_image is not None:
				map_area_master_details.map_image = map_image
			if water_source is not None:
				map_area_master_details.water_source = water_source
			if land_near_by is not None:
				map_area_master_details.land_near_by = land_near_by

			map_area_master_details.updated_by = request.user
			map_area_master_details.save()

		# Save or update MapAreaLandDetails for each MapAreaNameMaster
		for item in map_area_name_master_list:
			total_areas_str = request.POST.get(f'total_areas_{item.pk}')
			print(f"Processing item: {item.pk}")
			print(f"total_areas_{item.pk}: {total_areas_str}")

			if total_areas_str:
				try:
					total_areas = float(total_areas_str)
				except ValueError:
					total_areas = None

				print(f"total_areas ### {total_areas}")

				if total_areas is not None:
					with transaction.atomic():
						# Check if MapAreaLandDetails already exists
						map_areas_land_details = MapAreaLandDetails.objects.select_for_update().filter(
							map_area_master=map_area_master_details,
							map_area_name=item
						).first()

						print(f"map_areas_land_details ## {map_areas_land_details}")

						if map_areas_land_details:
							# Update the existing MapAreaLandDetails instance
							map_areas_land_details.total_areas = total_areas
							map_areas_land_details.updated_by = request.user
							if item.pk == 1:
								# Forcefully update for item.pk == 1
								# print(f"Forcefully updating map_areas_land_details for item: {item.pk}")
								# map_areas_land_details.total_areas = total_areas

								# map_areas_land_details_pk_1 = MapAreaLandDetails.cmobjects.filter(
								# 	grower=grower_details,
								# 	map_area_name_id=1
								# ).first()

								# map_areas_land_details_pk_1.total_areas = total_areas
								# map_areas_land_details_pk_1.save()

								# Fetch the object, or create it if it does not exist
								map_areas_land_details_pk_1, created = MapAreaLandDetails.cmobjects.get_or_create(
									grower=grower_details,
									map_area_name_id=1,
									defaults={'total_areas': total_areas}
								)

								# If the object was already existing, update the total_areas and save
								if not created:
									map_areas_land_details_pk_1.total_areas = total_areas
									map_areas_land_details_pk_1.save()

							else:
								map_areas_land_details.save()
							print(f"Updated map_areas_land_details for item: {item.pk}")
						else:
							map_areas_land_details = MapAreaLandDetails(
								map_area_master=map_area_master_details,
								map_area_name=item,
								grower=grower_details,
								total_areas=total_areas,
								created_by=request.user
							)
							map_areas_land_details.save()
							print(f"Created new map_areas_land_details for item: {item.pk}")

		messages.success(request, 'Map area details updated successfully')
		return HttpResponseRedirect(request.META.get("HTTP_REFERER"))

	else:
		form = MapAreaDetailsForm()

	map_area_url = 'total-land-under-agriculture'

	template_name = "farm_diary/farmers_mannual_map_edit.html"

	#### Get land details by land master Details
	land_item_list_dict = []
	for item in map_area_name_master_list:
		land_master_id = item.pk
		land_name = item.name
		land_area_details_list = MapAreaLandDetails.objects.filter(map_area_name_id=item.pk, grower=grower_details)

		# Assuming you want the total_areas of the first item in the list
		total_areas = land_area_details_list.first().total_areas if land_area_details_list.exists() else None

		land_data = {
			"land_master_id": land_master_id,
			"land_name": land_name,
			"total_areas": total_areas,
			"land_area_details_list": land_area_details_list,
		}
		land_item_list_dict.append(land_data)

	context = {
		"blf_details": blf_details,
		"grower_details": grower_details,
		"grower_pk": grower_pk,
		"form": form,
		"map_area_name_master_list": map_area_name_master_list,
		"map_area_master_details": map_area_master_details,
		"map_area_url": map_area_url,
		"land_details": land_details,
		"land_details_data_1": land_details_data_1,
		"land_details_data_2": land_details_data_2,
		"land_details_data_3": land_details_data_3,
		"land_details_data_4": land_details_data_4,
		"map_land_area_list": map_land_area_list,
		"land_item_list_dict": land_item_list_dict,
	}
	return CommonMixin.render(request, template_name, context)



# views.py
# @login_required
# def farm_diary_manual_map_edit(request, grower_pk):
# 	blf_details = BlfProfile.objects.filter(user=request.user).first()
# 	grower_details = GrowerProfile.objects.filter(user_id=grower_pk).first()
# 	map_area_name_master_list = MapAreaNameMaster.objects.all()
# 	map_area_master_details = MapAreaMaster.objects.filter(grower=grower_details).first()
# 	land_details = MapAreaLandDetails.objects.filter(grower=grower_details)

# 	map_land_area_list = MapAreaLandDetails.objects.filter(grower=grower_details)
# 	check_details_data = MapAreaLandDetails.objects.filter(grower=grower_details).first()

# 	land_details_data_1 = MapAreaLandDetails.objects.filter(map_area_name_id=1, grower=grower_details).first()
# 	land_details_data_2 = MapAreaLandDetails.objects.filter(map_area_name_id=2, grower=grower_details).first()
# 	land_details_data_3 = MapAreaLandDetails.objects.filter(map_area_name_id=3, grower=grower_details).first()
# 	land_details_data_4 = MapAreaLandDetails.objects.filter(map_area_name_id=4, grower=grower_details).first()

# 	if request.method == "POST":
# 		# Create or update MapAreaMaster
# 		if map_area_master_details:
# 			map_image = request.FILES.get('map_image')
# 			water_source = request.POST.get('water_source')
# 			land_near_by = request.POST.get('land_near_by')

# 			if map_image is not None:
# 				map_area_master_details.map_image = map_image
# 			if water_source is not None:
# 				map_area_master_details.water_source = water_source
# 			if land_near_by is not None:
# 				map_area_master_details.land_near_by = land_near_by

# 			map_area_master_details.updated_by = request.user
# 			map_area_master_details.save()

# 		# Save or update MapAreaLandDetails for each MapAreaNameMaster
# 		for item in map_area_name_master_list:
# 			total_areas_str = request.POST.get(f'total_areas_{item.pk}')
# 			print(f"total_areas_{item.pk}: {total_areas_str}")


# 			print("item ==", item.pk)

# 			if total_areas_str:
# 				try:
# 					total_areas = float(total_areas_str)
# 				except ValueError:
# 					total_areas = None

# 				print(f"total_areas ### {total_areas}")

# 				if total_areas is not None:
# 					# Check if MapAreaLandDetails already exists
# 					map_areas_land_details = MapAreaLandDetails.objects.filter(
# 						map_area_master=map_area_master_details,
# 						map_area_name=item
# 					).first()

# 					print(f"map_areas_land_details ## {map_areas_land_details}")

# 					if map_areas_land_details:
# 						# Update the existing MapAreaLandDetails instance
# 						map_areas_land_details.total_areas = total_areas
# 						map_areas_land_details.updated_by = request.user
# 						map_areas_land_details.save()
# 					else:
# 						map_areas_land_details = MapAreaLandDetails(
# 							map_area_master=map_area_master_details,
# 							map_area_name=item,
# 							grower=grower_details,
# 							total_areas=total_areas,
# 							created_by=request.user
# 						)
# 						map_areas_land_details.save()

# 		messages.success(request, 'Map area details updated successfully')
# 		return HttpResponseRedirect(request.META.get("HTTP_REFERER"))

# 	else:
# 		form = MapAreaDetailsForm()

# 	map_area_url = 'total-land-under-agriculture'

# 	template_name = "farm_diary/farmers_mannual_map_edit.html"

# 	#### Get land details by land master Details
# 	land_item_list_dict = []
# 	for item in map_area_name_master_list:
# 		land_master_id = item.pk
# 		land_name = item.name
# 		land_area_details_list = MapAreaLandDetails.objects.filter(map_area_name_id=item.pk, grower=grower_details)

# 		# Assuming you want the total_areas of the first item in the list
# 		total_areas = land_area_details_list.first().total_areas if land_area_details_list.exists() else None

# 		land_data = {
# 			"land_master_id": land_master_id,
# 			"land_name": land_name,
# 			"total_areas": total_areas,
# 			"land_area_details_list": land_area_details_list,
# 		}
# 		land_item_list_dict.append(land_data)

# 	context = {
# 		"blf_details": blf_details,
# 		"grower_details": grower_details,
# 		"grower_pk": grower_pk,
# 		"form": form,
# 		"map_area_name_master_list": map_area_name_master_list,
# 		"map_area_master_details": map_area_master_details,
# 		"map_area_url": map_area_url,
# 		"land_details": land_details,
# 		"land_details_data_1": land_details_data_1,
# 		"land_details_data_2": land_details_data_2,
# 		"land_details_data_3": land_details_data_3,
# 		"land_details_data_4": land_details_data_4,
# 		"map_land_area_list": map_land_area_list,
# 		"land_item_list_dict": land_item_list_dict,
# 	}
# 	return CommonMixin.render(request, template_name, context)









# @login_required
# def farm_diary_manual_map_edit(request, grower_pk):
# 	blf_details = BlfProfile.objects.filter(user=request.user).first()
# 	grower_details = GrowerProfile.objects.filter(user_id=grower_pk).first()
# 	map_area_name_master_list = MapAreaNameMaster.objects.all()
# 	map_area_master_details = MapAreaMaster.objects.filter(grower=grower_details).first()
# 	land_details = MapAreaLandDetails.objects.filter(grower=grower_details)

# 	map_land_area_list = MapAreaLandDetails.cmobjects.filter(
# 		grower=grower_details
# 	)
# 	check_details_data = MapAreaLandDetails.cmobjects.filter(
# 		grower=grower_details
# 	).first()

# 	# print("check_details_data Length #########", map_land_area_list_count)
# 	land_details_data_1 = MapAreaLandDetails.cmobjects.filter(
# 		map_area_name_id=1,
# 		grower=grower_details,
# 	).first()

# 	land_details_data_2 = MapAreaLandDetails.cmobjects.filter(
# 		map_area_name_id=2,
# 		grower=grower_details,
# 	).first()

# 	land_details_data_3 = MapAreaLandDetails.cmobjects.filter(
# 		map_area_name_id=3,
# 		grower=grower_details,
# 	).first()

# 	land_details_data_4 = MapAreaLandDetails.cmobjects.filter(
# 		map_area_name_id=4,
# 		grower=grower_details,
# 	).first()

# 	if request.method == "POST":
# 		# Create or update MapAreaMaster
# 		if map_area_master_details:
# 			map_image = request.FILES.get('map_image')
# 			water_source = request.POST.get('water_source')
# 			land_near_by = request.POST.get('land_near_by')

# 			if map_image is not None:
# 				map_area_master_details.map_image = map_image
# 			if water_source is not None:
# 				map_area_master_details.water_source = water_source
# 			if land_near_by is not None:
# 				map_area_master_details.land_near_by = land_near_by

# 			map_area_master_details.updated_by = request.user
# 			map_area_master_details.save()

# 		# Save or update MapAreaLandDetails for each MapAreaNameMaster
# 		for item in map_area_name_master_list:
# 			total_areas = request.POST.get(f'total_areas_{item.pk}')

# 			print(f"total_areas_{item.pk}:", item.pk)
# 			print("total_areas ###", total_areas)

# 			if total_areas:
# 				# Check if MapAreaLandDetails already exists
# 				map_areas_land_details = MapAreaLandDetails.objects.filter(
# 					map_area_master=map_area_master_details,
# 					map_area_name=item
# 				).first()

# 				print("map_areas_land_details ##", map_areas_land_details)

# 				if map_areas_land_details:
# 					# Update the existing MapAreaLandDetails instance
# 					map_areas_land_details.total_areas = total_areas
# 					map_areas_land_details.updated_by = request.user
# 					map_areas_land_details.save()
# 				else:
# 					map_areas_land_details = MapAreaLandDetails(
# 							map_area_master=map_area_master_details,
# 							map_area_name=item,
# 							grower=grower_details,
# 							total_areas=total_areas,
# 							created_by=request.user
# 						)
# 					map_areas_land_details.save()
				
# 		messages.success(request, 'Map area details updated successfully')
# 		return HttpResponseRedirect(request.META.get("HTTP_REFERER"))

# 	else:
# 		form = MapAreaDetailsForm()

# 	map_area_url = 'total-land-under-agriculture'

# 	template_name = "farm_diary/farmers_mannual_map_edit.html"

# 	#### Get land details by land master Details
# 	#view
# 	land_item_list_dict = []
# 	for item in map_area_name_master_list:
# 		land_master_id = item.pk
# 		land_name = item.name
# 		land_area_details_list = MapAreaLandDetails.objects.filter(map_area_name_id=item.pk, grower=grower_details)

# 		# Assuming you want the total_areas of the first item in the list
# 		total_areas = land_area_details_list.first().total_areas if land_area_details_list.exists() else None

# 		land_data = {
# 			"land_master_id": land_master_id,
# 			"land_name": land_name,
# 			"total_areas": total_areas,
# 			"land_area_details_list": land_area_details_list,
# 		}
# 		land_item_list_dict.append(land_data)


# 	context = {
# 		"blf_details": blf_details,
# 		"grower_details": grower_details,
# 		"grower_pk": grower_pk,
# 		"form": form,
# 		"map_area_name_master_list": map_area_name_master_list,
# 		"map_area_master_details": map_area_master_details,
# 		"map_area_url": map_area_url,
# 		"land_details": land_details,
# 		"land_details_data_1" : land_details_data_1,
# 		"land_details_data_2" : land_details_data_2,
# 		"land_details_data_3" : land_details_data_3,
# 		"land_details_data_4" : land_details_data_4,
# 		"map_land_area_list" : map_land_area_list,
# 		"land_item_list_dict" : land_item_list_dict,
# 	}
# 	return CommonMixin.render(request, template_name, context)









# @login_required
# def farm_diary_manual_map_edit(request, grower_pk):
# 	blf_details = BlfProfile.objects.filter(user=request.user).first()
# 	grower_details = GrowerProfile.objects.filter(user_id=grower_pk).first()
# 	map_area_name_master_list = MapAreaNameMaster.objects.all()
# 	map_area_master_details = MapAreaMaster.objects.filter(grower=grower_details).first()
# 	land_details = MapAreaLandDetails.objects.filter(grower=grower_details)

# 	if request.method == "POST":
# 		# Create or update MapAreaMaster
# 		if map_area_master_details:
# 			map_image = request.FILES.get('map_image')
# 			water_source = request.POST.get('water_source')
# 			land_near_by = request.POST.get('land_near_by')

# 			if map_image is not None:
# 				map_area_master_details.map_image = map_image
# 			if water_source is not None:
# 				map_area_master_details.water_source = water_source
# 			if land_near_by is not None:
# 				map_area_master_details.land_near_by = land_near_by

# 			map_area_master_details.updated_by = request.user
# 			map_area_master_details.save()

# 		# Save or update MapAreaLandDetails for each MapAreaNameMaster
# 		for item in map_area_name_master_list:
# 			total_areas = request.POST.get(f'total_areas_{item.pk}')
# 			print("total_areas ###", total_areas)
# 			if total_areas:
# 				# Check if MapAreaLandDetails already exists
# 				map_areas_land_details = MapAreaLandDetails.objects.filter(
# 					map_area_master=map_area_master_details,
# 					map_area_name=item
# 				).first()


# 				print("map_areas_land_details ##########", map_areas_land_details)

# 				if map_areas_land_details:
# 					# Update the existing MapAreaLandDetails instance
# 					map_areas_land_details.total_areas = total_areas
# 					map_areas_land_details.updated_by = request.user
# 					map_areas_land_details.save()

# 		messages.success(request, 'Map area details updated successfully')
# 		return HttpResponseRedirect(request.META.get("HTTP_REFERER"))

# 	else:
# 		form = MapAreaDetailsForm()

# 	map_area_url = 'total-land-under-agriculture'

# 	template_name = "farm_diary/farmers_mannual_map_edit.html"

# 	context = {
# 		"blf_details": blf_details,
# 		"grower_details": grower_details,
# 		"grower_pk": grower_pk,
# 		"form": form,
# 		"map_area_name_master_list": map_area_name_master_list,
# 		"map_area_master_details": map_area_master_details,
# 		"map_area_url": map_area_url,
# 		"land_details": land_details,
# 	}
# 	return CommonMixin.render(request, template_name, context)



# @login_required
# def farm_diary_manual_map_edit(request, grower_pk):
# 	blf_details = BlfProfile.objects.filter(user=request.user).first()
# 	grower_details = GrowerProfile.objects.filter(user_id=grower_pk).first()
# 	map_area_name_master_list = MapAreaNameMaster.objects.all()
# 	map_area_master_details = MapAreaMaster.objects.filter(grower=grower_details).first()
# 	land_details = MapAreaLandDetails.objects.filter(grower=grower_details)

# 	edit = request.POST.get('edit')

# 	if request.method == "POST":
# 		# Create or update MapAreaMaster
# 		if  map_area_master_details:
# 			map_area_master_details.map_image = request.POST['map_image']
# 			map_area_master_details.water_source = request.POST['water_source']
# 			map_area_master_details.land_near_by = request.POST['land_near_by']
# 			map_area_master_details.updated_by = request.user
# 			map_area_master_details.save()

# 		# Save or update MapAreaLandDetails for each MapAreaNameMaster
# 		for item in map_area_name_master_list:
# 			total_areas = request.POST.get(f'total_areas_{item.pk}')
# 			if total_areas:
# 				# Check if MapAreaLandDetails already exists
# 				map_areas_land_details = MapAreaLandDetails.objects.filter(
# 					map_area_master=map_area_master_details,
# 					map_area_name=item
# 				).first()

# 				# Update the existing MapAreaLandDetails instance
# 				map_areas_land_details.total_areas = total_areas
# 				map_areas_land_details.updated_by = request.user
# 				map_areas_land_details.save()

# 		messages.success(request, 'Map area details Updated successfully')
# 		return HttpResponseRedirect(request.META.get("HTTP_REFERER"))

# 	else:
# 		form = MapAreaDetailsForm()

# 	map_area_url = 'total-land-under-agriculuture'


# 	templates_name  = "farm_diary/farmers_mannual_map_edit.html"

# 	context = {
# 		"blf_details": blf_details,
# 		"grower_details": grower_details,
# 		"grower_pk": grower_pk,
# 		"form": form,
# 		"map_area_name_master_list": map_area_name_master_list,
# 		"map_area_master_details": map_area_master_details,
# 		"map_area_url": map_area_url,
# 		"land_details" : land_details,

# 	}
# 	return CommonMixin.render(request, templates_name, context)






import requests
from json.decoder import JSONDecodeError
from django.http import HttpResponse

import requests
from json.decoder import JSONDecodeError
from django.http import HttpResponse




def grower_map_area_details_total_api_view(request, grower_id, area_type):

	method = request.GET.get('method')
	if method:
		method = "edit"
	else:
		method = ""

	print("method ############################", method)
	
	map_area_name = MapAreaNameMaster.cmobjects.filter(slug__icontains=area_type).first()

	grower_details = GrowerProfile.cmobjects.filter(id=grower_id).first()

	check_land_details_list_count = MapAreaLandDetails.cmobjects.filter(
		grower=grower_details
	).count()

	check_details_data = MapAreaLandDetails.cmobjects.filter(
		grower=grower_details,
		map_area_name = map_area_name
	).first()

	print("map_area_name #########################", map_area_name)
	print("check_details_data", check_details_data)

	land_details_data_1 = MapAreaLandDetails.cmobjects.filter(
		map_area_name_id=1,
		grower=grower_details,
	).first()

	land_details_data_2 = MapAreaLandDetails.cmobjects.filter(
		map_area_name_id=2,
		grower=grower_details,
	).first()

	land_details_data_3 = MapAreaLandDetails.cmobjects.filter(
		map_area_name_id=3,
		grower=grower_details,
	).first()

	land_details_data_4 = MapAreaLandDetails.cmobjects.filter(
		map_area_name_id=4,
		grower=grower_details,
	).first()

	context = {
		"check_details_data": check_details_data,
		"grower_details" : grower_details,
		"land_details_data_1" : land_details_data_1,
		"land_details_data_2" : land_details_data_2,
		"land_details_data_3" : land_details_data_3,
		"land_details_data_4" : land_details_data_4,
		"check_land_details_list_count" : check_land_details_list_count,
		"method" : method,
	}

	return render(request, "farm_diary/grower_map_area_details_api_view.html", context)




def grower_map_area_details_api_view(request, grower_id, area_type):
	api_url = f'https://tracetea.org/api/grower/map-area-details-view/?grower_id={grower_id}&map_area={area_type}'

	try:
		response = requests.get(api_url)
		result = response.json()
		coordinates = []
		if result:
			coordinates = result['results'][area_type]['coordinate']
		
	except JSONDecodeError:
		return HttpResponse('Invalid JSON response from API')
	context = {
		"coordinates": coordinates,
	}

	return render(request, "farm_diary/grower_map_area_details_api_view.html", context)


################## Map data API View##########################################
class MapAreaNameMasterAPIView(APIView):
	"""Map Area Name Master list View"""
	authentication_classes = (TokenAuthentication,)
	permission_classes = (IsAuthenticated,)
	def get(self, request):
		id = self.request.query_params.get('id', None)
		all = self.request.query_params.get('all', None)
		order_by = self.request.query_params.get('order_by', '-id')
		search = {}
		search = custom_filters(self.request, search, [])
		if id:
			list_data = MapAreaNameMaster.cmobjects.filter(id=id).first()
			serializer = MapAreaNameMasterSerializer(list_data)
			return Response(serializer.data)
		list_data = MapAreaNameMaster.cmobjects.filter(*search).order_by(*str(order_by).split(",")).distinct()
		if all == 'true':
			serializer = MapAreaNameMasterSerializer(list_data, many=True)
			return Response({'results': serializer.data})
		page_size = int(request.query_params.get('page_size', settings.MIN_PAGE_SIZE))
		paginator = Paginator(list_data, page_size)
		page_number = self.request.query_params.get('page', 1)
		page = paginator.get_page(page_number)
		serializer = MapAreaNameMasterSerializer(page, many=True)
		return Response({
			'count': paginator.count,
			'next': page.next_page_number() if page.has_next() else None,
			'previous': page.previous_page_number() if page.has_previous() else None,
			'results': serializer.data,
		})
class GrowerMapAreaDetailsAPIView(APIView):
	def get(self, request, *args, **kwargs):
		try:
			map_area = self.request.query_params.get('map_area', None)
			id = self.request.query_params.get('id', None)
			user_id = self.request.query_params.get('user_id', None)
			grower_id = self.request.query_params.get('grower_id', None)
			map_area_details=None
			if map_area:
				map_area_details = MapAreaDetails.objects.filter(map_area_name__slug__icontains=map_area).order_by('-id')
			elif id:
				map_area_details = MapAreaDetails.objects.filter(id=id).order_by('-id')
			elif user_id:
				map_area_details = MapAreaDetails.objects.filter(created_by_id=user_id).order_by('-id')
			elif grower_id and map_area:
				map_area_details = MapAreaDetails.objects.filter(grower_id=grower_id, map_area_name__slug__icontains=map_area).order_by('-id')			
			else:
				map_area_details = MapAreaDetails.objects.all().order_by('-id')
			page_size = int(request.query_params.get('page_size', 10))
			paginator = Paginator(map_area_details, page_size)
			page_number = self.request.query_params.get('page', 1)
			page = paginator.get_page(page_number)
			serializer = MapAreaDetailsSerializer(page, many=True)
			data = self._format_response(serializer.data)
			return Response({
				'count': paginator.count,
				'next': page.next_page_number() if page.has_next() else None,
				'previous': page.previous_page_number() if page.has_previous() else None,
				'results': data,
			})
		except Exception as e:
			return Response({'status': status.HTTP_400_BAD_REQUEST, 'request_status': 0, 'msg': str(e)}, status=status.HTTP_400_BAD_REQUEST)
		
	def _format_response(self, data):
		formatted_data = {}
		all_slugs = MapAreaNameMaster.cmobjects.values_list('slug', 'name')
		existing_slugs = {item['map_area_name']['slug']: item for item in data}
		for slug, name in all_slugs:
			if slug in existing_slugs:
				formatted_data[slug] = existing_slugs[slug]
			else:
				formatted_data[slug] = None
		return formatted_data

from django.db.models import Prefetch
from django.db import transaction
from django.core.files.base import ContentFile
import base64

class MapAreaImageUploadAPIView(APIView):
	authentication_classes = (TokenAuthentication,)
	permission_classes = (IsAuthenticated,)


	def get(self, request, *args, **kwargs):
		try:
			grower_id = self.request.query_params.get('grower_id', None)
			if not grower_id:
				return Response({'error': 'grower_id is required'}, status=status.HTTP_400_BAD_REQUEST)

			# Fetch the MapAreaMaster objects with their related MapAreaLandDetails
			map_area_masters = MapAreaMaster.objects.filter(
				grower_id=grower_id
			).prefetch_related(
				Prefetch('map_area_land_details', queryset=MapAreaLandDetails.objects.filter(grower_id=grower_id))
			).order_by('-id')

			serializer = MapAreaMasterSerializer(map_area_masters, many=True)
			data = serializer.data

			# Format the response as per the example provided
			formatted_data = {
				'count': len(data),
				'results': data
			}
		
			return Response(formatted_data)
		except Exception as e:
			return Response({'status': status.HTTP_400_BAD_REQUEST, 'request_status': 0, 'msg': str(e)}, status=status.HTTP_400_BAD_REQUEST)


	def post(self, request, *args, **kwargs):

		print("UPDATE ** TOTAL AREA ##############")

		grower_id = request.data.get('grower_id')
		map_image_base64 = request.data.get('map_image')
		water_source = request.data.get('water_source')
		land_near_by = request.data.get('land_near_by')
		map_details = request.data.get('map_details', [])

		logged_user_details = Profile.objects.filter(user_id=request.user.id).first()
		logged_user_type = str(logged_user_details.user_type.name)
		aggregator_details, grower_details, blf_details = None, None, None
		
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
				map_area_master_details = MapAreaMaster.objects.filter(
					grower_id=grower_id
				).first()

				# mp_land_area_details = MapAreaLandDetails.cmobjects.filter(map_area_master=map_area_master_details).count()

				# print("mp_land_area_details====", mp_land_area_details)

				# print("EXIST ###", len(map_area_master_details))
				if map_area_master_details:
					map_area_master_details.water_source=water_source
					map_area_master_details.land_near_by = land_near_by
					map_area_master_details.map_image=map_image_file
					map_area_master_details.updated_by = request.user

					map_area_master_details.save()
				else:
					map_area_master_details = MapAreaMaster(
						grower=grower_details,
						water_source=water_source,
						land_near_by=land_near_by,
						map_image=map_image_file,
						is_image_upload=True,
						created_by=request.user
					)
					map_area_master_details.save()

			
				if aggregator_details:
						map_area_master_details.aggregator_id = aggregator_details.id
						map_area_master_details.save()

				for detail in map_details:
					map_area_id = detail.get('map_area_id')
					total_area = detail.get('total_area')
					
					map_area_name = MapAreaNameMaster.objects.filter(id=map_area_id).first()
					if not map_area_name:
						return Response({'msg': 'Map area name not found'}, status=status.HTTP_404_NOT_FOUND)

					map_area_details = MapAreaLandDetails.objects.filter(
						grower_id=grower_id,
						map_area_name=map_area_name
					).first()

					
					if map_area_details:
						map_area_details.grower=grower_details
						map_area_details.map_area_master_id=map_area_master_details.pk
						map_area_details.map_area_name=map_area_name
						map_area_details.total_areas = float(total_area)
						map_area_details.updated_by = request.user
						map_area_details.save()
					else:
						map_area_details = MapAreaLandDetails(
							grower=grower_details,
							map_area_master_id=map_area_master_details.pk,
							map_area_name=map_area_name,
							total_areas=float(total_area),
							created_by=request.user
						)
						map_area_details.save()

				# serializer = MapAreaDetailsSerializer(map_area_details)
				return Response({'results': {'Data': request.data}, 'msg': 'Map Area Details Created Successfully',
								'status': status.HTTP_201_CREATED, 'request_status': 1})
		except Exception as e:
			return Response({'status': status.HTTP_400_BAD_REQUEST, 'request_status': 0, 'msg': str(e)}, status=status.HTTP_400_BAD_REQUEST)

# DIGITAL MAP UPLOAD API VIEW
class MapAreaDetailsAPIView(APIView):
    """ Supply Management API View"""
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
            list_data = MapAreaMaster.cmobjects.filter(id=id).first()
            serializer = MapAreaMasterSerializer(list_data)
            return Response(serializer.data)
        list_data = MapAreaMaster.cmobjects.filter(*search).order_by(*str(order_by).split(","))
        if all == 'true':
            serializer = MapAreaMasterSerializer(list_data, many=True)
            return Response({'results': serializer.data})
        page_size = int(request.query_params.get('page_size', settings.MIN_PAGE_SIZE))
        paginator = Paginator(list_data, page_size)
        page_number = self.request.query_params.get('page', 1)
        page = paginator.get_page(page_number)
        serializer = MapAreaMasterSerializer(page, many=True)
        return Response({
            'count': paginator.count,
            'next': page.next_page_number() if page.has_next() else None,
            'previous': page.previous_page_number() if page.has_previous() else None,
            'results': serializer.data,
        })
    def post(self, request):
        request.data['created_by'] = request.user.id
        serializer = MapAreaMasterSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            # try:
            serializer.save()
            # except Exception as e:
            #     error_message = str(e.args[0]) if e.args else str(e)
            #     raise APIException({'request_status': 0, 'msg': error_message})
            return Response(
                {'results': {'Data': serializer.data,},
                    'msg': 'Successfully created',
                    'status': status.HTTP_201_CREATED,
                    "request_status": 1})
        raise APIException({'request_status': 0, 'msg': serializer.errors})
	
    def put(self, request):
        method = request.query_params.get('method')
        id = request.query_params.get('id')
        if not method:
            raise APIException({'request_status': 0, 'msg': "Method parameter is required"})
        if not id:
            raise APIException({'request_status': 0, 'msg': "ID parameter is required"})
        with transaction.atomic():
            if method.lower() == 'edit':
                _details = MapAreaMaster.cmobjects.filter(pk=id).first()
                if not _details:
                    raise APIException({'request_status': 0, 'msg': "Data not found"})
                serializer = MapAreaMasterSerializer(
                    _details, data=request.data, context={'request': request}
                )
                if serializer.is_valid():
                    try:
                        serializer.save()
                    except Exception as e:
                        error_message = str(e.args[0]) if e.args else str(e)
                        raise APIException({'request_status': 0, 'msg': error_message})
                    return Response({
                        'results': {'Data': serializer.data},
                        'msg': "Successfully updated",
                        'status': status.HTTP_202_ACCEPTED,
                        'request_status': 1
                    })
                else:
                    raise APIException({'request_status': 0, 'msg': serializer.errors})
            elif method.lower() == 'delete':
                supply = MapAreaMaster.cmobjects.filter(pk=id).first()
                if not supply:
                    raise APIException({'request_status': 0, 'msg': "Supply not found"})
                supply.is_deleted = True
                supply.updated_by_id = request.user.id
                supply.save()
                return Response({
                    'results': {'data': MapAreaMaster.cmobjects.filter(pk=id).values()},
                    'msg': 'Successfully deleted',
                    'request_status': 1
                })
            else:
                raise APIException({'request_status': 0, 'msg': "Invalid method parameter"})


############### Form aggreement API View###########################
class FarmersAggreementMasterAPIView(APIView):
	""" Farmers Agreement Master list View """
	authentication_classes = (TokenAuthentication,)
	permission_classes = (IsAuthenticated,)
	def get(self, request):
		id = self.request.query_params.get('id', None)
		all = self.request.query_params.get('all', None)
		order_by = self.request.query_params.get('order_by', '-id')
		search = custom_filters(self.request, {}, [])
		if id:
			list_data = FarmersAggreementMaster.cmobjects.filter(id=id).first()
			serializer = FarmersAggreementMasterSerializer(list_data)
			return Response(serializer.data)
		list_data = FarmersAggreementMaster.cmobjects.filter(*search).order_by(*str(order_by).split(","))
		if all == 'true':
			serializer = FarmersAggreementMasterSerializer(list_data, many=True)
			return Response({'results': serializer.data})
		page_size = int(request.query_params.get('page_size', settings.MIN_PAGE_SIZE))
		paginator = Paginator(list_data, page_size)
		page_number = self.request.query_params.get('page', 1)
		page = paginator.get_page(page_number)
		serializer = FarmersAggreementMasterSerializer(page, many=True)
		return Response({
			'count': paginator.count,
			'next': page.next_page_number() if page.has_next() else None,
			'previous': page.previous_page_number() if page.has_previous() else None,
			'results': serializer.data,
		})
class FarmersAggreementFormsAPIView(APIView):
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
			list_data = FarmersAggreementForms.cmobjects.filter(id=id).first()
			serializer = FarmersAggreementFormsSerializer(list_data)
			return Response(serializer.data)
		list_data = FarmersAggreementForms.cmobjects.filter(*search).order_by(*str(order_by).split(","))
		if all == 'true':
			serializer = FarmersAggreementFormsSerializer(list_data, many=True)
			return Response({'results': serializer.data})
		page_size = int(request.query_params.get('page_size', settings.MIN_PAGE_SIZE))
		paginator = Paginator(list_data, page_size)
		page_number = self.request.query_params.get('page', 1)
		page = paginator.get_page(page_number)
		serializer = FarmersAggreementFormsSerializer(page, many=True)
		return Response({
			'count': paginator.count,
			'next': page.next_page_number() if page.has_next() else None,
			'previous': page.previous_page_number() if page.has_previous() else None,
			'results': serializer.data,
		})
	
	def post(self, request, *args, **kwargs):
		try:
			agreement_form_details = None
			data = request.data
			grower_id = data.get('grower', None)
			aggreement_form_title_id = data.get('aggreement_form_title', None)
			date = data.get('date', None)
			place = data.get('place', None)
			
			with transaction.atomic():
				blf_details = BlfProfile.cmobjects.filter(user=request.user).first()
				aggregator_details = AggregatorProfile.cmobjects.filter(user=request.user).first()
				agreement_form_details = FarmersAggreementForms.cmobjects.filter(
                    grower_id=grower_id
                ).first()
				if agreement_form_details:
					agreement_form_details.updated_by = request.user
				else:
					agreement_form_details = FarmersAggreementForms.cmobjects.create(
						grower_id=grower_id,
						created_by=request.user
					)
				if agreement_form_details:
					if blf_details:
						agreement_form_details.blf_id = blf_details.id
					if aggregator_details:
						agreement_form_details.aggregator_id = aggregator_details.id    
					if date:
						agreement_form_details.date = date
					if place:
						agreement_form_details.place = place  
				
				serializer = FarmersAggreementFormsSerializer(agreement_form_details, data=data, partial=True, context={'request': request})
				if serializer.is_valid():
					serializer.save()
					return Response({'results': {'Data': serializer.data}, 'msg': 'Farmers Agreement Form Created Successfully', 'status': status.HTTP_201_CREATED, "request_status": 1})
				else:
					return Response({'msg': serializer.errors, 'status': status.HTTP_400_BAD_REQUEST, "request_status": 0})
		except Exception as e:
			return Response({'status': status.HTTP_400_BAD_REQUEST, 'request_status': 0, 'msg': str(e)}, status=status.HTTP_400_BAD_REQUEST)


	def put(self, request, *args, **kwargs):
		try:
			method = self.request.query_params.get('method', None)
			id = self.request.query_params.get('id', None)
			if not method or not id:
				return Response({'msg': 'Method and ID parameters are required'}, status=status.HTTP_400_BAD_REQUEST)

			agreement_form = FarmersAggreementForms.cmobjects.filter(pk=id).first()
			if not agreement_form:
				return Response({'msg': 'Farmers Agreement Form not found'}, status=status.HTTP_404_NOT_FOUND)

			if method.lower() == 'edit':
				serializer = FarmersAggreementFormsSerializer(agreement_form, data=request.data, partial=True, context={'request': request})
				if serializer.is_valid():
					serializer.save(updated_by=request.user)
					return Response({'results': {'Data': serializer.data}, 'msg': 'Farmers Agreement Form Updated Successfully', 'status': status.HTTP_200_OK, "request_status": 1})
				else:
					return Response({'msg': serializer.errors, 'status': status.HTTP_400_BAD_REQUEST, "request_status": 0})

			elif method.lower() == 'delete':
				agreement_form.is_deleted = True
				agreement_form.save()
				return Response({'results': {'Data': FarmersAggreementForms.objects.filter(pk=id).values()}, 'msg': 'Selected Farmers Agreement Form Deleted Successfully', "request_status": 1, 'status': status.HTTP_200_OK})

			return Response({'msg': 'Invalid method parameter'}, status=status.HTTP_400_BAD_REQUEST)
		
		except Exception as e:
			return Response({'status': status.HTTP_400_BAD_REQUEST, 'request_status': 0, 'msg': str(e)}, status=status.HTTP_400_BAD_REQUEST)
		
		











################## END ###############################################################



# MAP CREATE
@login_required
def farm_diary_map_create(request, grower_pk):
	grower_details = GrowerProfile.objects.filter(user_id=grower_pk).first()
	map_area_master_details = MapAreaMaster.cmobjects.filter(grower=grower_details).first()



	map_area_master_details = MapAreaMaster.cmobjects.filter(grower=grower_details).first()
	map_land_area_list = MapAreaLandDetails.cmobjects.filter(
		grower=grower_details
	)
	check_details_data = MapAreaLandDetails.cmobjects.filter(
		grower=grower_details
	).first()

	# print("check_details_data Length #########", map_land_area_list_count)
	land_details_data_1 = MapAreaLandDetails.cmobjects.filter(
		map_area_name_id=1,
		grower=grower_details,
	).first()

	land_details_data_2 = MapAreaLandDetails.cmobjects.filter(
		map_area_name_id=2,
		grower=grower_details,
	).first()

	land_details_data_3 = MapAreaLandDetails.cmobjects.filter(
		map_area_name_id=3,
		grower=grower_details,
	).first()

	land_details_data_4 = MapAreaLandDetails.cmobjects.filter(
		map_area_name_id=4,
		grower=grower_details,
	).first()

	context = {
		"grower_pk" : grower_pk,
		"map_area_master_details" : map_area_master_details,
		"grower_details" : grower_details,
		"land_details_data_1" : land_details_data_1,
		"land_details_data_2" : land_details_data_2,
		"land_details_data_3" : land_details_data_3,
		"land_details_data_4" : land_details_data_4,

	}

	return CommonMixin.render(request, "farm_diary/farm_diary_map_create.html", context)





import base64
from django.core.files.base import ContentFile
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import MapAreaMaster



class SaveMapImageAPI(APIView):
	authentication_classes = (TokenAuthentication,)
	permission_classes = (IsAuthenticated,)

	def post(self, request, *args, **kwargs):
		grower_id = request.data.get('grower_id')
		map_image_base64 = request.data.get('map_image')

		logged_user_details = Profile.objects.filter(user_id=request.user.id).first()
		logged_user_type = str(logged_user_details.user_type.name)
		aggregator_details, grower_details, blf_details = None, None, None

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
				map_area_master_details = MapAreaMaster.objects.filter(
					grower_id=grower_id
				).first()

				# print("EXIST ###", len(map_area_master_details))
				if map_area_master_details:
					map_area_master_details.map_image=map_image_file
					map_area_master_details.updated_by = request.user
					map_area_master_details.save()

				if aggregator_details:
						map_area_master_details.aggregator_id = aggregator_details.id
						map_area_master_details.save()

				# serializer = MapAreaDetailsSerializer(map_area_details)
				return Response({'results': {'Data': request.data}, 'msg': 'Map Area Details Created Successfully',
								'status': status.HTTP_201_CREATED, 'request_status': 1})
		except Exception as e:
			return Response({'status': status.HTTP_400_BAD_REQUEST, 'request_status': 0, 'msg': str(e)}, status=status.HTTP_400_BAD_REQUEST)






@csrf_exempt
def save_image(request, grower_id):

	type = request.GET.get('type', None)

	if type:
		grower_details = GrowerProfile.cmobjects.filter(id=grower_id).first()
	else:
		grower_details = GrowerProfile.cmobjects.filter(user_id=grower_id).first()

	if not grower_details:
		return JsonResponse({'status': 'failed', 'message': 'Grower not found'}, status=404)

	if request.method == 'POST':
		image_data = request.POST.get('image')
		if not image_data:
			return JsonResponse({'status': 'failed', 'message': 'No image data provided'}, status=400)

		try:
			format, imgstr = image_data.split(';base64,') 
			ext = format.split('/')[-1] 
			image_data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

			map_area_master_details = MapAreaMaster.cmobjects.filter(grower=grower_details).first()
			if not map_area_master_details:
				return JsonResponse({'status': 'failed', 'message': 'MapAreaMaster not found'}, status=404)

			map_area_master_details.map_image = image_data
			# map_area_master_details.pdf_map_image = image_data
			map_area_master_details.save()

			return JsonResponse({'status': 'success'})
		except Exception as e:
			return JsonResponse({'status': 'failed', 'message': str(e)}, status=400)

	return JsonResponse({'status': 'failed', 'message': 'Invalid request method'}, status=400)






from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.http import HttpResponse
import pdfkit		
from django.template.loader import render_to_string, get_template
from xhtml2pdf import pisa
from knox.auth import TokenAuthentication
from rest_framework import permissions
from knox.models import AuthToken
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, IsAuthenticatedOrReadOnly, AllowAny
from django.core.paginator import Paginator
from knox.auth import TokenAuthentication
from django.db import transaction
from rest_framework import status
from rest_framework.exceptions import APIException
from .serializers import *

from io import BytesIO
from PyPDF2 import PdfFileReader, PdfMerger
from PyPDF2 import PdfReader

# from pdfkit.exceptions import ConfigurationError



# def stg_farm_diary_pdf_generate(request, grower_id):
#     date_from = request.GET.get('date_from', None)
#     date_to = request.GET.get('date_to', None)
#     blf_id = request.user.id
#     blf_details = BlfProfile.cmobjects.filter(user_id=blf_id).first()
#     grower_details = GrowerProfile.cmobjects.filter(user_id=grower_id).first()

#     map_area_details = MapAreaMaster.cmobjects.filter(grower=grower_details).first()
#     map_area_land_details = MapAreaLandDetails.cmobjects.filter(grower=grower_details)

#     if map_area_land_details:
#         land_details_data_1 = MapAreaLandDetails.cmobjects.filter(
#             map_area_name_id=1,
#             grower=grower_details,
#         ).first()

#         land_details_data_2 = MapAreaLandDetails.cmobjects.filter(
#             map_area_name_id=2,
#             grower=grower_details,
#         ).first()

#         land_details_data_3 = MapAreaLandDetails.cmobjects.filter(
#             map_area_name_id=3,
#             grower=grower_details,
#         ).first()

#         land_details_data_4 = MapAreaLandDetails.cmobjects.filter(
#             map_area_name_id=4,
#             grower=grower_details,
#         ).first()
#     else:
#         land_details_data_1 = ""
#         land_details_data_2 = ""
#         land_details_data_3 = ""
#         land_details_data_4 = ""

#     if map_area_details and map_area_details.pdf_map_image:
#         map_image = map_area_details.pdf_map_image
#         map_image = f"https://tracetea.org/media/{map_image}"
#     else:
#         map_image = "https://placehold.co/800x400"

#     if not grower_details:
#         return Response({'status': 'Data not found', 'request_status': 0}, status=404)

#     form_details = FarmersAggreementForms.cmobjects.filter(
#         grower=grower_details
#     ).first()

#     if form_details:
#         stg_signature = f"https://tracetea.org/media/{form_details.farmer_signature_file}"
#     else:
#         stg_signature = ""

#     garden_details = Gardens.cmobjects.filter(grower=grower_details).first()
#     print("Garden", garden_details.grower)
#     if grower_details:
#         grower_username = grower_details.user.username
#     else:
#         grower_username = ""
#     if garden_details:
#         production_area = garden_details.production_area
#     else:
#         production_area = "NA"

#     monthly_shedule_list = MonthlySchedule.cmobjects.filter(grower_id=grower_details.id).order_by('-year')

#     labour_list = Labour.cmobjects.filter(
#         Q(grower_id=grower_details.id)).order_by('-id')

#     associated_entity = grower_details.associated_entity.first()
#     if associated_entity:
#         associated_entity_user = associated_entity.user if associated_entity else None
#     else:
#         associated_entity_user = None

#     grower_blf_details = BlfProfile.cmobjects.filter(user=associated_entity_user).first()

#     if blf_details:
#         blf_signature_details = BlfofficialSignature.cmobjects.filter(blf=grower_blf_details).first()
#     else:
#         blf_signature_details = None

#     if blf_signature_details:
#         blf_signature = f"https://tracetea.org/media/{blf_signature_details.blf_grade_official_signature_file}"
#     else:
#         blf_signature = ""

#     if grower_details and date_from and date_to:
#         date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
#         date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')

#         year_from = date_from_obj.year
#         year_to = date_to_obj.year

#         use_of_fertilizer_list = UseOfChemical.cmobjects.filter(
#             grower_id=grower_id, chemical__chemical_type__name__iexact="Fertilizer",
#             date__range=[date_from, date_to]
#         ).order_by('-id')
#         use_of_herbicides_list = UseOfChemical.cmobjects.filter(
#             grower_id=grower_id, chemical__chemical_type__name__iexact="Herbicides",
#             date__range=[date_from, date_to]
#         ).order_by('-id')
#         use_of_acaricides_list = UseOfChemical.cmobjects.filter(
#             grower_id=grower_id, chemical__chemical_type__name__iexact="Acaricides",
#             date__range=[date_from, date_to]
#         ).order_by('-id')
#         use_of_insecticides_list = UseOfChemical.cmobjects.filter(
#             grower_id=grower_id, chemical__chemical_type__name__iexact="Insecticides & Fungicides",
#             date__range=[date_from, date_to]
#         ).order_by('-id')

#         plucking_data_list = PluckingData.cmobjects.filter(
#             grower_id=grower_id,
#             date__range=[date_from, date_to]
#         ).order_by('-id')

#     else:
#         plucking_data_list = PluckingData.cmobjects.filter(
#             Q(grower_id=grower_details.id)).order_by('-date')

#         use_of_fertilizer_list = UseOfChemical.cmobjects.filter(
#             Q(grower_id=grower_details.id),
#             Q(chemical__chemical_type_id=1)).order_by('-date')

#         use_of_herbicides_list = UseOfChemical.cmobjects.filter(
#             Q(grower_id=grower_details.id),
#             Q(chemical__chemical_type_id=2)).order_by('-date')

#         use_of_insecticides_list = UseOfChemical.cmobjects.filter(
#             Q(grower_id=grower_details.id),
#             Q(chemical__chemical_type_id=3)).order_by('-date')

#         use_of_acaricides_list = UseOfChemical.cmobjects.filter(
#             Q(grower_id=grower_details.id),
#             Q(chemical__chemical_type_id=5)).order_by('-date')

#     context = {
#         'grower_details': grower_details,
#         'grower_pk': grower_details.pk,
#         'grower_details': grower_details,
#         'labour_list': labour_list,
#         'plucking_data_list': plucking_data_list,
#         "fertilizer_chemical_list": use_of_fertilizer_list,
#         "herbicides_chemical_list": use_of_herbicides_list,
#         "insecticides_chemical_list": use_of_insecticides_list,
#         "acaricides_chemical_list": use_of_acaricides_list,
#         "schedule_list": monthly_shedule_list,
#         "blf_details": blf_details,
#         "production_area": production_area,
#         "garden_details": garden_details,
#         "grower_username": grower_username,
#         "form_details": form_details,
#         "blf_signature": blf_signature,
#         "stg_signature": stg_signature,
#         "map_area_details": map_area_details,
#         "map_image": map_image,
#         "land_details_data_1": land_details_data_1,
#         "land_details_data_2": land_details_data_2,
#         "land_details_data_3": land_details_data_3,
#         "land_details_data_4": land_details_data_4,
#     }

#     html_templates = [
#         'farm_diary/pdf/1.html',
#         'farm_diary/pdf/2.html',
#         'farm_diary/pdf/3.html',
#         'farm_diary/pdf/4.html',
#         'farm_diary/pdf/5.html',
#         'farm_diary/pdf/6.html',
#         'farm_diary/pdf/7.html',
#         'farm_diary/pdf/8.html',
#         'farm_diary/pdf/9.html',
#         'farm_diary/pdf/10.html',
#         'farm_diary/pdf/11.html',
#         'farm_diary/pdf/12.html',
#         'farm_diary/pdf/13.html',
#         'farm_diary/pdf/14.html'
#     ]

#     # Configure pdfkit options
#     options = {
#         'page-size': 'letter',
#         'margin-top': '0.75in',
#         'margin-right': '0.75in',
#         'margin-bottom': '0.75in',
#         'margin-left': '0.75in',
#     }

#     # Set the path to the wkhtmltopdf executable
#     path_wkhtmltopdf = '/usr/bin/wkhtmltopdf'

#     # Convert HTML templates to PDF
#     pdfs = []
#     total_pages = 0
#     page_counts = []

#     # Render each HTML template to count pages and generate PDFs
#     for html_template in html_templates:
#         context['current_page'] = 1  # Initialize current page number for each template
#         html = render_to_string(html_template, context)
#         pdf = pdfkit.from_string(html, False, options=options, configuration=pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf))

#         # Count the number of pages
#         pdf_reader = PdfReader(BytesIO(pdf))
#         num_pages = len(pdf_reader.pages)
#         page_counts.append(num_pages)
#         total_pages += num_pages

#     # Add additional pages for labour_list rows beyond the first 20 rows
#     chunk_size = 20
#     labour_rows = labour_list.count()
#     labour_chunks = [labour_list[i:i + chunk_size] for i in range(0, labour_rows, chunk_size)]
    
#     for chunk in labour_chunks:
#         context['labour_list'] = chunk
#         html = render_to_string('farm_diary/pdf/3.html', context)
#         pdf = pdfkit.from_string(html, False, options=options, configuration=pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf))

#         # Count the number of pages
#         pdf_reader = PdfReader(BytesIO(pdf))
#         num_pages = len(pdf_reader.pages)
#         page_counts.append(num_pages)
#         total_pages += num_pages

#     current_page = 1

#     for index, html_template in enumerate(html_templates):
#         context['total_pages'] = total_pages
#         num_pages = page_counts[index]

#         for page_number in range(1, num_pages + 1):
#             context['current_page'] = current_page
#             html = render_to_string(html_template, context)
#             pdf = pdfkit.from_string(html, False, options=options, configuration=pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf))
#             pdfs.append(BytesIO(pdf))
#             current_page += 1

#     # Add additional pages for labour_list rows beyond the first 20 rows
#     for chunk in labour_chunks:
#         context['total_pages'] = total_pages
#         context['labour_list'] = chunk
#         num_pages = len(chunk) // chunk_size + 1  # Calculate number of pages for this chunk

#         for page_number in range(1, num_pages + 1):
#             context['current_page'] = current_page
#             html = render_to_string('farm_diary/pdf/3.html', context)
#             pdf = pdfkit.from_string(html, False, options=options, configuration=pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf))
#             pdfs.append(BytesIO(pdf))
#             current_page += 1

#     # Merge PDF files into a single file
#     merger = PdfMerger()
#     for pdf in pdfs:
#         merger.append(PdfReader(pdf))

#     merged_pdf = BytesIO()
#     merger.write(merged_pdf)

#     # Create a response object with the PDF file as content
#     response = HttpResponse(merged_pdf.getvalue(), content_type='application/pdf')
#     response['Content-Disposition'] = f'attachment; filename="consolidated-farm-diary.pdf"'

#     return response



def stg_farm_diary_pdf_generate(request, grower_id):
    date_from = request.GET.get('date_from', None)
    date_to = request.GET.get('date_to', None)
    blf_id = request.user.id
    blf_details = BlfProfile.cmobjects.filter(user_id=blf_id).first()
    grower_details = GrowerProfile.cmobjects.filter(user_id=grower_id).first()

    map_area_details = MapAreaMaster.cmobjects.filter(grower=grower_details).first()
    map_area_land_details = MapAreaLandDetails.cmobjects.filter(grower=grower_details)

    if map_area_land_details:
        land_details_data_1 = MapAreaLandDetails.cmobjects.filter(
            map_area_name_id=1,
            grower=grower_details,
        ).first()

        land_details_data_2 = MapAreaLandDetails.cmobjects.filter(
            map_area_name_id=2,
            grower=grower_details,
        ).first()

        land_details_data_3 = MapAreaLandDetails.cmobjects.filter(
            map_area_name_id=3,
            grower=grower_details,
        ).first()

        land_details_data_4 = MapAreaLandDetails.cmobjects.filter(
            map_area_name_id=4,
            grower=grower_details,
        ).first()
    else:
        land_details_data_1 = ""
        land_details_data_2 = ""
        land_details_data_3 = ""
        land_details_data_4 = ""

    if map_area_details and map_area_details.pdf_map_image:
        map_image = map_area_details.pdf_map_image
        map_image = f"https://tracetea.org/media/{map_image}"
    else:
        map_image = "https://placehold.co/800x400"

    if not grower_details:
        return Response({'status': 'Data not found', 'request_status': 0}, status=404)

    form_details = FarmersAggreementForms.cmobjects.filter(
        grower=grower_details
    ).first()

    if form_details:
        stg_signature = f"https://tracetea.org/media/{form_details.farmer_signature_file}"
    else:
        stg_signature = ""

    garden_details = Gardens.cmobjects.filter(grower=grower_details).first()
    print("Garden", garden_details.grower)
    if grower_details:
        grower_username = grower_details.user.username
    else:
        grower_username = ""
    if garden_details:
        production_area = garden_details.production_area
    else:
        production_area = "NA"

    monthly_shedule_list = MonthlySchedule.cmobjects.filter(grower_id=grower_details.id).order_by('-year')

    labour_list = Labour.cmobjects.filter(
        Q(grower_id=grower_details.id)).order_by('-id')

    # associated_entities = grower_details.associated_entity.all()
    associated_entity = grower_details.associated_entity.first()
    if associated_entity:
        associated_entity_user = associated_entity.user if associated_entity else None
        # associated_entity_names = [entity.user for entity in associated_entities]
    else:
        associated_entity_user = None

    grower_blf_details = BlfProfile.cmobjects.filter(user=associated_entity_user).first()

    # print("grower_blf_details ###", grower_blf_details)

    if blf_details:
        blf_signature_details = BlfofficialSignature.cmobjects.filter(blf=grower_blf_details).first()
    else:
        blf_signature_details = None

    if blf_signature_details:
        blf_signature = f"https://tracetea.org/media/{blf_signature_details.blf_grade_official_signature_file}"
    else:
        blf_signature = ""

    if grower_details and date_from and date_to:
        date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
        date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')

        year_from = date_from_obj.year
        year_to = date_to_obj.year

        use_of_fertilizer_list = UseOfChemical.cmobjects.filter(
            grower_id=grower_details.id, chemical__chemical_type__name__iexact="Fertilizer",
            date__range=[date_from, date_to]
        ).order_by('-id')
        use_of_herbicides_list = UseOfChemical.cmobjects.filter(
            grower_id=grower_details.id, chemical__chemical_type__name__iexact="Herbicides",
            date__range=[date_from, date_to]
        ).order_by('-id')
        use_of_acaricides_list = UseOfChemical.cmobjects.filter(
            grower_id=grower_details.id, chemical__chemical_type__name__iexact="Acaricides",
            date__range=[date_from, date_to]
        ).order_by('-id')
        use_of_insecticides_list = UseOfChemical.cmobjects.filter(
            grower_id=grower_details.id, chemical__chemical_type__name__iexact="Insecticides & Fungicides",
            date__range=[date_from, date_to]
        ).order_by('-id')

        plucking_data_list = PluckingData.cmobjects.filter(
            grower_id=grower_details.id,
            date__range=[date_from, date_to]
        ).order_by('-id')

        monthly_shedule_list = MonthlySchedule.cmobjects.filter(
            grower_id=grower_details.id,
            created_at__date__range=[date_from, date_to]
        ).order_by('-year')

        labour_list = Labour.cmobjects.filter(
            grower_id=grower_details.id,
            created_at__date__range=[date_from, date_to]
        ).order_by('-id')

    else:
        plucking_data_list = PluckingData.cmobjects.filter(
            Q(grower_id=grower_details.id)).order_by('-date')

        use_of_fertilizer_list = UseOfChemical.cmobjects.filter(
            Q(grower_id=grower_details.id),
            Q(chemical__chemical_type_id=1)).order_by('-date')

        use_of_herbicides_list = UseOfChemical.cmobjects.filter(
            Q(grower_id=grower_details.id),
            Q(chemical__chemical_type_id=2)).order_by('-date')

        use_of_insecticides_list = UseOfChemical.cmobjects.filter(
            Q(grower_id=grower_details.id),
            Q(chemical__chemical_type_id=3)).order_by('-date')

        use_of_acaricides_list = UseOfChemical.cmobjects.filter(
            Q(grower_id=grower_details.id),
            Q(chemical__chemical_type_id=5)).order_by('-date')

    context = {
        'grower_details': grower_details,
        'grower_pk': grower_details.pk,
        'grower_details': grower_details,
        'labour_list': labour_list,
        'plucking_data_list': plucking_data_list,
        "fertilizer_chemical_list": use_of_fertilizer_list,
        "herbicides_chemical_list": use_of_herbicides_list,
        "insecticides_chemical_list": use_of_insecticides_list,
        "acaricides_chemical_list": use_of_acaricides_list,
        "schedule_list": monthly_shedule_list,
        "blf_details": blf_details,
        "production_area": production_area,
        "garden_details": garden_details,
        "grower_username": grower_username,
        "form_details": form_details,
        "blf_signature": blf_signature,
        "stg_signature": stg_signature,
        "map_area_details": map_area_details,
        "map_image": map_image,
        "land_details_data_1": land_details_data_1,
        "land_details_data_2": land_details_data_2,
        "land_details_data_3": land_details_data_3,
        "land_details_data_4": land_details_data_4,
    }

    html_templates = [
        'farm_diary/pdf/1.html',
        'farm_diary/pdf/2.html',
		'farm_diary/pdf/3.html',
        'farm_diary/pdf/4.html',
        'farm_diary/pdf/5.html',
        'farm_diary/pdf/6.html',
        'farm_diary/pdf/7.html',
        'farm_diary/pdf/8.html',
        'farm_diary/pdf/9.html',
        'farm_diary/pdf/10.html',
        'farm_diary/pdf/11.html',
        'farm_diary/pdf/12.html',
        'farm_diary/pdf/13.html',
        'farm_diary/pdf/14.html'
    ]

    # Configure pdfkit options
    options = {
        'page-size': 'letter',
        'margin-top': '0.75in',
        'margin-right': '0.75in',
        'margin-bottom': '0.75in',
        'margin-left': '0.75in',
    }

    # Set the path to the wkhtmltopdf executable
    path_wkhtmltopdf = '/usr/bin/wkhtmltopdf'

    # Convert HTML templates to PDF
    pdfs = []
    total_pages = 0
    page_counts = []

    # Render each HTML template to count pages and generate PDFs
    for html_template in html_templates:
        html = render_to_string(html_template, context)
        pdf = pdfkit.from_string(html, False, options=options, configuration=pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf))

        # Count the number of pages
        pdf_reader = PdfReader(BytesIO(pdf))
        num_pages = len(pdf_reader.pages)
        page_counts.append(num_pages)
        total_pages += num_pages

    current_page = 1

    for index, html_template in enumerate(html_templates):
        context['total_pages'] = total_pages
        num_pages = page_counts[index]

        for page_number in range(1, num_pages + 1):
            context['current_page'] = current_page
            html = render_to_string(html_template, context)
            pdf = pdfkit.from_string(html, False, options=options, configuration=pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf))
            pdfs.append(BytesIO(pdf))
            current_page += 1

    # Merge PDF files into a single file
    merger = PdfMerger()
    for pdf in pdfs:
        merger.append(PdfReader(pdf))

    merged_pdf = BytesIO()
    merger.write(merged_pdf)

    # Create a response object with the PDF file as content
    response = HttpResponse(merged_pdf.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="consolidated-farm-diary.pdf"'

    return response


class GenerateFarmDiaryPdfAPIView(APIView):
	authentication_classes = (TokenAuthentication,)
	permission_classes = (IsAuthenticated,)
	def get(self, request):
		date_from = request.GET.get("date_from")
		date_to = request.GET.get("date_to")
		grower_id = request.GET.get("grower_id")

		if not (date_from and date_to):
			raise APIException({'request_status': 0, 'msg': "date_from and date_to are mandatory"})
		
		grower_details = GrowerProfile.cmobjects.filter(id=grower_id).annotate(
				grower_garden_name=F('gardens_grower__name'),
				grower_production_area=F('gardens_grower__production_area'),).values('grower_type','user__username','name',
						'mobile_number','address','grower_garden_name','grower_production_area',).first()
		
		if not grower_details:
			raise APIException({'request_status': 0, 'msg': "Invalid grower_id"})

		date_range = [date_from, date_to]
		search = {'grower_id': grower_id, "date__range": date_range}

		map_details = MapAreaLandDetails.cmobjects.select_related('map_area_master').filter(grower_id=grower_id, map_area_name_id=1).values(
			'map_area_master__map_image', 'map_area_master__pdf_map_image', 'total_areas', 'map_area_name__name').first()

		trust_tea_copy_form_details = FarmersAggreementForms.cmobjects.select_related('aggreement_form_title').filter(grower_id=grower_id, aggreement_form_title__slug="trust-tea-copy").values('aggreement_form_title__name', 
				'farmer_signature_file','blf_grade_official_signature_file').first()
		
		sellers_copy_form_details = FarmersAggreementForms.cmobjects.select_related('aggreement_form_title').filter(grower_id=grower_id, aggreement_form_title__slug="sellers-copy").values('aggreement_form_title__name', 
				'farmer_signature_file','blf_grade_official_signature_file').first()

		factory_copyform_details = FarmersAggreementForms.cmobjects.select_related('aggreement_form_title').filter(grower_id=grower_id, aggreement_form_title__slug="factory-copy").values('aggreement_form_title__name', 
				'farmer_signature_file','blf_grade_official_signature_file').first()

		monthly_schedule_list = list(
			MonthlySchedule.cmobjects.filter(grower_id=grower_id, created_at__date__range=date_range)
			.annotate(
				days=F('monthly_schedule_hour_details__days'),
				hour=F('monthly_schedule_hour_details__hour')
			)
			.values('year', 'month', 'no_of_working_days', 'total_hours',
					'hourly_rate', 'monthly_wages', 'days', 'hour')
			.order_by('-year')
		)
		labour_list = list(Labour.cmobjects.filter(grower_id=grower_id, created_at__date__range=date_range).values('name',
				'type', 'gender', 'age').order_by("-id"))
		
		# BLF signature
		# associated_entity_user = getattr(grower_details.associated_entity.first(), "user", None)
		# grower_blf_details = BlfProfile.cmobjects.filter(user=associated_entity_user).first()
		# blf_signature_details = (
		#     BlfofficialSignature.cmobjects.filter(blf=grower_blf_details).first()
		#     if grower_blf_details else None
		# ) 
		# blf_signature = (
		#     f"{os.getenv('BASE_URL', '')}/media/{blf_signature_details.blf_grade_official_signature_file}"
		#     if blf_signature_details else ""
		# )
		
		# Chemicals
		fertilizer_list = list(
			UseOfChemical.cmobjects.filter(**search, chemical__chemical_type__name__iexact="Fertilizer").
			values('date','chemical__chemical_name', 
				'labour__name', 'quantity', 'unit', 'plot__name', 'division__name', 'dose').order_by("-id")
		)
		other_chemicals_list = list(
			UseOfChemical.cmobjects.filter(**search)
			.exclude(chemical__chemical_type__name__iexact="Fertilizer").values('date','chemical__chemical_name', 
				'labour__name', 'quantity', 'unit', 'plot__name', 'division__name', 'dose').order_by("-id")
		)
		plucking_data_list = list(PluckingData.cmobjects.annotate(
			labours__names=GroupConcat(F('labours__name'),distinct=True),).filter(**search).values('date', 'start_time',
				'end_time','labours__names', 'division__name', 'plot__name', 'area_plucked', 'quantity_plucked', 'plucking_time').order_by("-id"))

		# Collect all relevant datasets into a single list
		data = [
			{"monthly_schedule_list": monthly_schedule_list},
			{"labour_list": labour_list},
			{"plucking_data_list": plucking_data_list},
			{"fertilizer_chemical_list": fertilizer_list},
			{"other_chemicals_list": other_chemicals_list},
		]
		# Build context
		context = {
			"base_url": f"{os.getenv('BASE_URL', '')}media/",
			"grower_details": grower_details,
			"grower_pk": grower_id,
			"labour_list": labour_list,
			"monthly_schedule_list": monthly_schedule_list,
			"trust_tea_copy_form_details": trust_tea_copy_form_details,
			"sellers_copy_form_details": sellers_copy_form_details,
			"factory_copy_form_details": factory_copyform_details,
			"map_details": map_details,
			"plucking_data_list": plucking_data_list,
			"fertilizer_chemical_list": fertilizer_list,
			"other_chemicals_list": other_chemicals_list
		}
		data = [item for item in data if any(item.values())]
		if not data:
			raise APIException({'request_status': 0, 'msg': "No data available for the given Date range"})
		
		# html_templates = [f"farm_diary/pdf/{i}.html" for i in range(1, 15)]
		html_templates = [
			'farm_diary/pdf/1.html',
			'farm_diary/pdf/2.html',
			'farm_diary/pdf/3.html',
			'farm_diary/pdf/4.html',
			'farm_diary/pdf/5.html',
			'farm_diary/pdf/6.html',
			'farm_diary/pdf/7.html',
			# 'farm_diary/pdf/8.html',
			# 'farm_diary/pdf/9.html',
			'farm_diary/pdf/10.html',
			'farm_diary/pdf/11.html',
			'farm_diary/pdf/12.html',
			'farm_diary/pdf/13.html',
			'farm_diary/pdf/14.html'
		]
		options = {
			"enable-local-file-access": "",
			"page-size": "Letter",
			"margin-top": "0.75in",
			"margin-right": "0.75in",
			"margin-bottom": "0.75in",
			"margin-left": "0.75in",
		}
		path_wkhtmltopdf = os.getenv("WKHTMLTOPDF_PATH", "")
		config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)
		# Count pages
		page_counts, total_pages = [], 0
		for template in html_templates:
			html = render_to_string(template, {**context, "current_page": 1})
			pdf = pdfkit.from_string(html, False, options=options, configuration=config)
			num_pages = len(PdfReader(BytesIO(pdf)).pages)
			page_counts.append(num_pages)
			total_pages += num_pages

		# Merge PDFs with correct page numbers
		merger, current_page = PdfMerger(), 1
		for index, template in enumerate(html_templates):
			for page_number in range(1, page_counts[index] + 1):
				html = render_to_string(template, {**context,
													"total_pages": total_pages,
													"current_page": current_page})
				pdf = pdfkit.from_string(html, False, options=options,
											configuration=pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf))
				merger.append(PdfReader(BytesIO(pdf)))
				current_page += 1

		merged_pdf = BytesIO()
		merger.write(merged_pdf)
		filename = f"consolidated-farm-diary_{date_from}_to_{date_to}_{uuid.uuid4().hex}.pdf"
		fs = FileSystemStorage(location=settings.MEDIA_ROOT)
		file_path = fs.save(filename, ContentFile(merged_pdf.getvalue()))
		file_url = request.build_absolute_uri(fs.url(file_path))

		return Response({
			"request_status": 1,
			"msg": "PDF generated successfully",
			"file_url": file_url,
			"context" : context,
		})


def stg_farm_diary_pdf_generate_app2(request):
	date_from = request.GET.get('date_from', None)
	date_to = request.GET.get('date_to', None)
	grower_id = request.GET.get('grower_id', None)
	
	blf_id = request.user.id
	blf_details = BlfProfile.cmobjects.filter(user_id=blf_id).first()
	grower_details = GrowerProfile.cmobjects.filter(id=grower_id).first()

	if not grower_details:
		return JsonResponse({'status': 'Data not found', 'request_status': 0}, status=404)

	map_area_details = MapAreaMaster.cmobjects.filter(grower=grower_details).first()
	map_area_land_details = MapAreaLandDetails.cmobjects.filter(grower=grower_details)

	if map_area_land_details:
		land_details_data_1 = MapAreaLandDetails.cmobjects.filter(
			grower=grower_details,
		).first()
	else:
		land_details_data_1 = ""

	if map_area_details and map_area_details.pdf_map_image:
		map_image = map_area_details.pdf_map_image
		map_image = f"{str(os.getenv('BASE_URL', ''))}media/{map_image}"
	else:
		map_image = "https://placehold.co/800x400"

	if not grower_details:
		return Response({'status': 'Data not found', 'request_status': 0}, status=404)

	form_details = FarmersAggreementForms.cmobjects.filter(
		grower=grower_details
	).first()

	if form_details:
		stg_signature = f"{str(os.getenv('BASE_URL', ''))}media/{form_details.farmer_signature_file}"
	else:
		stg_signature = ""

	garden_details = Gardens.cmobjects.filter(grower=grower_details).first()  
	if grower_details:
		grower_username = grower_details.user.username
	else:
		grower_username = ""
		
	if garden_details:
		production_area=garden_details.production_area
	else:
		production_area="NA"   

	monthly_shedule_list = MonthlySchedule.cmobjects.filter(grower_id=grower_details.id).order_by('-year')

	labour_list = Labour.cmobjects.filter(
			Q(grower_id=grower_details.id)).order_by('-id')


	# associated_entities = grower_details.associated_entity.all()
	associated_entity = grower_details.associated_entity.first()
	if associated_entity:
		associated_entity_user = associated_entity.user if associated_entity else None
		# associated_entity_names = [entity.user for entity in associated_entities]
	else:
		associated_entity_user = None

	grower_blf_details = BlfProfile.cmobjects.filter(user=associated_entity_user).first()

	# print("grower_blf_details ###", grower_blf_details)

	if grower_blf_details:
		blf_signature_details = BlfofficialSignature.cmobjects.filter(blf=grower_blf_details).first()
	else:
		blf_signature_details = None

	if blf_signature_details:
		blf_signature = f"{str(os.getenv('BASE_URL', ''))}/media/{blf_signature_details.blf_grade_official_signature_file}"
	else:
		blf_signature = ""

	if grower_details and date_from and date_to:
		date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
		date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')

		year_from = date_from_obj.year
		year_to = date_to_obj.year

		use_of_fertilizer_list= UseOfChemical.cmobjects.filter(
			grower_id=grower_id,chemical__chemical_type__name__iexact="Fertilizer",
			date__range=[date_from, date_to]
		).order_by('-id')
		use_of_herbicides_list= UseOfChemical.cmobjects.filter(
			grower_id=grower_id,chemical__chemical_type__name__iexact="Herbicides",
			date__range=[date_from, date_to]
		).order_by('-id')
		use_of_acaricides_list= UseOfChemical.cmobjects.filter(
			grower_id=grower_id,chemical__chemical_type__name__iexact="Acaricides",
			date__range=[date_from, date_to]
		).order_by('-id')
		use_of_insecticides_list= UseOfChemical.cmobjects.filter(
			grower_id=grower_id,chemical__chemical_type__name__iexact="Insecticides & Fungicides",
			date__range=[date_from, date_to]
		).order_by('-id')

		plucking_data_list = PluckingData.cmobjects.filter(
			grower_id=grower_id,
			date__range=[date_from, date_to]
		).order_by('-id')

	else:
		plucking_data_list = PluckingData.cmobjects.filter(
				Q(grower_id=grower_details.id)).order_by('-date')
		
		use_of_fertilizer_list = UseOfChemical.cmobjects.filter(
				Q(grower_id=grower_details.id),
				Q(chemical__chemical_type_id=1)).order_by('-date')
		
		use_of_herbicides_list = UseOfChemical.cmobjects.filter(
				Q(grower_id=grower_details.id),
				Q(chemical__chemical_type_id=2)).order_by('-date')
		
		use_of_insecticides_list = UseOfChemical.cmobjects.filter(
				Q(grower_id=grower_details.id),
				Q(chemical__chemical_type_id=3)).order_by('-date')

		use_of_acaricides_list = UseOfChemical.cmobjects.filter(
				Q(grower_id=grower_details.id),
				Q(chemical__chemical_type_id=5)).order_by('-date')
	context = {
		'grower_details' : grower_details,
		'grower_pk' : grower_details.pk,
		'grower_details' : grower_details,
		'labour_list' : labour_list,
		'plucking_data_list' : plucking_data_list,
		"fertilizer_chemical_list" : use_of_fertilizer_list,
		"herbicides_chemical_list" : use_of_herbicides_list,
		"insecticides_chemical_list" : use_of_insecticides_list,
		"acaricides_chemical_list" : use_of_acaricides_list,
		"schedule_list" : monthly_shedule_list,
		"blf_details": blf_details,
		"production_area":production_area,
		"garden_details" : garden_details,
		"grower_username" : grower_username,
		"production_area" : production_area,
		"form_details" : form_details,
		"blf_signature" : blf_signature,
		"stg_signature" : stg_signature,
		"map_area_details" : map_area_details,
		"map_image" : map_image,
		"land_details_data_1" : land_details_data_1,
	}

	html_templates = [
		'farm_diary/pdf/1.html',
		'farm_diary/pdf/2.html',
		'farm_diary/pdf/3.html',
		'farm_diary/pdf/4.html',
		'farm_diary/pdf/5.html',
		'farm_diary/pdf/6.html',
		'farm_diary/pdf/7.html',
		'farm_diary/pdf/8.html',
		'farm_diary/pdf/9.html',
		'farm_diary/pdf/10.html',
		'farm_diary/pdf/11.html',
		'farm_diary/pdf/12.html',
		'farm_diary/pdf/13.html',
		'farm_diary/pdf/14.html'
	]
	# Configure pdfkit options
	options = {
		'page-size': 'letter',
		'margin-top': '0.75in',
		'margin-right': '0.75in',
		'margin-bottom': '0.75in',
		'margin-left': '0.75in',
	}
	# Set the path to the wkhtmltopdf executable
	path_wkhtmltopdf = str(os.getenv('WKHTMLTOPDF_PATH', ''))
	# Convert HTML templates to PDF
	pdfs = []
	total_pages = 0
	page_counts = []

	# Render each HTML template to count pages and generate PDFs
	for html_template in html_templates:
		context['current_page'] = 1  # Initialize current page number for each template
		html = render_to_string(html_template, context)
		pdf = pdfkit.from_string(html, False, options=options, configuration=pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf))

		# Count the number of pages
		pdf_reader = PdfReader(BytesIO(pdf))
		num_pages = len(pdf_reader.pages)
		page_counts.append(num_pages)
		total_pages += num_pages

	current_page = 1
	for index, html_template in enumerate(html_templates):
		context['total_pages'] = total_pages
		num_pages = page_counts[index]

		for page_number in range(1, num_pages + 1):
			context['current_page'] = current_page
			html = render_to_string(html_template, context)
			pdf = pdfkit.from_string(html, False, options=options, configuration=pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf))
			pdfs.append(BytesIO(pdf))
			current_page += 1

	# # Merge PDF files into a single file
	# merger = PdfMerger()
	# for pdf in pdfs:
	# 	merger.append(PdfReader(pdf))

	# merged_pdf = BytesIO()
	# merger.write(merged_pdf)

	# filename = f"consolidated-farm-diary_{date_from}_to_{date_to}_{uuid.uuid4().hex}.pdf"
	# fs = FileSystemStorage(location=settings.MEDIA_ROOT)
	# file_path = fs.save(filename, ContentFile(pdf))
	# file_url = fs.url(file_path)

	# return Response({
	# 	'request_status': 1,
	# 	'msg': 'PDF generated successfully',
	# 	'file_url': request.build_absolute_uri(file_url)
	# })

	# Merge PDF files into a single file
	merger = PdfMerger()
	for pdf in pdfs:
		merger.append(PdfReader(pdf))

	merged_pdf = BytesIO()
	merger.write(merged_pdf)

	filename = f"consolidated-farm-diary_{date_from}_to_{date_to}_{uuid.uuid4().hex}.pdf"
	fs = FileSystemStorage(location=settings.MEDIA_ROOT)
	file_path = fs.save(filename, ContentFile(merged_pdf.getvalue()))
	file_url = fs.url(file_path)

	return JsonResponse({
		'request_status': 1,
		'msg': 'PDF generated successfully',
		'file_url': request.build_absolute_uri(file_url)
	}, status=200)


# API VIEW FOR SIGNATURE UPLOAD
class FarmersAggreementFormsUploadView(APIView):
	authentication_classes = (TokenAuthentication,)
	permission_classes = (IsAuthenticated,)
	def get(self, request, *args, **kwargs):
		grower_id = request.query_params.get('grower_id', None)
		if not grower_id:
			return Response({'status': status.HTTP_400_BAD_REQUEST, 'msg': 'grower_id is required', 'request_status': 0})

		agreement_form_details = FarmersAggreementForms.cmobjects.filter(grower_id=grower_id).first()
		if not agreement_form_details:
			return Response({'status': status.HTTP_404_NOT_FOUND, 'msg': 'Agreement form not found', 'request_status': 0})
		
		serializer = FarmersAggreementFormsSerializer(agreement_form_details)
		return Response({'results': {'Data': serializer.data}, 'status': status.HTTP_200_OK, 'request_status': 1})


	def post(self, request, *args, **kwargs):
		try:
			agreement_form_details = None
			data = request.data
			
			grower_id = data.get('grower_id', None)
			grower = GrowerProfile.cmobjects.filter(id=grower_id).first()
			# aggreement_form_title_id = data.get('aggreement_form_title_id', None)
			date = data.get('date', None)
			place = data.get('place', None)
			
			with transaction.atomic():
				blf_details = BlfProfile.cmobjects.filter(user=request.user).first()
				aggregator_details = AggregatorProfile.cmobjects.filter(user=request.user).first()
				agreement_form_details = FarmersAggreementForms.cmobjects.filter(
					grower_id=grower_id
				).first()

				if agreement_form_details:
					agreement_form_details.updated_by = request.user
				else:
					agreement_form_details = FarmersAggreementForms.objects.create(
						grower_id=grower_id,
						created_by=request.user
					)

				if agreement_form_details:
					if blf_details:
						agreement_form_details.blf_id = blf_details.id
					if aggregator_details:
						agreement_form_details.aggregator_id = aggregator_details.id    
					if date:
						agreement_form_details.date = date
					if place:
						agreement_form_details.place = place  


				serializer = FarmersAggreementFormsSerializer(agreement_form_details, data=data, partial=True, context={'request': request})
				if serializer.is_valid():
					serializer.save()
					return Response({'results': {'Data': serializer.data}, 'msg': 'Farmers Agreement Form Created Successfully', 'status': status.HTTP_201_CREATED, "request_status": 1})
				else:
					return Response({'msg': serializer.errors, 'status': status.HTTP_400_BAD_REQUEST, "request_status": 0})
		

		except Exception as e:
			return Response({'status': status.HTTP_400_BAD_REQUEST, 'request_status': 0, 'msg': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class MOnthlyShedulePdfGenerateAPIView(APIView):
	""" Supply Report List PDF Generate """
	authentication_classes = (TokenAuthentication,)
	permission_classes = (IsAuthenticated,)

	def get(self, request, *args, **kwargs):
		select_year= request.query_params.get('select_year', None)
		grower_id = request.query_params.get('grower_id', None)
		date_from = request.query_params.get('date_from')
		date_to = request.query_params.get('date_to')

		if not date_from or not date_to:
			raise APIException({'request_status': 0, 'msg': "date_from and date_to are mandatory"})

		grower_details=GrowerProfile.objects.filter(Q(user=request.user)|Q(id=grower_id)).first()
		monthly_shedule_list = MonthlySchedule.cmobjects.filter(year__year=select_year, grower_id=grower_details.id).order_by('-year')

		context = {
			'monthly_shedule_list' : monthly_shedule_list,
			'grower_pk' : grower_id,
			'growewr_details' : grower_details,
			
		}
		template = get_template('reports_pdf/monthly_schedule_list_pdf.html')
		html = template.render(context)
		options = {
			'page-size': 'A4',
			'encoding': "UTF-8",
			'dpi': 300,             
			'zoom': 1.3,             
			'no-outline': None,
			'margin-top': '0.75in',
			'margin-right': '0.75in',
			'margin-bottom': '0.75in',
			'margin-left': '0.75in',
			'enable-smart-shrinking': True,  # Better layout scaling
		}
		config = pdfkit.configuration(wkhtmltopdf=str(os.getenv('WKHTMLTOPDF_PATH', '')))
		pdf = pdfkit.from_string(html, False, options=options, configuration=config)

		# response = HttpResponse(pdf, content_type='application/pdf')
		# response['Content-Disposition'] = f'attachment; filename="supply_report_{date_from}_to_{date_to}.pdf"'
		# return response

		# Generate unique filename
		filename = f"monthly_schedule_list_pdf_{date_from}_to_{date_to}_{uuid.uuid4().hex}.pdf"
		fs = FileSystemStorage(location=settings.MEDIA_ROOT)
		file_path = fs.save(filename, ContentFile(pdf))
		file_url = fs.url(file_path)
		return Response({
			'request_status': 1,
			'msg': 'PDF generated successfully',
			'file_url': request.build_absolute_uri(file_url)
		})


# def generate_monthly_shedule_pdf(request):
# 	""" Labour Data generate pdf View """

# 	select_year= request.GET.get('select_year', None)
# 	grower_pk = request.GET.get('grower_id', None)
# 	date_from = request.GET.get('date_from')
# 	date_to = request.GET.get('date_to')

# 	grower_details = GrowerProfile.cmobjects.filter(user_id=grower_pk).first()
# 	if select_year:
# 		monthly_shedule_list = MonthlySchedule.cmobjects.filter(year__year=select_year, grower_id=grower_details.id).order_by('-year')
# 	else:
# 		monthly_shedule_list = MonthlySchedule.cmobjects.filter(grower_id=grower_details.id).order_by('-year')
	
# 	context = {
# 		'monthly_shedule_list' : monthly_shedule_list,
# 		'grower_pk' : grower_pk,
# 		'growewr_details' : grower_details,
		
# 	}
	
# 	# Create a response with PDF content
# 	response = HttpResponse(content_type='application/pdf')
# 	response['Content-Disposition'] = f'attachment; filename="monthly-schedule_of_work_list_pdf.pdf"'

# 	# Create an HTML template
# 	template = get_template('reports_pdf/monthly_schedule_list_pdf.html')
# 	html = template.render(context)  # Replace with your template context data

# 	# Generate PDF
# 	pisa.CreatePDF(html, dest=response)
# 	return response



