from django.shortcuts import render

# Create your views here.
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

from master.common import CommonMixin
from .models import *
from .forms import *
# Create your views here.


class LeafManagementListView(LoginRequiredMixin, CommonMixin, ListView):
	"""
	Leaf Management List View
	"""
	model = LeafManagement
	context_object_name = 'leaf_list'
	template_name = 'leaf_receipt/leaf_list.html'
	paginate_by = 10

	def get(self, request, *args, **kwargs):
		# try:
		#     if not self.request.user.is_superuser:
		#         messages.error(self.request, 'You have no permission to access the requested resource!')
		#         return redirect(reverse('index'))
		# except AttributeError as error:
		#     messages.error(self.request, 'You have no permission to access the requested resource!')
		#     return redirect(reverse('index'))

		return super().get(request, *args, **kwargs)


	def get_queryset(self, *args, **kwargs):
		qs = super().get_queryset(*args, **kwargs)
		start_date= self.request.GET.get('start_date')
		end_date= self.request.GET.get('end_date')
		if start_date and end_date:
			qs = LeafManagement.objects.filter(supply_date__range=(start_date,end_date), created_by_id=self.request.user.id)	
			return qs
		
		return LeafManagement.cmobjects.filter(created_by_id=self.request.user.id).order_by('-id')

	
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		# context['type_list'] = LeafManagement.objects.all().order_by('id')
		return context


class LeafManagementCreateView(LoginRequiredMixin, CreateView, CommonMixin):
	"""
	Leaf Receipt Create View @vivek, changes made by subhashis Neogi
	"""
	form_class = LeafManagementForm
	template_name = 'leaf_receipt/leaf_create.html'

	def get(self, request, *args, **kwargs):		
		return super().get(request, *args, **kwargs)
	
	def get_success_url(self, **kwargs):
		messages.success(self.request, 'Leaf Receipt Created Successfully')
		return reverse('leaf_receipt:leaf_list')
		
	def get_form_kwargs(self, **kwargs):
		""" Provides keyword arguemnt """
		kwargs = super(LeafManagementCreateView, self).get_form_kwargs()
		kwargs['user_id'] = self.request.user.id
		kwargs['weighted_id'] = None
		return kwargs

	def form_invalid(self, form):
		error_message = 'Error saving the Form, check fields below.'
		messages.error(self.request, error_message)
		return super().form_invalid(form)

	def form_valid(self, form):
		context = self.get_context_data()
		response = super().form_valid(form)
		object_id = self.object.pk
		
		# Weighment Details
		weighment_details = WeighmentSupply.cmobjects.filter(pk=form.instance.weighment_txn.id).first()

		if weighment_details.vehicle_no:
			vehicle_number = weighment_details.vehicle_no
		else:
			vehicle_number = ""

		if str(weighment_details.supplier_type) == "aggregator":
			profile_model = AggregatorProfile
		elif str(weighment_details.supplier_type) == "grower":
			profile_model = GrowerProfile
			garden_details = Gardens.cmobjects.filter(user_id=weighment_details.supplier).first()
			
		else:
			profile_model = ""


		# PROFILE DETAILS
		supplier_details = profile_model.cmobjects.filter(user_id=weighment_details.supplier).first()
		if str(weighment_details.supplier_type) == "grower":
			if PluckingData.cmobjects.filter(grower_id=supplier_details.id).exists():
				plucking_details = PluckingData.cmobjects.filter(grower_id=supplier_details.id).latest('id')
				plucking_details_id = plucking_details.id
			else:
				plucking_details = None
				plucking_details_id = None
		else:
			plucking_details = None

			
		# SUPPLY DETAILS
		supply_chalan_id = weighment_details.supply_challan.id
		supply_details = SupplyManagement.cmobjects.filter(id=supply_chalan_id).first()
		
		if weighment_details.vehicle_no:
			vehicle_details = VehicleManagement.cmobjects.filter(id=weighment_details.vehicle_no.id).first()

		with transaction.atomic():
			form.instance.created_by_id = self.request.user.id

			if str(form.instance.acknowledge_status) == "Received":
				weighment_details.is_processed=True
				# weighment_details.is_leaf_rejected = True
				weighment_details.save()

				if vehicle_number:
					""" Allocated Vehicle has been Released """
					vehicle_details.is_available = False
					vehicle_details.save()
				else:
					pass

				if str(weighment_details.mode_of_supply) == "Motorised 3 / 4 wheelers vehicle":
					pass
				else:
					net_leaf_weight = weighment_details.total_gross_weight_kg
					nt_wght =  round(net_leaf_weight - (net_leaf_weight * (form.instance.deduction/100)), 2)
					form.instance.net_leaf_weight = nt_wght

					# collection in respect of vehicle has been free
					CollectionFromGrower.objects.filter(vehicle_number=weighment_details.vehicle_no).update(is_complete=True)

					if not str(weighment_details.mode_of_supply) == "Motorised 3 / 4 wheelers vehicle":
						if str(weighment_details.supplier_type) == "aggregator":
							leaf_collection_create=LeafCollection.objects.create(
								leaf_receipt_id_id = object_id,
								weighment_supply_id_id=weighment_details.id,
								supply_id_id = supply_details.id,
								supplier_id = weighment_details.supplier_id,
								nt_wght=nt_wght,
								collection_date= form.instance.supply_date,
								supplier_type = weighment_details.supplier_type,
								aggregator_id = supplier_details.id,
								supply_date = supply_details.date_of_supply,
								created_by_id = self.request.user.id
							)	
							leaf_collection_create.save()
							
						elif str(weighment_details.supplier_type) == "grower":
							leaf_collection_create=LeafCollection.objects.create(
								leaf_receipt_id_id = object_id,
								weighment_supply_id_id=weighment_details.id,
								supply_id_id = supply_details.id,
								supplier_id = weighment_details.supplier_id,
								nt_wght=nt_wght,
								collection_date= form.instance.supply_date,
								supplier_type = weighment_details.supplier_type,
								grower_id = supplier_details.id,
								supply_date = supply_details.date_of_supply,
								created_by_id = self.request.user.id
							)
							leaf_collection_create.save()

							if plucking_details_id:
								leaf_collection_create.plucking_data_id=plucking_details_id
								leaf_collection_create.save()
		
			elif str(form.instance.acknowledge_status) == "Rejected":

				if vehicle_number:
					vehicle_details.is_available = False
					vehicle_details.save()
				else:
					pass
				weighment_details.is_processed=True
				# weighment_details.is_leaf_rejected = True
				weighment_details.save()
				nt_wght = 0


			self.get_object = form.save()
				
			if not form.is_valid():
				# formsets or form is invalid; render the form with error
				return self.render_to_response(context)
			
		return response



class LeafManagementUpdateView(LoginRequiredMixin, CommonMixin, UpdateView):
	"""
	Leaf Management Create and Update View @vivek
	"""
	model = LeafManagement
	form_class = LeafManagementForm
	template_name = 'leaf_receipt/leaf_create.html'

	def get(self, request, *args, **kwargs):

		return super().get(request, *args, **kwargs)

	def get_success_url(self, **kwargs):
		messages.success(self.request, 'Leaf Receipt Updated Successfully')
		return reverse('leaf_receipt:leaf_list')

	def get_form_kwargs(self, **kwargs):
		""" Provides keyword arguemnt """
		kwargs = super(LeafManagementUpdateView, self).get_form_kwargs()
		leaf_details = LeafManagement.cmobjects.filter(id=self.kwargs.get('id', None)).first()
		kwargs['user_id'] = self.request.user.id
		kwargs['weighted_id'] = leaf_details.weighment_txn_id
		return kwargs

	def get_object(self,queryset=None):
		leaf_details = LeafManagement.cmobjects.filter(pk=self.kwargs['id']).first()
		return leaf_details

	def get_context_data(self, **kwargs):
		context = super(LeafManagementUpdateView, self).get_context_data(**kwargs)
		leaf_details = LeafManagement.cmobjects.filter(pk=self.kwargs['id']).first()
		context['weighment_details'] = WeighmentSupply.cmobjects.filter(pk=leaf_details.weighment_txn.id).first()
		context['leaf_details'] = self.get_object()
		return context
	
	def form_valid(self, form):
		self.id = self.kwargs['id']
		context = self.get_context_data()
		self.created_by_id = self.request.user.id
		leaf_details = LeafManagement.cmobjects.filter(pk=self.kwargs['id']).first()
		weighment_details = WeighmentSupply.cmobjects.filter(pk=leaf_details.weighment_txn.id).first()
		
		with transaction.atomic():
			# if self.isinstance.weighment_txn:
			# 	weighment_details.is_processed = False
			# 	weighment_details.save()
			self.object = form.save()

		return super(LeafManagementUpdateView, self).form_valid(form)
	


@login_required
def leaf_management_delete(request, id):
	leaf = LeafManagement.cmobjects.filter(id=id).first()
	leaf.is_deleted=True
	leaf.save()
	weighment_details = WeighmentSupply.cmobjects.filter(id=leaf.weighment_txn.id).first()
	weighment_details.is_processed = False
	print(weighment_details)
	messages.success(
		request, 'Leaf Receipt Deleted Successfully')
	return redirect(reverse('leaf_receipt:leaf_list'))    


@login_required
def leaf_management_view(request, id):

		result = LeafManagement.objects.filter(pk=id).first()
		context={
			'leaf_list' : result,
		}
		return CommonMixin.render(request, 'leaf_receipt/leaf_view.html', context)	


def load_supply_date(request):
	id = request.GET.get('id', None)
	weighment_details= WeighmentSupply.cmobjects.filter(pk=id).first()
	supply_date = weighment_details.supply_date
	data = {
		"value" : supply_date,
	}
	return JsonResponse(data)