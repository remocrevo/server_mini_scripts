# main.py
from flask import Flask
from reviewer_signup import reviewer_bp
from submission_review import submissions_bp

def create_app():
    app = Flask(__name__)
    
    # Register blueprints
    app.register_blueprint(reviewer_bp)
    app.register_blueprint(submissions_bp)
    
    return app

app = create_app()

if __name__ == '__main__':
    app.run()
