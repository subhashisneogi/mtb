from django.contrib import admin
from .models import *

class BatchListAdmin(admin.TabularInline):
	"""
	Batch List  Admin
	"""
	model = BatchList
	fk_name = 'invoice_no'
	
class InvoiceManagmentAdmin(admin.ModelAdmin):

	list_display = ['id', 'invoice_no', 'invoice_date']
	inlines = (BatchListAdmin,)



class BatchAdmin(admin.ModelAdmin):
    list_display = ['id','invoice_no', 'lot_batch', 'bag_no_range']

admin.site.register(Invoice, InvoiceManagmentAdmin)
admin.site.register(BatchList, BatchAdmin)

