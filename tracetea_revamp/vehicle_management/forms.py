from django import forms

from .models import VehicleManagement


class VehicleManagementForm(forms.ModelForm):
    class Meta:
        model = VehicleManagement
        fields = ("vehicle_type", "vehicle_number", "mobile_number", "is_available")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["vehicle_type"].widget.attrs = {
            "class": "form-control",
            "required": "required",
        }
        self.fields["vehicle_number"].widget.attrs = {
            "class": "form-control",
            "required": "required",
            "placeholder": "Vehicle Number",
        }
        self.fields["mobile_number"].widget.attrs = {
            "class": "form-control",
            "placeholder": "Mobile Number",
        }
        self.fields["is_available"].widget.attrs = {
            "class": "form-check-input",
        }

        self.fields["vehicle_type"].required = True
        self.fields["vehicle_number"].required = True
