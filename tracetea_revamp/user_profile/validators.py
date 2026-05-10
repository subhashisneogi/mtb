import os
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import InMemoryUploadedFile

def validate_image_file_extension(value):
    ext = os.path.splitext(value.name)[1]  # [0] returns path+filename
    valid_extensions = ['.jpg', '.jpeg', '.png']
    if not ext.lower() in valid_extensions:
        raise ValidationError('Only jpg/jpeg/png files are allowed!')
    


def validate_signature_file_extension(value):
    if not isinstance(value, InMemoryUploadedFile):  # Check if the value is a file
        return  # Skip validation if it's not a file
    ext = os.path.splitext(value.name)[1].lower()
    valid_extensions = ['.jpg', '.jpeg', '.png']
    if ext not in valid_extensions:
        raise ValidationError('Only JPG, JPEG, and PNG files are allowed.')

