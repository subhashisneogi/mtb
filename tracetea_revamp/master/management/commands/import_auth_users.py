from django.contrib.auth import get_user_model
User = get_user_model()
import pandas as pd
from django.core.management.base import BaseCommand
from user_profile.models import *
from django.contrib.auth.hashers import make_password


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
            username = row['username']  # Replace 'username' with the actual column name in your Excel file
            password =  str(row['password'])
            
            # Create a new user with a secure password
            create = User.objects.create_user(username=username, password=password)

            profile_type_details=ProfileType.objects.filter(name='blf').first()

            profile_details_create=Profile(user=create, user_type_id=profile_type_details.id)
            profile_details_create.save()

            blf_create=BlfProfile(user=create)
            blf_create.save()

            blf_create.region_id = row['region']
            blf_create.state_id = row['state']
            blf_create.district_id = row['district']

            blf_create.entity_unit=row['entity_unit']
            blf_create.mobile_number=row['mobile_number']

            blf_create.save()

            self.stdout.write(self.style.SUCCESS(f'Successfully imported user: {username}'))