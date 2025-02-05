from flask import Flask, request, render_template, jsonify
from c_to_c_functions import *
from . import address_to_library_card_bp

@address_to_library_card_bp.route('/')
def home():
    return render_template('index.html')

@address_to_library_card_bp.route('/get_library_card', methods=['POST'])
def get_library_card():
    street_address = request.form['street_address']

    # Using the geopy library to take a street address as input and return lat and long coordinates
    latitude, longitude = get_coordinates(street_address)

    # Function to take latitude and longitude and return tile coordinates (which is what census reporter uses)
    county_subdivision, full_name = coordinates_to_csubdivision(latitude, longitude)

    # Based on the inputted county_subdivision returns what library the patrons should get
    results_df = csubdivision_to_lib_df(county_subdivision, street_address)

    # Loading in the Address DB, appending the current address results, and then resaves it 
    resave_json(results_df)

    response = {
        'full_name': full_name,
        'latitude': latitude,
        'longitude': longitude,
        'results_df': results_df.to_dict()  # Convert DataFrame to dictionary for JSON response
    }
    return jsonify(response)

if __name__ == '__main__':
    address_to_library_card_bp.run(debug=True)
