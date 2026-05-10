
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
from django.db import transaction
from master.common import CommonMixin
from .models import *
from .forms import *
from django.http import HttpResponse
from django.conf import settings
from urlbox import UrlboxClient
from django.shortcuts import get_object_or_404
from django.utils.http import url_has_allowed_host_and_scheme
from user_profile.helpers import *
from user_profile.serializers import *

FERTILIZER_TYPE_ID = 1


def get_fertilizer_type():
	return ChemicalType.objects.filter(id=FERTILIZER_TYPE_ID).first() or ChemicalType.objects.filter(
		name__iexact="Fertilizer"
	).first()


def is_ajax_request(request):
	return request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'


def apply_chemical_search(queryset, search_term):
	if not search_term:
		return queryset
	return queryset.filter(
		Q(chemical_name__icontains=search_term) |
		Q(chemical_type__name__icontains=search_term) |
		Q(manufacturer__icontains=search_term) |
		Q(brand_local_name__icontains=search_term) |
		Q(composition__icontains=search_term)
	)


def get_safe_next_url(request, default_url):
	next_url = request.GET.get('next') or request.POST.get('next')
	if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
		return next_url
	return default_url


class FertilizerListView(LoginRequiredMixin, CommonMixin, ListView):
	"""
	Fertilizer Data List View
	"""
	model = ChemicalData
	context_object_name = 'chemical_list'
	template_name = 'chemical/chemical_list.html'
	paginate_by = 10

	def get(self, request, *args, **kwargs):
		try:
			if not self.request.user.is_superuser:
				messages.error(self.request, 'You have no permission to access the requested resource!')
				return redirect(reverse('index'))
		except AttributeError as error:
			messages.error(self.request, 'You have no permission to access the requested resource!')
			return redirect(reverse('index'))
		return super().get(request, *args, **kwargs)

	def get_queryset(self, *args, **kwargs):
		fertilizer_type = get_fertilizer_type()
		qs = ChemicalData.objects.select_related('chemical_type').filter(is_deleted=False)
		if fertilizer_type:
			qs = qs.filter(chemical_type=fertilizer_type)
		else:
			qs = qs.filter(chemical_type__name__iexact="Fertilizer")
		return apply_chemical_search(qs, self.request.GET.get('q', '').strip()).order_by('-id')

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['type_list'] = ChemicalType.objects.all().order_by('id')
		context['is_fertilizer'] = True
		context['search_query'] = self.request.GET.get('q', '').strip()
		context['list_url'] = reverse('chemical_data:fertilizer_list')
		context['current_list_url'] = self.request.get_full_path()
		return context

	def render_to_response(self, context, **response_kwargs):
		if is_ajax_request(self.request):
			return render(self.request, 'chemical/_chemical_table.html', context)
		return super().render_to_response(context, **response_kwargs)
	
class ChemicalListView(LoginRequiredMixin, CommonMixin, ListView):
    model = ChemicalData
    context_object_name = 'chemical_list'
    template_name = 'chemical/chemical_list.html'
    paginate_by = 10

    # ✅ Clean permission handling
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            messages.error(request, 'You have no permission to access this resource!')
            return redirect('index')
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        fertilizer_type = get_fertilizer_type()
        qs = ChemicalData.objects.select_related('chemical_type').filter(is_deleted=False)
        if fertilizer_type:
            qs = qs.exclude(chemical_type=fertilizer_type)
        else:
            qs = qs.exclude(chemical_type__name__iexact="Fertilizer")
        return apply_chemical_search(qs, self.request.GET.get('q', '').strip()).order_by('-id')

        chemical_type = self.request.GET.get('chemical_type')
        chemical_name = self.request.GET.get('chemical_name')

        # ✅ FIX: Don't return early
        if chemical_type:
            qs = qs.filter(chemical_type__name__icontains=chemical_type)

        if chemical_name:
            qs = qs.filter(chemical_name__icontains=chemical_name)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        fertilizer_type = get_fertilizer_type()
        type_list = ChemicalType.objects.all()
        if fertilizer_type:
            type_list = type_list.exclude(id=fertilizer_type.id)
        context['type_list'] = type_list.order_by('id')
        context['is_fertilizer'] = False
        context['search_query'] = self.request.GET.get('q', '').strip()
        context['list_url'] = reverse('chemical_data:chemical_list')
        context['current_list_url'] = self.request.get_full_path()
        return context

    def render_to_response(self, context, **response_kwargs):
        if is_ajax_request(self.request):
            return render(self.request, 'chemical/_chemical_table.html', context)
        return super().render_to_response(context, **response_kwargs)
    

class ChemicalCreateView(LoginRequiredMixin, CommonMixin, CreateView):
    model = ChemicalData
    form_class = ChemicalDataForm
    template_name = 'chemical/chemical_data_create.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            messages.error(request, 'You have no permission!')
            return redirect('index')
        return super().dispatch(request, *args, **kwargs)

    # ✅ Read query param
    def get_is_fertilizer(self):
        return self.request.GET.get('is_fertilizer') == '1'

    # ✅ Inject into form
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['is_fertilizer'] = self.get_is_fertilizer()
        return kwargs

    # ✅ Pass to template
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_fertilizer'] = self.get_is_fertilizer()
        default_url = reverse('chemical_data:fertilizer_list') if context['is_fertilizer'] else reverse('chemical_data:chemical_list')
        context['next_url'] = get_safe_next_url(self.request, default_url)
        return context

    def form_valid(self, form):
        try:
            if self.get_is_fertilizer():
                fertilizer_type = get_fertilizer_type()

                if fertilizer_type:
                    form.instance.chemical_type = fertilizer_type
            form.instance.created_by = self.request.user

            messages.success(self.request, 'Data Created Successfully')
            return super().form_valid(form)

        except Exception as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)

    def get_success_url(self):
        default_url = reverse('chemical_data:fertilizer_list') if self.get_is_fertilizer() else reverse('chemical_data:chemical_list')
        next_url = get_safe_next_url(self.request, default_url)
        if next_url != default_url:
            return next_url
        if self.get_is_fertilizer():
            return reverse('chemical_data:fertilizer_list')
        return reverse('chemical_data:chemical_list')


class ChemicalDataUpdateView(LoginRequiredMixin, CommonMixin, UpdateView):
    model = ChemicalData
    form_class = ChemicalDataForm
    template_name = 'chemical/chemical_data_create.html'
    pk_url_kwarg = 'id'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            messages.error(request, 'You have no permission!')
            return redirect('index')
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        return get_object_or_404(ChemicalData, pk=self.kwargs['id'], is_deleted=False)

    # ✅ Detect fertilizer from DB
    def get_is_fertilizer(self):
        obj = self.get_object()
        fertilizer_type = get_fertilizer_type()
        if fertilizer_type:
            return obj.chemical_type_id == fertilizer_type.id
        return obj.chemical_type and obj.chemical_type.name and obj.chemical_type.name.lower() == 'fertilizer'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['is_fertilizer'] = self.get_is_fertilizer()
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_fertilizer'] = self.get_is_fertilizer()
        default_url = reverse('chemical_data:fertilizer_list') if context['is_fertilizer'] else reverse('chemical_data:chemical_list')
        context['next_url'] = get_safe_next_url(self.request, default_url)
        return context

    def form_valid(self, form):
        with transaction.atomic():
            if self.get_is_fertilizer():
                fertilizer_type = get_fertilizer_type()
                if fertilizer_type:
                    form.instance.chemical_type = fertilizer_type
            self.object = form.save()

        messages.success(self.request, 'Data Updated Successfully')
        return super().form_valid(form)

    def get_success_url(self):
        default_url = reverse('chemical_data:fertilizer_list') if self.get_is_fertilizer() else reverse('chemical_data:chemical_list')
        next_url = get_safe_next_url(self.request, default_url)
        if next_url != default_url:
            return next_url
        if self.get_is_fertilizer():
            return reverse('chemical_data:fertilizer_list')
        return reverse('chemical_data:chemical_list')






# class ChemicalCreateView2(LoginRequiredMixin, CreateView, CommonMixin):
#     """
#     Chemical Create View @vivek
#     """
#     form_class = ChemicalDataForm
#     template_name = 'chemical/chemical_data_create.html'

#     def get(self, request, *args, **kwargs):

        
#         return super().get(request, *args, **kwargs)


#     def get_success_url(self, **kwargs):
#         messages.success(self.request, 'Chemical Data Created Successfully')
#         return reverse('chemical_data:chemical_list')

#     def form_invalid(self, form):
#         error_message = 'Error saving the Form, check fields below.'
#         messages.error(self.request, error_message)
#         return super().form_invalid(form)


# class ChemicalDataUpdateView(LoginRequiredMixin, CommonMixin, UpdateView):
# 	"""
# 	Chemical Data Create and Update View @vivek
# 	"""
# 	model = ChemicalData
# 	form_class = ChemicalDataForm
# 	template_name = 'chemical/chemical_data_create.html'

# 	def get(self, request, *args, **kwargs):
# 	# checking if the user is customer
# 		try:
# 			if not self.request.user.is_superuser:
# 				messages.error(self.request, 'You have no permission to access the requested resource!')
# 				return redirect(reverse('index'))
# 		except AttributeError as error:
# 			messages.error(self.request, 'You have no permission to access the requested resource!')
# 			return redirect(reverse('index'))

# 		return super().get(request, *args, **kwargs)

# 	def get_success_url(self, **kwargs):
# 		messages.success(self.request, 'Chemical Data Updated Successfully')
# 		return reverse('chemical_data:chemical_list')


# 	def get_object(self,queryset=None):
# 		chemical_details = get_object_or_404(ChemicalData,pk=self.kwargs['id'])
# 		return chemical_details

# 	def get_context_data(self, **kwargs):
# 		context = super(ChemicalDataUpdateView, self).get_context_data(**kwargs)

# 		context['chemical_details'] = self.get_object()
# 		return context
# 	def form_valid(self, form):
		
# 		self.id = self.kwargs['id']
# 		context = self.get_context_data()


# 		with transaction.atomic():
# 			self.object = form.save()


# 		return super(ChemicalDataUpdateView, self).form_valid(form)
	
@login_required
def chemical_delete(request, id):
	try:
		if not request.user.is_superuser:
			messages.error(request, 'You have no permission to access the requested resource!')
			return redirect(reverse('index'))
	except AttributeError as error:
		messages.error(request, 'You have no permission to access the requested resource!')
		return redirect(reverse('index'))
	chemical = ChemicalData.objects.filter(id=id, is_deleted=False).first()
	if not chemical:
		messages.error(request, 'Data not found.')
		return redirect(reverse('chemical_data:chemical_list'))

	fertilizer_type = get_fertilizer_type()
	is_fertilizer = fertilizer_type and chemical.chemical_type_id == fertilizer_type.id
	if is_fertilizer:
		default_url = reverse('chemical_data:fertilizer_list')
	else:
		default_url = reverse('chemical_data:chemical_list')
	return soft_delete_instance_for_web(
		request,
		chemical,
		get_safe_next_url(request, default_url),
		success_message='Data Deleted Successfully',
	)

@login_required
def chemical_search(request):
	if request.method == "POST":
		chemical_type_id= request.POST.get('chemical_type_id')
		print(chemical_type_id)
		type_list=ChemicalType.objects.all().order_by('id')


		edit_url = 'chemical_data:chemical_edit'


		chemical_name=request.POST.get('chemical_name')

		filter = {}
		if chemical_type_id:
			filter["chemical_type__id"] = chemical_type_id
		if chemical_name:
			filter["chemical_name__icontains"] = chemical_name


		result = ChemicalData.objects.filter(**filter)
		print(result)

		print(filter)

		context={
			'chemical_list' : result,
			'chemical_type' : chemical_type_id,
			'edit_url' : edit_url,
			'chemical_name' : chemical_name,
			'type_list':type_list
		}

		return CommonMixin.render(request, 'chemical/chemical_list.html', context)
	
	
@login_required
def chemical_view(request, id):
	chemical_details = ChemicalData.objects.filter(pk=id, is_deleted=False).first()
	fertilizer_type = get_fertilizer_type()
	is_fertilizer = fertilizer_type and chemical_details and chemical_details.chemical_type_id == fertilizer_type.id

	map_arear_mastr_list = MapAreaNameMaster.cmobjects.all()
	context={
		'chemical_details' : chemical_details,
		"map_arear_mastr_list" : map_arear_mastr_list,
		"is_fertilizer": is_fertilizer,
		"next_url": get_safe_next_url(request, reverse('chemical_data:fertilizer_list') if is_fertilizer else reverse('chemical_data:chemical_list')),
	}
	return CommonMixin.render(request, 'chemical/chemical_view.html', context)	
	


# Upload Farmer Signature file 

from django.core.files.base import ContentFile
import base64



@login_required
def uplaod_farmers_signature(request):
    if request.method == 'POST':
        signature_type = request.POST.get('signature_type')
        grower_pk = request.POST.get('grower_pk')
        signature_file = request.FILES.get('farmer_signature_file')
        place = request.POST.get('place')
        date = request.POST.get('date')

        # Check if a file was uploaded
        if signature_file:
            try:
                validate_image_file_extension(signature_file)
            except ValidationError as e:
                messages.error(request, f'Error: {e.message}')
                return HttpResponseRedirect(request.META.get("HTTP_REFERER"))
        # else:
        #     messages.error(request, 'Error: No file uploaded.')
        #     return HttpResponseRedirect(request.META.get("HTTP_REFERER"))

        blf_details = BlfProfile.objects.filter(user=request.user).first()
        grower_details = GrowerProfile.objects.filter(user=grower_pk).first()

        check_form_details = FarmersAggreementForms.objects.filter(
            blf=blf_details,
            grower=grower_details
        ).first()

        if check_form_details:
            ## UPDATE THE FORM 
            if not str(signature_type) == "digital_signature":
                # Image File Upload 
                check_form_details.farmer_signature_file = signature_file
                check_form_details.place = place
                check_form_details.date = date
                check_form_details.save()
                messages.success(request, 'Signature updated successfully.')
                return HttpResponseRedirect(request.META.get("HTTP_REFERER"))
            else:
                # Digital Signature 
                signature_data = request.POST.get('signature_data')
                if signature_data:
                    format, imgstr = signature_data.split(';base64,')
                    ext = format.split('/')[-1]
                    data = ContentFile(base64.b64decode(imgstr), name='signature.' + ext)

                    check_form_details.farmer_signature_file.save('signature.' + ext, data)
                    check_form_details.place = place
                    check_form_details.date = date
                    check_form_details.save()

                    messages.success(request, 'Signature updated successfully.')
                    return HttpResponseRedirect(request.META.get("HTTP_REFERER"))

        else:
            ## CREATE THE FORM
            if not str(signature_type) == "digital_signature":
                ## Image File Upload 
                create = FarmersAggreementForms.objects.create(
                    blf=blf_details,
                    grower=grower_details,
                    farmer_signature_file=signature_file,
                    place=place,
                    date=date,
                    created_by=request.user
                )
                messages.success(request, 'Signature Uploaded successfully.')
                return HttpResponseRedirect(request.META.get("HTTP_REFERER"))

            else:
                # Digital Signature
                signature_data = request.POST.get('signature_data')
                if signature_data:
                    format, imgstr = signature_data.split(';base64,')
                    ext = format.split('/')[-1]
                    data = ContentFile(base64.b64decode(imgstr), name='signature.' + ext)

                    farmers_agreement_form = FarmersAggreementForms.objects.create(
                        blf=blf_details,
                        grower=grower_details,
                        place=place,
                        date=date,
                        created_by=request.user
                    )
                    farmers_agreement_form.farmer_signature_file.save('signature.' + ext, data)

                    messages.success(request, 'Signature Uploaded successfully.')
                    return HttpResponseRedirect(request.META.get("HTTP_REFERER"))

    else:
        messages.error(request, 'Failed to upload signature.')
        return HttpResponseRedirect(request.META.get("HTTP_REFERER"))





# BLF SIGNATURE
@login_required
def uplaod_blf_signature_upload(request):

	if request.method == 'POST':
		signature_type = request.POST.get('signature_type')
		signature_file = request.FILES.get('blf_grade_official_signature_file')
		blf_details = BlfProfile.objects.filter(user=request.user).first()
		
		# Add the validation check here
		# try:
		# 	validate_image_file_extension(signature_file)
		# except ValidationError as e:
		# 	messages.error(request, f'Error: {e.message}')
		# 	return HttpResponseRedirect(request.META.get("HTTP_REFERER"))
		# 	# return redirect(reverse('chemical_data:farmers_aggreements_forms_details', kwargs={"grower_pk": grower_pk, "id": form_master_pk}))
		

		if signature_file:
			try:
				validate_image_file_extension(signature_file)
			except ValidationError as e:
				messages.error(request, f'Error: {e.message}')
				return HttpResponseRedirect(request.META.get("HTTP_REFERER"))



		check_signature_details = BlfofficialSignature.objects.filter(blf=blf_details).first()

		if not str(signature_type) == "digital_signature":

			if check_signature_details:
				check_signature_details.blf_grade_official_signature_file = signature_file
				check_signature_details.save()
				messages.success(request, 'Signature updated successfully.')
				return HttpResponseRedirect(request.META.get("HTTP_REFERER"))
				# return redirect(reverse('chemical_data:farmers_aggreements_forms_list', kwargs={"grower_pk": grower_pk }))

			else:
				create = BlfofficialSignature.objects.create(
					blf=blf_details,
					blf_grade_official_signature_file=signature_file,
					created_by=request.user
				)
				messages.success(request, 'Signature Uploaded successfully.')
				return HttpResponseRedirect(request.META.get("HTTP_REFERER"))
				# return redirect(reverse('chemical_data:farmers_aggreements_forms_list', kwargs={"grower_pk": grower_pk }))

		else:

			if check_signature_details:
				signature_data = request.POST.get('signature_data')
				if signature_data:
					format, imgstr = signature_data.split(';base64,')
					ext = format.split('/')[-1]
					data = ContentFile(base64.b64decode(imgstr), name='signature.' + ext)

					check_signature_details.blf_grade_official_signature_file.save('signature.' + ext, data)
					messages.success(request, 'Signature updated successfully.')
					return HttpResponseRedirect(request.META.get("HTTP_REFERER"))
					# return redirect(reverse('chemical_data:farmers_aggreements_forms_list', kwargs={"grower_pk": grower_pk }))

			else:

				signature_data = request.POST.get('signature_data')
				print("signature_data **###", signature_data)
				if signature_data:
					format, imgstr = signature_data.split(';base64,')
					ext = format.split('/')[-1]
					data = ContentFile(base64.b64decode(imgstr), name='signature.' + ext)

					create = BlfofficialSignature.objects.create(
						blf=blf_details,
						created_by=request.user
					)
					create.blf_grade_official_signature_file.save('signature.' + ext, data)

			messages.success(request, 'Signature Uploaded successfully.')
			return HttpResponseRedirect(request.META.get("HTTP_REFERER"))
			# return redirect(reverse('chemical_data:farmers_aggreements_forms_list', kwargs={"grower_pk": grower_pk}))
	else:
		messages.error(request, 'Failed to upload signature.')
		return HttpResponseRedirect(request.META.get("HTTP_REFERER"))
		# return redirect(reverse('chemical_data:farmers_aggreements_forms_list', kwargs={"grower_pk": grower_pk }))




@login_required
def edit_farmers_signature(request):
	if request.method == 'POST':
		grower_pk = request.POST.get('grower_pk')
		signature_file = request.FILES.get('farmer_signature_file')
		form_master_pk = request.POST.get('form_master_pk')

		blf_details = BlfProfile.objects.filter(user=request.user).first()
		grower_details = GrowerProfile.objects.filter(user=grower_pk).first()
		form_master_details = FarmersAggreementMaster.objects.filter(pk=form_master_pk).first()

		form_details = FarmersAggreementForms.objects.filter(
			blf=blf_details,
			grower=grower_details,
			aggreement_form_title=form_master_details,
		).first()

		if form_details.farmer_signature_file:
			form_details.farmer_signature_file = signature_file
			form_details.save()
			messages.success(request, 'Signature updated successfully.')
		else:
			messages.error(request, 'Failed to update signature.')
		return redirect(reverse('chemical_data:farmers_aggreements_forms_list', kwargs={"grower_pk": grower_pk }))
	else:
		messages.error(request, 'Failed to update signature.')
		return redirect('some_error_url')
	



def aggreements_form_date(request):

	id = request.GET.get('id', None)
	form_details = FarmersAggreementForms.cmobjects.filter(pk=id).first()

	print("form_details  DATE ###",form_details.date)

	form_details_date = form_details.date


	data = {
		"value" : form_details_date,
	}

	print("data ----", data)

	return JsonResponse(data)


@login_required
def farmers_aggreements_forms_details(request, grower_pk ):

	blf_details = BlfProfile.objects.filter(user=request.user).first()
	grower_details = GrowerProfile.objects.filter(user=grower_pk).first()
	# form_master_details = FarmersAggreementMaster.objects.filter(pk=id).first()

	form_details = FarmersAggreementForms.cmobjects.filter(grower=grower_details).first()
	
	print("form_details ##", form_details)

	context={
		"blf_details" : blf_details,
		"grower_details" : grower_details,
		# "form_master_details" : form_master_details,
		'grower_pk' : grower_pk,
		"form_details" : form_details,
		"form_master_pk" : id,
	}
	return CommonMixin.render(request, 'farm_diary/farmers_aggreements_form_details.html', context)	



def farmers_aggreements_blf_signature(request, grower_pk):

	blf_details = BlfProfile.objects.filter(user=request.user).first()

	signature_details = BlfofficialSignature.cmobjects.filter(blf=blf_details).first()

	context={
		"blf_details" : blf_details,
		'grower_pk' : grower_pk,
		"signature_details" : signature_details,
	}
	return CommonMixin.render(request, 'farm_diary/blf_signature.html', context)	




@login_required
def farmers_aggreements_form_view(request, grower_pk):
	blf_details = BlfProfile.objects.filter(user=request.user).first()
	grower_details = GrowerProfile.objects.filter(user=grower_pk).first()
	form_details = FarmersAggreementForms.cmobjects.filter(aggreement_form_title=form_master_details, blf=blf_details, grower=grower_details).first()
	garden_details = Gardens.cmobjects.filter(grower=grower_details).first()
	template_name = "farm_diary/farmers_aggreements_form_web.html"

	context={
		"blf_details" : blf_details,
		"grower_details" : grower_details,
		"form_master_details" : form_master_details,
		'grower_pk' : grower_pk,
		"form_details" : form_details,
		"form_master_pk" : id,
		"garden_details" : garden_details,
	}

	return CommonMixin.render(request, template_name, context)	





# mobile APP map template
def mobile_app_map_template(request):

	context= {

	}
	
	return render(request, 'farm_diary/mobile_app_map_template.html', context)


############# Agreement form pdf download ####################
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

# import pdfkit


# from io import BytesIO
# from PyPDF2 import PdfFileReader, PdfMerger
# from PyPDF2 import PdfReader

# def farmers_agreement_pdf_generate(request, grower_pk, form_id):

# 	blf_id = request.user.id

# 	# Fetch data based on query parameters
# 	blf_details = BlfProfile.cmobjects.filter(user_id=blf_id).first()
# 	grower_details = GrowerProfile.cmobjects.filter(id=grower_pk).first()
# 	form_master_details = FarmersAggreementMaster.cmobjects.filter(id=form_id).first()
# 	print(form_master_details)
# 	if  not grower_details or not form_master_details:
# 		return Response({'status': 'Data not found', 'request_status': 0}, status=404)

# 	form_details = FarmersAggreementForms.cmobjects.filter(
# 		aggreement_form_title=form_master_details,
# 		grower=grower_details
# 	).first()

# 	garden_details = Gardens.cmobjects.filter(grower_id=grower_pk).first()	
# 	if grower_details:
# 		grower_username = grower_details.user.username
# 	else:
# 		grower_username = ""
# 	if garden_details:
# 		production_area=garden_details.production_area
# 	else:
# 		production_area="NA"	

# 	# Prepare context for the template
# 	context = {
# 		"blf_details": blf_details,
# 		"grower_details": grower_details,
# 		"form_master_details": form_master_details,
# 		'grower_pk': grower_pk,
# 		"form_details": form_details,
# 		"form_master_pk": form_id,
# 		"production_area":production_area,
# 		"garden_details" : garden_details,
# 	}


# 	html_templates = [
# 		'farm_diary/agreement_form_download.html',
# 		'farm_diary/test_pdf.html'
# 	]

# 	# Configure pdfkit options
# 	options = {
# 		'page-size': 'A4',
# 		'margin-top': '0.75in',
# 		'margin-right': '0.75in',
# 		'margin-bottom': '0.75in',
# 		'margin-left': '0.75in',	
# 	}

# 	# Set the path to the wkhtmltopdf executable
# 	path_wkhtmltopdf = '/usr/bin/wkhtmltopdf'

# 	# Convert HTML templates to PDF
# 	pdfs = []
# 	for html_template in html_templates:
# 		html = render_to_string(html_template, context)
# 		pdf = pdfkit.from_string(html, False, options=options, configuration=pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf))
# 		pdfs.append(BytesIO(pdf))

# 	# Merge PDF files into a single file
# 	merger = PdfMerger()
# 	for pdf in pdfs:
# 		merger.append(PdfReader(pdf))  # Use PdfReader instead of PdfFileReader

# 	merged_pdf = BytesIO()
# 	merger.write(merged_pdf)

# 	# Create a response object with the PDF file as content
# 	response = HttpResponse(merged_pdf.getvalue(), content_type='application/pdf')
# 	response['Content-Disposition'] = f'attachment; filename="farmers-agreement-form.pdf"'

# 	return response

@login_required
def farmers_map_area_total_pdf(request, grower_pk):

	
	blf_id = request.user.id

	# Fetch data based on query parameters
	blf_details = BlfProfile.cmobjects.filter(user_id=blf_id).first()
	grower_details = GrowerProfile.cmobjects.filter(id=grower_pk).first()

	map_area_details_1 = MapAreaDetails.objects.filter(blf=blf_details, grower=grower_details, map_area_name_id=1).first()
	map_area_details_2= MapAreaDetails.objects.filter(blf=blf_details, grower=grower_details, map_area_name_id=2).first()
	map_area_details_3 = MapAreaDetails.objects.filter(blf=blf_details, grower=grower_details, map_area_name_id=3).first()
	map_area_details_4 = MapAreaDetails.objects.filter(blf=blf_details, grower=grower_details, map_area_name_id=4).first()

	print("map_area_details_4", map_area_details_4)

	# Prepare context for the template
	context = {
		"blf_details": blf_details,
		"grower_details": grower_details,
		"map_area_details_1": map_area_details_1,
		"map_area_details_2": map_area_details_2,
		"map_area_details_3": map_area_details_3,
		"map_area_details_4": map_area_details_4,
		'grower_pk': grower_pk,
	}

	return render(request, "farm_diary/pdf/grower_total_map_area_pdf.html", context)





import requests


def farm_diary_pdf_generate(request, grower_pk):
    blf_id = request.user.id

    # Fetch data based on query parameters
    blf_details = BlfProfile.cmobjects.filter(user_id=blf_id).first()
    grower_details = GrowerProfile.cmobjects.filter(id=grower_pk).first()

    map_area_details_1 = MapAreaDetails.objects.filter(blf=blf_details, grower=grower_details, map_area_name_id=1).first()
    map_area_details_2 = MapAreaDetails.objects.filter(blf=blf_details, grower=grower_details, map_area_name_id=2).first()
    map_area_details_3 = MapAreaDetails.objects.filter(blf=blf_details, grower=grower_details, map_area_name_id=3).first()
    map_area_details_4 = MapAreaDetails.objects.filter(blf=blf_details, grower=grower_details, map_area_name_id=4).first()

    # Prepare context for the template
    context = {
        "blf_details": blf_details,
        "grower_details": grower_details,
        "map_area_details_1": map_area_details_1,
        "map_area_details_2": map_area_details_2,
        "map_area_details_3": map_area_details_3,
        "map_area_details_4": map_area_details_4,
        'grower_pk': grower_pk,
    }

    # Generate a static map image using the Google Static Maps API
    # You'll need to construct the URL with your API key and the appropriate center/zoom/size parameters
    static_map_url = "https://maps.googleapis.com/maps/api/staticmap?center=-34.397,150.644&zoom=2&size=600x400&key=YOUR_API_KEY"
    response = requests.get(static_map_url)
    with open("static_map.png", "wb") as f:
        f.write(response.content)

    # Include the static map image in your context
    context["static_map_image"] = "static_map.png"

    html = render_to_string('farm_diary/pdf/grower_total_map_area_pdf_app.html', context)

    # Configure pdfkit options
    options = {
        'page-size': 'A4',
        'margin-top': '0.75in',
        'margin-right': '0.75in',
        'margin-bottom': '0.75in',
        'margin-left': '0.75in',
    }

    # Set the path to the wkhtmltopdf executable
    path_wkhtmltopdf = '/usr/bin/wkhtmltopdf'

    # Convert HTML to PDF
    pdf = pdfkit.from_string(html, False, options=options, configuration=pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf))

    # Create a response object with the PDF file as content
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="farmers-agreement-form.pdf"'

    return response



def farmers_agreement_pdf_generate(request, grower_pk, form_id):

	blf_id = request.user.id

	# Fetch data based on query parameters
	blf_details = BlfProfile.cmobjects.filter(user_id=blf_id).first()
	grower_details = GrowerProfile.cmobjects.filter(id=grower_pk).first()
	form_master_details = FarmersAggreementMaster.cmobjects.filter(id=form_id).first()

	if  not grower_details or not form_master_details:
		return Response({'status': 'Data not found', 'request_status': 0}, status=404)

	form_details = FarmersAggreementForms.cmobjects.filter(
		# aggreement_form_title=form_master_details,
		grower=grower_details
	).first()


	# BLF SIGNATURE
	associated_entity = grower_details.associated_entity.first()
	if associated_entity:
		associated_entity_user = associated_entity.user if associated_entity else None
		# associated_entity_names = [entity.user for entity in associated_entities]
	else:
		associated_entity_user = None

	grower_blf_details = BlfProfile.cmobjects.filter(user=associated_entity_user).first()

	if grower_blf_details:
		blf_signature_details = BlfofficialSignature.cmobjects.filter(blf=grower_blf_details).first()
	else:
		blf_signature_details = None

	if blf_signature_details:
		blf_signature = f"https://tracetea.org/media/{blf_signature_details.blf_grade_official_signature_file}"
	else:
		blf_signature = ""


	# GROWER SIGNATURE

	# form_details = FarmersAggreementForms.cmobjects.filter(
	#     grower=grower_details
	# ).first()

	if form_details:
		stg_signature = f"https://tracetea.org/media/{form_details.farmer_signature_file}"
	else:
		stg_signature = ""



	garden_details = Gardens.cmobjects.filter(grower_id=grower_pk).first()	

	if grower_details:
		grower_username = grower_details.user.username
	else:
		grower_username = ""
	if garden_details:
		production_area=garden_details.production_area
	else:
		production_area="NA"	

	# Prepare context for the template
	context = {
		"blf_details": blf_details,
		"grower_details": grower_details,
		"form_master_details": form_master_details,
		'grower_pk': grower_pk,
		"form_details": form_details,
		"form_master_pk": form_id,
		"production_area":production_area,
		"garden_details" : garden_details,
		"blf_signature" : blf_signature,
		"stg_signature" : stg_signature,
		
	}

	html = render_to_string('farm_diary/agreement_form_download.html', context)

	# Configure pdfkit options
	options = {
		'page-size': 'A4',
		'margin-top': '0.75in',
		'margin-right': '0.75in',
		'margin-bottom': '0.75in',
		'margin-left': '0.75in',
	}

	# Set the path to the wkhtmltopdf executable
	path_wkhtmltopdf = '/usr/bin/wkhtmltopdf'

	# Convert HTML to PDF
	pdf = pdfkit.from_string(html, False, options=options, configuration=pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf))

	# Create a response object with the PDF file as content
	response = HttpResponse(pdf, content_type='application/pdf')
	response['Content-Disposition'] = f'attachment; filename="farmers-agreement-form.pdf"'

	return response












class FarmersAgreementPDFAPIView(APIView):
	def get(self, request):
		# Extract query parameters
		grower_id = self.request.query_params.get('grower_id', None)
		form_id = self.request.query_params.get('form_id', None)
		blf_id = self.request.query_params.get('blf_id', None)

		# Validate query parameters
		if not grower_id or not form_id:
			return Response({'status': 'Missing query parameters', 'request_status': 0}, status=400)

		# Fetch data based on query parameters
		blf_details = BlfProfile.cmobjects.filter(user_id=blf_id).first()
		grower_details = GrowerProfile.cmobjects.filter(id=grower_id).first()
		form_master_details = FarmersAggreementMaster.cmobjects.filter(id=form_id).first()
		print(form_master_details)
		if  not grower_details or not form_master_details:
			return Response({'status': 'Data not found', 'request_status': 0}, status=404)

		form_details = FarmersAggreementForms.cmobjects.filter(
			aggreement_form_title=form_master_details,
			grower=grower_details
		).first()

		garden_details = Gardens.cmobjects.filter(grower_id=grower_id).first()	
		if grower_details:
			grower_username = grower_details.user.username
		else:
			grower_username = ""
		if garden_details:
			production_area=garden_details.production_area
		else:
			production_area="NA"	

		# Prepare context for the template
		context = {
			"blf_details": blf_details,
			"grower_details": grower_details,
			"form_master_details": form_master_details,
			'grower_pk': grower_id,
			"form_details": form_details,
			"form_master_pk": form_id,
			"production_area":production_area,
			"garden_details" : garden_details,
		}


		html = render_to_string('farm_diary/agreement_form_download.html', context)

		# Configure pdfkit options
		options = {
			'page-size': 'A4',
			'margin-top': '0.75in',
			'margin-right': '0.75in',
			'margin-bottom': '0.75in',
			'margin-left': '0.75in',
		}

		# Set the path to the wkhtmltopdf executable
		path_wkhtmltopdf = '/usr/bin/wkhtmltopdf'

		# Convert HTML to PDF
		pdf = pdfkit.from_string(html, False, options=options, configuration=pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf))

		# Create a response object with the PDF file as content
		response = HttpResponse(pdf, content_type='application/pdf')
		response['Content-Disposition'] = f'attachment; filename="farmers-agreement-form.pdf"'

		return response




class FarmersAgreementPDFAPIView_2(APIView):
	# authentication_classes = (TokenAuthentication,)
	# permission_classes = (IsAuthenticated,)
	permission_classes = [AllowAny]
	def get(self, request, *args, **kwargs):
		try:
			# Extract query parameters
			grower_id = self.request.query_params.get('grower_id', None)
			form_id = self.request.query_params.get('form_id', None)
			blf_id = self.request.query_params.get('blf_id', None)

			# Validate query parameters
			if not grower_id or not form_id:
				return Response({'status': 'Missing query parameters', 'request_status': 0}, status=400)

			# Fetch data based on query parameters
			blf_details = BlfProfile.cmobjects.filter(user_id=blf_id).first()
			grower_details = GrowerProfile.cmobjects.filter(id=grower_id).first()
			form_master_details = FarmersAggreementMaster.cmobjects.filter(id=form_id).first()
			print(form_master_details)
			if  not grower_details or not form_master_details:
				return Response({'status': 'Data not found', 'request_status': 0}, status=404)

			form_details = FarmersAggreementForms.cmobjects.filter(
				aggreement_form_title=form_master_details,
				grower=grower_details
			).first()

			garden_details = Gardens.cmobjects.filter(grower_id=grower_id).first()	
			if grower_details:
				grower_username = grower_details.user.username
			else:
				grower_username = ""
			if garden_details:
				production_area=garden_details.production_area
			else:
				production_area="NA"		
			# Prepare context for the template
			context = {
				"blf_details": blf_details,
				"grower_details": grower_details,
				"form_master_details": form_master_details,
				'grower_pk': grower_id,
				"form_details": form_details,
				"form_master_pk": form_id,
				"production_area":production_area
			}

			# Render HTML template
			template_path = 'farm_diary/agreement_form_download.html'
			template = get_template(template_path)
			html = template.render(context)

			# Generate PDF from the rendered HTML using xhtml2pdf
			response = HttpResponse(content_type='application/pdf')
			response['Content-Disposition'] = f'attachment; filename="farmers-agreement-form-{grower_username}.pdf"'

			pisa_status = pisa.CreatePDF(html, dest=response)
			if pisa_status.err:
				return HttpResponse('Error generating PDF', status=500)
			
			return response
		

		except Exception as e:
			return Response({'status': 'error', 'request_status': 0, 'msg': str(e)}, status=400)
		







def map_area_take_screenshot(request):
    # URL of the page you want to take a screenshot of
    user_url = "https://tracetea.org/farmers/map-area-total-pdf/12/"

    # Initialize the UrlboxClient with your API key and secret
    urlbox_client = UrlboxClient(api_key=settings.API_KEY, api_secret=settings.API_SECRET)

    # Take a screenshot of the webpage using UrlboxClient
    response = urlbox_client.get({"url": user_url, "viewport": "1280x1024", "full_page": True, "format": "png"})

    # Set the Content-Type and Content-Disposition headers
    response_content_type = 'image/png'
    response_content_disposition = 'attachment; filename="screenshot.png"'

    # Create the HttpResponse object with the screenshot content
    http_response = HttpResponse(content_type=response_content_type)
    http_response['Content-Disposition'] = response_content_disposition
    http_response.write(response.content)

    return http_response




def digital_signature_app_template(request):

	context ={

	}
	return render(request, 'farm_diary/digital_signature_app_template.html', context)

# NEW Chemical API VIEWS
class FarmDiaryChemicalTypeAPIView(APIView):
	""" chemical Type Master API View """
	authentication_classes = (TokenAuthentication,)
	permission_classes = (IsAuthenticated,)
	def get(self, request):
		id = self.request.query_params.get('id', None)
		all = self.request.query_params.get('all', None)
		order_by = self.request.query_params.get('order_by', '-id')
		search = custom_filters(self.request, {}, [])
		if id:
			list_data = ChemicalType.cmobjects.filter(id=id).first()
			serializer = ChemicalTypeSerializer(list_data)
			return Response(serializer.data)
		list_data = ChemicalType.cmobjects.filter(*search).order_by(*str(order_by).split(","))
		if all == 'true':
			serializer = ChemicalTypeSerializer(list_data, many=True)
			return Response({'results': serializer.data})
		page_size = int(request.query_params.get('page_size', settings.MIN_PAGE_SIZE))
		paginator = Paginator(list_data, page_size)
		page_number = self.request.query_params.get('page', 1)
		page = paginator.get_page(page_number)
		serializer = ChemicalTypeSerializer(page, many=True)
		return Response({
			'count': paginator.count,
			'next': page.next_page_number() if page.has_next() else None,
			'previous': page.previous_page_number() if page.has_previous() else None,
			'results': serializer.data,
		})

class FarmDiaryChemicalDataAPIView(APIView):
	""" chemical Data API View """
	authentication_classes = (TokenAuthentication,)
	permission_classes = (IsAuthenticated,)
	def get(self, request):
		id = self.request.query_params.get('id', None)
		all = self.request.query_params.get('all', None)
		order_by = self.request.query_params.get('order_by', '-id')
		search = {}
		search = custom_filters(self.request, search, [])
		if id:
			list_data = ChemicalData.objects.filter(id=id, is_deleted=False).first()
			serializer = ChemicalDataSerializer(list_data)
			return Response(serializer.data)
		list_data = ChemicalData.objects.filter(is_deleted=False, *search).order_by(*str(order_by).split(","))
		if all == 'true':
			serializer = ChemicalDataSerializer(list_data, many=True)
			return Response({'results': serializer.data})
		page_size = int(request.query_params.get('page_size', settings.MIN_PAGE_SIZE))
		paginator = Paginator(list_data, page_size)
		page_number = self.request.query_params.get('page', 1)
		page = paginator.get_page(page_number)
		serializer = ChemicalDataSerializer(page, many=True)
		return Response({
			'count': paginator.count,
			'next': page.next_page_number() if page.has_next() else None,
			'previous': page.previous_page_number() if page.has_previous() else None,
			'results': serializer.data,
		})

class FarmDiaryUseOfChemicalAPIView(APIView):
	""" Use Of chemical API View """
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
			list_data = UseOfChemical.cmobjects.filter(id=id).first()
			serializer = UseOfChemicalSerializer(list_data)
			return Response(serializer.data)
		list_data = UseOfChemical.cmobjects.filter(*search).order_by(*str(order_by).split(",")).distinct()
		if all == 'true':
			serializer = UseOfChemicalSerializer(list_data, many=True)
			return Response({'results': serializer.data})
		page_size = int(request.query_params.get('page_size', settings.MIN_PAGE_SIZE))
		paginator = Paginator(list_data, page_size)
		page_number = self.request.query_params.get('page', 1)
		page = paginator.get_page(page_number)
		serializer = UseOfChemicalSerializer(page, many=True)
		return Response({
			'count': paginator.count,
			'next': page.next_page_number() if page.has_next() else None,
			'previous': page.previous_page_number() if page.has_previous() else None,
			'results': serializer.data,
		})
	def post(self, request):
		request.data['created_by'] = request.user.id
		serializer = UseOfChemicalSerializer(data=request.data, context={'request': request})
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
		details = UseOfChemical.cmobjects.filter(pk=id).first()
		with transaction.atomic():
			if method.lower() == 'edit':
				if UseOfChemical.cmobjects.filter(pk=id).exists():
					details = UseOfChemical.cmobjects.filter(pk=id).first()
					serializer = UseOfChemicalSerializer(details, data=request.data,
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
				if UseOfChemical.cmobjects.filter(pk=id).exists():
					details = UseOfChemical.cmobjects.get(pk=id)
					details.is_deleted = True
					details.save()
					return Response({'results': {
						'details': UseOfChemical.cmobjects.filter(pk=id).values(),
					},
						'msg': 'Successfully deleted',
						"request_status": 1})
				else:
					raise APIException({'request_status': 1, 'msg': "Something went wrong"})
