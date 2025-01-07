from flask import Flask, send_file, abort, request, jsonify
import requests
import os
from dotenv import load_dotenv
import io
import logging
from requests.exceptions import RequestException
import sys
from . import bookcover_bp

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class BookCoverError(Exception):
    """Custom exception for book cover retrieval errors"""
    def __init__(self, message, status_code=500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

@bookcover_bp.errorhandler(BookCoverError)
def handle_book_cover_error(error):
    response = jsonify({'error': error.message})
    response.status_code = error.status_code
    return response

@bookcover_bp.route('/book-cover', methods=['GET'])
def get_book_cover():
    try:
        # Check if API key exists
        api_key = os.getenv('BIBLIOCOMMONS_API_KEY')
        if not api_key:
            raise BookCoverError(
                "API key not found. Please set BIBLIOCOMMONS_API_KEY in environment variables.",
                status_code=500
            )

        # Validate book title parameter
        #book_title = request.args.get('title')
        book_title_id = request.args.get('title_id')
        if not book_title_id:
            raise BookCoverError(
                "Book ID is required. Use ?title_id=<ID NUMBER> in the URL.",
                status_code=400
            )
        if len(book_title_id.strip()) < 2:
            raise BookCoverError(
                "Book ID must be at least 2 characters long.",
                status_code=400
            )

        # Prepare the API URL
        if book_title_id:
            api_url = (f"https://api.bibliocommons.com/v1/titles/{book_title_id}?"
                      f"library=kdl&api_key={api_key}")
        #else:
        #    encoded_title = requests.utils.quote(book_title)
        #    api_url = (f"https://api.bibliocommons.com/v1/titles?"
        #              f"library=kdl&search_type=custom&"
        #              f"q=formatcode%3A(BK )%20%20anywhere%3A({encoded_title})&"
        #              f"api_key={api_key}")

        try:
            # Make the API request with timeout
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()  # Raises an HTTPError for bad responses
        except requests.exceptions.Timeout:
            raise BookCoverError(
                "Request to Bibliocommons API timed out. Please try again.",
                status_code=504
            )
        except requests.exceptions.HTTPError as e:
            if response.status_code == 401:
                raise BookCoverError(
                    "Invalid API key or unauthorized access.",
                    status_code=401
                )
            elif response.status_code == 429:
                raise BookCoverError(
                    "Rate limit exceeded. Please try again later.",
                    status_code=429
                )
            else:
                raise BookCoverError(
                    f"Bibliocommons API error: {str(e)}",
                    status_code=response.status_code
                )
        except RequestException as e:
            raise BookCoverError(
                f"Error connecting to Bibliocommons API: {str(e)}",
                status_code=503
            )

        try:
            data = response.json()
        except ValueError:
            raise BookCoverError(
                "Invalid JSON response from Bibliocommons API",
                status_code=502
            )

        # Check if we got valid data structure
        if not isinstance(data, dict):
            raise BookCoverError(
                "Unexpected response format from API",
                status_code=502
            )

        # Check if ISBN exists
        if (not data.get('title') or 
            not data['title'].get('isbns') or 
            not data['title']['isbns']):
            raise BookCoverError(
                f"No ISBN found for book ID: {book_title_id}, URL = " + api_url,
                status_code=404
            )

        # Get the first ISBN
        isbn = data['title']['isbns'][0]
        
        # Construct image URL
        image_url = f"https://secure.syndetics.com/index.aspx?isbn={isbn}/LC.GIF"
        
        try:
            # Fetch the image with timeout
            image_response = requests.get(image_url, timeout=10)
            image_response.raise_for_status()
        except requests.exceptions.Timeout:
            raise BookCoverError(
                "Request to Syndetics API timed out. Please try again.",
                status_code=504
            )
        except RequestException as e:
            raise BookCoverError(
                f"Error retrieving book cover image: {str(e)}",
                status_code=503
            )

        # Check if we got an actual image
        content_type = image_response.headers.get('content-type', '')
        if not content_type.startswith('image/'):
            raise BookCoverError(
                "Retrieved content is not an image",
                status_code=502
            )

        # Return the image
        return send_file(
            io.BytesIO(image_response.content),
            mimetype=content_type
        )

    except BookCoverError as e:
        # Log the error and re-raise it to be handled by the error handler
        logger.error(f"Book cover error: {str(e)}")
        raise

    except Exception as e:
        # Log unexpected errors
        logger.exception("Unexpected error occurred")
        raise BookCoverError(
            f"An unexpected error occurred: {str(e)}",
            status_code=500
        )

if __name__ == '__main__':
    # Verify environment on startup
    if not os.getenv('BIBLIOCOMMONS_API_KEY'):
        logger.error("BIBLIOCOMMONS_API_KEY not found in environment variables")
        sys.exit(1)
        
    bookcover_bp.run(debug=True)
