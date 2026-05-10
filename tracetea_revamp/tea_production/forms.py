"""
Forms
"""
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


class TeaGradeForm(forms.ModelForm):
    """
    Tea Grade Form
    """
    class Meta:
        model = TeaGradeDetails
        fields = ('tea_type', 'grade')

    def __init__(self, *args, **kwargs):
        super(TeaGradeForm, self).__init__(*args, **kwargs)

        self.fields['tea_type'].required = True
        self.fields['grade'].required = True
        self.fields['tea_type'].queryset = TeaType.objects.filter(is_deleted=False).order_by('name')

        self.fields['tea_type'].widget.attrs = {
            'class': 'select2_demo_1 form-control', 'id' : 'grade_id'}
        self.fields['grade'].widget.attrs = {
            'class': 'form-control', 'placeholder' : 'Tea Grade',}
        
