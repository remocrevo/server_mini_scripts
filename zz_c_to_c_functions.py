import requests
import math
from geopy.geocoders import Nominatim
import pandas as pd
import json
import os
from datetime import datetime
import streamlit as st
from filelock import FileLock, Timeout


# Using the geopy library to take a street address as input and return lat and long coordinates
def get_coordinates(street_address):
    geolocator = Nominatim(user_agent="my_app")

    location = geolocator.geocode(street_address, timeout=5)

    if location:
        latitude = round(location.latitude, 5)
        longitude = round(location.longitude, 5)

        return latitude, longitude


# function to turn latitude and longitude into x & y title coordinates to fit census reporter inputs
def latlon_to_tile(lat, lon, zoom):
    lat_rad = math.radians(lat)
    n = 2.0 ** zoom
    x_tile = int((lon + 180.0) / 360.0 * n)
    y_tile = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
    return x_tile, y_tile


# Takes coordinates and returns associated county subdivision
def coordinates_to_csubdivision(latitude, longitude):
    # Static Parameters
    release = "latest"
    sumlevel = "060"  # Summary level for county subdivisions
    zoom = 20  # Higher zoom level for more detail
    # latitude, longitude values taken dynamically from get_coordinates() function

    # Convert latitude and longitude to tile x and y
    x, y = latlon_to_tile(latitude, longitude, zoom)

    # URL format from census reporter API Docs https://github.com/censusreporter/census-api/blob/master/API.md
    url = f"https://api.censusreporter.org/1.0/geo/{release}/tiles/{sumlevel}/{zoom}/{x}/{y}.geojson"

    # Making request to census reporter 
    response = requests.get(url)
    data = response.json()

    # Parsing the returned GeoJson output, only returning county subdivision
    full_name = data['features'][0]['properties']['name']
    county_subdivision = full_name.split(",")[0]

    return county_subdivision, full_name



# Reading in the list of county subdivisions for KDL, GRPL, and LLC
def list_csubdivisions():

    # Reading in static KDL townships 
    kdl_townships = ['ada township', 'algoma township', 'alpine township', 'bowne township',
                  'byron township', 'caledonia charter township', 'cannon township', 'cascade charter township',
                  'courtland township', 'east grand rapids city', 'gaines charter township', 'grand rapids charter township',
                  'grandville city', 'grattan township', 'kentwood city', 'lowell charter township',
                  'lowell city', 'nelson township', 'oakfield township', 'plainfield charter township',
                  'rockford city', 'spencer township', 'tyrone township', 'vergennes township',
                  'walker city', 'wyoming city']
    
    # Reading in list and dictionary of LLC municpalities and their associated libraries 
    with open('llc.json', 'r') as f:
        data = json.load(f)
        llc_townships_list = data['list']
        llc_dict = data['dict']

    return kdl_townships, llc_townships_list, llc_dict
 


# Based on the inputted county_subdivision returns what librarythe patrons should get
def csubdivision_to_lib_df(county_subdivision, street_address):
    # Taking the county_subdivision input gathered from an API and converting it to lowercase to match list
    county_subdivision = county_subdivision.lower()

    kdl_townships, llc_townships_list, llc_dict = list_csubdivisions()

    # Create df to store output from address to library card function
    columns = ["street_address", "county_subdivision", "library_card_type", "time"]
    results_df = pd.DataFrame(columns=columns)

    # Retrieve current time for logging usage 
    c_time = datetime.now()
    c_time_formatted = c_time.strftime("%Y-%m-%d_%H-%M-%S")  #2024-05-16_13-23-55

    # Conditional code to link the address to appropriate library card 
    if county_subdivision in kdl_townships:
        card_type = "KDL"
        st.write("KDL Card! :sunglasses:")
    elif county_subdivision == "grand rapids city":
        card_type = "GRPL"
        st.write("GRPL Card!")
    elif county_subdivision in llc_townships_list:
        if county_subdivision == "ensley township":
            card_type = "PANIC IT's ENSLEY"
            st.write("PANIC IT's ENSLEY")
        else:
            card_type = f"LLC - {llc_dict[county_subdivision]}"
            st.write(f"LLC card for {county_subdivision}. Please direct patron to '{llc_dict[county_subdivision]}' in {county_subdivision}.")
    else:
        card_type = "non-llc"
        st.write("Not in our LLC system")
        
    # Create a new DataFrame with the current result
    new_row = pd.DataFrame([{
        "street_address": street_address,
        "county_subdivision": county_subdivision,
        "library_card_type": card_type,
        "time": c_time_formatted
    }])

    # Concatenate the new row to the results DataFrame (used because .append method throws a warning)
    results_df = pd.concat([results_df, new_row], ignore_index=True)

    return results_df



# Loading in the Address DB, appending the current address results, and then resaves it 
save_folder = r"C:\Users\Ryan\Coding Projects\KDL Project\AI PT\Address to card\Address Data"
file_path = os.path.join(save_folder, 'Address_db.json')
lock_file_path = file_path + '.lock'

# Ensure the save folder exists
os.makedirs(save_folder, exist_ok=True)

# Function to save the updated address database
def resave_json(results_df):
    new_results = results_df.to_dict(orient='records')
    lock = FileLock(lock_file_path, timeout=10)

    try:
        with lock:
            # Load the address database within the lock context
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    address_db = json.load(f)
            else:
                address_db = [] 

            # Append the new entry
            address_db.extend(new_results)

            # Save the updated address database
            with open(file_path, 'w') as f:
                json.dump(address_db, f, indent=4)

            print("Results have been saved to the JSON file.")

    except Timeout:
        print("Another process is currently accessing the file. Please try again later.")
