from django.contrib import admin

from .models import *

class PlotDetailsAdmin(admin.TabularInline):
	"""
	Garden Plot Details  Admin
	"""
	model = Plot
	fk_name = 'garden'
	
class GardenAdmin(admin.ModelAdmin):
	"""
	Gardens Admin Model
	"""
	list_display = ['id', 'grower', 'grower_id', 'name', 'production_area']
	search_fields = ['grower__user__username', 'user__id']
	inlines = (PlotDetailsAdmin,)


class SectionDetailsAdmin(admin.TabularInline):
	"""
	Garden Plot Details  Admin
	"""
	model = Section
	fk_name = 'division'

class DivisionAdmin(admin.ModelAdmin):
	"""
	Division Admin Model
	"""
	list_display = ['id','name', 'garden_id']
	inlines = (SectionDetailsAdmin,)


class EstateGardenAdmin(admin.ModelAdmin):
	list_display = ['id', 'name', 'estate']


class PlotListAdmin(admin.ModelAdmin):
	list_display = ['id', 'name', 'plot_area', 'garden_id']


class SectionListAdmin(admin.ModelAdmin):
	list_display = ['id', 'name', 'section_area', 'division_id', 'garden_id']


admin.site.register(EstateGardens, EstateGardenAdmin)
admin.site.register(Gardens, GardenAdmin)
admin.site.register(LandType)
admin.site.register(Division, DivisionAdmin)
admin.site.register(Plot, PlotListAdmin)
admin.site.register(Section, SectionListAdmin)