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


class LotBatchForm(forms.ModelForm):
    """
        Lot Batch Form
    """
    class Meta:
        model = LotBatchDetails
        fields = ('lot_batch_no', 'bag_sl_no_range', 'lot_batch_date', 'grade', 'bag_sl_no_from', 'sl_no_to', 'bag_weight_kg', 'mark')
        widgets = {
	    	'lot_batch_date': DateInput(),
        }
    

    def __init__(self, *args, **kwargs):
        blf_user_id = kwargs.pop('blf_user_id', None)
        super(LotBatchForm, self).__init__(*args, **kwargs)
        self.blf_user_id = blf_user_id


        self.fields['lot_batch_no'].required = True
        self.fields['bag_sl_no_from'].required = True
        self.fields['sl_no_to'].required = True

        self.fields['lot_batch_no'].widget.attrs = {
            'class': 'form-control', 'placeholder' : 'Lot/Batch No'}
        self.fields['lot_batch_date'].widget.attrs = {
            'class': 'form-control ', 'placeholder' : 'Lot/Batch Date',}
        self.fields['grade'].widget.attrs = {
            'class': 'form-control', }
        self.fields['bag_sl_no_from'].widget.attrs = {
            'class': 'form-control', 'placeholder' : 'Bag SL No. From',}
        self.fields['sl_no_to'].widget.attrs = {
            'class': 'form-control', 'placeholder' : 'Bag SL No. To',}
        self.fields['bag_weight_kg'].widget.attrs = {
            'class': 'form-control', 'placeholder' : 'Bag Weight (in Kg.)',}
        self.fields['mark'].widget.attrs = {
            'class': 'form-control',}
        
        if blf_user_id:
            self.fields['mark'].queryset = BlfTeaProduction.objects.filter(blf_id=blf_user_id)
    
    def clean(self):
        cleaned_data = super(LotBatchForm, self).clean()
        bag_sl_no_from = self.cleaned_data.get('bag_sl_no_from')
        sl_no_to = self.cleaned_data.get('sl_no_to')
        
        # print("BLF USER####",self.blf_user_id)
        blf_user=self.blf_user_id

        if self.instance.id:
            tot_range_list = LotBatchDetails.cmobjects.filter(created_by__username=blf_user).exclude(id=self.instance.id)
        else:
            tot_range_list = LotBatchDetails.cmobjects.filter(created_by__username=blf_user)

        range_list = []

        for i in tot_range_list:
            for j in range(i.bag_sl_no_from, i.sl_no_to + 1):
                range_list.append(j)
            
        if bag_sl_no_from and bag_sl_no_from > sl_no_to:
                raise ValidationError({'bag_sl_no_from': ["Can not greater than " + str(sl_no_to)]})
        
        if sl_no_to and bag_sl_no_from > sl_no_to:
                raise ValidationError({'sl_no_to': ["Can not less than " + str(bag_sl_no_from)]})

        if bag_sl_no_from in range_list:
            raise ValidationError({'bag_sl_no_from': [str(bag_sl_no_from) +" alraedy Exists" ]})
    
        if sl_no_to in range_list:
            raise ValidationError({'sl_no_to': [str(sl_no_to) +" alraedy Exists" ]})
        
        return cleaned_data









        
    

