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


class LotBatchListView(LoginRequiredMixin, CommonMixin, ListView):
    """
    Lot/Batch List View
    """
    model = LotBatchDetails
    context_object_name = 'lot_batch_list'
    template_name = 'lot_batch_list.html'
    paginate_by = 5

    def get(self, request, *args, **kwargs):
    # checking if the user is customer
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
        lot_batch_no=self.request.GET.get('lot_batch_no')

        if lot_batch_no:
            return qs.filter(lot_batch_no__icontains=lot_batch_no)
       
        return LotBatchDetails.cmobjects.filter(created_by_id=self.request.user.id).order_by('-id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context





class LotBatchCreateView(LoginRequiredMixin, CreateView, CommonMixin):
    """
    Stock Group Create View
    """
    form_class = LotBatchForm
    template_name = 'lot_create_form.html'

    def get_success_url(self, **kwargs):
        messages.success(self.request, 'Lot/Batch Created Successfully')
        return reverse('lot_batch_details:lot_batch_list')

    def get_form_kwargs(self, **kwargs):
        kwargs = super(LotBatchCreateView, self).get_form_kwargs()
        user = self.request.user
        blf_user = BlfProfile.cmobjects.filter(user=user).first()
        
        kwargs['blf_user_id'] = blf_user.pk

        return kwargs


    def form_valid(self, form):
        # form.instance.user = self.request.user
        context = self.get_context_data()
        print("hjcehc", form.instance.id)
        BagSlNoRange.objects.update_or_create(lot_batch_no_id=form.instance.pk, defaults={
            'bag_sl_no_range': form.instance.bag_sl_no_range,})

        with transaction.atomic():
            form.instance.created_by_id = self.request.user.id
            self.object = form.save()

        if not form.is_valid():
            # formsets or form is invalid; render the form with error
            return self.render_to_response(context)
        
        return super(LotBatchCreateView, self).form_valid(form)


    def form_invalid(self, form):
        error_message = 'Error saving the Form, check fields below.'
        messages.error(self.request, error_message)
        return super().form_invalid(form)
	





	

class LotBatchUpdateView(LoginRequiredMixin, CommonMixin, UpdateView):
    """
    Lot/Batch Update View
    """
    model = LotBatchDetails
    form_class = LotBatchForm
    template_name = 'lot_create_form.html'

    # def get(self, request, *args, **kwargs):
    # checking if the user is customer
        # try:
        #     if not self.request.user.is_superuser:
        #         messages.error(self.request, 'You have no permission to access the requested resource!')
        #         return redirect(reverse('index'))
        # except AttributeError as error:
        #     messages.error(self.request, 'You have no permission to access the requested resource!')
        #     return redirect(reverse('index'))

        # return super().get(request, *args, **kwargs)

    def get_success_url(self, **kwargs):
        messages.success(self.request, 'Lot/Batch Updated Successfully')
        return reverse('lot_batch_details:lot_batch_list')

    def get_object(self):
        tea_lot_batch_details = LotBatchDetails.objects.filter(pk=self.kwargs['lot_batch_pk']).first()
        return tea_lot_batch_details

    def form_invalid(self, form):
        error_message = 'Error saving the Form, check fields below.'
        messages.error(self.request, error_message)
        return super().form_invalid(form)
    
    def get_form_kwargs(self, **kwargs):
        kwargs = super(LotBatchUpdateView, self).get_form_kwargs()
        user = self.request.user
        blf_user = BlfProfile.cmobjects.filter(user=user).first()
        
        kwargs['blf_user_id'] = blf_user

        return kwargs

    def form_valid(self, form):
        # form.instance.user = self.request.user
        context = self.get_context_data()
        
        BagSlNoRange.objects.update_or_create(lot_batch_no_id=form.instance.pk, defaults={
			'bag_sl_no_range': form.instance.bag_sl_no_range,})

        with transaction.atomic():
            self.created_by_id = self.request.user.id
            self.object = form.save()

        if not form.is_valid():
            # formsets or form is invalid; render the form with error
            return self.render_to_response(context)

        return super(LotBatchUpdateView, self).form_valid(form)



# @permission_required_admin
@login_required
def lot_batch_details(request, lot_batch_pk):

    lot_batch_details = LotBatchDetails.objects.filter(pk=lot_batch_pk).first()

    context = {
        'lot_batch_details' : lot_batch_details,
    }

    return CommonMixin.render(request, 'lot_batch_details.html', context)




@login_required
# @permission_required_admin
def LotBatchDeleteView(request, lot_batch_pk):
    """
    Delete Lot/Batch View
    """

    # try:
    #     if not request.user.is_superuser:
    #         messages.error(request, 'You have no permission to access the requested resource!')
    #         return redirect(reverse('index'))
    # except AttributeError as error:
    #     messages.error(request, 'You have no permission to access the requested resource!')
    #     return redirect(reverse('index'))

    details = LotBatchDetails.objects.filter(pk=lot_batch_pk).first()

    details.is_deleted = True

    details.save()

    messages.success(
        request, 'Lot/Batch Deleted Successfully')

    return redirect(reverse('lot_batch_details:lot_batch_list'))








