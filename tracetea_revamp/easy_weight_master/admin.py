from django.contrib import admin
from .models import *
# Register your models here.



# admin.site.register(EasyWeightWt)
# admin.site.register(EasyWeightAdv)
# admin.site.register(EasyWeightGwt)

class EasyWeightMasterAdmin(admin.ModelAdmin):

	list_display = ['id','collection_center','tracetea_id','month_year',]
admin.site.register(EasyWeightMaster,EasyWeightMasterAdmin)	
class EasyWeightWtAdmin(admin.ModelAdmin):

	list_display = ['id','easy_weight','wt','value',]

admin.site.register(EasyWeightWt,EasyWeightWtAdmin)

class EasyWeightGwtAdmin(admin.ModelAdmin):

	list_display = ['id','easy_weight','gwt','value',]

admin.site.register(EasyWeightGwt,EasyWeightGwtAdmin)

class EasyWeightAdvAdmin(admin.ModelAdmin):

	list_display = ['id','easy_weight','adv','value',]

admin.site.register(EasyWeightAdv,EasyWeightAdvAdmin)

class EasyWeightMiscAdmin(admin.ModelAdmin):

	list_display = ['id','easy_weight','misc','value',]

admin.site.register(EasyWeightMisc,EasyWeightMiscAdmin)


