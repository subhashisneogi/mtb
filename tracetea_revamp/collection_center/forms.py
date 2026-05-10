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


class CollectionCenterForm(forms.ModelForm):
    """
    Collection Center Form
    """
    class Meta:
        model = CollectionCenter
        fields = ('name',)

    def __init__(self, *args, **kwargs):
        super(CollectionCenterForm, self).__init__(*args, **kwargs)

        self.fields['name'].required = True

        self.fields['name'].widget.attrs = {
            'class': 'form-control', 'placeholder' : 'Name'}

        
