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
    




from django.forms import BaseInlineFormSet

class CustomBatchListFormSet(BaseInlineFormSet):
    def get_form_kwargs(self, index):
        kwargs = super().get_form_kwargs(index)
        kwargs['user_id'] = self.user_id  # Pass the user_id to the form
        return kwargs







class InvoiceForm(forms.ModelForm):
    """
        Invoice Form
    """
    class Meta:
        model = Invoice
        fields = ('invoice_no', 'invoice_date',)
        widgets = {
	    	'invoice_date': DateInput(),
        }

    def __init__(self, *args, **kwargs):
        super(InvoiceForm, self).__init__(*args, **kwargs)

        self.fields['invoice_no'].required = True
        self.fields['invoice_date'].required = True

        self.fields['invoice_no'].widget.attrs = {
            'class': 'form-control', 'placeholder' : 'Invoice No'}
        self.fields['invoice_date'].widget.attrs = {
            'class': 'form-control ',}


        

class BatchListForm(forms.ModelForm):
    """
        BatchList Form
    """
    class Meta:
        model = BatchList
        fields = ('lot_batch', 'bag_no_range',)

    def __init__(self, *args, **kwargs):
        user_id = kwargs.pop('user_id', None)
        super(BatchListForm, self).__init__(*args, **kwargs)

        self.fields['lot_batch'].required = False
        self.fields['lot_batch'].widget.attrs = {
            'class': 'form-control', 'placeholder' : 'Lot Batch No', "onchange": "product_type_change(this)"}
        self.fields['bag_no_range'].widget.attrs = {
            'class': 'form-control ', 'readonly' : 'readonly',  }
        
        self.user_id = user_id
        self.fields['lot_batch'].queryset = LotBatchDetails.cmobjects.filter(created_by_id=user_id)

    # def clean(self):
    #     cleaned_data = super().clean()
    #     lot_batch = cleaned_data.get('lot_batch')
    #     if lot_batch:
    #         # Check if the selected lot_batch is already associated with another Invoice.
    #         existing_invoice = Invoice.objects.filter(batchlist_invoice_no__lot_batch=lot_batch).first()
    #         if existing_invoice:
    #             raise ValidationError("This lot_batch is already associated with another invoice.")

    #     return cleaned_data

    # def clean(self):
    #     cleaned_data = super().clean()
    #     lot_batch = cleaned_data.get('lot_batch')

    #     if lot_batch:
    #         # Check if the selected lot_batch is valid (e.g., unique within invoices)
    #         if BatchList.objects.filter(lot_batch__lot_batch_no=lot_batch).exclude(pk=self.instance.pk).exists():
    #             # raise ValidationError("This lot_batch is already associated with another invoice.")
    #             raise ValidationError({'lot_batch': ["Lot batch No Should be unique"]})

    #     return cleaned_data
    


    # def clean(self):
    #     cleaned_data = super().clean()
    #     lot_batch = cleaned_data.get('lot_batch')
    #     invoice_no = cleaned_data.get('invoice_no')

    #     if lot_batch and invoice_no:
    #         existing_batch_list = BatchList.objects.filter(lot_batch=lot_batch, invoice_no=invoice_no).exclude(pk=self.instance.pk)
    #         if existing_batch_list.exists():
    #             raise forms.ValidationError('Lot Batch must be unique for each invoice.')

    #     return cleaned_data

    def clean(self):
        cleaned_data = super(BatchListForm, self).clean()
        lot_batch = self.cleaned_data.get('lot_batch')

        if BatchList.objects.filter(lot_batch__lot_batch_no=lot_batch).exclude(pk=self.instance.pk).exists():
            raise ValidationError({'lot_batch': ["Lot Batch must be unique for each invoice."]})

        return cleaned_data



# BATCH_LIST_FORM_SET = inlineformset_factory(
#     Invoice,
#     BatchList,
#     form=BatchListForm,
#     extra=0,
#     min_num=1,
#     max_num=100,
#     validate_max=True,
#     can_delete=True
# )

BATCH_LIST_FORM_SET = inlineformset_factory(
    Invoice,
    BatchList,
    form=BatchListForm,
    extra=0,
    min_num=1,
    max_num=100,
    validate_max=True,
    can_delete=True,
    formset=CustomBatchListFormSet  # Use the custom formset class
)