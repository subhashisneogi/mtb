import datetime

from django.shortcuts import render, redirect
from django.conf import settings
from django.urls import reverse
from django.contrib import messages
from django.http import HttpResponseRedirect, HttpResponseForbidden 


from functools import wraps
from django.core.exceptions import ImproperlyConfigured

from user_profile.models import *


def permission_required_admin(view_func):
    """
        Permission required view for BLF Login
    """
    def wrapper_func(request, *args, **Kwargs):
        if not request.user.id == 1:
            messages.error(request, 'You have no permission to access the requested resource!')
            return redirect(reverse('index'))
        else:
            return view_func(request, *args, **Kwargs)

    return wrapper_func



def permission_required_blf(view_func):
    """
        Permission required view for BLF Login
    """

    def wrapper_func(request, *args, **Kwargs):
        if not request.user.id == 1:
            messages.error(request, 'You have no permission to access the requested resource!')
            return redirect(reverse('index'))
        else:
            return view_func(request, *args, **Kwargs)

    return wrapper_func



def permission_blf(view_func):
    """
        Permission required view for BLF Login
    """
    def wrapper_func(request, *args, **Kwargs):

        user_details = Profile.objects.filter(user_id=request.user.id).first()
        logged_user_type= user_details.user_type.pk

        if not logged_user_type == 5:
            messages.error(request, 'You have no permission to access the requested resource!')
            return redirect(reverse('index'))
        else:
            return view_func(request, *args, **Kwargs)

    return wrapper_func



# DECORATS FOR LOGIN PERMISSION BLF
def user_type_required(user_type):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **Kwargs):
            logged_user_type = Profile.objects.filter(user_type__name="blf").first()
            if request.user.is_authenticated  and  logged_user_type == user_type or request.user.id == 1:
                return view_func(request, *args, **Kwargs)
            else:
                return HttpResponseForbidden("You have no permission to access the requested resource!")
        return _wrapped_view
    return decorator




# def permission_required_costcenter(view_func):
#     """
#         Permission required view for Cost center 
#     """

#     def wrapper_func(request, *args, **Kwargs):
#         if request.user.profile.user_type == 'EMPLOYEE':
#             messages.error(request, 'You have no permission to access the requested resource!')
#             return redirect(reverse('manager_timesheet_dashboard', kwargs={'month' : datetime.datetime.now().month,\
# 					'year': datetime.datetime.now().year}))

#         else:
#             return view_func(request, *args, **Kwargs)

#     return wrapper_func



# def permission_required_employee(view_func):
#     """
#         Permission required view for employee Login
#     """
#     def wrapper_func(request, *args, **Kwargs):
#         if request.user.profile.user_type == 'MANAGER':
#             messages.error(request, 'You have no permission to access the requested resource!')
#             return redirect(reverse('manager_dashboard'))
#         elif request.user.profile.user_type == 'EMPLOYEE':
#             messages.error(request, 'You have no permission to access the requested resource!')
#             return redirect(reverse('manager_timesheet_dashboard', kwargs={'month' : datetime.datetime.now().month,\
# 					'year': datetime.datetime.now().year}))

#         else:
#             return view_func(request, *args, **Kwargs)

#     return wrapper_func


# def permission_required_manager(view_func):
#     """
#         Permission required view for manager Login
#     """
#     def wrapper_func(request, *args, **Kwargs):
#         if request.user.profile.user_type == 'ADMIN':
#             messages.error(request, 'You have no permission to access the requested resource!')
#             return redirect(reverse('hr_index'))
#         elif request.user.profile.user_type == 'EMPLOYEE':
#             messages.error(request, 'You have no permission to access the requested resource!')
#             return redirect(reverse('manager_timesheet_dashboard', kwargs={'month' : datetime.datetime.now().month,\
# 					'year': datetime.datetime.now().year}))

#         else:
#             return view_func(request, *args, **Kwargs)

#     return wrapper_func


# def permission_required_timesheet(view_func):
#     """
#         Permission required view for Timesheet
#     """
#     def wrapper_func(request, *args, **Kwargs):
#         if request.user.profile.user_type == 'ADMIN':
#             messages.error(request, 'You have no permission to access the requested resource!')
#             return redirect(reverse('hr_index'))
#         else:
#             return view_func(request, *args, **Kwargs)

#     return wrapper_func
