from django.contrib import admin
from .models import *

class WeighmentAdmin(admin.ModelAdmin):
   list_display = ['id', 'weighment_txn_id', 'supplier_type', 'supplier', 'supply_challan', 'mode_of_supply', 'is_deleted']
   search_fields = ['supply_challan__supply_challan_id', 'weighment_txn_id']

admin.site.register(WeighmentSupply, WeighmentAdmin)
admin.site.register(BlfSupplier)
