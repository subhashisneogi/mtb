from django.contrib import admin
from .models import *
# Register your models here.
class VehicleManagementAdmin(admin.ModelAdmin):

	list_display = ['id','vehicle_number','vehicle_type','mobile_number','is_available']

admin.site.register(VehicleManagement, VehicleManagementAdmin)

	