from django.contrib import admin
from .models import *
from user_profile.aggregator_api_models import *
from user_profile.blf_api_models import *
from user_profile.grower_api_models import *
from import_export.admin import ImportExportModelAdmin

class ThroughDetailsEstateAdmin(admin.TabularInline):
	"""
		Through Detqails Estate Admin
	"""
	model = TroughDetailsEstate
	fk_name = 'user_profile_estate'

class TeaProductionAdmin(admin.TabularInline):
	model = EstateTeaProduction
	fk_name = 'estate'
	
class EstateProfileAdmin(admin.ModelAdmin):
	"""
	Estate PROFILE Admin Model
	"""
	list_display = ['id','user', ] 
	inlines = (ThroughDetailsEstateAdmin, TeaProductionAdmin)


class BlffactoryAdmin(admin.TabularInline):
	model = BlfFactoryMarks
	fk_name = 'blf'


class BlfProfileAdmin(admin.ModelAdmin):
	"""
	Blf PROFILE Admin Model
	"""
	list_display = ['id', 'user', 'entity_unit', 'entity_name', 'region', 'tcms_unit_id', 'is_tcms_user', 'is_deleted',]
	search_fields = ['user__username', 'id', 'user__id', 'entity_unit', 'entity_name']
	inlines = (BlffactoryAdmin,)


admin.site.register(EstateProfile, EstateProfileAdmin)
admin.site.register(FactoryDetailsMarks)
admin.site.register(TroughDetailsEstate)
admin.site.register(BlfProfile, BlfProfileAdmin)
admin.site.register(BlfFactoryDetailsMarks)
admin.site.register(EstateProductionTeaType)
admin.site.register(GrowerQrCode)
admin.site.register(AggregatorQrCode)
# admin.site.register(CollectionFromGrower)
class CollectionFromGrowerAdmin(admin.ModelAdmin):
	list_display = ['id','grower','receipt_no', 'quantity','vehicle_number','date']
	search_fields = ['receipt_no', 'grower__user__username','grower__name','vehicle_number__vehicle_number','quantity']

admin.site.register(CollectionFromGrower, CollectionFromGrowerAdmin)
admin.site.register(CollectionFromAggregator)


class LabourAdmin(admin.ModelAdmin):
	list_display = ['id', 'created_by', 'created_by_id', 'grower', 'grower_id', 'name']
	search_fields = ['created_by']

admin.site.register(Labour, LabourAdmin)


class PluckingDataAdmin(admin.ModelAdmin):
	list_display = ['id', 'grower', 'grower_id', 'created_by', 'created_by_id', 'date', 'plot', 'area_plucked']

admin.site.register(PluckingData, PluckingDataAdmin)
# admin.site.register(UseOfChemical)
# admin.site.register(SupplyManagement)
# admin.site.register(GrowerDetailsSupply)
# admin.site.register(SupplierExit)


class SupplyManagementAdmin(admin.ModelAdmin):

	list_display = ['id','created_by_id', 'created_by', 'date_of_supply', 'supply_to','consumer','supply_challan_id', 'is_weighment_proceed'  ]
	search_fields = ['supply_challan_id']



admin.site.register(SupplyManagement,SupplyManagementAdmin)

class GrowerDetailsSupplyAdmin(admin.ModelAdmin):
	list_display = ['id','supply','grower', 'collected_date', 'collected_quantity', 'created_by']
	search_fields = ['grower__user__username', 'supply__supply_challan_id', 'created_by__username']


admin.site.register(GrowerDetailsSupply,GrowerDetailsSupplyAdmin)

class SupplierExitAdmin(admin.ModelAdmin):

	list_display = ['id','weighment_txn','is_released','unloaded_vehicle_weight',]

admin.site.register(SupplierExit,SupplierExitAdmin)
admin.site.register(Year)

class MonthlyScheduleAdmin(admin.ModelAdmin):

	list_display = ['id','year','month','no_of_working_days','monthly_wages']



admin.site.register(MonthlySchedule,MonthlyScheduleAdmin)







class GrowerProfileAdmin(admin.ModelAdmin):
	"""
	Grower PROFILE Admin Model

	"""
	list_display = ['id', 'user_id', 'user',  'name', 'mobile_number']
	search_fields = ['user__username', 'id', 'user__id']





admin.site.register(GrowerProfile, GrowerProfileAdmin)

class AggregatorProfileAdmin(admin.ModelAdmin):
	"""
	Grower PROFILE Admin Model
	"""
	list_display = ['id', 'user_id', 'user',  'name', 'mobile_number']
	search_fields = ['user__id', 'user__username']

admin.site.register(AggregatorProfile, AggregatorProfileAdmin)

admin.site.register(ProfileType)
admin.site.register(GrowerType)

admin.site.register(AggregatorType)
admin.site.register(ShgCooperativeType)
admin.site.register(ShgCooperativeProfile)
admin.site.register(AdvisoryProfile)
admin.site.register(ConsigneeProfile)


admin.site.register(EstateTeaProduction)

admin.site.register(BlfTroughDetails)




class EstateTroughDetailsAdmin(admin.TabularInline):
	model = EstateTroughDetails
	fk_name = 'factory'


class FactoryTroughDetailsAdmin(admin.ModelAdmin):
	"""
	Factory Estate  Admin Model
	"""
	list_display = ['id','estate_id', 'user_id', 'name' ] 
	inlines = (EstateTroughDetailsAdmin, )


admin.site.register(FactoryTroughDetails, FactoryTroughDetailsAdmin)



class ProfileAdmin(admin.ModelAdmin):
	"""
	Factory Estate  Admin Model
	"""
	list_display = ['id', 'user', 'user_type', 'full_name','email', 'phone_no', ] 
	search_fields = ['user__username', 'full_name', 'phone_no']
	list_filter = ['user_type']
    
admin.site.register(Profile, ProfileAdmin)

admin.site.register(BlfofficialSignature)

class UserFileUploadAdmin(admin.ModelAdmin):
	list_display = ['file_name', 'file']
admin.site.register(UserFileUpload, UserFileUploadAdmin)

@admin.register(UserOTP)
class UserOTPAdmin(admin.ModelAdmin):
    model = UserOTP
    list_display = ['id','user','expiry','otp_secret','is_used','is_deleted']
    search_fields = ['user']
    list_filter = ('is_used', 'is_deleted')

@admin.register(UserProfileAttachments)
class UserProfileIDAttachmentsAdmin(admin.ModelAdmin):
	model = UserProfileAttachments
	list_display = ['id','grower','doc_type','attachment_name','doc_no', 'attachment']
	search_fields = ['doc_no',]
	list_filter = ('is_deleted',)