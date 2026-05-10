"""
Forms
"""

from django import forms
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.forms import inlineformset_factory
from django.forms import ModelForm, Textarea
from .models import *
from django.contrib.auth import get_user_model
User = get_user_model()
from django.db.models import CharField, Value
from django.db.models.functions import Concat


def scoped_fk_queryset(model, selected_id=None, **filters):
	qs = model.objects.filter(**filters) if filters else model.objects.all()
	if selected_id:
		qs = (qs | model.objects.filter(id=selected_id)).distinct()
	return qs


def scoped_m2m_queryset(model, selected_ids=None, **filters):
	selected_ids = list(selected_ids or [])
	qs = model.cmobjects.filter(**filters) if hasattr(model, "cmobjects") else model.objects.filter(**filters)
	if selected_ids:
		base = model.cmobjects if hasattr(model, "cmobjects") else model.objects
		qs = (qs | base.filter(id__in=selected_ids)).distinct()
	return qs


class DateInput(forms.DateInput):
    """
    Widgets support for date input
    """
    input_type = 'date'


class GrowerProfileForm(forms.ModelForm):
	""" Employee Profile Create Form """

	def __init__(self, *args, **kwargs):
		user_create_pk = kwargs.pop('user_create_pk', None)
		logged_user_id = kwargs.pop('logged_user', None)
		super(GrowerProfileForm, self).__init__(*args, **kwargs)

		self.fields['grower_type'].widget.attrs = {'class': 'select2_demo form-control', 'id' : 'id_grower_type'}
		
		self.fields['voter_id'].required = False
		self.fields['name'].required = True
		self.fields['mobile_number'].required = False
		self.fields['grower_type'].required = True
		self.fields['state'].required = True
		self.fields['district'].required = True
		self.fields['region'].required = True
		self.fields['village_or_town'].required = False
		self.fields["age"].widget.attrs["readonly"] = False
		self.fields["gender"].required = True

		
		for field in self.fields.values():
			field.widget.attrs = {"class": "form-control"}

		self.fields['name'].widget.attrs = {'class': 'form-control', 'placeholder' : "Name"}
		self.fields['mobile_number'].widget.attrs = {'class': 'form-control', 'placeholder' : "Mobile No"}
		self.fields['certificate_no'].widget.attrs = {'class': 'form-control', 'placeholder' : "Certificate No."}
		self.fields['region'].widget.attrs = {'class': 'form-control', 'placeholder' : "Region", 'id' : 'id_region'}
		self.fields['state'].widget.attrs = {'class': 'form-control', 'placeholder' : "State"}
		self.fields['district'].widget.attrs = {'class': 'form-control', 'placeholder' : "District"}
		self.fields['address'].widget.attrs = {'class': 'form-control', 'placeholder' : "Address"}
		self.fields['village_or_town'].widget.attrs = {'class': 'form-control', 'placeholder' : "Village or Town"}
		self.fields['postoffice'].widget.attrs = {'class': 'form-control', 'placeholder' : "Post office."}
		self.fields['pincode'].widget.attrs = {'class': 'form-control', 'placeholder' : "Pincode"}
		self.fields['voter_id'].widget.attrs = {'class': 'form-control', 'placeholder' : "Voter ID"}
		self.fields['aadhar_no'].widget.attrs = {'class': 'form-control', 'placeholder' : "Aadhar No."}
		self.fields['trustea_id'].widget.attrs = {'class': 'form-control', 'placeholder' : "Trust tea id"}
		self.fields['existing_trust_tea_id'].widget.attrs = {'class': 'form-control', 'placeholder' : "Existing trust tea id"}
		self.fields['father_name'].widget.attrs = {'class': 'form-control', 'placeholder' : "Father's Name"}
		self.fields['date_of_birth'].widget.attrs = {'class': 'form-control', 'placeholder' : "MM/DD/YYYY", 'id' : 'date_of_birth', 'onchange' : 'ageCalculator(this)'}
		self.fields['age'].widget.attrs = {'class': 'form-control readonly-field', 'placeholder' : "Age", 'readonly' : 'readonly', 'id' : 'age'}
		self.fields['tea_board_id'].widget.attrs = {'class': 'form-control', 'placeholder' : "Tea board id"}
		self.fields['total_male_worker'].widget.attrs = {'class': 'form-control', 'placeholder' : "Total male worker"}
		self.fields['total_female_worker'].widget.attrs = {'class': 'form-control', 'placeholder' : "Total female worker"}
		self.fields['estimated_production_of_green_tea'].widget.attrs = {'class': 'form-control', 'placeholder' : "Estimated production of green tea"}
		self.fields['estimated_production_of_made_tea'].widget.attrs = {'class': 'form-control', 'placeholder' : "Estimated production of made tea"}
		self.fields['additional_information'].widget.attrs = {'class': 'form-control', 'placeholder' : "Additional information", 'id' : 'id_additional_information'}
		# self.fields['state'].queryset = State.objects.none()

		self.fields['region'].queryset = Region.objects.filter(is_deleted=False).order_by('region_name')
		if self.instance and self.instance.pk:
			self.fields['state'].queryset = scoped_fk_queryset(State, getattr(self.instance, "state_id", None)).order_by('name')
			self.fields['district'].queryset = scoped_fk_queryset(District, getattr(self.instance, "district_id", None), state_id=getattr(self.instance, "state_id", None)).order_by('name')
		self.fields['associated_unit'].widget.attrs = {'class': 'form-control'}

		self.fields['associated_entity'].widget.attrs = {'class': 'form-control select2_ass_entity', 'id' : 'associated_entity'}
		
		self.fields['associated_aggregator'].widget.attrs = {'class': 'form-control select2_ass_agg', 'id' : 'id_aggregator'}
		selected_aggregators = self.instance.associated_aggregator.values_list("id", flat=True) if self.instance and self.instance.pk else []
		selected_entities = self.instance.associated_entity.values_list("id", flat=True) if self.instance and self.instance.pk else []
		aggregator_filters = {"user__is_active": True}
		if self.instance and self.instance.region_id:
			aggregator_filters["region_id"] = self.instance.region_id
		self.fields['associated_aggregator'].queryset = scoped_m2m_queryset(
			AggregatorProfile,
			selected_aggregators,
			**aggregator_filters,
		).order_by('user__username')
		
		# self.fields['associated_aggregator'].queryset = AggregatorProfile.objects.all().annotate(Name=Concat(str('name'), 
        #   Value(' - '), 'user__username', output_field=CharField())).values_list('Name', flat=True).order_by('-id')

		entity_filters = {}
		if self.instance and self.instance.region_id:
			entity_filters["region_id"] = self.instance.region_id
		self.fields['associated_entity'].queryset = scoped_m2m_queryset(
			BlfProfile,
			selected_entities,
			**entity_filters,
		).order_by('user__username')

	
		if 'region' in self.data:
			try:
				region_id = int(self.data.get('region'))
				self.fields['associated_entity'].queryset = BlfProfile.cmobjects.filter(region_id=region_id).order_by('-id')
				# associated_entity_id = BlfProfile.cmobjects.filter(id=associated_entity_id).values('id')

				# for data in associated_entity_id:
				# 	data=data.get('id')
				# 	print(data)
				# 	self.fields['associated_aggregator'].queryset=AggregatorProfile.cmobjects.none()

			except (ValueError, TypeError):
				pass  # invalid input from the client; ignore and fallback to empty City queryset

		elif self.instance.pk:
			pass

		if 'state' in self.data:
			try:
				state_id = int(self.data.get('state'))
				self.fields['state'].queryset=State.objects.filter(id=state_id).order_by('name')
				state_id=State.objects.filter(id=state_id).values('id')
				
				for data in state_id:
					data=data.get('id')
					self.fields['district'].queryset=District.objects.filter(state_id=data).order_by('name')
			except (ValueError, TypeError):
				pass  # invalid input from the client; ignore and fallback to empty City queryset

	class Meta:
		model = GrowerProfile
		fields = ('name', 'mobile_number', 'grower_type', 'certificate_no', 'region', 'state', 'district', 'address', 'village_or_town', 
	    		'postoffice', 'pincode', 'voter_id', 'aadhar_no', 'trustea_id', 'existing_trust_tea_id', 'associated_entity',
				'associated_aggregator', 'associated_unit', 'father_name', 'date_of_birth', 'age', 'gender', 'tea_board_id',
	    		'total_male_worker', 'total_female_worker', 'estimated_production_of_green_tea', 'estimated_production_of_made_tea',
			    'id_proof_type', 'id_proof_file', 'additional_information', 'photo',
		  )
		
		widgets = {
            'address': Textarea(attrs={'rows':80, 'cols':20}),
	    	'date_of_birth': DateInput(),
        }


class GrowerIDProofAttachmentForm(forms.ModelForm):
	"""Multiple ID proof upload form for grower profile edit."""

	class Meta:
		model = UserProfileAttachments
		fields = ("attachment_name", "doc_no", "attachment")
		widgets = {
			"attachment_name": forms.Select(attrs={"class": "form-control proof-type"}),
			"doc_no": forms.TextInput(attrs={"class": "form-control", "placeholder": "Document number"}),
			"attachment": forms.ClearableFileInput(attrs={"class": "form-control proof-file"}),
		}

	def clean(self):
		cleaned_data = super().clean()
		if cleaned_data.get("DELETE"):
			return cleaned_data

		attachment_name = cleaned_data.get("attachment_name")
		doc_no = cleaned_data.get("doc_no")
		attachment = cleaned_data.get("attachment")
		has_existing_file = bool(getattr(self.instance, "attachment", None))
		has_any_value = bool(attachment_name or doc_no or attachment or has_existing_file)

		if not has_any_value:
			return cleaned_data

		if not attachment_name:
			self.add_error("attachment_name", "Select ID proof type.")
		if not doc_no:
			self.add_error("doc_no", "Enter document number.")
		if not attachment and not has_existing_file:
			self.add_error("attachment", "Upload ID proof document.")
		return cleaned_data


GrowerIDProofAttachmentFormSet = inlineformset_factory(
	GrowerProfile,
	UserProfileAttachments,
	form=GrowerIDProofAttachmentForm,
	extra=1,
	can_delete=True,
)


class AggregatorProfileForm(forms.ModelForm):
	""" Aggregator Profile Create Form @vivek"""

	def __init__(self, *args, **kwargs):
		user_create_pk = kwargs.pop('user_create_pk', None)
		logged_user_id = kwargs.pop('logged_user', None)
		super(AggregatorProfileForm, self).__init__(*args, **kwargs)
		

		self.fields['state'].required = True
		self.fields['district'].required = True
		self.fields['region'].required = True
		self.fields['name'].required = True
		self.fields['mobile_number'].required = False

		# self.fields['grower_type'].required = True
		# self.fields['grower_type'].required = True
		# self.fields['grower_type'].required = True

		self.fields['aggregator_type'].widget.attrs = {'class': 'select2_demo form-control', 'id' : 'aggregator_type'}
		# self.fields['associated_entity'].widget.attrs = {'class': 'select2_demo form-control', 'id' : 'associated_entity'}
		# self.fields['state'].widget.attrs = {'class': 'select2_demo form-control', 'id' : 'state'}
		# self.fields['district'].widget.attrs = {'class': 'select2_demo form-control', 'id' : 'district'}
		for field in self.fields.values():
			field.widget.attrs = {"class": "form-control"}
		self.fields['name'].widget.attrs = {'class': 'form-control', 'placeholder' : "Name"}
		self.fields['mobile_number'].widget.attrs = {'class': 'form-control', 'placeholder' : "Mobile No"}
		# self.fields['aggregator_type'].widget.attrs = {'class': 'form-control', 'placeholder' : "Aggregator Type"}
		self.fields['region'].widget.attrs = {'class': 'form-control', 'placeholder' : "Region"}
		# self.fields['state'].widget.attrs = {'class': 'form-control', 'placeholder' : "State"}
		# self.fields['district'].widget.attrs = {'class': 'form-control', 'placeholder' : "District"}
		self.fields['address'].widget.attrs = {'class': 'form-control', 'placeholder' : "Address"}
		self.fields['associated_entity'].widget.attrs = {'class': 'form-control js-example-basic-multiple', 'id' : 'associated_entity'}
		self.fields['gstin_no'].widget.attrs = {'class': 'form-control', 'placeholder' : "GSTIN NO."}
		# self.fields['state'].queryset = State.objects.none()
		# self.fields['district'].queryset = District.objects.none()	
		# self.fields['associated_entity'].queryset = AssociatedEntity.objects.none()
		self.fields['region'].queryset = Region.objects.filter(is_deleted=False).order_by('region_name')
		if self.instance and self.instance.pk:
			self.fields['state'].queryset = scoped_fk_queryset(State, getattr(self.instance, "state_id", None)).order_by('name')
			self.fields['district'].queryset = scoped_fk_queryset(District, getattr(self.instance, "district_id", None), state_id=getattr(self.instance, "state_id", None)).order_by('name')

		selected_entities = self.instance.associated_entity.values_list("id", flat=True) if self.instance and self.instance.pk else []
		entity_filters = {"user__is_active": True}
		if self.instance and self.instance.region_id:
			entity_filters["region_id"] = self.instance.region_id
		self.fields['associated_entity'].queryset = scoped_m2m_queryset(
			BlfProfile,
			selected_entities,
			**entity_filters,
		).order_by('user__username')
	
		if 'state' in self.data :
			try:
				state_id = int(self.data.get('state'))
				self.fields['state'].queryset=State.objects.filter(id=state_id).order_by('name')
				state_id=State.objects.filter(id=state_id).values('id')
				
				for data in state_id:
					data=data.get('id')
					self.fields['district'].queryset=District.objects.filter(state_id=data).order_by('name')
			except (ValueError, TypeError):
				pass  # invalid input from the client; ignore and fallback to empty City queryset
		
		
	class Meta:
		model = AggregatorProfile
		fields = ('name', 'email','mobile_number', 'aggregator_type', 'region', 'state', 'district',
	     'address', 'associated_entity', \
	     'gstin_no', 'user_file'
	     
	     )
		widgets = {
            'address': Textarea(attrs={'rows':80, 'cols':20}),
        }
		

class BlfProfileForm(forms.ModelForm):
	""" BLF Profile Create Form """

	def __init__(self, *args, **kwargs):
		user_create_pk = kwargs.pop('user_create_pk', None)
		logged_user_id = kwargs.pop('logged_user', None)
		super(BlfProfileForm, self).__init__(*args, **kwargs)

		for field in self.fields.values():
			field.widget.attrs = {"class": "form-control"}

		self.fields['state'].required = True
		self.fields['district'].required = True
		self.fields['region'].required = True
		self.fields["entity_unit"].required = True

		self.fields['entity_name'].widget.attrs = {'class': 'form-control', 'placeholder' : "Entity Name"}
		self.fields['entity_unit'].widget.attrs = {'class': 'form-control', 'placeholder' : "Unit Name"}
		self.fields['certificate_no'].widget.attrs = {'class': 'form-control', 'placeholder' : "Certificate No"}
		self.fields['region'].widget.attrs = {'class': 'form-control', 'placeholder' : "Region"}
		self.fields['address'].widget.attrs = {'class': 'form-control', 'placeholder' : "Address"}
		self.fields['ho_contact_number'].widget.attrs = {'class': 'form-control', 'placeholder' : "Contact Number"}
		self.fields['ho_contact_person'].widget.attrs = {'class': 'form-control', 'placeholder' : "Contact Person"}
		self.fields['ho_contact_email'].widget.attrs = {'class': 'form-control', 'placeholder' : "Email Address"}
		self.fields['garden_contact_number'].widget.attrs = {'class': 'form-control', 'placeholder' : "Contact Number"}
		self.fields['garden_contact_person'].widget.attrs = {'class': 'form-control', 'placeholder' : "Contact Person"}
		self.fields['garden_contact_email'].widget.attrs = {'class': 'form-control', 'placeholder' : "Email Address"}
		self.fields['manager_contact_number'].widget.attrs = {'class': 'form-control', 'placeholder' : "Contact Number"}
		self.fields['manager_contact_person'].widget.attrs = {'class': 'form-control', 'placeholder' : "Contact Person"}
		self.fields['manager_contact_email'].widget.attrs = {'class': 'form-control', 'placeholder' : "Email Address"}
		self.fields['trust_tea_officer_contact_number'].widget.attrs = {'class': 'form-control', 'placeholder' : "Contact Number"}
		self.fields['trust_tea_officer_contact_person'].widget.attrs = {'class': 'form-control', 'placeholder' : "Contact Person"}
		self.fields['trust_tea_officer_contact_email'].widget.attrs = {'class': 'form-control', 'placeholder' : "Email Address"}
		self.fields['data_operator_contact_number'].widget.attrs = {'class': 'form-control', 'placeholder' : "Contact Number"}
		self.fields['data_operator_contact_person'].widget.attrs = {'class': 'form-control', 'placeholder' : "Contact Person"}
		self.fields['data_operator_contact_email'].widget.attrs = {'class': 'form-control', 'placeholder' : "Email Address"}
		self.fields['factory_details_likely_production'].widget.attrs = {'class': 'form-control', 'placeholder' : "in Mn.kg", "step" : '0.01'}
		# self.fields['factory_details_marks'].widget.attrs = {'class': 'form-control select2_demo_marks', 'placeholder' : "Marks"}
		self.fields['factory_details_other_certificate'].widget.attrs = {'class': 'form-control', 'placeholder' : "Certificate No."}
		self.fields['ownership_details_managing_company'].widget.attrs = {'class': 'form-control', 'placeholder' : "Managing company"}
		self.fields['ownership_details_name_of_tea_company'].widget.attrs = {'class': 'form-control', 'placeholder' : "Name of tea company"}
		self.fields['ownership_details_email'].widget.attrs = {'class': 'form-control', 'placeholder' : "Mailing Address"}
		self.fields['user_file'].widget.attrs = {'class': 'file-upload'}

			
		self.fields['region'].queryset = Region.objects.filter(is_deleted=False)

		if 'state' in self.data:
			try:
				state_id = int(self.data.get('state'))
				self.fields['state'].queryset=State.objects.filter(id=state_id).order_by('name')
				state_id=State.objects.filter(id=state_id).values('id')
				
				for data in state_id:
					data=data.get('id')
					print(data)
					self.fields['district'].queryset=District.objects.filter(state_id=data).order_by('name')
			except (ValueError, TypeError):
				pass  # invalid input from the client; ignore and fallback to empty City queryset

	class Meta:
		model = BlfProfile

		fields = ('certificate_no', 'region', 'state', 'district',
	     'address', 'ho_contact_number', 'ho_contact_person', 'ho_contact_email', 'garden_contact_number', 'garden_contact_person',
		  'garden_contact_email', 'manager_contact_number', 'manager_contact_person', 'manager_contact_email',
		    'trust_tea_officer_contact_number',
		   'trust_tea_officer_contact_person', 'trust_tea_officer_contact_email',
		     'data_operator_contact_number',
		    'data_operator_contact_person', 'data_operator_contact_email', 'factory_details_likely_production', 
			 'factory_details_other_certificate', 'ownership_details_managing_company', 'ownership_details_name_of_tea_company',
			  'ownership_details_email', 'user_file',
			    'entity_name', 'entity_unit', 'easy_weight_system'
			   )
		
		widgets = {
            'address': Textarea(attrs={'rows':80, 'cols':20}),
        }




class EstateProfileForm(forms.ModelForm):
	""" Estate Profile Create Form """

	def __init__(self, *args, **kwargs):
		user_create_pk = kwargs.pop('user_create_pk', None)
		logged_user_id = kwargs.pop('logged_user', None)
		super(EstateProfileForm, self).__init__(*args, **kwargs)

		for field in self.fields.values():
			field.widget.attrs = {"class": "form-control"}

		self.fields['is_fetch_from_tcms'].required = False
		
		self.fields['state'].required = True
		self.fields['district'].required = True
		self.fields['region'].required = True


		self.fields['certificate_no'].widget.attrs = {'class': 'form-control', 'placeholder' : "Certificate No"}
		self.fields['region'].widget.attrs = {'class': 'form-control', 'placeholder' : "Region"}
		self.fields['address'].widget.attrs = {'class': 'form-control', 'placeholder' : "Address"}
		self.fields['ho_contact_number'].widget.attrs = {'class': 'form-control', 'placeholder' : "Contact Number"}
		self.fields['ho_contact_person'].widget.attrs = {'class': 'form-control', 'placeholder' : "Contact Person"}
		self.fields['ho_contact_email'].widget.attrs = {'class': 'form-control', 'placeholder' : "Email Address"}
		self.fields['garden_contact_number'].widget.attrs = {'class': 'form-control', 'placeholder' : "Contact Number"}
		self.fields['garden_contact_person'].widget.attrs = {'class': 'form-control', 'placeholder' : "Contact Person"}
		self.fields['garden_contact_email'].widget.attrs = {'class': 'form-control', 'placeholder' : "Email Address"}
		self.fields['manager_contact_number'].widget.attrs = {'class': 'form-control', 'placeholder' : "Contact Number"}
		self.fields['manager_contact_person'].widget.attrs = {'class': 'form-control', 'placeholder' : "Contact Person"}
		self.fields['manager_contact_email'].widget.attrs = {'class': 'form-control', 'placeholder' : "Email Address"}
		self.fields['trust_tea_officer_contact_number'].widget.attrs = {'class': 'form-control', 'placeholder' : "Contact Number"}
		self.fields['trust_tea_officer_contact_person'].widget.attrs = {'class': 'form-control', 'placeholder' : "Contact Person"}
		self.fields['trust_tea_officer_contact_email'].widget.attrs = {'class': 'form-control', 'placeholder' : "Email Address"}
		self.fields['data_operator_contact_number'].widget.attrs = {'class': 'form-control', 'placeholder' : "Contact Number"}
		self.fields['data_operator_contact_person'].widget.attrs = {'class': 'form-control', 'placeholder' : "Contact Person"}
		self.fields['data_operator_contact_email'].widget.attrs = {'class': 'form-control', 'placeholder' : "Email Address"}
		self.fields['factory_details_likely_production'].widget.attrs = {'class': 'form-control', 'placeholder' : "in Mn.kg", 'step' : '0.01'}
		# self.fields['factory_details_marks'].widget.attrs = {'class': 'form-control select2_demo_marks', 'placeholder' : "Marks"}
		self.fields['factory_details_other_certificate'].widget.attrs = {'class': 'form-control', 'placeholder' : "Certificate No."}
		self.fields['ownership_details_managing_company'].widget.attrs = {'class': 'form-control', 'placeholder' : "Managing company"}
		self.fields['ownership_details_name_of_tea_company'].widget.attrs = {'class': 'form-control', 'placeholder' : "Name of tea company"}
		self.fields['ownership_details_email'].widget.attrs = {'class': 'form-control', 'placeholder' : "Mailing Address" }
		self.fields['user_file'].widget.attrs = {'class': 'file-upload'}

		self.fields['entity_name'].widget.attrs = {'class': 'form-control', 'placeholder' : "Estate Name"}
		self.fields['entity_unit'].widget.attrs = {'class': 'form-control', 'placeholder' : "Garden/Entity Unit"}

		self.fields['total_male_worker'].widget.attrs = {'class': 'form-control', 'placeholder' : "Total male worker"}
		self.fields['total_female_worker'].widget.attrs = {'class': 'form-control', 'placeholder' : "Total Female worker"}
		self.fields['estimated_production_of_green_leaves'].widget.attrs = {'class': 'form-control', 'placeholder' : "Estimated Production of Green Leaves (Kg)"}
		self.fields['estimated_production_of_made_tea'].widget.attrs = {'class': 'form-control', 'placeholder' : "Estimated Production of Made Tea (Kg)"}

		self.fields['is_fetch_from_tcms'].widget.attrs = {'class': 'form-control', 'id' : "is_fetch_from_tcms"}

		# self.fields['state'].queryset = State.objects.none()
		# self.fields['district'].queryset = District.objects.none()

		self.fields['region'].queryset = Region.objects.filter(is_deleted=False)
		
		if 'state' in self.data:
			try:
				state_id = int(self.data.get('state'))
				self.fields['state'].queryset=State.objects.filter(id=state_id).order_by('name')
				# self.fields['factory_estate_state'].queryset=State.objects.filter(id=state_id).order_by('name')
				state_id=State.objects.filter(id=state_id).values('id')
				
				for data in state_id:
					data=data.get('id')
					print(data)
					self.fields['district'].queryset=District.objects.filter(state_id=data).order_by('name')
					# self.fields['factory_estate_district'].queryset=District.objects.filter(state_id=data).order_by('name')
			except (ValueError, TypeError):
				pass 


	class Meta:
		model = EstateProfile
		fields = ('certificate_no', 'region', 'state', 'district',
	     'address', 'ho_contact_number', 'ho_contact_person', 'ho_contact_email', 'garden_contact_number', 'garden_contact_person',
		  'garden_contact_email', 'manager_contact_number', 'manager_contact_person', 'manager_contact_email',
		    'trust_tea_officer_contact_number',
		   'trust_tea_officer_contact_person', 'trust_tea_officer_contact_email',
		     'data_operator_contact_number',
		    'data_operator_contact_person', 'data_operator_contact_email', 'factory_details_likely_production', 
			 'factory_details_other_certificate', 'ownership_details_managing_company', 'ownership_details_name_of_tea_company',
			  'ownership_details_email', 'user_file', 'is_fetch_from_tcms', 'third_party_easy_weight_system',
			  'total_male_worker', 'total_female_worker', 'estimated_production_of_green_leaves',
			    'estimated_production_of_made_tea', 'api_entity_name', 'api_entity_unit', 'entity_name', 'entity_unit', 'easy_weight_system'
			   )
		
		widgets = {
            'address': Textarea(attrs={'rows':80, 'cols':20}),
        }




		

class BlfTroughDetailsForm(forms.ModelForm):

	class Meta:
		model = BlfTroughDetails
		fields = ('capacity_qty', 'name', 'leaf_type', 'size_width', 'size_height')

	def __init__(self, *args, **kwargs):
		super(BlfTroughDetailsForm, self).__init__(*args, **kwargs)

		self.fields['capacity_qty'].widget.attrs = {'class': 'form-control', 'placeholder' : "Capacity Qty"}
		self.fields['size_width'].widget.attrs = {'class': 'form-control', 'placeholder' : "width"}
		self.fields['size_height'].widget.attrs = {'class': 'form-control', 'placeholder' : "height"}
		self.fields['name'].widget.attrs = {'class': 'form-control', 'placeholder' : "Trough Name"}
		self.fields['leaf_type'].widget.attrs = {'class': 'form-control', 'placeholder' : "Type of Leaf"}







class EstateProductionForm(forms.ModelForm):

	class Meta:
		model = EstateTeaProduction
		fields = ('tea_type', 'tea_grade', 'marks', 'quantity')

	def __init__(self, *args, **kwargs):
		super(EstateProductionForm, self).__init__(*args, **kwargs)

		self.fields['tea_type'].widget.attrs = {'class': 'form-control select2_tea_type', "onchange": "product_type_change(this)" }
		self.fields['tea_grade'].widget.attrs = {'class': 'form-control select2_tea_grade'}
		self.fields['marks'].widget.attrs = {'class': 'form-control select2_marks'}
		self.fields['quantity'].widget.attrs = {'class': 'form-control', 'placeholder' : "Quantity"}


class EstateTeaProductionForm(forms.ModelForm):

	class Meta:
		model = EstateTeaProduction
		fields = ('tea_type', 'tea_grade', 'marks', 'quantity')

	def __init__(self, *args, **kwargs):
		super(EstateTeaProductionForm, self).__init__(*args, **kwargs)

		self.fields['tea_type'].widget.attrs = {'class': 'form-control ' }
		self.fields['tea_grade'].widget.attrs = {'class': 'form-control '}
		self.fields['marks'].widget.attrs = {'class': 'form-control '}
		self.fields['quantity'].widget.attrs = {'class': 'form-control', 'placeholder' : "Quantity"}


class EstateProductionTeaTypeForm(forms.ModelForm):

	class Meta:
		model = EstateProductionTeaType
		fields = ('tea_type', 'tea_grade', 'marks', 'quantity')

	def __init__(self, *args, **kwargs):
		super(EstateProductionTeaTypeForm, self).__init__(*args, **kwargs)

		self.fields['tea_type'].widget.attrs = {'class': 'form-control' }
		self.fields['tea_grade'].widget.attrs = {'class': 'form-control'}
		self.fields['marks'].widget.attrs = {'class': 'form-control'}
		self.fields['quantity'].widget.attrs = {'class': 'form-control', 'placeholder' : "Quantity"}



class BlfTeaProductionForm(forms.ModelForm):

	class Meta:
		model = BlfTeaProduction
		fields = ('tea_type', 'tea_grade', 'marks', 'quantity')

	def __init__(self, *args, **kwargs):
		super(BlfTeaProductionForm, self).__init__(*args, **kwargs)

		self.fields['tea_type'].widget.attrs = {'class': 'form-control', "onchange": "product_type_change(this)" }
		self.fields['tea_grade'].widget.attrs = {'class': 'form-control'}
		self.fields['marks'].widget.attrs = {'class': 'form-control'}
		self.fields['quantity'].widget.attrs = {'class': 'form-control', 'placeholder' : "Quantity"}




class BlfFactoryDetailsMarksForm(forms.ModelForm):

	class Meta:
		model = BlfFactoryDetailsMarks
		fields = ('name',)

	def __init__(self, *args, **kwargs):
		super(BlfFactoryDetailsMarksForm, self).__init__(*args, **kwargs)

		self.fields['name'].widget.attrs = {'class': 'form-control' , 'placeholder' : 'Creatre marks', 'id' : 'factory_marks_id'}


class FactoryDetailsMarksForm(forms.ModelForm):

	class Meta:
		model = FactoryDetailsMarks
		fields = ('name',)

	def __init__(self, *args, **kwargs):
		super(FactoryDetailsMarksForm, self).__init__(*args, **kwargs)

		self.fields['name'].widget.attrs = {'class': 'form-control' , 'placeholder' : 'Creatre marks', 'id' : 'factory_marks_id'}



class BlfMarksForm(forms.ModelForm):

	class Meta:
		model = BlfFactoryMarks
		fields = ('name',)

	def __init__(self, *args, **kwargs):
		super(BlfMarksForm, self).__init__(*args, **kwargs)

		self.fields['name'].widget.attrs = {'class': 'form-control' , 'placeholder' : 'Creatre marks', 'id' : 'factory_marks_id'}





############ Estate Trough Details FORMS #########

class FactoryTroughDetailsForm(forms.ModelForm):
    """
    Factory Trough Details Form
    """
    class Meta:
        model = FactoryTroughDetails
        fields = ('name',)

    def __init__(self, *args, **kwargs):
        super(FactoryTroughDetailsForm, self).__init__(*args, **kwargs)

        self.fields['name'].widget.attrs = {'class': 'form-control', 'placeholder' : "*Name"}


class EstateTroughDetailsForm(forms.ModelForm):
	"""
	Estate Trough Details Form
	"""
	class Meta:
		model = EstateTroughDetails
		fields = ('name', 'capacity_qty', 'size_width', 'size_height', 'leaf_type')

	def __init__(self, *args, **kwargs):
		super(EstateTroughDetailsForm, self).__init__(*args, **kwargs)

		self.fields['capacity_qty'].widget.attrs = {'class': 'form-control', 'placeholder' : "Capacity Qty"}
		self.fields['size_width'].widget.attrs = {'class': 'form-control', 'placeholder' : "width"}
		self.fields['size_height'].widget.attrs = {'class': 'form-control', 'placeholder' : "height"}
		self.fields['name'].widget.attrs = {'class': 'form-control', 'placeholder' : "Trough Name"}
		self.fields['leaf_type'].widget.attrs = {'class': 'form-control', 'placeholder' : "Type of Leaf"}



ESTATE_TROUGH_FORM_SET = inlineformset_factory(
    FactoryTroughDetails,
    EstateTroughDetails,
    form=EstateTroughDetailsForm,
    extra=0,
    min_num=1,
    max_num=100,
    validate_max=True,
    can_delete=True
)



# ########### END #######################


BLF_MAARKS_FORM_SET = inlineformset_factory(
    BlfProfile,
    BlfFactoryMarks,
    form=BlfMarksForm,
    extra=0,
    min_num=1,
    max_num=100,
    validate_max=True,
    can_delete=True
)



FACTORY_DETAILS_MARKS_FORM_SET = inlineformset_factory(
    EstateProfile,
    FactoryDetailsMarks,
    form=FactoryDetailsMarksForm,
    extra=0,
    min_num=1,
    max_num=100,
    validate_max=True,
    can_delete=True
)

BLF_TROUGH_FORMSET = inlineformset_factory(
    BlfProfile,
    BlfTroughDetails,
    form=BlfTroughDetailsForm,
    extra=0,
    min_num=1,
    max_num=100,
    validate_max=True,				
    can_delete=True
)


ESTATE_TROUGH_DETAILS_ROW_FORM_SET = inlineformset_factory(
    EstateProfile,
    TroughDetailsEstate,
    form=BlfTroughDetailsForm,
    extra=0,
    min_num=1,
    max_num=100,
    validate_max=True,
    can_delete=True
)

ESTATE_TEA_PRODUCTION_FORM_SET = inlineformset_factory(
    EstateProfile,
    EstateTeaProduction,
    form=EstateProductionForm,
    extra=0,
    min_num=1,
    max_num=100,
    validate_max=True,
    can_delete=True
)

ESTATE_PRODUCTIONS_FORM_SET = inlineformset_factory(
    EstateProfile,
    EstateProductionTeaType,
    form=EstateProductionTeaTypeForm,
    extra=0,
    min_num=1,
    max_num=100,
    validate_max=True,
    can_delete=True
)









BLF_TEA_PRODUCTION_FORM_SET = inlineformset_factory(
    BlfProfile,
    BlfTeaProduction,
    form=BlfTeaProductionForm,
    extra=0,
    min_num=1,
    max_num=100,
    validate_max=True,
    can_delete=True
)


BLF_FACTORY_DETAILS_MARKS_FORM_SET = inlineformset_factory(
    BlfProfile,
    BlfFactoryDetailsMarks,
    form=BlfFactoryDetailsMarksForm,
    extra=0,
    min_num=1,
    max_num=100,
    validate_max=True,
    can_delete=True
)


class AdvisoryProfileForm(forms.ModelForm):
	""" Advisory User Profile Create Form @vivek"""

	def __init__(self, *args, **kwargs):
		user_create_pk = kwargs.pop('user_create_pk', None)
		logged_user_id = kwargs.pop('logged_user', None)
		super(AdvisoryProfileForm, self).__init__(*args, **kwargs)

		for field in self.fields.values():
			field.widget.attrs = {"class": "form-control"}

		self.fields['region'].required = True
		self.fields['organization_name'].required = True


		self.fields['name'].widget.attrs = {'class': 'form-control', 'placeholder' : "Name"}
		self.fields['mobile_number'].widget.attrs = {'class': 'form-control', 'placeholder' : "Mobile No"}
		self.fields['region'].widget.attrs = {'class': 'form-control', 'placeholder' : "Region"}
		self.fields['state'].widget.attrs = {'class': 'form-control', 'placeholder' : "State"}
		self.fields['district'].widget.attrs = {'class': 'form-control', 'placeholder' : "District"}
		self.fields['organization_name'].widget.attrs = {'class': 'form-control', 'placeholder' : "Organization name"}
		self.fields['expert_name'].widget.attrs = {'class': 'form-control', 'placeholder' : "Expert name"}
			
		# self.fields['state'].queryset = State.objects.none()
		# self.fields['district'].queryset = District.objects.none()	
		self.fields['region'].queryset = Region.objects.filter(is_deleted=False)
	
		if 'state' in self.data:
			try:
				state_id = int(self.data.get('state'))
				self.fields['state'].queryset=State.objects.filter(id=state_id).order_by('name')
				state_id=State.objects.filter(id=state_id).values('id')
				
				for data in state_id:
					data=data.get('id')
					print(data)
					self.fields['district'].queryset=District.objects.filter(state_id=data).order_by('name')
			except (ValueError, TypeError):
				pass  




	class Meta:
		model = AdvisoryProfile
		fields = ('name', 'email','mobile_number', 'region', 'state', 'district',\
	      'organization_name', \
	     'expert_name',  'user_file', \
	     
	     )
		widgets = {
            'address': Textarea(attrs={'rows':80, 'cols':20}),
        }
	
class ConsigneeProfileForm(forms.ModelForm):
	""" Consignee User Profile Create Form @vivek"""

	def __init__(self, *args, **kwargs):
		user_create_pk = kwargs.pop('user_create_pk', None)
		logged_user_id = kwargs.pop('logged_user', None)
		super(ConsigneeProfileForm, self).__init__(*args, **kwargs)

		for field in self.fields.values():
			field.widget.attrs = {"class": "form-control"}

		self.fields['organization_name'].required = True
		self.fields['buyer_name'].required = False
		self.fields['mobile_number'].required = False
		self.fields['region'].required = False

		self.fields['mobile_number'].widget.attrs = {'class': 'form-control', 'placeholder' : "Mobile No"}
		self.fields['region'].widget.attrs = {'class': 'form-control', 'placeholder' : "Region"}
		self.fields['buyer_name'].widget.attrs = {'class': 'form-control', 'placeholder' : "Buyer name"}
		self.fields['organization_name'].widget.attrs = {'class': 'form-control', 'placeholder' : "Organization Name"}	

		self.fields['region'].queryset = Region.objects.filter(is_deleted=False)
		
	class Meta:
		model = ConsigneeProfile
		fields = ('mobile_number', 'region', 'buyer_name', 'organization_name')
		
		


class ShgCooperativeProfileForm(forms.ModelForm):
	""" SHG Cooperative User Profile Create Form @vivek"""

	def __init__(self, *args, **kwargs):
		user_create_pk = kwargs.pop('user_create_pk', None)
		logged_user_id = kwargs.pop('logged_user', None)
		super(ShgCooperativeProfileForm, self).__init__(*args, **kwargs)
		self.fields['shg_cooperative_type'].widget.attrs = {'class': 'select2_demo form-control', 'id' : 'shg_cooperative_type'}

		for field in self.fields.values():
			field.widget.attrs = {"class": "form-control"}
		self.fields['name'].widget.attrs = {'class': 'form-control', 'placeholder' : "Name"}
		self.fields['mobile_number'].widget.attrs = {'class': 'form-control', 'placeholder' : "Mobile No"}
		# self.fields['shg_cooperative_type'].widget.attrs = {'class': 'form-control', 'placeholder' : "SHG type"}

		self.fields['region'].widget.attrs = {'class': 'form-control', 'placeholder' : "Region"}
		self.fields['state'].widget.attrs = {'class': 'form-control', 'placeholder' : "State"}
		self.fields['district'].widget.attrs = {'class': 'form-control', 'placeholder' : "District"}
		self.fields['total_no_members'].widget.attrs = {'class': 'form-control', 'placeholder' : "Total member"}
		self.fields['no_of_associated_non_member'].widget.attrs = {'class': 'form-control', 'placeholder' : "No. of associated non member"}
		self.fields['govt_registration_no'].widget.attrs = {'class': 'form-control', 'placeholder' : "Govt. registration no."}
		self.fields['trustea_id'].widget.attrs = {'class': 'form-control', 'placeholder' : "Trust tea id"}
		self.fields['address'].widget.attrs = {'class': 'form-control', 'placeholder' : "Address"}
		self.fields['region'].queryset = Region.objects.filter(is_deleted=False)	
		# self.fields['state'].queryset = State.objects.none()
		# self.fields['district'].queryset = District.objects.none()	
		
	
		if 'state' in self.data:
			try:
				state_id = int(self.data.get('state'))
				self.fields['state'].queryset=State.objects.filter(id=state_id).order_by('name')
				state_id=State.objects.filter(id=state_id).values('id')
				
				for data in state_id:
					data=data.get('id')
					print(data)
					self.fields['district'].queryset=District.objects.filter(state_id=data).order_by('name')
			except (ValueError, TypeError):
				pass  
		

	class Meta:
		model = ShgCooperativeProfile
		fields = ('name','email', 'mobile_number','shg_cooperative_type', 'region', 'state', 'district','address',\
	      'total_no_members','no_of_associated_non_member','govt_registration_no' ,'trustea_id',\
	      'user_file', \
	     
	     )
		widgets = {
            'address': Textarea(attrs={'rows':80, 'cols':20}),
        }
		



class ProfileForm(forms.ModelForm):
	""" Profile Create Form"""

	def __init__(self, *args, **kwargs):
		user_create_pk = kwargs.pop('user_create_pk', None)
		logged_user_id = kwargs.pop('logged_user', None)
		super(ProfileForm, self).__init__(*args, **kwargs)

		for field in self.fields.values():
			field.widget.attrs = {"class": "form-control"}

		self.fields['full_name'].required = True
		self.fields['trustea_id'].required = True
		self.fields['region'].required = True

		self.fields['full_name'].widget.attrs = {'class': 'form-control', 'placeholder' : "Full Name"}
		self.fields['region'].widget.attrs = {'class': 'form-control', 'placeholder' : "Region"}
		self.fields['phone_no'].widget.attrs = {'class': 'form-control', 'placeholder' : "Contact No"}
		self.fields['address'].widget.attrs = {'class': 'form-control', 'placeholder' : "Address"}	
		self.fields['state'].widget.attrs = {'class': 'form-control'}
		self.fields['district'].widget.attrs = {'class': 'form-control'}
		self.fields['email'].widget.attrs = {'class': 'form-control', 'placeholder' : "Email"}
		self.fields['region'].widget.attrs = {'class': 'form-control'}
		self.fields['trustea_id'].widget.attrs = {'class': 'form-control', 'placeholder' : "Trustea Id"}	
		self.fields['region'].queryset = Region.objects.filter(is_deleted=False)
		
	class Meta:
		model = Profile
		fields = ('full_name', 'email', 'phone_no', 'region', 'address', 'state', 'district', 'trustea_id')
