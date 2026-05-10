from master.models import *
import json
import os
from django.conf import settings

from user_profile.models import GrowerProfile, AggregatorProfile,BlfProfile


def import_state():
    """ import script for State @vivek"""

    try:
        Json_file = os.path.join(settings.BASE_DIR, 'state+city.json')
        with open(Json_file,encoding="utf-8") as json_file:
            data = json.load(json_file)

            for i in data:
                country_data = "India"
                if country_data:
                    for item in i["states"]:
                        if not State.objects.filter(name=item['name'],).exists():
                            state_data = State.objects.create(
                                 name=item['name'],state_id=item['id']\
                                   )
                            state_data.save()
                        else:
                            print("State Already Exists - State name - " + str(item["name"]))

                else:
                    print("Country Already Exists- Country name - " + str(country_data.name) + " state " + str(item['name'])) 

    except Exception as e:
        print("Error is "+ str(e))

from django.db import transaction


def import_city():
    """ import script for City @vivek"""
    
    try:
        Json_file = os.path.join(settings.BASE_DIR, 'state+city.json')
        with open(Json_file,encoding="utf-8") as json_file:
            data = json.load(json_file)
            for i in data:
                country_data = 'India'
                if country_data:
                    for state_item in i['states']:
                        state_data = State.objects.filter(name=state_item["name"]).first()
                        print(state_data)
                        if state_data:
                            for item in state_item["cities"]:
                                if not District.objects.filter(state=state_data, name=item['name'],).exists():
                                    city_data = District.objects.create(
                                        state=state_data, name=item['name'],district_id=item['id'])
                                    city_data.save()
                                else:
                                    print("City Already Exists - city name - " + str(item["name"]))
                        else:
                            print("State not found- State name - " + str(state_data.name) )             

                else:
                    print("Country not found- Country name - " + str(country_data.name) ) 

    except Exception as e:
        print("Error is "+ str(e))

from django.core.exceptions import ObjectDoesNotExist
import sys
import pandas as pd
def update_associated_aggregators():
    try:
        file_path = os.path.join(settings.BASE_DIR, 'grower_update_aggregator_linkage.xlsx')
        df = pd.read_excel(file_path)
        if df.empty:
            print('Empty Excel file')
            return

        for index, row in df.iterrows():
            username = row['username']
            associated_aggregator_data = row['associated_aggregator']
            try:
                grower = User.objects.get(username=username)
                grower_profile = GrowerProfile.objects.get(user=grower)

                if associated_aggregator_data:
                    if isinstance(associated_aggregator_data, str):
                        associated_aggregators_list = associated_aggregator_data.split(',')
                    else:
                        associated_aggregators_list = str(associated_aggregator_data).split(',')

                    for aggregator_username in associated_aggregators_list:
                        aggregator_username = aggregator_username.strip()
                        try:
                            aggregator_profile = AggregatorProfile.objects.get(user__username=aggregator_username)
                            grower_profile.associated_aggregator.add(aggregator_profile)
                        except ObjectDoesNotExist:
                            print(f"Aggregator '{aggregator_username}' does not exist.")
                
                grower_profile.save()
                print(f"Updated associated aggregators for grower '{username}'")
            except User.DoesNotExist:
                print(f"Grower '{username}' does not exist.")
            except GrowerProfile.DoesNotExist:
                print(f"Grower profile for '{username}' does not exist.")
    except pd.errors.EmptyDataError:
        print('Empty Excel file or incorrect format.')
    except Exception as e:
        print(f"An error occurred: {str(e)}")