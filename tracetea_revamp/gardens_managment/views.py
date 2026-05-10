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


from django.db.models import Avg, Value
from django.db.models.functions import Coalesce

from django.db import transaction


from master.common import CommonMixin
from .models import *
from .forms import *
from accounts.forms import CreateUserForm

from django.db.models import FloatField, F

class GardenLisView(LoginRequiredMixin, CommonMixin, ListView):
    """
    Tea Graden List View
    """
    model = Gardens
    context_object_name = 'garden_list'
    template_name = 'garden_list.html'
    paginate_by = 5

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

    def get_queryset(self):
        return Gardens.objects.filter(grower_id=self.kwargs['grower_pk']).order_by('-id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['grower_details'] = GrowerProfile.objects.filter(pk=self.kwargs['grower_pk']).first()
        user_details = User.objects.filter(pk=self.kwargs['grower_pk']).first() 
        context['grower_pk'] = self.kwargs['grower_pk']
        print(self.kwargs['grower_pk'])
        # print(user_details.username)
        return context
    


class GardenCreateView(LoginRequiredMixin, CreateView, CommonMixin):
    """
    Garden Create View
    """
    form_class = GardenForm
    template_name = 'garden_form.html'

    def get(self, request, *args, **kwargs):

        # try:
        #     if request.user.profile.user_type == 'EMPLOYEE':
        #         messages.error(request, 'You have no permission to access the requested resource!')
        #         return redirect(reverse('hr:employee_dashboard'))
        #     elif request.user.profile.user_type == 'CUSTOMER':
        #         messages.error(request, 'You have no permission to access the requested resource!')
        #         return redirect(reverse('crm:customer_dashboard'))
        # except AttributeError as error:
        #     messages.error(request, 'You have no permission to access the requested resource!')
        #     return redirect(reverse('index'))
        
        return super().get(request, *args, **kwargs)


    def get_success_url(self, **kwargs):
        messages.success(self.request, 'Garden Created Successfully')
        grower_details = GrowerProfile.objects.filter(user_id=self.kwargs['grower_pk']).first()
        print("$$$$$$$$$############## Grower ID")
        print(grower_details.id )

        return reverse('gardens_managment:garden_details', kwargs={"grower_pk": grower_details.id } )
    

    def form_valid(self, form):
        context = self.get_context_data()

        plot_details_form_set = context['plot_details_form_set']

        with transaction.atomic():
            self.object = form.save()

            if plot_details_form_set.is_valid():
                plot_details_form_set.instance = self.object
                plot_details_form_set.save()


            if not form.is_valid() or not plot_details_form_set.is_valid():
                # formsets or form is invalid; render the form with error
                return self.render_to_response(context)

        return super(GardenCreateView, self).form_valid(form)


    def form_invalid(self, form):
        error_message = 'Error saving the Form, check fields below.'
        messages.error(self.request, error_message)
        return super().form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super(GardenCreateView, self).get_context_data(**kwargs)  
        grower_details = GrowerProfile.objects.filter(user_id=self.kwargs['grower_pk']).first()
        context['grower_id'] = grower_details.id

        if self.request.POST:
            context['plot_details_form_set'] = PLOT_DETAILS_FORM_SET(self.request.POST)
            # context['division_form_set'] = DIVISION_FORM_SET(self.request.POST)            
        else:
            context['plot_details_form_set'] = PLOT_DETAILS_FORM_SET()
            # context['division_form_set'] = DIVISION_FORM_SET()
            
        return context
    



class GardenDetailsUpdateView(LoginRequiredMixin, CommonMixin, UpdateView):

    model = Gardens
    form_class = GardenForm
    template_name = 'garden_form.html'

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
        messages.success(self.request, 'Garden Updated Successfully')
        grower_details = GrowerProfile.objects.filter(user_id=self.kwargs['grower_pk']).first()

        print(grower_details)

        return reverse('gardens_managment:garden_details', kwargs={"grower_pk": self.kwargs['grower_pk'] } )
        # return reverse('gardens_managment:garden_details', kwargs={"grower_pk": grower_details })

    def get_object(self):
        garden_details = Gardens.objects.filter(pk=self.kwargs['garden_pk'], grower_id=self.kwargs['grower_pk']).first()
        return garden_details


    def get_context_data(self, **kwargs):
        context = super(GardenDetailsUpdateView, self).get_context_data(**kwargs)

        garden_details = Gardens.objects.filter(pk=self.kwargs['garden_pk'], grower_id=self.kwargs['grower_pk']).first()
        
        # print(garden_details.grower_id)
        
        context['garden_id'] = garden_details
        context['grower_id'] = garden_details.grower_id
        

        if self.request.POST:
            context['plot_details_form_set'] = PLOT_DETAILS_FORM_SET(self.request.POST, instance=self.get_object())
            
        else:
            context['plot_details_form_set'] = PLOT_DETAILS_FORM_SET(instance=self.get_object())

        
        return context

    def form_valid(self, form):
        
        self.garden_id = self.kwargs['garden_pk']
        context = self.get_context_data()

        plot_details_form_set = context['plot_details_form_set']

        with transaction.atomic():
            self.object = form.save()

            if plot_details_form_set.is_valid():
                plot_details_form_set.instance = self.object
                plot_details_form_set.save()

            if not form.is_valid() or not plot_details_form_set.is_valid():
                # formsets or form is invalid; render the form with error
                return self.render_to_response(context)

        return super(GardenDetailsUpdateView, self).form_valid(form)



def garden_details_view(request, grower_pk):

    grower_details = GrowerProfile.objects.filter(pk=grower_pk).first()
    garden_details = Gardens.objects.filter(grower_id=grower_details).first()

    division_details = Division.objects.filter(garden_id=garden_details.pk).first()

    total_section_area = Section.objects.filter(garden_id=garden_details.pk).aggregate(
        the_sum=Coalesce(Sum('section_area'), Value(0), output_field=FloatField()))['the_sum']
    division_list = Division.objects.filter(garden_id=garden_details.id).order_by('-id')


    context = {
        'grower_details' : grower_details,
        'garden_details' : garden_details,
        'division_list' : division_list,
        'total_section_area' : round(total_section_area, 2),
    }

    return CommonMixin.render(request, 'garden_deatils.html', context)




def garden_delete(request, garden_pk):
    """ Garden Details Delete view """
    try:
        if not request.user.is_superuser:
            messages.error(request, 'You have no permission to access the requested resource!')
            return redirect(reverse('index'))
    except AttributeError as error:
        messages.error(request, 'You have no permission to access the requested resource!')
        return redirect(reverse('index'))

    garden_details = Gardens.objects.filter(id=garden_pk).first()
    garden_details.delete()
    messages.success(
        request, 'Garden Deleted Successfully')
    return redirect(reverse('gardens_managment:garden_list')) 




def sesarch_garden(request):

    template = 'garden_list.html'
    name = request.GET.get('name')
    print(name)

    if name:
        result = Gardens.objects.filter(name__icontains=name)
    else:
        result = Gardens.objects.all()

    page = request.GET.get('page', 6)

    paginator = Paginator(result, 1)
    try:
        garden_list = paginator.page(page)
    except PageNotAnInteger:
        garden_list = paginator.page(1)
    except EmptyPage:
        garden_list = paginator.page(paginator.num_pages)


    context = {
        'search_result': name,
        'garden_list': garden_list,
        'name' : name,
    }

    return CommonMixin.render(request, template, context)



###################################################################
###   ESTTAE GARDENS VIEWS #####
###################################################################

class GardenUpdateView(LoginRequiredMixin, CommonMixin, UpdateView):

    model = Gardens
    form_class = UserGardenForm
    template_name = 'user_garden_form.html'

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
        messages.success(self.request, 'Garden Updated Successfully')
        return reverse('gardens_managment:user_garden_details', kwargs={"user_pk": self.kwargs['user_pk'] } )

    def get_object(self):
        garden_details = Gardens.objects.filter(pk=self.kwargs['garden_pk'], user_id=self.kwargs['user_pk']).first()
        return garden_details


    def get_context_data(self, **kwargs):
        context = super(GardenUpdateView, self).get_context_data(**kwargs)
        garden_details = Gardens.objects.filter(pk=self.kwargs['garden_pk'], user_id=self.kwargs['user_pk']).first()
        context['profile_type'] = "estate"    
        context['garden_id'] = garden_details
        context['user_id'] = self.kwargs['user_pk']
        if self.request.POST:
            context['plot_details_form_set'] = PLOT_DETAILS_FORM_SET(self.request.POST, instance=self.get_object())
        else:
            context['plot_details_form_set'] = PLOT_DETAILS_FORM_SET(instance=self.get_object())
        return context

    def form_valid(self, form):
        self.garden_id = self.kwargs['garden_pk']
        self.user_id = self.kwargs['user_pk']
        context = self.get_context_data()
        plot_details_form_set = context['plot_details_form_set']

        with transaction.atomic():
            form.instance.user_id = self.kwargs['user_pk']
            
            if plot_details_form_set.is_valid():
                plot_details_form_set.instance = self.object
                plot_details_form_set.save()

            if not form.is_valid() or not plot_details_form_set.is_valid():
                return self.render_to_response(context)
            
            self.object = form.save()

        return super(GardenUpdateView, self).form_valid(form)


def user_garden_details_view(request, user_pk):

    user_details = EstateProfile.objects.filter(user=user_pk).first()

    garden_details = Gardens.objects.filter(user_id=user_pk).first()

    # print("garedn Details here $$$$$$$$$$$")
    print(garden_details)

    division_list = Division.objects.filter(garden_id=garden_details.id).order_by('-id')

    total_section_area = Section.objects.filter(garden_id=garden_details.pk).aggregate(
        the_sum=Coalesce(Sum('section_area'), Value(0), output_field=FloatField()))['the_sum']

    context = {
        'user_details' : user_details,
        'garden_details' : garden_details,
        'division_list' : division_list,
        'user_id' : user_pk,
        'total_section_area' : round(total_section_area, 2),

    }

    return CommonMixin.render(request, 'user_garden_details.html', context)




#############     Division view ##############

class DivisionLisView(LoginRequiredMixin, CommonMixin, ListView):
    """
    Tea Graden List View
    """
    model = Division
    context_object_name = 'division_list'
    template_name = 'division_list.html'
    paginate_by = 5


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

    def get_queryset(self):
        return Division.objects.filter(garden_id=self.kwargs['garden_pk']).order_by('-id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        garden_details = Gardens.objects.filter(pk=self.kwargs['garden_pk']).first()
        grower_details = GrowerProfile.objects.filter(pk=garden_details.grower_id).first()
        # print(grower_details.profile_type)

        context['grower_details'] = grower_details

        # context['division_list'] = TeaType.objects.all().order_by('id')
        return context
    


class DivisionCreateView(LoginRequiredMixin, CreateView, CommonMixin):
    """
    Division Create View
    """
    form_class = DivisionForm
    template_name = 'division_form.html'

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
        messages.success(self.request, 'Division Created Successfully')
        garden_details = Gardens.objects.filter(pk=self.kwargs['garden_pk']).first()
        grower_id = garden_details.grower.id
        return reverse('gardens_managment:garden_details', kwargs={"grower_pk": grower_id })
    
    def get_form_kwargs(self):
        data = super(DivisionCreateView, self).get_form_kwargs()
        garden_pk = self.kwargs['garden_pk']
        data.update(
            garden_pk=garden_pk,
        )
        return data

    def get_context_data(self, **kwargs):
        context = super(DivisionCreateView, self).get_context_data(**kwargs)
        context['pk'] = self.kwargs['garden_pk']
        kwargs['garden_pk'] = self.kwargs['garden_pk']
        garden_details = Gardens.objects.filter(pk=self.kwargs['garden_pk']).first()
        grower_details = GrowerProfile.objects.filter(pk=garden_details.grower_id).first()

        total_section_area = Section.objects.filter(garden_id=self.kwargs['garden_pk']).aggregate(
                the_sum=Coalesce(Sum('section_area'), Value(0), output_field=FloatField()))['the_sum']

        # total_section_area= Sum(F('section_area'), output_field=FloatField())
        
        
        # Sum(F('total_sold')*F('final_price'), output_field=FloatField())
        

        context['garden_details_pk'] = self.kwargs['garden_pk']
        context['grower_details'] = grower_details
        context['total'] = garden_details.production_area
        context['total_sec_area'] = total_section_area
        context['total_section_area'] = float(total_section_area)
        if self.request.POST:
            context['section_form_set'] = SECTION_DETAILS_FORM_SET(self.request.POST)
        else:
            context['section_form_set'] = SECTION_DETAILS_FORM_SET()
        return context
    

    def form_invalid(self, form):
        error_message = 'Error saving the Form, check fields below.'
        messages.error(self.request, error_message)
        return super().form_invalid(form)

    def form_valid(self, form):

        garden_details = Gardens.objects.filter(pk=self.kwargs['garden_pk']).first()
        form.instance.garden_id = self.kwargs['garden_pk']
        context = self.get_context_data()
        section_form_set = context['section_form_set']

        with transaction.atomic():
                self.object = form.save()

                if section_form_set.is_valid():
                    section_form_set.instance = self.object
                    section_form_set.save()

                    # print(section_form_set.initial)

                for item in Section.objects.filter(division=self.object):
                    item.garden_id = self.kwargs['garden_pk']
                    item.save()

        if not form.is_valid() or not section_form_set.is_valid():      
                # formsets or form is invalid; render the form with error
                return self.render_to_response(context)

        return super(DivisionCreateView, self).form_valid(form)


# Division Details Update Viuew
class DivisionDetailsUpdateView(LoginRequiredMixin, CommonMixin, UpdateView):
    model = Division
    form_class = DivisionForm
    template_name = 'division_form.html'


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
        messages.success(self.request, 'Division Updated Successfully')

        garden_details = Gardens.objects.filter(pk=self.kwargs['garden_pk']).first()
        grower_id = garden_details.grower.id
        return reverse('gardens_managment:garden_details', kwargs={"grower_pk": grower_id })

        # return reverse('product:product_details_admin', kwargs={'user_create_pk' : self.object.slug})

    def get_object(self):
        division_details = Division.objects.filter(pk=self.kwargs['division_pk']).first()
        return division_details

    def get_context_data(self, **kwargs):
        context = super(DivisionDetailsUpdateView, self).get_context_data(**kwargs)

        context['division_details'] = self.get_object()
        garden_details = Gardens.objects.filter(pk=self.kwargs['garden_pk']).first()
        grower_details = GrowerProfile.objects.filter(pk=garden_details.grower_id).first()
        context['grower_details'] = grower_details  
        
        total_section_area = Section.objects.filter(garden_id=self.kwargs['garden_pk']).exclude(\
            division=self.get_object()).aggregate(
                the_sum=Coalesce(Sum('section_area'), Value(0), output_field=FloatField()))['the_sum']
        
        context['garden_details_pk'] = self.kwargs['garden_pk']
        context['grower_details'] = grower_details
        context['total'] = garden_details.production_area
        context['total_sec_area'] = total_section_area
        context['total_section_area'] = int(total_section_area)

        if self.request.POST:
            context['section_form_set'] = SECTION_DETAILS_FORM_SET(self.request.POST, instance=self.get_object())
        else:
            context['section_form_set'] = SECTION_DETAILS_FORM_SET(instance=self.get_object())
        return context


    def form_invalid(self, form):
        error_message = 'Error saving the Form, check fields below.'
        messages.error(self.request, error_message)
        return super().form_invalid(form)

    def form_valid(self, form):
        self.garden_id = self.kwargs['garden_pk']
        context = self.get_context_data()
        section_form_set = context['section_form_set']

        with transaction.atomic():
            self.object = form.save()

            if section_form_set.is_valid():
                section_form_set.instance = self.object
                section_form_set.save()

            for item in Section.objects.filter(division=self.object):
                item.garden_id = self.kwargs['garden_pk']
                item.save()

            if not form.is_valid() or not section_form_set.is_valid():
                # formsets or form is invalid; render the form with error
                return self.render_to_response(context)

        return super(DivisionDetailsUpdateView, self).form_valid(form)



# ESTATE VIEWS #############################

class EstateDivisionCreateView(LoginRequiredMixin, CreateView, CommonMixin):
    """
    Estate Division Create View
    """
    form_class = DivisionForm
    template_name = 'estate_division_form.html'

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
        messages.success(self.request, 'Division Created Successfully')
        garden_details = Gardens.objects.filter(pk=self.kwargs['garden_pk']).first()
        estate_id = garden_details.estate.id
        user_id = garden_details.user_id

        return reverse('gardens_managment:user_garden_details', kwargs={"user_pk": user_id })
    
    def get_context_data(self, **kwargs):
        context = super(EstateDivisionCreateView, self).get_context_data(**kwargs)
        context['pk'] = self.kwargs['garden_pk']
        kwargs['garden_pk'] = self.kwargs['garden_pk']
        garden_details = Gardens.objects.filter(pk=self.kwargs['garden_pk']).first()
        grower_details = GrowerProfile.objects.filter(pk=garden_details.grower_id).first()

        total_section_area = Section.objects.filter(garden_id=self.kwargs['garden_pk']).aggregate(
                the_sum=Coalesce(Sum('section_area'), Value(0), output_field=FloatField()))['the_sum']
        context['garden_details_pk'] = self.kwargs['garden_pk']
        context['grower_details'] = grower_details
        context['total'] = garden_details.production_area
        context['total_sec_area'] = total_section_area
        context['total_section_area'] = int(total_section_area)

        context['user_pk'] = garden_details.user_id

        if self.request.POST:
            context['section_form_set'] = SECTION_DETAILS_FORM_SET(self.request.POST)
        else:
            context['section_form_set'] = SECTION_DETAILS_FORM_SET()
        return context
    

    def form_invalid(self, form):
        error_message = 'Error saving the Form, check fields below.'
        messages.error(self.request, error_message)
        return super().form_invalid(form)

    def form_valid(self, form):

        garden_details = Gardens.objects.filter(pk=self.kwargs['garden_pk']).first()
        form.instance.garden_id = self.kwargs['garden_pk']
        context = self.get_context_data()
        section_form_set = context['section_form_set']

        with transaction.atomic():
                self.object = form.save()

                if section_form_set.is_valid():
                    section_form_set.instance = self.object
                    section_form_set.save()

                    # print(section_form_set.initial)

                for item in Section.objects.filter(division=self.object):
                    item.garden_id = self.kwargs['garden_pk']
                    item.save()

        if not form.is_valid() or not section_form_set.is_valid():      
                # formsets or form is invalid; render the form with error
                return self.render_to_response(context)

        return super(EstateDivisionCreateView, self).form_valid(form)




# ESTATE Division Details Update Viuew
class UserDivisionDetailsUpdateView(LoginRequiredMixin, CommonMixin, UpdateView):
    model = Division
    form_class = DivisionForm
    template_name = 'estate_division_form.html'


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
        messages.success(self.request, 'Division Updated Successfully')
        garden_details = Gardens.objects.filter(pk=self.kwargs['garden_pk']).first()
        estate_id = garden_details.estate.id
        user_id = garden_details.user_id

        return reverse('gardens_managment:user_garden_details', kwargs={"user_pk": user_id })

    def get_object(self):
        division_details = Division.objects.filter(pk=self.kwargs['division_pk']).first()
        return division_details

    def get_context_data(self, **kwargs):
        context = super(UserDivisionDetailsUpdateView, self).get_context_data(**kwargs)

        context['division_details'] = self.get_object()
        garden_details = Gardens.objects.filter(pk=self.kwargs['garden_pk']).first()
        grower_details = GrowerProfile.objects.filter(pk=garden_details.grower_id).first()
        context['grower_details'] = grower_details  
        
        total_section_area = Section.objects.filter(garden_id=self.kwargs['garden_pk']).exclude(\
            division=self.get_object()).aggregate(
                the_sum=Coalesce(Sum('section_area'), Value(0), output_field=FloatField()))['the_sum']
        
        context['garden_details_pk'] = self.kwargs['garden_pk']
        context['grower_details'] = grower_details
        context['total'] = garden_details.production_area
        context['total_sec_area'] = total_section_area
        context['total_section_area'] = int(total_section_area)

        context['user_pk'] = garden_details.user_id

        if self.request.POST:
            context['section_form_set'] = SECTION_DETAILS_FORM_SET(self.request.POST, instance=self.get_object())
        else:
            context['section_form_set'] = SECTION_DETAILS_FORM_SET(instance=self.get_object())
        return context


    def form_invalid(self, form):
        error_message = 'Error saving the Form, check fields below.'
        messages.error(self.request, error_message)
        return super().form_invalid(form)

    def form_valid(self, form):
        self.garden_id = self.kwargs['garden_pk']
        context = self.get_context_data()
        section_form_set = context['section_form_set']

        with transaction.atomic():
            self.object = form.save()

            if section_form_set.is_valid():
                section_form_set.instance = self.object
                section_form_set.save()

            for item in Section.objects.filter(division=self.object):
                item.garden_id = self.kwargs['garden_pk']
                item.save()

            if not form.is_valid() or not section_form_set.is_valid():
                # formsets or form is invalid; render the form with error
                return self.render_to_response(context)

        return super(UserDivisionDetailsUpdateView, self).form_valid(form)




#
def section_details(request, division_pk, garden_pk):

    division_details = Division.objects.filter(pk=division_pk).first()

    section_list = Section.objects.filter(division_id=division_details.pk).order_by('-id')

    total_section_area = Section.objects.filter(division_id=division_details.pk).aggregate(
                the_sum=Coalesce(Sum('section_area'), Value(0), output_field=FloatField()))['the_sum']
    
    garden_details = Gardens.objects.filter(pk=garden_pk).first()

    div_garden_details_pk = Division.objects.filter(garden_id=garden_details.pk).first()

    total_garden_wise_area = Section.objects.filter(division_id=div_garden_details_pk.pk).aggregate(
                the_sum=Coalesce(Sum('section_area'), Value(0), output_field=FloatField()))['the_sum']

    print("DIV garden pk")
    print(div_garden_details_pk.pk)

    grower_pk = garden_details.grower_id

    garden_area = garden_details.production_area

    print(garden_area)
    print("Total AREA DIV GARDEN WISE")
    print(total_garden_wise_area)


    # if garden_area < total_section_area:
    #     pass
    
    context={

        'division_details' : division_details,
        'section_list' : section_list,
        'total_area' : total_section_area,
        'garden_details' : garden_details,
        'grower_pk' : grower_pk,

    }

    return CommonMixin.render(request, 'section_details.html', context)



def user_section_details(request, division_pk, garden_pk):

    division_details = Division.objects.filter(pk=division_pk).first()

    section_list = Section.objects.filter(division_id=division_details.pk).order_by('-id')

    total_section_area = Section.objects.filter(division_id=division_details.pk).aggregate(
                the_sum=Coalesce(Sum('section_area'), Value(0), output_field=FloatField()))['the_sum']
    
    garden_details = Gardens.objects.filter(pk=garden_pk).first()

    context={

        'division_details' : division_details,
        'section_list' : section_list,
        'total_area' : total_section_area,
        'garden_details' : garden_details,
        'user_pk' : garden_details.user_id,
    }

    return render(request, 'user_section_details.html', context)





















def division_delete(request, division_pk ):
    """ Division Details Delete view """

    try:
        if not request.user.is_superuser:
            messages.error(request, 'You have no permission to access the requested resource!')
            return redirect(reverse('index'))
    except AttributeError as error:
        messages.error(request, 'You have no permission to access the requested resource!')
        return redirect(reverse('index'))

    division_details = Division.objects.filter(pk=division_pk).first()  
    division_details.delete()

    messages.success(
        request, 'Division Deleted Successfully')
    
    return HttpResponseRedirect(request.META.get("HTTP_REFERER"))
    
    # return redirect(reverse('gardens_managment:garden_details', kwargs={"grower_pk": grower_id })) 

