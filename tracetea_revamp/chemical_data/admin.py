from django.contrib import admin
from .models import *

class MapAreaNameMasterAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'slug']

class MapAreaDetailsAdmin(admin.ModelAdmin):
    list_display = ['id', 'created_by', 'blf',  'grower_id', 'is_image_upload',  'grower', 'map_area_name', 'total_areas', 'coordinate']


# Register your models here.
class ChemicalTypeAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']

admin.site.register(ChemicalType, ChemicalTypeAdmin)

admin.site.register(ChemicalData)
admin.site.register(MapAreaNameMaster, MapAreaNameMasterAdmin)
admin.site.register(MapAreaDetails, MapAreaDetailsAdmin)


admin.site.register(FarmersAggreementMaster)

class FarmersAggreementFormsAdmin(admin.ModelAdmin):
    list_display = ['id', 'blf', 'grower', 'aggregator', 'aggreement_form_title', 'farmer_signature_file', 'blf_grade_official_signature_file', 'date', 'place']

admin.site.register(FarmersAggreementForms, FarmersAggreementFormsAdmin)

class UseOfChemicalAdmin(admin.ModelAdmin):
    list_display = ['id', 'grower', 'aggregator', 'blf', 'created_by', 'chemical', 'quantity', 'unit', 'is_deleted']

admin.site.register(UseOfChemical, UseOfChemicalAdmin)

class MapAreaMasterAdmin(admin.ModelAdmin):
    list_display = ['id', 'blf', 'grower', 'aggregator', 'map_image', 'digital_map_image', 'pdf_map_image', 'is_image_upload', 'is_digital_upload']

admin.site.register(MapAreaMaster, MapAreaMasterAdmin)

class MapAreaLandDetailsAdmin(admin.ModelAdmin):
    list_display = ['id', 'grower', 'map_area_master', 'map_area_name_id', 'total_areas', 'coordinate']

admin.site.register(MapAreaLandDetails, MapAreaLandDetailsAdmin)