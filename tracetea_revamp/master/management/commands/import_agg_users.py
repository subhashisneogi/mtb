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
            username = str(row['username'])  # Replace 'username' with the actual column name in your Excel file
            password =  str(row['password'])

            check_username = User.objects.filter(username=username).first()

            if not check_username:
                # Create a new user with a secure password

                create = User.objects.create_user(username=username, password=password)
                profile_type_details=ProfileType.objects.filter(name='aggregator').first()
                profile_details_create=Profile(user=create, user_type_id=profile_type_details.id)
                profile_details_create.save()

                aggregator_create=AggregatorProfile(user=create)
                aggregator_create.save()
                
                aggregator_create.profile_type_id = profile_type_details.id

                if row['region_id'] is not None and not math.isnan(row['region_id']):
                    aggregator_create.region_id = row['region_id']

                if row['state_id'] is not None and not math.isnan(row['state_id']):
                    aggregator_create.state_id = row['state_id']

                if row['district_id'] is not None and not math.isnan(row['district_id']):
                    aggregator_create.district_id = row['district_id']

                if row['name'] is not None:
                    aggregator_create.name=row['name']
    
                if row['mobile_number'] is not None and not math.isnan(row['mobile_number']):
                    aggregator_create.mobile_number= int(row['mobile_number'])
                
                aggregator_create.save()

                self.stdout.write(self.style.SUCCESS(f'Successfully imported Aggregator user: {username}'))
            else:
                self.stdout.write(self.style.SUCCESS(f'User Exists: {username}'))

        
            