from django.contrib.auth import get_user_model
User = get_user_model()
import pandas as pd
from django.core.management.base import BaseCommand
from user_profile.models import *
from django.contrib.auth.hashers import make_password
from gardens_managment.models import *
import math

# USER DATA UPLOAD SCRIPT
class Command(BaseCommand):

    help = 'Import users from Excel file'
    
    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Path to the Excel file')

    def handle(self, *args, **options):
        file_path = options['file_path']
        df = pd.read_excel(file_path)

        for index, row in df.iterrows():
            # USER CREATION
            username = row['username']  
            # password =  str(row['password'])
            # Create a new user with a secure password
            # create = User.objects.filter(username=username).first()


            grower_details = GrowerProfile.cmobjects.filter(user__username__exact=username).first()


            # update mobile No
            if row['mobile_number'] is not None and not math.isnan(row['mobile_number']):
                grower_details.mobile_number= int(row['mobile_number'])
                grower_details.save()
            else:
                grower_details.mobile_number= None
                grower_details.save()

            self.stdout.write(self.style.SUCCESS(f'Successfully updated imported user: {username}'))