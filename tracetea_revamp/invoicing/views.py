import json

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
from datetime import datetime, timedelta
from django.db import transaction
from datetime import datetime as dt
from master.common import CommonMixin
from .models import *
from django.http import HttpResponse
from xhtml2pdf import pisa
from django.template.loader import get_template
from chemical_data.models import *
from django.http import HttpResponse
from django.template.loader import get_template
from .forms import *
from master.decorators import *
from packaging.models import Packaging
from lot_batch_details.models import LotBatchDetails

from leaf_receipt.models import *

from weighment_supply.models import *

from django.shortcuts import get_object_or_404

from django.db.models import Q


class InvoiceListView(LoginRequiredMixin, CommonMixin, ListView):
    """
    Invoice Management List View
    """
    model = Invoice
    context_object_name = 'invoice_list'
    template_name = 'invoice_list.html'
    paginate_by = 10

    def get(self, request, *args, **kwargs):
        logged_user_type = Profile.objects.filter(user_id=request.user.id).first()
        user_type = logged_user_type.user_type
        try:
            if not str(user_type.name) == "blf" and request.user.is_authenticated:
                messages.error(request, 'You have no permission to access the requested resource!')
                return redirect(reverse('index'))
        except AttributeError as error:
            messages.error(request, 'You have no permission to access the requested resource!')
            return redirect(reverse('index'))
        
        return super().get(request, *args, **kwargs)

    def get_queryset(self, *args, **kwargs):

        qs = super().get_queryset(*args, **kwargs)
        start_date= self.request.GET.get('start_date')
        end_date= self.request.GET.get('end_date')
        invoice_no= self.request.GET.get('invoice_no')

        if start_date and end_date:
            qs = Invoice.cmobjects.filter(invoice_date__range=(
                start_date,
                end_date
            ), created_by_id=self.request.user.id)	
            return qs
        
        if invoice_no:
             qs = Invoice.cmobjects.filter(invoice_no=invoice_no, created_by_id=self.request.user.id).order_by('-id')
             return qs

        return Invoice.cmobjects.filter(created_by_id=self.request.user.id).order_by('-id')

        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # context['type_list'] = Invoice.objects.all().order_by('id')
        
        return context



class InvoiceCreateView(LoginRequiredMixin, CreateView, CommonMixin):
    """
    Invoice  Create View 
    """
    form_class = InvoiceForm
    template_name = 'invoice_create.html'


    def get(self, request, *args, **kwargs):
        logged_user_type = Profile.objects.filter(user_id=request.user.id).first()
        user_type = logged_user_type.user_type
        try:
            if not str(user_type.name) == "blf" and request.user.is_authenticated:
                messages.error(request, 'You have no permission to access the requested resource!')
                return redirect(reverse('index'))
        except AttributeError as error:
            messages.error(request, 'You have no permission to access the requested resource!')
            return redirect(reverse('index'))
        return super().get(request, *args, **kwargs)

    def get_success_url(self, **kwargs):
        messages.success(self.request, 'Invoice  Created Successfully')
        return reverse('invoicing:invoice_list')

    def form_invalid(self, form):
        error_message = 'Error saving the Form, check fields below.'
        messages.error(self.request, error_message)
        return super().form_invalid(form)


    def form_valid(self, form):
        context = self.get_context_data()
        batch_list_form_set = context['batch_list_form_set']

        
        with transaction.atomic():
            if form.is_valid() and batch_list_form_set.is_valid():
                form.instance.created_by_id = self.request.user.id
                self.object = form.save()

                if batch_list_form_set.is_valid():
                    batch_list_form_set.instance = self.object
                    batch_list_form_set.save()
            else:
                return self.render_to_response(context)

        return super(InvoiceCreateView, self).form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super(InvoiceCreateView, self).get_context_data(**kwargs)

        user_id = self.request.user.id

        if self.request.POST:
            formset = BATCH_LIST_FORM_SET(self.request.POST)
            formset.user_id = user_id  # Set the user_id attribute on the formset
        else:
            formset = BATCH_LIST_FORM_SET()
            formset.user_id = user_id  # Set the user_id attribute on the formset

        context['batch_list_form_set'] = formset
        return context

    
    



def load_range(request):

    # print("TEA GRADE ###################")

    logged_user_type = Profile.objects.filter(user_id=request.user.id).first()
    user_type = logged_user_type.user_type
    try:
        if not str(user_type.name) == "blf" and request.user.is_authenticated:
            messages.error(request, 'You have no permission to access the requested resource!')
            return redirect(reverse('index'))
    except AttributeError as error:
        messages.error(request, 'You have no permission to access the requested resource!')
        return redirect(reverse('index'))

    lot_batch_no = request.GET.get('lot_batch_no', None)
    # print(lot_batch_no)
    range_details = LotBatchDetails.cmobjects.filter(lot_batch_no=lot_batch_no).first()
    range = range_details.bag_sl_no_range
    print(range)

    # context = {
    #     "range" : range_details,
    # }

    # if request.is_ajax():
    #     html = render_to_string('load_range_list.html',
    #                             context, request=request)
    # data = {
    #     'html': html
    # }

    data = {
        'value': range
    }

    return JsonResponse(data)


class InvoiceUpdateView(LoginRequiredMixin, CommonMixin, UpdateView):
    """
    Invoice Management Create and Update View @vivek
    """
    model = Invoice
    form_class = InvoiceForm
    template_name = 'invoice_create.html'

    def get(self, request, *args, **kwargs):
        logged_user_type = Profile.objects.filter(user_id=request.user.id).first()
        user_type = logged_user_type.user_type
        try:
            if not str(user_type.name) == "blf" and request.user.is_authenticated:
                messages.error(request, 'You have no permission to access the requested resource!')
                return redirect(reverse('index'))
        except AttributeError as error:
            messages.error(request, 'You have no permission to access the requested resource!')
            return redirect(reverse('index'))
        return super().get(request, *args, **kwargs)
    
    def get_success_url(self, **kwargs):
        messages.success(self.request, 'Invoice  Updated Successfully')
        return reverse('invoicing:invoice_list')

    def get_object(self, queryset=None):
        invoice_details = Invoice.cmobjects.filter(created_by_id=self.request.user.id, pk=self.kwargs['invoice_pk']).first()
        return invoice_details

    def get_context_data(self, **kwargs):
        context = super(InvoiceUpdateView, self).get_context_data(**kwargs)
        context['invoice_details'] = self.get_object()

        user_id = self.request.user.id

        if self.request.POST:
            formset = BATCH_LIST_FORM_SET(self.request.POST, instance=self.get_object())
            formset.user_id = user_id
                   
        else:
            formset = BATCH_LIST_FORM_SET(instance=self.get_object()    )
            formset.user_id = user_id

        context['batch_list_form_set'] = formset

        return context

    def form_valid(self, form):
        context = self.get_context_data()
        batch_list_form_set = context['batch_list_form_set']
        with transaction.atomic():
            self.created_by_id = self.request.user.id

            self.object = form.save()
            if batch_list_form_set.is_valid():
                batch_list_form_set.instance = self.object
                batch_list_form_set.save()

            if not form.is_valid() or not batch_list_form_set.is_valid():
                # formsets or form is invalid; render the form with error
                return self.render_to_response(context)

        return super(InvoiceUpdateView, self).form_valid(form)
	

@login_required
def invoice_delete(request, invoice_pk):

    logged_user_type = Profile.objects.filter(user_id=request.user.id).first()
    user_type = logged_user_type.user_type
    try:
        if not str(user_type.name) == "blf" and request.user.is_authenticated:
            messages.error(request, 'You have no permission to access the requested resource!')
            return redirect(reverse('index'))
    except AttributeError as error:
        messages.error(request, 'You have no permission to access the requested resource!')
        return redirect(reverse('index'))

    invoice = Invoice.cmobjects.filter(id=invoice_pk).first()
    invoice.is_deleted=True
    invoice.save()
    # user_type = 
    messages.success(
        request, 'Invoice Deleted Successfully')

    return redirect(reverse('invoicing:invoice_list', ))    



@login_required
def invoice_details(request,id):
    result = Invoice.cmobjects.filter(pk=id, created_by_id=request.user.id).first()
    context={
        'invoice_list' : result,
    }
    return CommonMixin.render(request, 'invoice_view.html', context)	


@login_required
def load_supply_date(request):

	id = request.GET.get('id', None)

	weighment_details= WeighmentSupply.cmobjects.filter(pk=id).first()

	print(weighment_details.supply_date)

	supply_date = weighment_details.supply_date

	# suppliers_list = AggregatorProfile.objects.filter(associated_entity__user=request.user).order_by('-id')
	# context ={
	#     'suppliers_list' : suppliers_list,
	# }
	# return render(request, 'weighment/suppliers_dropdown_list_options.html', context)


	data = {
		"value" : supply_date,
	}

	return JsonResponse(data)



### INVOICE LIST REPORTS BLF ###
@login_required
def invoice_register_reports(request):
    """ Invoice list register reports  """
    logged_user_type = Profile.objects.filter(user_id=request.user.id).first()
    user_type = logged_user_type.user_type
    try:
        if not str(user_type.name) == "blf" and request.user.is_authenticated:
            messages.error(request, 'You have no permission to access the requested resource!')
            return redirect(reverse('index'))
    except AttributeError as error:
        messages.error(request, 'You have no permission to access the requested resource!')
        return redirect(reverse('index'))

    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if start_date and end_date:
        result = Invoice.cmobjects.filter(invoice_date__range=(
                start_date,
                end_date
            ), created_by_id=request.user.id).order_by('-id')   
    else:
        result = Invoice.cmobjects.filter(created_by_id=request.user.id).order_by('-id')
    
    page = request.GET.get('page', 1)
    paginator = Paginator(result, 10)
    try:
        result = paginator.page(page)
    except PageNotAnInteger:
        result = paginator.page(1)
    except EmptyPage:
        result = paginator.page(paginator.num_pages)

    context= {
        "start_date" : start_date,
        "end_date" : end_date,
        "result" : result,
    }

    return CommonMixin.render(request, "invoice_register_reports.html", context)



### INVOICE LIST REPORTS ADMIN ###
@login_required
def invoice_register_reports_admin(request):
    """ Invoice list register reports  """

    region_list = Region.cmobjects.all()
    region = request.GET.get('region')
    entity_id = request.GET.get('entity_id')

    if region:
        entity_list = BlfProfile.cmobjects.filter(region_id=region).order_by('-id')
    else:
        entity_list = None

    if region and entity_id:
        blf_details = BlfProfile.cmobjects.filter(id=entity_id).first()
        user_details = User.objects.filter(username=blf_details.user).first()
        user_id = user_details.pk
        blf_username = blf_details.user
        blf_name = blf_details.entity_unit
    else:
        blf_username = ""
        blf_name = ""
        user_id = request.user.id
        blf_details = None

    logged_user_type = Profile.objects.filter(user_id=request.user.id).first()
    user_type = logged_user_type.user_type
    # try:
    #     if not str(user_type.name) == "ADMIN" and request.user.is_authenticated:
    #         messages.error(request, 'You have no permission to access the requested resource!')
    #         return redirect(reverse('index'))
    # except AttributeError as error:
    #     messages.error(request, 'You have no permission to access the requested resource!')
    #     return redirect(reverse('index'))

    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if start_date and end_date:
        result = Invoice.cmobjects.filter(invoice_date__range=(
                start_date,
                end_date
            ), created_by_id=user_id).order_by('-id')   
    else:
        result = Invoice.cmobjects.filter(created_by_id=user_id).order_by('-id')

    page = request.GET.get('page', 1)
    paginator = Paginator(result, 10)
    try:
        result = paginator.page(page)
    except PageNotAnInteger:
        result = paginator.page(1)
    except EmptyPage:
        result = paginator.page(paginator.num_pages)

    context= {
        "start_date" : start_date,
        "end_date" : end_date,
        "result" : result,
        "region_list" : region_list,
        "region" : region,
        "entity_id" : entity_id,
        "blf_name" : blf_name,
        "blf_username" : blf_username,
        "user_type" : user_type,
        "entity_list" : entity_list,

    }

    return CommonMixin.render(request, "invoice_register_reports.html", context)






# REPORTS PDF GENERATE
@login_required
def invoice_register_reports_pdf(request):
    """ Labour Data generate pdf View """
    logged_user_type = Profile.objects.filter(user_id=request.user.id).first()
    user_type = logged_user_type.user_type
    try:
        if not str(user_type.name) == "blf" and str(user_type.name) == "ADMIN" and  request.user.is_authenticated:
            messages.error(request, 'You have no permission to access the requested resource!')
            return redirect(reverse('index'))
    except AttributeError as error:
        messages.error(request, 'You have no permission to access the requested resource!')
        return redirect(reverse('index'))


    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if start_date and end_date:
        result = Invoice.cmobjects.filter(invoice_date__range=(
                start_date,
                end_date
            ), created_by_id=request.user.id).order_by('-id')   
    else:
        result = Invoice.cmobjects.filter(created_by_id=request.user.id).order_by('-id')

    blf_profile = BlfProfile.objects.filter(user=request.user).first()
    
    minimum_date = datetime.strptime(str(start_date), "%Y-%m-%d") if start_date else start_date
    maximum_date = datetime.strptime(str(end_date), "%Y-%m-%d") if end_date else end_date

    if not start_date:
        result_date = result.aggregate(min_date=Min('invoice_date'))
        minimum_date = result_date['min_date']

    if not end_date:
        result_date = result.aggregate(max_date=Max('invoice_date'))
        maximum_date = result_date['max_date']

    context= {
        "start_date" : minimum_date,
        "end_date" : maximum_date,
        "result" : result,
        "blf_profile": blf_profile,
    }

    
    # return CommonMixin.render(request, "blf_reports_pdf/invoice_register_reports_pdf.html", context)

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

    # Create an HTML template
    template_name = 'blf_reports_pdf/invoice_register_reports_pdf.html'
    html = render_to_string(template_name, context)

    config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)

    # Generate PDF
    pdf = pdfkit.from_string(html, False, options, configuration=config)

    # Create HTTP response
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="invoice_register_reports_pdf.pdf"'

    return response




# INVOIVCE PDF FOR ADMIN
@login_required
def invoice_register_reports_pdf_admin(request):
    """ Labour Data generate pdf View ADMIN """
    
    region_list = Region.cmobjects.all()

    region = request.GET.get('region')
    entity_id = request.GET.get('entity_id')

    if region and entity_id:
        blf_profile = BlfProfile.cmobjects.filter(id=entity_id).first()
        user_details = User.objects.filter(username=blf_profile.user).first()
        user_id = user_details.pk
        blf_username = blf_profile.user
        blf_name = blf_profile.entity_unit
    else:
        blf_username = ""
        blf_name = ""
        user_id = request.user.id
        blf_profile = None

    logged_user_type = Profile.objects.filter(user_id=request.user.id).first()
    user_type = logged_user_type.user_type

    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if start_date and end_date:
        result = Invoice.cmobjects.filter(invoice_date__range=(
                start_date,
                end_date
            ), created_by_id=user_id).order_by('-id')   
    else:
        result = Invoice.cmobjects.filter(created_by_id=user_id).order_by('-id')

    minimum_date = datetime.strptime(str(start_date), "%Y-%m-%d") if start_date else start_date
    maximum_date = datetime.strptime(str(end_date), "%Y-%m-%d") if end_date else end_date

    if not start_date:
        result_date = result.aggregate(min_date=Min('invoice_date'))
        minimum_date = result_date['min_date']

    if not end_date:
        result_date = result.aggregate(max_date=Max('invoice_date'))
        maximum_date = result_date['max_date']


    context= {
        "start_date" : minimum_date,
        "end_date" : maximum_date,
        "result" : result,
        "blf_profile": blf_profile
    }

    # print("***********************result", result)

    # return CommonMixin.render(request, "blf_reports_pdf/invoice_register_reports_pdf.html", context)

    # # Create a response with PDF content
    # response = HttpResponse(content_type='application/pdf')
    # response['Content-Disposition'] = f'attachment; filename="invoice_register_reports_pdf.pdf"'

    # # Create an HTML tem    plate
    # template = get_template('blf_reports_pdf/invoice_register_reports_pdf.html')
    # html = template.render(context)  # Replace with your template context data

    # # Generate PDF
    # pisa.CreatePDF(html, dest=response) 
    # return response


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

    # Create an HTML template
    template_name = 'blf_reports_pdf/invoice_register_reports_pdf.html'
    html = render_to_string(template_name, context)

    config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)

    # Generate PDF
    pdf = pdfkit.from_string(html, False, options, configuration=config)

    # Create HTTP response
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="invoice_register_reports_pdf.pdf"'

    return response









# INVOIVCE PDF FOR ADMIN
@login_required
def invoice_register_reports_pdf_admin_backup(request):
    """ Labour Data generate pdf View ADMIN """

    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    region = request.GET.get('region')
    entity_id = request.GET.get('entity_id')

    print("region", region)
    print("entity_id", entity_id)


    if region and entity_id:
        blf_details = BlfProfile.cmobjects.filter(id=entity_id).first()
        user_details = User.objects.filter(username=blf_details.user).first()
        user_id = user_details.pk
        blf_username = blf_details.user
        blf_name = blf_details.entity_unit
    else:
        blf_username = ""
        blf_name = ""
        user_id = request.user.id


    logged_user_type = Profile.objects.filter(user_id=user_id).first()
    user_type = logged_user_type.user_type

    # try:
    #     if not str(user_type.name) == "ADMIN" and  request.user.is_authenticated:
    #         messages.error(request, 'You have no permission to access the requested resource!')
    #         return redirect(reverse('index'))
    # except AttributeError as error:
    #     messages.error(request, 'You have no permission to access the requested resource!')
    #     return redirect(reverse('index'))

    from django.http import HttpResponse
    from xhtml2pdf import pisa
    from django.template.loader import get_template


    if start_date and end_date:
        result = Invoice.cmobjects.filter(invoice_date__range=(
                start_date,
                end_date
            ), created_by_id=request.user.id).order_by('-id')   
    else:
        result = Invoice.cmobjects.filter(created_by_id=request.user.id).order_by('-id')


    context= {
        "start_date" : start_date,
        "end_date" : end_date,
        "result" : result,
    }

    print("***********************result", result)

    # Create a response with PDF content
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_register_reports_pdf.pdf"'

    # Create an HTML tem    plate
    template = get_template('blf_reports_pdf/invoice_register_reports_pdf.html')
    html = template.render(context)  # Replace with your template context data

    # Generate PDF
    pisa.CreatePDF(html, dest=response) 
    return response











# BACKWARD TRACEBILITY REPORTS DETAILS
@login_required
def backward_traceability_report(request):
    """ Backward Tracebility Report """
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    invoice_no = request.GET.get('invoice_no')
    entity_id = request.GET.get('entity_id')
    region = request.GET.get('region')


    blf_list = BlfProfile.cmobjects.filter(region=region)


    user_details = Profile.objects.filter(user_id=request.user.id).first()
    logged_user_type = str(user_details.user_type)

    if logged_user_type == "ADMIN" and entity_id:
        blf_details = BlfProfile.cmobjects.filter(id=entity_id).first()
        user_details = User.objects.filter(username=blf_details).first()
        user_id = user_details.pk
        blf_name = blf_details.entity_unit
    else:
        user_id = request.user.id
        blf_name = ""

    # print("logged user ID #######",user_id)

    filter = {"created_by_id": user_id}
    if start_date and end_date:
        filter["invoice_date__range"] = (start_date, end_date)
        # filter["created_by_id"] = user_id
    if invoice_no:
        filter["invoice_no__icontains"] = invoice_no
        # filter["created_by_id"] = user_id

    result = Invoice.cmobjects.filter(**filter)

    page = request.GET.get('page', 1)
    paginator = Paginator(result, 10)
    try:
        result = paginator.page(page)
    except PageNotAnInteger:
        result = paginator.page(1)
    except EmptyPage:
        result = paginator.page(paginator.num_pages)

    region_list = Region.cmobjects.all()


    context= {
        "start_date" : start_date,
        "end_date" : end_date,
        "result" : result,
        "region_list" : region_list,
        "region" : region,
        "entity_id" : entity_id,
        "blf_name" : str(blf_name),
        "blf_list" : blf_list,
    }
    return CommonMixin.render(request, "backward_traceability_report.html", context)




@login_required
def admin_backward_traceability_details(request, id, entity_id):

    from django.db.models import F, ExpressionWrapper, fields

    invoice_details = Invoice.cmobjects.filter(id=id).first()
    invoice_date = invoice_details.invoice_date
    package_details = Packaging.cmobjects.filter(invoice_no_id=id).first()
    lot_details_list = BatchList.objects.filter(invoice_no_id=id).order_by('-id')


    # Calculate the date range for data retrieval
    invoice_date = invoice_date  # Replace this with the actual invoice date
    start_date = invoice_date - timedelta(days=4)  # 4 days before the invoice date
    end_date = invoice_date - timedelta(days=2)  # 2 days before the invoice date

    blf_details = BlfProfile.cmobjects.filter(id=entity_id).first()
    user_details = User.objects.filter(username=blf_details).first()
    user_id = user_details.pk
    
    # if logged_user_type == "ADMIN":
    #     user_id = request.user.id
    # else:
    #     user_id = request.user.id

    # Use the calculated date range to fetch the data
    agg_supplier_list = LeafCollection.objects.filter(supply_date__range=(
            start_date,
            end_date
        ), supplier_type__exact="aggregator", created_by_id=user_id).order_by('-id')

    leaf_collections = LeafCollection.objects.filter(supply_date__range=(
            start_date,
            end_date
        ), supplier_type__exact="grower", created_by_id=user_id).order_by('-id') 
    

    # Retrieve LeafCollection records for the given invoice_no_id
    # leaf_collections = LeafCollection.objects.filter(supplier_type="grower", supply_id_id=id)

    grower_data_list = []

    for leaf_collection in leaf_collections:
        grower = leaf_collection.grower
        grower_user = leaf_collection.grower.user
        nt_wght = leaf_collection.nt_wght
        plucking_data = leaf_collection.plucking_data

        supply_date = leaf_collection.supply_date

        # print("Supply Date", supply_date)
        # Retrieve the list of UseOfChemical records for this grower
        use_of_chemical_list = UseOfChemical.objects.filter(grower=grower)

        # Retrieve the closest PluckingData details for the given grower and supply_date
        closest_plucking_data = PluckingData.objects.filter(
            grower=grower,
            date__lte=supply_date
        ).annotate(date_difference=ExpressionWrapper(
            supply_date - F('date'), output_field=fields.DurationField()
        )).order_by('date_difference').first()


        if closest_plucking_data:
            closest_plucking_data_details = closest_plucking_data  # No need for .date here
            print("Closest Plucking Details###############", closest_plucking_data_details.date)
        else:
            closest_plucking_data_details = None

        # plucking_details = PluckingData.cmobjects.filter(grower=grower).
        grower_data = {
            'grower_name': grower.name,  # Replace 'name' with the actual field name of grower's name
            "supply_date" : supply_date,
            'nt_wght': nt_wght,
            'plucking_data': plucking_data,
            'use_of_chemical_list': use_of_chemical_list,
            "grower_user" : grower_user,
            "plucking_data_details" : closest_plucking_data_details,
        }

        grower_data_list.append(grower_data)                    


    # Grower Data list by Aggregators chalan ID
    agg_grower_list = []
    for leaf_collection in agg_supplier_list:
        # print("supply_id ##### ***", leaf_collection.supply_id.supply_challan_id)
        nt_wght = leaf_collection.nt_wght
        plucking_data = leaf_collection.plucking_data
        supply_date = leaf_collection.supply_date
        supply_id = leaf_collection.supply_id
        grower_supply_details = GrowerDetailsSupply.objects.filter(supply_id=supply_id)

        for grower_item in grower_supply_details:
            # Extracting fields from GrowerDetailsSupply
            grower_name = grower_item.grower.name
            grower_user = grower_item.grower.user

            use_of_chemical_list = UseOfChemical.objects.filter(grower=grower_item.grower)
                    # Retrieve the closest PluckingData details for the given grower and supply_date
            closest_plucking_data = PluckingData.objects.filter(
                grower=grower_item.grower,
                date__lte=supply_date
            ).annotate(date_difference=ExpressionWrapper(
                supply_date - F('date'), output_field=fields.DurationField()
            )).order_by('date_difference').first()

            if closest_plucking_data:
                closest_plucking_data_details = closest_plucking_data  # No need for .date here
                # print("Closest Plucking Details###############", closest_plucking_data_details.date)
            else:
                closest_plucking_data_details = None

            grower_data = {
                'grower_name': grower_name,  
                "supply_date" : supply_date,
                'nt_wght': nt_wght,
                'plucking_data': plucking_data,
                'use_of_chemical_list': use_of_chemical_list,
                "grower_user" : grower_user,
                "plucking_data_details" : closest_plucking_data_details,
            }
            agg_grower_list.append(grower_data)


    final_grower_list = grower_data_list + agg_grower_list

    context= {
        "invoice_details" : invoice_details,
        "invoice_date" : invoice_date,
        "package_details" : package_details,
        "lot_details" : lot_details_list,
        "agg_supplier_list" : agg_supplier_list,
        "grower_data_list" : final_grower_list,
        "start_date" : start_date,
        "end_date" : end_date,
        # 'use_of_chemical_list' : use_of_chemical_list,
    }

    return CommonMixin.render(request, "backward_traceability_details.html", context)




@login_required
def backward_traceability_details(request, id):

    from django.db.models import F, ExpressionWrapper, fields

    invoice_details = Invoice.cmobjects.filter(id=id).first()
    invoice_date = invoice_details.invoice_date
    package_details = Packaging.cmobjects.filter(invoice_no_id=id).first()
    lot_details_list = BatchList.objects.filter(invoice_no_id=id).order_by('-id')

    # print("REQUEST USER ID #########", request.user.id)
    # print(id)
    # print(lot_details_list)
    # print("package_details",package_details)
    # end_date = datetime.now()
    # start_date = end_date - timedelta(days=4)

    # Calculate the date range for data retrieval
    invoice_date = invoice_date  # Replace this with the actual invoice date
    start_date = invoice_date - timedelta(days=4)  # 4 days before the invoice date
    end_date = invoice_date - timedelta(days=2)  # 2 days before the invoice date


    user_details = Profile.objects.filter(user_id=request.user.id).first()
    logged_user_type = str(user_details.user_type)
    
    if logged_user_type == "ADMIN":
        user_id = request.user.id
    else:
        user_id = request.user.id

    # Use the calculated date range to fetch the data
    agg_supplier_list = LeafCollection.objects.filter(supply_date__range=(
            start_date,
            end_date
        ), supplier_type__exact="aggregator", created_by_id=request.user.id).order_by('-id')


    leaf_collections = LeafCollection.objects.filter(supply_date__range=(
            start_date,
            end_date
        ), supplier_type__exact="grower", created_by_id=request.user.id).order_by('-id') 
    

    # Retrieve LeafCollection records for the given invoice_no_id
    # leaf_collections = LeafCollection.objects.filter(supplier_type="grower", supply_id_id=id)

    grower_data_list = []

    for leaf_collection in leaf_collections:
        grower = leaf_collection.grower
        grower_user = leaf_collection.grower.user
        nt_wght = leaf_collection.nt_wght
        plucking_data = leaf_collection.plucking_data

        supply_date = leaf_collection.supply_date

        print("Supply Date", supply_date)
        # Retrieve the list of UseOfChemical records for this grower
        use_of_chemical_list = UseOfChemical.objects.filter(grower=grower)

        # plucking_data_details = PluckingData.objects.filter(
        #     grower=grower,
        #     date__range=(supply_date - timedelta(days=5), supply_date + timedelta(days=5))
        # ).first()

        # plucking_data_details = PluckingData.objects.filter(
        #     grower=grower
        # ).annotate(date_difference=ExpressionWrapper(
        #     F('date') - supply_date, output_field=fields.DurationField()
        # )).order_by('date_difference').first()

        # if plucking_data_details:
        #     print("Plucking Details###############", plucking_data_details.date)


        # Retrieve the closest PluckingData details for the given grower and supply_date
        # closest_plucking_data = PluckingData.objects.filter(
        #     grower=grower,
        #     date__lt=supply_date  # Filter to get dates before the supply_date
        # ).annotate(date_difference=ExpressionWrapper(
        #     supply_date - F('date'), output_field=fields.DurationField()
        # )).aggregate(closest_date=Max('date'))

        # Retrieve the closest PluckingData details for the given grower and supply_date
        closest_plucking_data = PluckingData.objects.filter(
            grower=grower,
            date__lte=supply_date
        ).annotate(date_difference=ExpressionWrapper(
            supply_date - F('date'), output_field=fields.DurationField()
        )).order_by('date_difference').first()


        if closest_plucking_data:
            closest_plucking_data_details = closest_plucking_data  # No need for .date here
            # print("Closest Plucking Details###############", closest_plucking_data_details.date)
        else:
            closest_plucking_data_details = None

        # plucking_details = PluckingData.cmobjects.filter(grower=grower).

        grower_data = {
            'grower_name': grower.name,  # Replace 'name' with the actual field name of grower's name
            "supply_date" : supply_date,
            'nt_wght': nt_wght,
            'plucking_data': plucking_data,
            'use_of_chemical_list': use_of_chemical_list,
            "grower_user" : grower_user,
            "plucking_data_details" : closest_plucking_data_details,
        }

        grower_data_list.append(grower_data)


    # Grower Data list by Aggregators chalan ID
    agg_grower_list = []
    for leaf_collection in agg_supplier_list:
        # print("supply_id ##### ***", leaf_collection.supply_id.supply_challan_id)
        nt_wght = leaf_collection.nt_wght
        plucking_data = leaf_collection.plucking_data
        supply_date = leaf_collection.supply_date
        supply_id = leaf_collection.supply_id
        grower_supply_details = GrowerDetailsSupply.objects.filter(supply_id=supply_id)

        for grower_item in grower_supply_details:
            # Extracting fields from GrowerDetailsSupply
            grower_name = grower_item.grower.name
            grower_user = grower_item.grower.user

            use_of_chemical_list = UseOfChemical.objects.filter(grower=grower_item.grower)
                    # Retrieve the closest PluckingData details for the given grower and supply_date
            closest_plucking_data = PluckingData.objects.filter(
                grower=grower_item.grower,
                date__lte=supply_date
            ).annotate(date_difference=ExpressionWrapper(
                supply_date - F('date'), output_field=fields.DurationField()
            )).order_by('date_difference').first()


            if closest_plucking_data:
                closest_plucking_data_details = closest_plucking_data  # No need for .date here
                # print("Closest Plucking Details###############", closest_plucking_data_details.date)
            else:
                closest_plucking_data_details = None

            grower_data = {
                'grower_name': grower_name,  
                "supply_date" : supply_date,
                'nt_wght': nt_wght,
                'plucking_data': plucking_data,
                'use_of_chemical_list': use_of_chemical_list,
                "grower_user" : grower_user,
                "plucking_data_details" : closest_plucking_data_details,
            }
            agg_grower_list.append(grower_data)


    final_grower_list = grower_data_list + agg_grower_list


    # print("Grower List #############", grower_data_list)
    # print("AGG Challan Grower List #############", agg_grower_list)
    # print("Final Grower List #############", final_grower_list)


    context= {
        "invoice_details" : invoice_details,
        "invoice_date" : invoice_date,
        "package_details" : package_details,
        "lot_details" : lot_details_list,
        "agg_supplier_list" : agg_supplier_list,
        "grower_data_list" : final_grower_list,
        "start_date" : start_date,
        "end_date" : end_date,
        
        # 'use_of_chemical_list' : use_of_chemical_list,
    }
    return CommonMixin.render(request, "backward_traceability_details.html", context)



################# PDF Generate ###########

import pdfkit

@login_required
def backward_traceability_details_pdf(request, id):

    from django.http import HttpResponse
    from xhtml2pdf import pisa
    from django.template.loader import get_template
    from django.db.models import F, ExpressionWrapper, fields

    invoice_details = Invoice.cmobjects.filter(id=id).first()
    invoice_date = invoice_details.invoice_date
    package_details = Packaging.cmobjects.filter(invoice_no_id=id).first()
    lot_details_list = BatchList.objects.filter(invoice_no_id=id).order_by('-id')

    blf_profile = BlfProfile.objects.filter(user=request.user).first()

    # print(id)
    # print(lot_details_list)
    # print("package_details",package_details)
    # end_date = datetime.now()
    # start_date = end_date - timedelta(days=4)

    # Calculate the date range for data retrieval
    invoice_date = invoice_date  # Replace this with the actual invoice date
    start_date = invoice_date - timedelta(days=4)  # 4 days before the invoice date
    end_date = invoice_date - timedelta(days=2)  # 2 days before the invoice date

    # Use the calculated date range to fetch the data
    agg_supplier_list = LeafCollection.objects.filter(supply_date__range=(
            start_date,
            end_date
        ), supplier_type__exact="aggregator", created_by_id=request.user.id).order_by('-id')


    leaf_collections = LeafCollection.objects.filter(supply_date__range=(
            start_date,
            end_date
        ), supplier_type__exact="grower", created_by_id=request.user.id).order_by('-id') 
    

    # Retrieve LeafCollection records for the given invoice_no_id
    # leaf_collections = LeafCollection.objects.filter(supplier_type="grower", supply_id_id=id)

    grower_data_list = []

    for leaf_collection in leaf_collections:
        grower = leaf_collection.grower
        grower_user = leaf_collection.grower.user
        nt_wght = leaf_collection.nt_wght
        plucking_data = leaf_collection.plucking_data
        supply_date = leaf_collection.supply_date

        # Retrieve the list of UseOfChemical records for this grower
        use_of_chemical_list = UseOfChemical.objects.filter(grower=grower)

        # Retrieve the closest PluckingData details for the given grower and supply_date
        closest_plucking_data = PluckingData.objects.filter(
            grower=grower,
            date__lte=supply_date
        ).annotate(date_difference=ExpressionWrapper(
            supply_date - F('date'), output_field=fields.DurationField()
        )).order_by('date_difference').first()


        if closest_plucking_data:
            closest_plucking_data_details = closest_plucking_data  # No need for .date here
            # print("Closest Plucking Details###############", closest_plucking_data_details.date)
        else:
            closest_plucking_data_details = None

        grower_data = {
            'grower_name': grower.name, 
            "supply_date" : supply_date,
            'nt_wght': nt_wght,
            'plucking_data': plucking_data,
            'use_of_chemical_list': use_of_chemical_list,
            "grower_user" : grower_user,
            "plucking_data_details" : closest_plucking_data_details,
            
        }

        grower_data_list.append(grower_data)



    # Grower Data list by Aggregators chalan ID
    agg_grower_list = []
    for leaf_collection in agg_supplier_list:
        # print("supply_id ##### ***", leaf_collection.supply_id.supply_challan_id)
        nt_wght = leaf_collection.nt_wght
        plucking_data = leaf_collection.plucking_data
        supply_date = leaf_collection.supply_date
        supply_id = leaf_collection.supply_id
        grower_supply_details = GrowerDetailsSupply.objects.filter(supply_id=supply_id)

        for grower_item in grower_supply_details:
            # Extracting fields from GrowerDetailsSupply
            grower_name = grower_item.grower.name
            grower_user = grower_item.grower.user

            use_of_chemical_list = UseOfChemical.objects.filter(grower=grower_item.grower)
                    # Retrieve the closest PluckingData details for the given grower and supply_date
            closest_plucking_data = PluckingData.objects.filter(
                grower=grower_item.grower,
                date__lte=supply_date
            ).annotate(date_difference=ExpressionWrapper(
                supply_date - F('date'), output_field=fields.DurationField()
            )).order_by('date_difference').first()


            if closest_plucking_data:
                closest_plucking_data_details = closest_plucking_data  # No need for .date here
                # print("Closest Plucking Details###############", closest_plucking_data_details.date)
            else:
                closest_plucking_data_details = None

            grower_data = {
                'grower_name': grower_name,  
                "supply_date" : supply_date,
                'nt_wght': nt_wght,
                'plucking_data': plucking_data,
                'use_of_chemical_list': use_of_chemical_list,
                "grower_user" : grower_user,
                "plucking_data_details" : closest_plucking_data_details,
            }
            agg_grower_list.append(grower_data)


    final_grower_list = grower_data_list + agg_grower_list


    context= {
        "blf_profile" : blf_profile,
        "invoice_details" : invoice_details,
        "invoice_date" : invoice_date,
        "package_details" : package_details,
        "lot_details" : lot_details_list,
        "agg_supplier_list" : agg_supplier_list,
        "grower_data_list" : final_grower_list,
        "start_date" : start_date,
        "end_date" : end_date,
        # 'use_of_chemical_list' : use_of_chemical_list,
    }


    # # Create a response with PDF content
    # response = HttpResponse(content_type='application/pdf')
    # response['Content-Disposition'] = f'attachment; filename="backward_traceability_details_pdf.pdf"'

    # # Create an HTML tem    plate
    # template = get_template('blf_reports_pdf/backward_traceability_details_pdf.html')
    # html = template.render(context)  # Replace with your template context data

    # # Generate PDF
    # pisa.CreatePDF(html, dest=response) 
    # return response



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

    # Create an HTML template
    template_name = 'blf_reports_pdf/backward_traceability_details_pdf.html'
    html = render_to_string(template_name, context)

    config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)

    # Generate PDF
    pdf = pdfkit.from_string(html, False, options, configuration=config)

    # Create HTTP response
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="backward-traceability-details-pdf.pdf"'

    return response



# def forward_traceability_report(request):
#     start_date = request.GET.get('start_date')
#     end_date = request.GET.get('end_date')
#     grower_id = request.GET.get('grower_id')

#     print("GROWER ID", grower_id)

#     blf_details = BlfProfile.objects.filter(user_id=request.user.id).first()
#     grower_list = GrowerProfile.cmobjects.filter(associated_entity=blf_details).order_by('-id')

#     if start_date and end_date and grower_id:
#         user_details = GrowerProfile.cmobjects.filter(id=grower_id).first()
#         print("USER ID ##########################",user_details.user.id)
#         result = SupplyManagement.cmobjects.all()
#         print("result $$$$$$$$$$$$$$$$$$$$", result)

#     else:
#         result = ""

#     grower_supplied_from_to = []
#     for item in result:
#         grower_supplied_from_to.append(item)

#     print("Grower Supplied From and TO #####", grower_supplied_from_to)
    

#     invoive_after_2_4_days = []
#     packaging_list =[]
#     for item in grower_supplied_from_to:
#         print("SUPPLY date :", item.date_of_supply)
#         start_date = item.date_of_supply + timedelta(days=2)  # 4 days before the invoice date
#         end_date = item.date_of_supply + timedelta(days=4)  # 2 days before the invoice date
#         print("START DATE", start_date)
#         print("END DATE", end_date)
#         invloice_lists = Invoice.cmobjects.filter(invoice_date__range=(
#             start_date,
#             end_date
#         ),)
#         invloice_list = Invoice.cmobjects.filter(invoice_date__range=(
#             start_date,
#             end_date
#         ),).values()

#         for i in invloice_lists:
#             print(i)
#             packaging_lists = Packaging.cmobjects.filter(invoice_no_id=i.id)
#             print("packagining LIST #############", packaging_lists)
#             # invoive_after_2_4_days.append(packaging_lists)

#         invoive_after_2_4_days.append(invloice_list)    

    
#     # print("invlice reports", invoive_after_2_4_days)
#     page = request.GET.get('page', 1)
#     paginator = Paginator(result, 10)

#     try:
#         result = paginator.page(page)
#     except PageNotAnInteger:
#         result = paginator.page(1)
#     except EmptyPage:
#         result = paginator.page(paginator.num_pages)


#     context= {
#         "start_date" : start_date,
#         "end_date" : end_date,
#         # "result" : result,
#         'grower_list' : grower_list,
#         # "invoive_after_2_4_days" : invoive_after_2_4_days,
#         "grower_id": grower_id,
#         "result" : result,
#     }

#     return CommonMixin.render(request, "forward_traceability_report.html", context)




#FORWARD TRACEBILITY REPORT
@login_required
# @permission_required_admin
def forward_traceability_report(request):
    """ Forward Tracebility Report """

    # print("Grower List", grower_list)
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    grower = request.GET.get('grower_id')

    user_id = request.user
    blf_details = BlfProfile.objects.filter(user_id=request.user.id).first()
    grower_list = GrowerProfile.cmobjects.filter(associated_entity=blf_details).order_by('-id')

    if start_date and end_date and grower:
        grower_details = GrowerProfile.cmobjects.filter(user_id=grower).first()
        result = SupplyManagement.objects.filter(date_of_supply__range=(start_date, end_date), created_by_id=grower, consumer_id=request.user.id)
    else:
        result = ""
        grower_details = None

    # filter = {}
    # if start_date and end_date:
    #     filter["date_of_supply__range"] = (start_date, end_date)
    # if grower:
    #     filter["created_by_id"] = grower_user_id

    # result = SupplyManagement.objects.filter(Q(**filter), consumer_id=request.user.id)

    grower_supplied_from_to = []
    for item in result:
        grower_supplied_from_to.append(item)

    invoive_after_2_4_days = []
    if grower_supplied_from_to:

        for item in grower_supplied_from_to:
            start_invoice_date = item.date_of_supply + timedelta(days=2)  # 4 days before the invoice date
            end_invoice_date = item.date_of_supply + timedelta(days=4)  # 2 days before the invoice date
            invloice_lists = Invoice.cmobjects.filter(invoice_date__range=(
                start_invoice_date,
                end_invoice_date
            ), created_by_id=request.user.id)

            invloice_list = Invoice.cmobjects.filter(invoice_date__range=(
                start_invoice_date,
                end_invoice_date
            ), created_by_id=request.user.id).order_by('-id').values()
            invoive_after_2_4_days.append(invloice_list)    

    else:
        start_invoice_date = None
        end_invoice_date = None


    if grower_supplied_from_to:
        # # PACKAGING
        result_items = []
        for invoices_lists in invloice_lists:
            # id = invoices_lists.id
            invoice_no = invoices_lists.invoice_no
            invoice_date = invoices_lists.invoice_date
        
            use_of_chemical_list = Packaging.cmobjects.filter(invoice_no_id=invoices_lists.id).order_by('-id')

            batch_lists = BatchList.objects.filter(invoice_no_id=invoices_lists.id).order_by('-id')            
            invoices_data ={
                "invoice_no" : invoice_no,
                "invoice_date" : invoice_date,
                "use_of_chemical_list" : use_of_chemical_list,
                "batch_lists" : batch_lists,
            }

            result_items.append(invoices_data)
    
    else:
        result_items = None


    # print("FINAL RESULT ITEMS ##########", result_items)


    # result_items = []
    # for invoices_lists in invloice_lists:
    #     id = invoices_lists.id
    #     invoice_no = invoices_lists.invoice_no.id
    #     invoice_date = invoices_lists.invoice_date

    #     # Retrieve the list of packaging records for this invoice
    #     use_of_chemical_list = Packaging.cmobjects.filter(invoice_no_id=invoice_no)

    #     invoices_data ={
    #         "invoice_no" : invoice_no,
    #         "invoice_date" : invoice_date,
    #         "use_of_chemical_list" : use_of_chemical_list,
    #     }
    #     result_items.append(invoices_data)


    # print("invlice reports", invoive_after_2_4_days)
    page = request.GET.get('page', 1)
    paginator = Paginator(result, 10)
    try:
        result = paginator.page(page)
    except PageNotAnInteger:
        result = paginator.page(1)
    except EmptyPage:
        result = paginator.page(paginator.num_pages)

    context= {
        "start_invoice_date" : start_invoice_date,
        "end_invoice_date" : end_invoice_date,
        "result" : result,
        'grower_list' : grower_list,
        "invoive_after_2_4_days" : invoive_after_2_4_days,
        "grower": grower,
        "grower_details" : grower_details,

        # final result
        "result_items" : result_items,
    }

    return CommonMixin.render(request, "forward_traceability_report.html", context)



@login_required
# @permission_required_admin
def forward_traceability_reports_pdf(request):
    """ Forward Tracebility Report PDF Doenload """

    print("###############################################  PDF REPORTS  ################################################################")


    # print("Grower List", grower_list)
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    grower = request.GET.get('grower_id')

    user_id = request.user
    blf_details = BlfProfile.objects.filter(user_id=request.user.id).first()
    grower_list = GrowerProfile.cmobjects.filter(associated_entity=blf_details).order_by('-id')

    if start_date and end_date and grower:
        grower_details = GrowerProfile.cmobjects.filter(user_id=grower).first()
        result = SupplyManagement.objects.filter(date_of_supply__range=(start_date, end_date), created_by_id=grower, consumer_id=request.user.id)
    else:
        result = ""
        grower_details = None

    grower_supplied_from_to = []
    for item in result:
        grower_supplied_from_to.append(item)

    invoive_after_2_4_days = []
    if grower_supplied_from_to:

        for item in grower_supplied_from_to:
            print("SUPPLY date :", item.date_of_supply)
            start_invoice_date = item.date_of_supply + timedelta(days=2)  # 4 days before the invoice date
            end_invoice_date = item.date_of_supply + timedelta(days=4)  # 2 days before the invoice date
            print("START DATE", start_invoice_date)
            print("END DATE", end_invoice_date)
            invloice_lists = Invoice.cmobjects.filter(invoice_date__range=(
                start_invoice_date,
                end_invoice_date
            ), created_by_id=request.user.id)

            invloice_list = Invoice.cmobjects.filter(invoice_date__range=(
                start_invoice_date,
                end_invoice_date
            ), created_by_id=request.user.id).order_by('-id').values()
            invoive_after_2_4_days.append(invloice_list)    

    else:
        start_invoice_date = None
        end_invoice_date = None


    
    if grower_supplied_from_to:
        # # PACKAGING
        result_items = []
        for invoices_lists in invloice_lists:
            # id = invoices_lists.id
            invoice_no = invoices_lists.invoice_no
            invoice_date = invoices_lists.invoice_date
        
            use_of_chemical_list = Packaging.cmobjects.filter(invoice_no_id=invoices_lists.id).order_by('-id')

            batch_lists = BatchList.objects.filter(invoice_no_id=invoices_lists.id).order_by('-id')            
            invoices_data ={
                "invoice_no" : invoice_no,
                "invoice_date" : invoice_date,
                "use_of_chemical_list" : use_of_chemical_list,
                "batch_lists" : batch_lists,
            }

            result_items.append(invoices_data)
    else:
        result_items = None

    context= {
        "start_invoice_date" : start_invoice_date,
        "end_invoice_date" : end_invoice_date,
        "result" : result,
        'grower_list' : grower_list,
        "invoive_after_2_4_days" : invoive_after_2_4_days,
        "grower": grower,
        "grower_details" : grower_details,
        # final result
        "result_items" : result_items,
    }


    print("########################  PDF DWNLAOD FORWARD ######################")

    # Create a response with PDF content
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="forward_traceability_pdf.pdf"'

    # Create an HTML tem    plate
    template = get_template('blf_reports_pdf/forward_traceability_report_pdf.html')
    html = template.render(context)  # Replace with your template context data

    # Generate PDF
    pisa.CreatePDF(html, dest=response) 
    return response



def forward_reports_pdf(request):
    from django.http import HttpResponse
    from xhtml2pdf import pisa
    from django.template.loader import get_template

    # print("Grower List", grower_list)
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    grower = request.GET.get('grower_id')

    user_id = request.user
    blf_details = BlfProfile.objects.filter(user_id=request.user.id).first()
    grower_list = GrowerProfile.cmobjects.filter(associated_entity=blf_details).order_by('-id')

    if start_date and end_date and grower:
        grower_details = GrowerProfile.cmobjects.filter(user_id=grower).first()
        result = SupplyManagement.objects.filter(date_of_supply__range=(start_date, end_date), created_by_id=grower, consumer_id=request.user.id)
    else:
        result = ""
        grower_details = None

    grower_supplied_from_to = []
    for item in result:
        grower_supplied_from_to.append(item)

    invoive_after_2_4_days = []
    if grower_supplied_from_to:

        for item in grower_supplied_from_to:
            print("SUPPLY date :", item.date_of_supply)
            start_invoice_date = item.date_of_supply + timedelta(days=2)  # 4 days before the invoice date
            end_invoice_date = item.date_of_supply + timedelta(days=4)  # 2 days before the invoice date
            print("START DATE", start_invoice_date)
            print("END DATE", end_invoice_date)
            invloice_lists = Invoice.cmobjects.filter(invoice_date__range=(
                start_invoice_date,
                end_invoice_date
            ), created_by_id=request.user.id)

            invloice_list = Invoice.cmobjects.filter(invoice_date__range=(
                start_invoice_date,
                end_invoice_date
            ), created_by_id=request.user.id).order_by('-id').values()
            invoive_after_2_4_days.append(invloice_list)    

    else:
        start_invoice_date = None
        end_invoice_date = None

    if grower_supplied_from_to:
        # # PACKAGING
        result_items = []
        for invoices_lists in invloice_lists:
            # id = invoices_lists.id
            invoice_no = invoices_lists.invoice_no
            invoice_date = invoices_lists.invoice_date
        
            use_of_chemical_list = Packaging.cmobjects.filter(invoice_no_id=invoices_lists.id).order_by('-id')

            batch_lists = BatchList.objects.filter(invoice_no_id=invoices_lists.id).order_by('-id')            
            invoices_data ={
                "invoice_no" : invoice_no,
                "invoice_date" : invoice_date,
                "use_of_chemical_list" : use_of_chemical_list,
                "batch_lists" : batch_lists,
            }

            result_items.append(invoices_data)
    else:
        result_items = None

    context= {
        "start_invoice_date" : start_invoice_date,
        "end_invoice_date" : end_invoice_date,
        "result" : result,
        'grower_list' : grower_list,
        "invoive_after_2_4_days" : invoive_after_2_4_days,
        "grower": grower,
        "grower_details" : grower_details,
        # final result
        "result_items" : result_items,
    }

    # Create a response with PDF content
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="forward_traceability_pdf.pdf"'

    # Create an HTML tem    plate
    template = get_template('blf_reports_pdf/forward_traceability_report_pdf.html')
    html = template.render(context)  # Replace with your template context data

    # Generate PDF
    pisa.CreatePDF(html, dest=response) 
    return response
