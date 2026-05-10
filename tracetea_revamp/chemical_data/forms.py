from django import forms
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.forms import inlineformset_factory
from django.forms import ModelForm, Textarea
from .models import *
from user_profile.aggregator_api_models import *
from user_profile.grower_api_models import *
from gardens_managment.models import *

class DateInput(forms.DateInput):
    """
    Widgets support for date input
    """
    input_type = 'date'
    
class TimeInput(forms.TimeInput):
	"""
	Widgets support for Time input
	"""
	input_type = 'time'


class ChemicalDataForm(forms.ModelForm):
	""" Chemical Data Create Form @vivek"""

	def __init__(self, *args, **kwargs):
		self.is_fertilizer = kwargs.pop('is_fertilizer', False)
		super().__init__(*args, **kwargs)
		fertilizer_type = ChemicalType.objects.filter(id=1).first() or ChemicalType.objects.filter(
			name__iexact="Fertilizer"
		).first()

		# Styling
		self.fields['chemical_name'].widget.attrs = {
			'class': 'form-control', 'required': 'required', 'placeholder': "Chemical Name"
		}
		self.fields['manufacturer'].widget.attrs = {
			'class': 'form-control', 'placeholder': "Manufacturer Name"
		}
		self.fields['brand_local_name'].widget.attrs = {
			'class': 'form-control', 'placeholder': "Brand/Local Name"
		}
		self.fields['composition'].widget.attrs = {
			'class': 'form-control', 'placeholder': "Composition"
		}

		self.fields['chemical_type'].widget.attrs = {
			'class': 'select2_demo_1 form-control',
			'required': 'required',
			'id': 'select2-chemical_type'
		}

		# ✅ MAIN LOGIC
		if self.is_fertilizer:
			if fertilizer_type:
				self.fields['chemical_type'].initial = fertilizer_type
				self.fields['chemical_type'].queryset = ChemicalType.objects.filter(id=fertilizer_type.id)

				# 🔥 Hide dropdown (optional but recommended)
				self.fields['chemical_type'].widget = forms.HiddenInput()
			self.fields['chemical_type'].required = False
		else:
			chemical_type_qs = ChemicalType.objects.all()
			if fertilizer_type:
				chemical_type_qs = chemical_type_qs.exclude(id=fertilizer_type.id)
			self.fields['chemical_type'].queryset = chemical_type_qs.order_by('name')

	class Meta:
		model = ChemicalData
		fields = ('chemical_type','chemical_name', 'manufacturer','brand_local_name', 'composition', 
			
			)
		widgets = {
			'address': Textarea(attrs={'rows':80, 'cols':20}),
		}



class UseOfChemicalForm(forms.ModelForm):
	""" Chemical Data Create Form """
	chemical_type_filter = forms.ModelChoiceField(
		queryset=ChemicalType.objects.none(),
		required=False,
		label="Chemical Type",
		empty_label="Select chemical type",
	)

	def __init__(self, *args, **kwargs):
		type_id = kwargs.pop('chemical_type_pk', None)
		grower_pk = kwargs.pop('grower_pk', None)
		garden_pk = kwargs.pop('garden_pk', None)
		grower_details_id = kwargs.pop('grower_details_id', None)
		self.request_user = kwargs.pop("request_user", None)

		super(UseOfChemicalForm, self).__init__(*args, **kwargs)
		# for field in self.fields.values():
		# 	field.widget.attrs = {"class": "form-control"}

		self.fields['date'].required = True
		self.fields['chemical'].required = True
		self.fields['quantity'].required = True
		self.fields['unit'].required = True
		

		self.fields['date'].widget.attrs = {'class': 'form-control',}
		self.fields['chemical'].widget.attrs = {'class': 'form-control select2_chemical', }
		self.fields['labour'].widget.attrs = {'class': 'form-control select2_labour', 'placeholder' : "Labour"}
		self.fields['division'].widget.attrs = {'class': 'form-control select2_division'}
		self.fields['plot'].widget.attrs = {'class': 'form-control select2_plot',}
		non_fertilizer_types = ChemicalType.objects.exclude(name__iexact="Fertilizer").order_by('name')
		self.fields['chemical_type_filter'].queryset = non_fertilizer_types
		self.fields['chemical_type_filter'].widget.attrs = {'class': 'form-control select2_chemical_type'}
		if str(type_id) in ["0", "chemical", "None"]:
			self.fields['chemical'].queryset = ChemicalData.objects.exclude(
				chemical_type__name__iexact="Fertilizer"
			).filter(is_deleted=False).order_by('-id')
			self.fields['chemical_type_filter'].required = True
			if self.instance.pk and self.instance.chemical_id:
				self.fields['chemical_type_filter'].initial = self.instance.chemical.chemical_type_id
		else:
			self.fields['chemical'].queryset = ChemicalData.objects.filter(chemical_type_id=type_id).order_by('-id')
		self.fields['plot'].queryset = Plot.objects.filter(garden_id=garden_pk).order_by('-id')
		self.fields['labour'].queryset = Labour.cmobjects.filter(created_by_id=grower_pk).order_by('-id')
		self.fields['division'].queryset = Division.objects.filter(garden_id=garden_pk).order_by('-id')
		

		self.fields['labour'].queryset = Labour.cmobjects.filter(grower_id=grower_details_id).order_by('-id')

		print("TYPE ID", type_id)

		if type_id == 1:
			self.fields['quantity'].widget.attrs = {	
			'class': 'form-control', 'placeholder' : 'Quantity'}
		else:
			self.fields['quantity'].widget.attrs = {	
			'class': 'form-control', 'placeholder' : 'Quantity'}

	class Meta:	
		model = UseOfChemical
		fields = ('date','chemical', 'labour','plot', 'quantity', 'unit', 'grower', 'division' )
		widgets = {
			'date': DateInput(),

		}
	def clean(self):
		cleaned_data = super().clean()
		date = cleaned_data.get("date")
		chemical = cleaned_data.get("chemical")
		chemical_type_filter = cleaned_data.get("chemical_type_filter")
		labour = cleaned_data.get("labour")
		plot = cleaned_data.get("plot")
		if chemical_type_filter and chemical and chemical.chemical_type_id != chemical_type_filter.id:
			raise forms.ValidationError(
				"Selected chemical data does not belong to the selected chemical type"
			)

		# use the logged-in user instead of cleaned_data.get("created_by")
		created_by = self.request_user

		if all([date, chemical, labour, plot, created_by]):
			qs = UseOfChemical.cmobjects.filter(
				date=date,
				chemical=chemical,
				labour=labour,
				created_by=created_by,
			)
			if self.instance.pk:
				qs = qs.exclude(pk=self.instance.pk)
			if qs.exists():
				raise forms.ValidationError(
					"This chemical has already been recorded for the selected Date, Labour, and Plot"
				)
		return cleaned_data








class PluckingDataForm(forms.ModelForm):
	""" Plucking Data Create Form """
	labours = forms.ModelMultipleChoiceField(
		queryset=Labour.cmobjects.none(),
		required=True,
		label="Labours",
		widget=forms.SelectMultiple(attrs={
			"class": "form-control select2_labours",
			"data-placeholder": "Select labours",
		}),
	)

	def __init__(self, *args, **kwargs):
		grower_pk = kwargs.pop('grower_pk', None)
		garden_pk = kwargs.pop('garden_pk', None)
		grower_details_id = kwargs.pop('grower_details_id', None)
		super(PluckingDataForm, self).__init__(*args, **kwargs)

		self.fields['date'].required = True
		self.fields['date'].widget.attrs = {'class': 'form-control',}
		self.fields['start_time'].widget.attrs = {'class': 'form-control', 'placeholder' : "Start Time", 'id' : 'start_time'}
		self.fields['end_time'].widget.attrs = {'class': 'form-control', 'placeholder' : "End Time", 'id' : 'end_time', 'onchange' : 'Compare()'}
		self.fields['division'].widget.attrs = {
            'class': 'select2_demo_1 form-control',}
		self.fields['plot'].widget.attrs = {'class': 'form-control', }
		self.fields['area_plucked'].widget.attrs = {
            'class': 'form-control', 'placeholder' : "Area Plucked"}
		self.fields['quantity_plucked'].widget.attrs = {
            'class': ' form-control', 'placeholder' : "Quantity Plucked"}
		
		self.fields['plot'].queryset = Plot.objects.filter(garden_id=garden_pk).order_by('-id')
		self.fields['labours'].queryset = Labour.cmobjects.filter(grower_id=grower_details_id).order_by('name')
		if self.instance and self.instance.pk:
			selected_labours = self.instance.labours.all()
			if selected_labours.exists():
				self.fields['labours'].initial = selected_labours
			elif self.instance.labour_id:
				self.fields['labours'].initial = [self.instance.labour_id]


	
	class Meta:
		model = PluckingData
		fields = ('date','start_time', 'end_time','plot', 'division', 'area_plucked', 'quantity_plucked', 'labours')
		widgets = {
            'date': DateInput(),
	    	'start_time' : TimeInput(),
		    'end_time' : TimeInput(),
        }

	def save(self, commit=True):
		instance = super().save(commit=False)
		selected_labours = list(self.cleaned_data.get("labours") or [])
		instance.labour = selected_labours[0] if selected_labours else None
		if commit:
			instance.save()
			self.save_m2m()
		return instance


class LabourDataForm(forms.ModelForm):
	""" Plucking Data Create Form """
	def __init__(self, *args, **kwargs):
		
		super(LabourDataForm, self).__init__(*args, **kwargs)

		self.fields['name'].required = True

		self.fields['name'].widget.attrs = {'class': 'form-control', 'placeholder' : "Name"  }
		self.fields['type'].widget.attrs = {'class': 'form-control',}
		self.fields['gender'].widget.attrs = {'class': 'form-control', }
		self.fields['age'].widget.attrs = {'class': 'form-control', 'placeholder' : "Age" }
		
	class Meta:
		model = Labour
		fields = ('name','type', 'gender', 'age' )
		widgets = {
            # 'date': DateInput(),
        }


class MonthlyScheduleForm(forms.ModelForm):
	""" Monthly Schedule  Create Form """
	def __init__(self, *args, **kwargs):
		
		super(MonthlyScheduleForm, self).__init__(*args, **kwargs)

		self.fields['year'].required = True
		self.fields['month'].required = True
		self.fields['hourly_rate'].required = True
		self.fields['monthly_wages'].required = True

		self.fields['year'].widget.attrs = {'class': 'form-control', 'placeholder' : "Name"  }
		self.fields['month'].widget.attrs = {'class': 'form-control',}
		self.fields['no_of_working_days'].widget.attrs = {'class': 'form-control', 'placeholder' : "Total no. of working days", 'readonly': 'readonly' }
		self.fields['total_hours'].widget.attrs = {'class': 'form-control', 'placeholder' : "Total Hours", 'readonly': 'readonly' }
		self.fields['hourly_rate'].widget.attrs = {'class': 'form-control', 'placeholder' : "Hourly Rate" }
		self.fields['monthly_wages'].widget.attrs = {'class': 'form-control', 'placeholder' : "Monthly Wages", 'readonly': 'readonly' }
		
		
	class Meta:
		model = MonthlySchedule
		fields = ('year','month', 'no_of_working_days', 'total_hours', 'hourly_rate', 'monthly_wages' )
		widgets = {
            # 'date': DateInput(),
        }



class MapAreaDetailsForm(forms.ModelForm):
	"""Map Area Details  Create Form """
	def __init__(self, *args, **kwargs):
		
		super(MapAreaDetailsForm, self).__init__(*args, **kwargs)

		self.fields['map_image'].required = True
		self.fields['water_source'].required = True
		self.fields['land_near_by'].required = True

		self.fields['map_image'].widget.attrs = {'class': 'form-control',}
		self.fields['water_source'].widget.attrs = {'class': 'form-control', }
		self.fields['land_near_by'].widget.attrs = {'class': 'form-control', }
		
	class Meta:
		model = MapAreaMaster
		fields = ('blf', 'grower', 'aggregator', 'map_image','water_source', 'land_near_by', 'is_image_upload', 'is_digital_upload')
		widgets = {
            # 'date': DateInput(),
        }


class ManualMapUploadForm(forms.ModelForm):
	total_area = forms.FloatField(
		required=True,
		min_value=0.1,
		label="Total Area",
		widget=forms.NumberInput(attrs={
			"class": "form-control",
			"placeholder": "Total Area",
			"step": "0.01",
			"min": "0.1",
		}),
	)

	def __init__(self, *args, **kwargs):
		initial_total_area = kwargs.pop("initial_total_area", None)
		super().__init__(*args, **kwargs)
		self.fields["map_image"].required = not bool(self.instance and self.instance.pk and self.instance.map_image)
		self.fields["map_image"].widget.attrs = {"class": "form-control", "accept": "image/*"}
		self.fields["land_near_by"].required = True
		self.fields["land_near_by"].label = "Map Details"
		self.fields["land_near_by"].widget = forms.TextInput(attrs={
			"class": "form-control",
			"placeholder": "Enter map details",
		})
		if initial_total_area is not None:
			self.fields["total_area"].initial = initial_total_area

	class Meta:
		model = MapAreaMaster
		fields = ("map_image", "land_near_by", "total_area")
