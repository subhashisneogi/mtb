"""
Forms
"""
from django import forms
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.forms import inlineformset_factory
from django.forms import ModelForm, Textarea

from .models import *
from user_profile.blf_api_models import SupplierExit
from leaf_receipt.models import *

class DateInput(forms.DateInput):
    """
    Widgets support for date input
    """
    input_type = 'date'



class WeighmentSupplyForm(forms.ModelForm):
    """
    Weighment Supply Form
    """

    class Meta:
        model = WeighmentSupply
        fields = ('supplier_type', 'supplier', 'supply_challan', 'mode_of_supply', \
                  'supply_date', 'vehicle_no', 'total_gross_weight_kg', 'mobile_number')
        widgets = {
            'supply_date': forms.DateInput(
                format=('%Y-%m-%d'),
                attrs={'class': 'form-control', 
                    'placeholder': 'Select a date',
                    'type': 'date',
                    'id' : 'supply_date',
                    }),
        }
        
    def __init__(self, *args, **kwargs):
        supplier_details_id = kwargs.pop('supplier_details_id', None)
        super(WeighmentSupplyForm, self).__init__(*args, **kwargs)

        # self.fields['supplier_type'].widget.attrs['disabled'] = True

        self.fields['mode_of_supply'].required = True
        self.fields['total_gross_weight_kg'].required = True

        self.fields['supplier_type'].widget.attrs = {
            'class': 'form-control', 'id' : 'supplier_type_id', 'disabled' : 'disabled'}
        self.fields['supplier'].widget.attrs = {
            'class': 'form-control readonly-field', 'id' : 'supplier', 'disabled' : 'disabled'}
        self.fields['supply_challan'].widget.attrs = {
            'class': 'form-control readonly-field', 'id' : 'supply_challan_id', "input_type" : "text", 'disabled' : 'disabled'}
        self.fields['supply_date'].widget.attrs = {
            'class': 'form-control', 'id' : 'supply_date'}
        self.fields['mobile_number'].widget.attrs = {
            'class': 'form-control',  }
        self.fields['vehicle_no'].widget.attrs = {
            'class': 'form-control readonly-field',  'readonly' : 'readonly', 'id' : 'vehicle_no', 'disabled' : 'disabled'}
        self.fields['total_gross_weight_kg'].widget.attrs = {
            'class': 'form-control', 'id' : 'total_gross_weight_kg_id', 'placeholder' : 'Total Gross Weight (Kg)'}
        
        self.fields['mode_of_supply'].widget.attrs = {
            'class': 'form-control ', 'id' : 'mode_of_supply', 'required': 'required'}
        
        # self.fields['mode_of_supply'].queryset = SupplyManagement.objects.filter(pk=supplier_details_id, )
        
        SupplyManagement.objects.filter(pk=supplier_details_id, vehicle_option="Yes").first()

        print("dewdwd", supplier_details_id)

        # self.fields['supply_challan'].queryset = 


class SupplierExitForm(forms.ModelForm):
    """
    SupplierExit Form
    """
    class Meta:
        model = SupplierExit
        fields = ('weighment_txn', 'unloaded_vehicle_weight', 'date_of_supply', 'is_released', \
                    'net_supplied_qty')
        widgets = {
            'date_of_supply': DateInput(),
        }
        
    def __init__(self, *args, **kwargs):
        user_id = kwargs.pop('user_id', None)
        super(SupplierExitForm, self).__init__(*args, **kwargs)

        self.fields['weighment_txn'].required = True
        self.fields['unloaded_vehicle_weight'].required = True
        self.fields['is_released'].required = True
        self.fields['weighment_txn'].widget.attrs = {
            'class': 'form-control select2_demo_1', 'id' : 'weighment_txn_id'}
        self.fields['unloaded_vehicle_weight'].widget.attrs = {
            'class': 'form-control', 'placeholder' : 'Unloaded Vehicle Weight'}
        self.fields['date_of_supply'].widget.attrs = {
            'class': 'form-control', 'id' : 'supply_challan_id'}
        self.fields['is_released'].widget.attrs = {
            'class': 'form-control'}
        self.fields['net_supplied_qty'].widget.attrs = {    
            'class': 'form-control readonly-field', 'placeholder ' : 'Net Supplied Qty' , 'readonly' : 'readonly'}
        

        leaf_receipt_id = list(LeafManagement.cmobjects.filter(created_by_id=user_id,\
                            acknowledge_status="Received").values_list('weighment_txn', flat=True))
                
        self.fields['weighment_txn'].queryset = WeighmentSupply.cmobjects.filter(id__in=leaf_receipt_id,\
                mode_of_supply= 'Motorised 3 / 4 wheelers vehicle', is_supplier_exit_proceed=False).order_by('-id')


    def clean(self):
        cleaned_data = super(SupplierExitForm, self).clean()

        unloaded_vehicle_weight = self.cleaned_data.get('unloaded_vehicle_weight')
        weighment_txn = self.cleaned_data.get('weighment_txn')
        
        print("unloaded vehicle weight",unloaded_vehicle_weight)
        print("weighment txn", weighment_txn)
        if weighment_txn:
            weighment_details = WeighmentSupply.cmobjects.filter(weighment_txn_id=weighment_txn).first()
            weighment_gross_kg = weighment_details.total_gross_weight_kg
            if unloaded_vehicle_weight >= weighment_gross_kg:
                raise ValidationError({'unloaded_vehicle_weight': ["Can not greater than " + str(weighment_gross_kg)]})
        
        return self.cleaned_data 

