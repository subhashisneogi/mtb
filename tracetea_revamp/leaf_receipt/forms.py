from django import forms
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.forms import inlineformset_factory
from django.forms import ModelForm, Textarea
from .models import *


class DateInput(forms.DateInput):
    """
    Widgets support for date input
    """
    input_type = 'date'


class LeafManagementForm(forms.ModelForm):
	""" Leaf Receipt Create Form @vivek"""

	def __init__(self, *args, **kwargs):
		user_id = kwargs.pop('user_id', None)
		weighted_id = kwargs.pop('weighted_id', None)
		super(LeafManagementForm, self).__init__(*args, **kwargs)
		self.fields['acknowledge_status'].required = True
		self.fields['deduction'].required = True
		self.fields['final_leaf_count'].required = True
		self.fields['payment_record_option'].required = True


		self.fields['weighment_txn'].widget.attrs = {
            'class': 'select2_demo_1 form-control', 'required' : 'required', 'id' : 'weighment_txn'}
		self.fields['supply_date'].widget.attrs = {
            'class': 'form-control', 'id' : 'supply_date'}
		self.fields['deduction'].widget.attrs = {'class': 'form-control', 'placeholder' : "Deduction in percentage", 'step' : '0.01'}
		self.fields['final_leaf_count'].widget.attrs = {'class': 'form-control', 'placeholder' : "Final leaf count in percentage", 'step' : '0.01'}
		self.fields['rate'].widget.attrs = {'class': 'form-control', 'placeholder' : "Rate in Rs.", 'id' : 'rate'}
		self.fields['acknowledge_status'].widget.attrs = {
            'class': 'select2_demo_1 form-control' ,'id' : 'select2-acknowledge_status'}
		self.fields['quality_standard'].widget.attrs = {
            'class': 'select2_demo_1 form-control','id' : 'select2-quality_standard'}
		self.fields['payment_record_option'].widget.attrs = {
            'class': 'select2_demo_1 form-control','id' : 'payment_record_option'}
		

		if weighted_id:
			from django.db.models import Q
			weight_ids = list(WeighmentSupply.cmobjects.filter(created_by=user_id, \
									    is_processed=False).values_list('id', flat=True))
			weight_ids.append(weighted_id)
			self.fields['weighment_txn'].queryset = WeighmentSupply.cmobjects.filter(id__in=weight_ids).order_by('-id')
		else:
			self.fields['weighment_txn'].queryset = WeighmentSupply.cmobjects.filter(created_by=user_id, \
									    is_processed=False).order_by('-id')

	class Meta:
		model = LeafManagement
		fields = ('weighment_txn', 'supply_date','deduction', 'final_leaf_count','rate', 'acknowledge_status', 'quality_standard',\
	     'payment_record_option'
	     )
		widgets = {
	    	'supply_date': DateInput(),
        }