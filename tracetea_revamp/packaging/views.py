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
from master.decorators import *

from django.shortcuts import get_object_or_404

class PackagingListView(LoginRequiredMixin, CommonMixin, ListView):
    """
    Packaging Management List View
    """
    model = Packaging
    context_object_name = 'packaging_list'
    template_name = 'packaging_list.html'
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
        invoice_no= self.request.GET.get('invoice_no')
        if invoice_no:
             qs = Packaging.objects.filter(invoice_no__invoice_no=invoice_no, created_by_id=self.request.user.id).order_by('-id')
             return qs

        return Packaging.cmobjects.filter(created_by_id=self.request.user.id).order_by('-id')

        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # context['type_list'] = Packaging.objects.all().order_by('id')
        return context



class PackagingCreateView(LoginRequiredMixin, CreateView, CommonMixin):
    """
    Packaging  Create View 
    """
    form_class = PackagingForm
    template_name = 'packaging_create.html'

    def get(self, request, *args, **kwargs):

        return super().get(request, *args, **kwargs)

    def get_success_url(self, **kwargs):
        messages.success(self.request, 'Packaging  Created Successfully')
        return reverse('packaging:packaging_list')

    def get_form_kwargs(self):
        kwargs = super(PackagingCreateView, self).get_form_kwargs()
        kwargs['user_id'] = self.request.user.id
        return kwargs

    def form_invalid(self, form):
        error_message = 'Error saving the Form, check fields below.'
        messages.error(self.request, error_message)
        return super().form_invalid(form)

    def form_valid(self, form):
        context = self.get_context_data()
        
        with transaction.atomic():
            form.instance.created_by_id = self.request.user.id

            if form.instance.invoice_no:
                invoice_details = Invoice.cmobjects.filter(invoice_no=form.instance.invoice_no, created_by_id=self.request.user.id).first()
                invoice_details.is_packaged = True
                invoice_details.save()

            self.object = form.save()
            if not form.is_valid() :
                return self.render_to_response(context)   
        return super(PackagingCreateView, self).form_valid(form)

    def get_context_data(self, **kwargs):
        context = super(PackagingCreateView, self).get_context_data(**kwargs)  
        return context
    
    

def load_range(request):
    lot_batch_no = request.GET.get('lot_batch_no', None)
    # print(lot_batch_no)
    range_details = LotBatchDetails.cmobjects.filter(lot_batch_no=lot_batch_no).first()
    range = range_details.bag_sl_no_range

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


class PackagingUpdateView(LoginRequiredMixin, CommonMixin, UpdateView):
    """
    Packaging Management Create and Update View @vivek
    """
    model = Packaging
    form_class = PackagingForm
    template_name = 'packaging_create.html'

    def get(self, request, *args, **kwargs):

        return super().get(request, *args, **kwargs)

    def get_success_url(self, **kwargs):
        messages.success(self.request, 'Packaging  Updated Successfully')
        return reverse('packaging:packaging_list')

    def get_form_kwargs(self):
        kwargs = super(PackagingUpdateView, self).get_form_kwargs()
        packaging_details = Packaging.cmobjects.filter(pk=self.kwargs['packaging_pk'],\
                                     created_by_id=self.request.user.id).first()    
        kwargs['invoice_no_id'] = packaging_details.invoice_no_id
        kwargs['user_id'] = self.request.user.id

        return kwargs

    def get_object(self,queryset=None):
        packaging_details = Packaging.cmobjects.filter(pk=self.kwargs['packaging_pk'], created_by_id=self.request.user.id).first()
        return packaging_details

    def get_context_data(self, **kwargs):
        context = super(PackagingUpdateView, self).get_context_data(**kwargs)
        context['packaging_details'] = self.get_object()
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        packaging_details = Packaging.cmobjects.filter(pk=self.kwargs['packaging_pk'], created_by_id=self.request.user.id).first()
        
        with transaction.atomic():
            self.updated_by_id = self.request.user.id

            invoice_details = Invoice.cmobjects.filter(invoice_no=form.instance.invoice_no,\
                                                    created_by_id=self.request.user.id).first()
            invoice_details.is_packaged = True
            invoice_details.save()
            
            pre_invoice_details = Invoice.cmobjects.filter(id=packaging_details.invoice_no_id,\
                                created_by_id=self.request.user.id).first()
            pre_invoice_details.is_packaged = False
            pre_invoice_details.save()


            
            if not form.is_valid():
                # formsets or form is invalid; render the form with error
                return self.render_to_response(context)

        return super(PackagingUpdateView, self).form_valid(form)
	

@login_required
def packaging_delete(request, packaging_pk):
    packaging = Packaging.cmobjects.filter(id=packaging_pk).first()

    pre_invoice_details = Invoice.cmobjects.filter(id=packaging.invoice_no_id,\
                        created_by_id=request.user.id).first()
    pre_invoice_details.is_packaged = False
    pre_invoice_details.save()

    packaging.delete()


    messages.success(
        request, 'Packaging Deleted Successfully')
    return redirect(request.META['HTTP_REFERER'])   


@login_required
def packaging_details(request, id):
    result = Packaging.cmobjects.filter(pk=id, created_by_id=request.user.id).first()
    context={
        'packaging_list' : result,
    }
    return CommonMixin.render(request, 'packaging_view.html', context)	















