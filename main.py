# main.py (this is your entry point)
from flask import Flask
from reviewer_signup.routes import reviewer_bp
from submission_review.routes import submissions_bp

def create_app():
    app = Flask(__name__)
    
    # Register blueprints
    app.register_blueprint(reviewer_bp)
    app.register_blueprint(submissions_bp)
    
    return app

# Create the application instance
app = create_app()
