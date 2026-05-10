from django import forms
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.forms import inlineformset_factory
from django.forms import ModelForm, Textarea

from .models import *

class RegionForm(forms.ModelForm):
	""" Region Create Form @vivek"""

	def __init__(self, *args, **kwargs):
		super(RegionForm, self).__init__(*args, **kwargs)

		for field in self.fields.values():
			field.widget.attrs = {"class": "form-control"}
		self.fields['region_name'].widget.attrs = {'class': 'form-control', 'placeholder': "Region Name", 'required': 'required'}
		self.fields['abbrevation'].widget.attrs = {'class': 'form-control', 'placeholder': "Abbreviation", 'required': 'required'}
		self.fields['state'].widget.attrs = {
			'class': 'select2_demo_3 form-control', 'multiple': 'multiple', 'required': 'required', 'id': 'id_state'}

	class Meta:
		model = Region
		fields = ('state', 'region_name', 'abbrevation',)

	def clean_region_name(self):
		region_name = self.cleaned_data.get('region_name')
		qs = Region.objects.filter(region_name__iexact=region_name, is_deleted=False)
		if self.instance and self.instance.pk:
			qs = qs.exclude(pk=self.instance.pk)
		if qs.exists():
			raise ValidationError('This region name already exists. Please choose a different name.')
		return region_name



class WarehouseManagementForm(forms.ModelForm):
	""" Warehouse Management Create Form @vivek"""

	def __init__(self, *args, **kwargs):
		
		super(WarehouseManagementForm, self).__init__(*args, **kwargs)

		# for field in self.fields.values():
		# 	field.widget.attrs = {"class": "form-control"}
		self.fields['name'].widget.attrs = {'class': 'form-control', 'placeholder' : "Warehoue Name",'required' : 'required' }
		self.fields['address'].widget.attrs = {'class': 'form-control', 'placeholder' : "Address"}

		self.fields['warehouse_type'].widget.attrs = {
            'class': 'select2_demo_1 form-control','required' : 'required' , 'id' : 'select2-warehouse_type'}
	
	class Meta:
		model = WarehouseManagement
		fields = ('warehouse_type','name', 'address', 
	     
	     )
		# widgets = {
        #     'address': Textarea(attrs={'rows':80, 'cols':20}),
        # }
