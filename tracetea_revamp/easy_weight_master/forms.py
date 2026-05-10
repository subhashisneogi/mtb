from django import forms
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.forms import inlineformset_factory
from django.forms import ModelForm, Textarea

from .models import *
class DateInput(forms.DateInput):
    # input_type = 'year'
    input_type='month'

class EasyWeightForm(forms.ModelForm):
   
    def __init__(self, *args, **kwargs):
		
        super(EasyWeightForm, self).__init__(*args, **kwargs  )      
        # for field in self.fields.values():
        # 	field.widget.attrs = {"class": "form-control"}

        self.fields['collection_center'].widget.attrs = {
            'class': 'select2_demo_1 form-control','required' : 'required' , 'id' : 'select2-collection_center'}
        self.fields['month_year'].widget.attrs = {'class': 'form-control', 'required' : 'required','placeholder' : "Month Year"}
    class Meta:
        model = EasyWeightMaster
        fields = ('collection_center', 'month_year',

         )
       
        widgets = {

            'month_year': DateInput(),

        }