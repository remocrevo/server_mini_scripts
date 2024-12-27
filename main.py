# main.py
from flask import Flask
import os
from dotenv import load_dotenv
from reviewer_signup import reviewer_bp
from submission_review import submissions_bp

# Load environment variables
load_dotenv()

def create_app():
    app = Flask(__name__)
    
    # Register blueprints
    app.register_blueprint(reviewer_bp)
    app.register_blueprint(submissions_bp)
    
    return app

app = create_app()

port = int(os.getenv("PORT", 8000))
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port)
