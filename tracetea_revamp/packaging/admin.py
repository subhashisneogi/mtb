from django.contrib import admin
from .models import *
# Register your models here.


class PackagingAdmin(admin.ModelAdmin):

    list_display = ['id', 'invoice_no', 'type_of_dispatch', 'consignee', 'warehouse']

admin.site.register(Packaging, PackagingAdmin)