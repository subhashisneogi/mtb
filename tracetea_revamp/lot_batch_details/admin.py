from django.contrib import admin
from .models import *
# Register your models here.

class MemberAdmin(admin.ModelAdmin):
  list_display = ("id", "lot_batch_no", "bag_sl_no_from", "sl_no_to")

class BagRangeAdmin(admin.ModelAdmin):
  list_display = ("id", "lot_batch_no", "bag_sl_no_range")


admin.site.register(LotBatchDetails, MemberAdmin)
admin.site.register(BagSlNoRange, BagRangeAdmin)