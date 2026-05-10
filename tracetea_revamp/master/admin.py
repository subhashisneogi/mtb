from django.contrib import admin

# Register your models here.
from .models import *


class StateAdmin(admin.ModelAdmin):
    """ State admin """
    model = State
    list_display = ('state_id','name','pk',)
    search_fields = ('name',)
admin.site.register(State, StateAdmin) 
   

class DistrictAdmin(admin.ModelAdmin):
    """ City admin"""
    model = District
    list_display = ('state_id','district_id','name','pk',)
    search_fields = ('name', )
admin.site.register(District, DistrictAdmin)    

class AssociatedEntityAdmin(admin.ModelAdmin):
    """ AssociatedEntity admin"""
    model = AssociatedEntity
    list_display = ('name','region',)
admin.site.register(AssociatedEntity, AssociatedEntityAdmin) 
admin.site.register(TeaType)
class TeaTypeGradeAdmin(admin.ModelAdmin):
    """ Tea Grade admin"""
    model = TeaGradeDetails
    list_display = ('grade','tea_type',)
admin.site.register(TeaGradeDetails,TeaTypeGradeAdmin)

admin.site.register(Region)
admin.site.register(WarehouseManagement)
admin.site.register(WarehouseType)
admin.site.register(PeriodSelected)
admin.site.register(PrivacyPolicy)

admin.site.register(AndroidVersion)