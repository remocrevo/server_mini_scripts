# main.py
from flask import Flask
import os
from dotenv import load_dotenv
from reviewer_signup import reviewer_bp
from submission_review import submissions_bp
from bookcover import bookcover_bp
from address_to_library_card_type import address_to_library_card_type_bp

# Load environment variables
load_dotenv()

def create_app():
    app = Flask(__name__)
    
    # Register blueprints
    app.register_blueprint(reviewer_bp)
    app.register_blueprint(submissions_bp)
    app.register_blueprint(bookcover_bp)
    app.register_blueprint(address_to_library_card_type_bp)
    
    return app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(
        host="0.0.0.0",
        port=port,
        debug=os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    )
