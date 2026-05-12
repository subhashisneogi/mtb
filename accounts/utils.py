import random
import string
from django.utils.text import slugify
from io import BytesIO
import requests
from rest_framework.response import Response

def otp_generator():
    otp = random.randint(999, 9999)
    # otp = random.randint(100000, 999999) 
    return otp





 
