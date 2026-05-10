"""
Forms
"""
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError
from django import forms
from django.contrib.auth.forms import PasswordChangeForm

class UserCustomPasswordChangeForm(forms.Form):
    """
    Admin form for setting a profile user's password.
    """
    password = forms.CharField(
        label="New Password",
        strip=False,
        required=True,
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Enter New Password",
            "autocomplete": "new-password",
            "required": "required",
        }),
    )

    confirm_password = forms.CharField(
        label="Confirm Password",
        strip=False,
        required=True,
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Confirm New Password",
            "autocomplete": "new-password",
            "required": "required",
        }),
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super(UserCustomPasswordChangeForm, self).__init__(*args, **kwargs)

    def clean_password(self):
        password = self.cleaned_data.get("password")
        if password:
            password_validation.validate_password(password, self.user)
        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            self.add_error("confirm_password", "Password and confirm password do not match.")

        return cleaned_data

    def save(self, commit=True):
        password = self.cleaned_data["password"]
        self.user.set_password(password)
        if commit:
            self.user.save(update_fields=["password"])
        return self.user





class CreateUserForm(UserCreationForm):
    """
    Create User Form
    """
    email = forms.EmailField()

    class Meta:
        fields = ("username", "email", "password1",
                  "password2",)
        model = get_user_model()

    def __init__(self, *args, **kwargs):
        super(CreateUserForm, self).__init__(*args, **kwargs)

        self.fields['email'].required = False

        self.fields['username'].widget.attrs.update(
            {'class' : 'form-control','placeholder': 'Enter User Name', 'id' : 'id_username'})
        self.fields['email'].widget.attrs.update(
            {'class' : 'form-control','placeholder': 'Enter Email'})
        self.fields['password1'].widget.attrs.update(
            {'class' : 'form-control', 'id' :'myInput',  'placeholder': 'Enter Password'})
        self.fields['password2'].widget.attrs.update(
            {'class' : 'form-control', 'id' :'myInput2','placeholder': 'Confirm Password'})

        for fieldname in ['username', 'password1', 'password2']:
            self.fields[fieldname].help_text = None

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and get_user_model().objects.filter(email__iexact=email).exists():
            raise ValidationError(u'This email address is already registered.')
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username and get_user_model().objects.filter(username__iexact=username).exists():
            raise ValidationError(u'This username/user ID already exists.')
        return username
    


class CreateUserFormedit(UserCreationForm):
    """
    Create User Form
    """
    email = forms.EmailField()

    class Meta:
        fields = ("username", "email", "password1",
                  "password2",)
        model = get_user_model()

    def __init__(self, *args, **kwargs):
        super(CreateUserFormedit, self).__init__(*args, **kwargs)

        self.fields['email'].required = False

        self.fields['password1'].required = False

        self.fields['username'].widget.attrs.update(
            {'class' : 'form-control','placeholder': 'Enter User Name', 'id' : 'id_username', 'readonly' : 'readonly'})
        self.fields['email'].widget.attrs.update(
            {'class' : 'form-control','placeholder': 'Enter Email'})
        self.fields['password1'].widget.attrs.update(
            {'class' : 'form-control','placeholder': 'Enter Password'})
        self.fields['password2'].widget.attrs.update(
            {'class' : 'form-control','placeholder': 'Confirm Password'})

        for fieldname in ['username', 'password1', 'password2']:
            self.fields[fieldname].help_text = None

    def clean_email(self):
        email = self.cleaned_data.get('email')
        username = self.cleaned_data.get('username')
        if email and get_user_model().objects.filter(email=email).exclude(username=username).exists():
            raise ValidationError(u'This Email address was already registered')
        return email
