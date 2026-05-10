"""
Forms
"""
from django import forms
from django.db.models import Q, Min, IntegerField
from django.db.models.functions import Cast
from django.core.exceptions import ValidationError
from django.forms import inlineformset_factory
from django.forms import ModelForm, Textarea

from .models import *

import operator as op

class DateInput(forms.DateInput):
    """
    Widgets support for date input
    """
    input_type = 'date'
    

class PackagingForm(forms.ModelForm):
    """
        Packaging Form
    """
    class Meta:
        model = Packaging
        fields = ('invoice_no', 'type_of_dispatch', 'consignee', 'warehouse')
        widgets = {
	    	# 'invoice_date': DateInput(),
        }

    def __init__(self, *args, **kwargs):

        user_id = kwargs.pop('user_id', None)
        invoice_no_id = kwargs.pop('invoice_no_id', None)

        super(PackagingForm, self).__init__(*args, **kwargs)

        # self.fields['invoice_no'].required = True
        # self.fields['invoice_date'].required = True

        self.fields['invoice_no'].widget.attrs = {
            'class': 'form-control select2_demo_1'}
        self.fields['type_of_dispatch'].widget.attrs = {
            'class': 'form-control select2_demo_2', 'id' : 'type_of_dispatch'}
        
        self.fields['consignee'].widget.attrs = {
        'class': 'form-control ', 'placeholder' : 'Consignee', 'id' : 'consignee'}
        self.fields['warehouse'].widget.attrs = {
        'class': 'form-control ', 'id' : 'warehouse'}
        
        self.fields['warehouse'].queryset = WarehouseManagement.objects.filter(created_by_id=user_id).order_by('-id')

        if invoice_no_id:
            from django.db.models import Q
            invoice_ids = list(Invoice.cmobjects.filter(created_by_id=user_id, is_packaged=False).values_list('id', flat=True))
            invoice_ids.append(invoice_no_id)
            self.fields['invoice_no'].queryset = Invoice.cmobjects.filter(id__in=invoice_ids).order_by('-id')
        else:
            self.fields['invoice_no'].queryset = Invoice.cmobjects.filter(is_packaged=False,\
                created_by_id=user_id).order_by('-id')
            







        
    

