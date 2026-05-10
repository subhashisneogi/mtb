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




class CollectionCenterListView(LoginRequiredMixin, CommonMixin, ListView):
    """
    Collection Center List View
    """
    model = CollectionCenter
    context_object_name = 'collection_center_list'
    template_name = 'collection_center_list.html'
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
        name=self.request.GET.get('name')

        if name:
            return qs.filter(name__icontains=name)
       
        return CollectionCenter.objects.filter(created_by_id=self.request.user.id).order_by('-id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context





class CollectionCenterCreateView(LoginRequiredMixin, CreateView, CommonMixin):
    """
    Stock Group Create View
    """
    form_class = CollectionCenterForm
    template_name = 'create_form.html'

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

    def get_success_url(self, **kwargs):
        messages.success(self.request, 'Collection Center Created Successfully')
        return reverse('collection_center:collection_center_list')

    def form_valid(self, form):
    
        context = self.get_context_data()

        with transaction.atomic():
            form.instance.created_by_id = self.request.user.id
            self.object = form.save()

        return super(CollectionCenterCreateView, self).form_valid(form)



    def form_invalid(self, form):
        error_message = 'Error saving the Form, check fields below.'
        messages.error(self.request, error_message)
        return super().form_invalid(form)
	
	

class CollectionCenterUpdateView(LoginRequiredMixin, CommonMixin, UpdateView):
    """
    Collection Center Update View
    """
    model = CollectionCenter
    form_class = CollectionCenterForm
    template_name = 'create_form.html'

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

    def get_success_url(self, **kwargs):
        messages.success(self.request, 'Collection Center Updated Successfully')
        return reverse('collection_center:collection_center_list')

    def get_object(self):
        collection_center_details = CollectionCenter.objects.filter(pk=self.kwargs['collection_center_pk']).first()
        return collection_center_details

    def form_invalid(self, form):
        error_message = 'Error saving the Form, check fields below.'
        messages.error(self.request, error_message)
        return super().form_invalid(form)



# @permission_required_admin
@login_required
def collection_center_details(request, collection_center_pk):

    collection_center_details = CollectionCenter.objects.filter(pk=collection_center_pk).first()

    context = {
        'collection_center_details' : collection_center_details,
    }

    return CommonMixin.render(request, 'collection_center_details.html', context)




@login_required
def CollectionCenterDeleteView(request, collection_center_pk):
    """
    Delete Collection Center View
    """

    # try:
    #     if not request.user.is_superuser:
    #         messages.error(request, 'You have no permission to access the requested resource!')
    #         return redirect(reverse('index'))
    # except AttributeError as error:
    #     messages.error(request, 'You have no permission to access the requested resource!')
    #     return redirect(reverse('index'))

    attribute_details = CollectionCenter.objects.filter(pk=collection_center_pk).first()

    attribute_details.delete()

    messages.success(
        request, 'Collection Center Deleted Successfully')

    return redirect(reverse('collection_center:collection_center_list'))



# @login_required
# @permission_required_admin
# def search_collection_center(request):

#     tea_type=request.GET.get('tea_type')
#     grade=request.GET.get('grade')

#     if tea_type:
#         result = CollectionCenter.objects.filter(Q(tea_type__name=tea_type) | Q(grade=grade))
#     else:
#         result = CollectionCenter.objects.all()
    
#     if grade:
#         result = TeaGradeDetails.objects.filter(Q(tea_type__name=tea_type) | Q(grade=grade))
#     else:
#         result = TeaGradeDetails.objects.all()

#     if tea_type == "all":
#         result = TeaGradeDetails.objects.all()


#     page = request.GET.get('page', 1)
#     paginator = Paginator(result, 10)
    
#     try:
#         collection_center_list = paginator.page(page)
#     except PageNotAnInteger:
#         collection_center_list = paginator.page(1)
#     except EmptyPage:
#         collection_center_list = paginator.page(paginator.num_pages)

#     tea_type_list = TeaType.objects.all().order_by('id')

#     context={
#         'collection_center_list' : collection_center_list,
#         'tea_type_list' : tea_type_list,
#         'grade' : grade,
#         'tea_type' : tea_type,
        
#     }

#     return CommonMixin.render(request, 'collection_center_list.html', context)




