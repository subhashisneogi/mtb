"""
Forms
"""
from django import forms
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.forms import inlineformset_factory

from django.forms.models import inlineformset_factory
from django.forms.models import BaseInlineFormSet



from .models import *


class DateInput(forms.DateInput):
    """
    Widgets support for date input
    """
    input_type = 'date'



class GardenForm(forms.ModelForm):
    """
    Garden Create Category Form
    """
    class Meta:
        model = Gardens
        fields = ['name', 'grower', 'land_type', 'production_area', 'is_division', 'is_plot']

    def __init__(self, *args, **kwargs):
        super(GardenForm, self).__init__(*args, **kwargs)

        self.fields['grower'].required = False
        self.fields['land_type'].required = False
        self.fields['name'].required = True
        self.fields['production_area'].required = False
        self.fields['grower'].widget.attrs = {
            'class': 'select2_demo_1 form-control', 'required' : 'required' , 'id' : 'select2-grower'}
        self.fields['land_type'].widget.attrs = {
            'class': 'select2_demo_2 form-control', 'id' : 'select2-land_type'}
        self.fields['name'].widget.attrs = {
            'class': 'form-control', 'placeholder' : 'Name', 'required' : 'required'}
        self.fields['production_area'].widget.attrs = {
            'class': 'form-control', 'placeholder' : 'Production Area (hec)',}
        self.fields['is_division'].widget.attrs = {'class': 'js-switch_1', }
        self.fields['is_plot'].widget.attrs = {'class': 'js-switch_2', }






class UserGardenForm(forms.ModelForm):
    """
    Garden Create Category Form
    """
    class Meta:
        model = Gardens
        fields = ['name', 'user', 'land_type', 'production_area', 'is_division', 'is_plot', 'estate_total_area']

    def __init__(self, *args, **kwargs):
        super(UserGardenForm, self).__init__(*args, **kwargs)

 
        self.fields['land_type'].required = False
        self.fields['name'].required = True
        self.fields['production_area'].required = False
        self.fields['land_type'].widget.attrs = {
            'class': 'select2_demo_2 form-control', 'id' : 'select2-land_type'}
        self.fields['name'].widget.attrs = {
            'class': 'form-control', 'placeholder' : 'Name', 'required' : 'required'}
        self.fields['production_area'].widget.attrs = {
            'class': 'form-control', 'placeholder' : 'Production Area (hec)',}
        self.fields['is_division'].widget.attrs = {'class': 'js-switch_1', }
        self.fields['is_plot'].widget.attrs = {'class': 'js-switch_2', }
        self.fields['estate_total_area'].widget.attrs = {
            'class': 'form-control', 'placeholder' : 'Total Area (hec)',}



class PlotDetailsForm(forms.ModelForm):
    """
    Plot Details Form
    """
    class Meta:
        model = Plot
        fields = ('name', 'plot_area')

    def __init__(self, *args, **kwargs):
        super(PlotDetailsForm, self).__init__(*args, **kwargs)


        self.fields['name'].widget.attrs = {'class': 'form-control', 'placeholder' : "*Name", 'id' : "plot_name_id"}
        self.fields['plot_area'].widget.attrs = {'class': 'form-control', 'placeholder' : "Plot Area"}







class DivisionForm(forms.ModelForm):
    """
    Division Details Form 
    """
    class Meta:
        model = Division
        fields = ('name',)

    def __init__(self, *args, **kwargs):
        garden_pk = kwargs.pop('garden_pk', None)
        super(DivisionForm, self).__init__(*args, **kwargs)

        self.fields['name'].required = True
        self.fields['name'].widget.attrs = {'class': 'form-control', 'placeholder' : "Division Name", }


    # def name_title(self):
    #     costcenter_title = self.cleaned_data.get('costcenter_title')
    #     if costcenter_title and CostCenter.objects.filter(costcenter_title=costcenter_title).exists():
    #         raise ValidationError(u'This Cost Center is already exists')
    #     return costcenter_title







        
class SectionDetailsForm(forms.ModelForm):
    """
    Section Details Form
    """
    class Meta:
        model = Section
        fields = ('name', 'section_area', )

    def __init__(self, *args, **kwargs):
        garden_pk = kwargs.pop('garden_pk', None)
        super(SectionDetailsForm, self).__init__(*args, **kwargs)

        self.fields['name'].required = True
        self.fields['name'].widget.attrs = {'class': 'form-control', 'placeholder' : "Name", 'required' : 'required'}
        self.fields['section_area'].widget.attrs = {'class': 'form-control', 'step' : 'any', 'placeholder' : "Section Area", "onchange": "product_type_change(this)"}
        # self.fields['garden'].queryset = Gardens.objects.filter(id=garden_pk).first()

    # def area_clean(self):
    #     super(SectionDetailsForm, self).clean()
    #     areas = []
    #     for form in self.forms:
    #         section_area = form.cleaned_data['section_area']
    #         areas.append(section_area)
    #     total_area = 124
    #     if areas > 124:
    #         raise ValidationError(u'This Cost Center is already exists')
    #     return areas

     
class BaseSectionDetailsForm(BaseInlineFormSet):

    def clean(self):
        super(SectionDetailsForm, self).clean()
        areas = []
        for form in self.forms:
            section_area = form.cleaned_data.get['section_area']
            areas.append(section_area)
        total_area = 124
        if int(areas) > 124:
            raise ValidationError('This Cost Center is already exists')




        


PLOT_DETAILS_FORM_SET = inlineformset_factory(
    Gardens,
    Plot,
    form=PlotDetailsForm,
    extra=0,
    min_num=1,
    max_num=100,
    validate_max=True,
    can_delete=True
)


SECTION_DETAILS_FORM_SET = inlineformset_factory(
    Division,
    Section,
    form=SectionDetailsForm,
    extra=0,
    min_num=1,
    max_num=100,
    validate_max=True,
    can_delete=True
)


DIVISION_FORM_SET = inlineformset_factory(Gardens, Division, form=DivisionForm, extra=1)
SECTION_FORM_SET = inlineformset_factory(Division, Section, form=SectionDetailsForm, extra=1)

