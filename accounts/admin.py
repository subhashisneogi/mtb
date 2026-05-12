from django.contrib import admin
from .models import *







# Register your models here.
@admin.register(LoginLogoutLoggedTable)
class LoginLogoutLoggedTable(admin.ModelAdmin):
    list_display = [field.name for field in LoginLogoutLoggedTable._meta.fields]
    search_fields = ('user__username', 'ip_address',)