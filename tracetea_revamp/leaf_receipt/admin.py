from django.contrib import admin
from .models import *
# Register your models here.
# admin.site.register(VehicleNumberTxnId)

class LeafAdmin(admin.ModelAdmin):
    search_fields = ['weighment_txn__weighment_txn_id', 'id' ]
    list_display = ['id', 'weighment_txn', 'acknowledge_status', ]


class LeafCollectionAdmin(admin.ModelAdmin):
    list_display = ['id', 'created_by', 'supply_date', 'weighment_supply_id', 'supply_id', 'supplier_type', 'supplier', 'aggregator', 'grower', 'nt_wght', 'plucking_data_id' ]
    search_fields = ['supplier_type', 'weighment_supply_id__weighment_txn_id']


admin.site.register(LeafManagement, LeafAdmin)

admin.site.register(LeafCollection, LeafCollectionAdmin)

