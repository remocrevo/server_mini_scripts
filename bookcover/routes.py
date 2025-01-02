import requests
import os
from flask import Flask, send_file, abort
from dotenv import load_dotenv
import io

# Load environment variables
load_dotenv()

app = Flask(__name__)

@app.route('/book-cover', methods=['GET'])
def get_book_cover():
    # Get the book title from query parameters
    book_title = request.args.get('title')
    
    if not book_title:
        abort(400, description="Book title is required")
    
    # Get API key from environment variables
    api_key = os.getenv('BIBLIOCOMMONS_API_KEY')
    
    # Prepare the API URL
    encoded_title = requests.utils.quote(book_title)
    api_url = (f"https://api.bibliocommons.com/v1/titles?"
               f"library=kdl&search_type=custom&"
               f"q=formatcode%3A(BK )%20%20anywhere%3A({encoded_title})&"
               f"api_key={api_key}")
    
    try:
        # Make the API request
        response = requests.get(api_url)
        data = response.json()
        
        # Check if ISBN exists
        if (data.get('title') and 
            data['title'].get('isbns') and 
            len(data['title']['isbns']) > 0):
            
            # Get the first ISBN
            isbn = data['title']['isbns'][0]
            
            # Construct image URL
            image_url = f"https://secure.syndetics.com/index.aspx?isbn={isbn}/LC.GIF"
            
            # Fetch the image
            image_response = requests.get(image_url)
            
            # Check if image was successfully retrieved
            if image_response.status_code == 200:
                # Return the image directly
                return send_file(
                    io.BytesIO(image_response.content),
                    mimetype='image/gif'
                )
            else:
                abort(404, description="Book cover image not found")
        
        else:
            abort(404, description="No ISBN found for the book")
    
    except Exception as e:
        abort(500, description=f"An error occurred: {str(e)}")

if __name__ == '__main__':
    app.run(debug=True)
