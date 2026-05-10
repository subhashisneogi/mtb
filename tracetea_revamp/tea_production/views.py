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
from django.utils.http import url_has_allowed_host_and_scheme

from django.db import transaction

from master.common import CommonMixin
from .models import *
from .forms import *
from user_profile.helpers import soft_delete_instance_for_web

from master.decorators import *


def is_ajax_request(request):
    return request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'


def get_safe_next_url(request, default_url):
    next_url = request.GET.get('next') or request.POST.get('next')
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        return next_url
    return default_url



class TeaGradeListView(LoginRequiredMixin, CommonMixin, ListView):
    """
    Tea Grade List View
    """
    model = TeaGradeDetails
    context_object_name = 'tea_grade_list'
    template_name = 'tea_grade_list.html'
    paginate_by = 10
    
    def get(self, request, *args, **kwargs):
    # checking if the user is customer
        try:
            if not self.request.user.is_superuser:
                messages.error(self.request, 'You have no permission to access the requested resource!')
                return redirect(reverse('index'))
        except AttributeError as error:
            messages.error(self.request, 'You have no permission to access the requested resource!')
            return redirect(reverse('index'))

        return super().get(request, *args, **kwargs)


    def get_queryset(self, *args, **kwargs):
        query = self.request.GET.get('q', '').strip()
        qs = TeaGradeDetails.objects.select_related('tea_type').filter(is_deleted=False)
        if query:
            qs = qs.filter(
                Q(tea_type__name__icontains=query) |
                Q(grade__icontains=query)
            )
        return qs.order_by('-id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tea_type_list'] = TeaType.objects.filter(is_deleted=False).order_by('-id')
        context['search_query'] = self.request.GET.get('q', '').strip()
        context['list_url'] = reverse('tea_production:tea_grade_list')
        context['current_list_url'] = self.request.get_full_path()
        return context

    def render_to_response(self, context, **response_kwargs):
        if is_ajax_request(self.request):
            return render(self.request, 'tea_grade_table.html', context)
        return super().render_to_response(context, **response_kwargs)





class TeaGradeCreateView(LoginRequiredMixin, CreateView, CommonMixin):
    """
    Stock Group Create View
    """
    form_class = TeaGradeForm
    template_name = 'tea_grade_form.html'

    def get(self, request, *args, **kwargs):
    # checking if the user is customer
        try:
            if not self.request.user.is_superuser:
                messages.error(self.request, 'You have no permission to access the requested resource!')
                return redirect(reverse('index'))
        except AttributeError as error:
            messages.error(self.request, 'You have no permission to access the requested resource!')
            return redirect(reverse('index'))
        
        return super().get(request, *args, **kwargs)    

    def get_success_url(self, **kwargs):
        messages.success(self.request, 'Tea Grade Created Successfully')
        return get_safe_next_url(self.request, reverse('tea_production:tea_grade_list'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['next_url'] = get_safe_next_url(self.request, reverse('tea_production:tea_grade_list'))
        return context

    def form_invalid(self, form):
        error_message = 'Error saving the Form, check fields below.'
        messages.error(self.request, error_message)
        return super().form_invalid(form)
	
	

class TeaGradeUpdateView(LoginRequiredMixin, CommonMixin, UpdateView):
    """
    Tea Grade Update View
    """
    model = TeaGradeDetails
    form_class = TeaGradeForm
    template_name = 'tea_grade_form.html'

    def get(self, request, *args, **kwargs):
    # checking if the user is customer
        try:
            if not self.request.user.is_superuser:
                messages.error(self.request, 'You have no permission to access the requested resource!')
                return redirect(reverse('index'))
        except AttributeError as error:
            messages.error(self.request, 'You have no permission to access the requested resource!')
            return redirect(reverse('index'))

        return super().get(request, *args, **kwargs)

    def get_success_url(self, **kwargs):
        messages.success(self.request, 'Tea Grade Updated Successfully')
        return get_safe_next_url(self.request, reverse('tea_production:tea_grade_list'))

    def get_object(self):
        tea_grade_details = TeaGradeDetails.objects.filter(pk=self.kwargs['tea_grade_pk'], is_deleted=False).first()
        return tea_grade_details

    def form_invalid(self, form):
        error_message = 'Error saving the Form, check fields below.'
        messages.error(self.request, error_message)
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['next_url'] = get_safe_next_url(self.request, reverse('tea_production:tea_grade_list'))
        return context



@permission_required_admin
@login_required
def grade_details(request, tea_grade_pk):

    grade_details = TeaGradeDetails.objects.filter(pk=tea_grade_pk, is_deleted=False).first()

    context = {
        'grade_details' : grade_details,
        'next_url': get_safe_next_url(request, reverse('tea_production:tea_grade_list')),
    }

    return CommonMixin.render(request, 'grade_details.html', context)




@login_required
@permission_required_admin
def TeaGradeDeleteView(request, tea_grade_pk):
    """
    Delete Tea Grade View
    """

    try:
        if not request.user.is_superuser:
            messages.error(request, 'You have no permission to access the requested resource!')
            return redirect(reverse('index'))
    except AttributeError as error:
        messages.error(request, 'You have no permission to access the requested resource!')
        return redirect(reverse('index'))

    attribute_details = TeaGradeDetails.objects.filter(pk=tea_grade_pk, is_deleted=False).first()
    return soft_delete_instance_for_web(
        request,
        attribute_details,
        get_safe_next_url(request, reverse('tea_production:tea_grade_list')),
        success_message='Tea Grade Deleted Successfully',
        not_found_message='Tea Grade not found.',
    )



@login_required
@permission_required_admin
def search_tea_grade(request):

    tea_type=request.GET.get('tea_type')
    grade=request.GET.get('grade')

    if tea_type:
        result = TeaGradeDetails.objects.filter(Q(tea_type__name=tea_type) | Q(grade=grade))
    else:
        result = TeaGradeDetails.objects.all()
    
    if grade:
        result = TeaGradeDetails.objects.filter(Q(tea_type__name=tea_type) | Q(grade=grade))
    else:
        result = TeaGradeDetails.objects.all()

    if tea_type == "all":
        result = TeaGradeDetails.objects.all()


    page = request.GET.get('page', 1)
    paginator = Paginator(result, 10)
    
    try:
        tea_grade_list = paginator.page(page)
    except PageNotAnInteger:
        tea_grade_list = paginator.page(1)
    except EmptyPage:
        tea_grade_list = paginator.page(paginator.num_pages)

    tea_type_list = TeaType.objects.all().order_by('id')

    context={
        'tea_grade_list' : tea_grade_list,
        'tea_type_list' : tea_type_list,
        'grade' : grade,
        'tea_type' : tea_type,
        
    }

    return CommonMixin.render(request, 'tea_grade_list.html', context)




