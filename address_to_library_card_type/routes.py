from flask import Flask, request, render_template, jsonify
from .c_to_c_functions import *
from . import address_to_library_card_type_bp

@address_to_library_card_type_bp.route('/')
def home():
    return render_template('address_to_library_card_type/index.html')

@address_to_library_card_type_bp.route('/get_library_card', methods=['POST'])
def get_library_card():
    street_address = request.form['street_address']

    logging.info(f"Received street address: {street_address}")

    try:
        # Using the geopy library to take a street address as input and return lat and long coordinates
        latitude, longitude = get_coordinates(street_address)
        logging.info(f"Coordinates obtained: latitude={latitude}, longitude={longitude}")

        # Function to take latitude and longitude and return tile coordinates (which is what census reporter uses)
        county_subdivision, full_name = coordinates_to_csubdivision(latitude, longitude)
        logging.info(f"County subdivision: {county_subdivision}, Full name: {full_name}")

        # Based on the inputted county_subdivision returns what library the patrons should get
        results_df = csubdivision_to_lib_df(county_subdivision, street_address)
        logging.info("Library card type determined successfully")

        results = {
            'full_name': full_name,
            'latitude': latitude,
            'longitude': longitude,
            'results_df': results_df.to_dict(orient='records')  # Convert DataFrame to list of dictionaries for better formatting
        }

        logging.info("Results prepared successfully")
    except Exception as e:
        logging.error(f"Error occurred: {e}")
        return jsonify({'error': str(e)}), 500

    return render_template('address_to_library_card_type/index.html', 
                           street_address=street_address,
                           results=results)

if __name__ == '__main__':
    address_to_library_card_type_bp.run(debug=True)
