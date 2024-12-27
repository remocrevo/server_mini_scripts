# submission_review/__init__.py
from flask import Blueprint

# Create the blueprint
submissions_bp = Blueprint('submissions', __name__,
    url_prefix='/submission_review',
    template_folder='templates/submission_review')
    
# Import routes at the bottom to avoid circular imports
from . import routes
