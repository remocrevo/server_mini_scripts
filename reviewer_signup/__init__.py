# reviewer_signup/__init__.py
from flask import Blueprint

# Create the blueprint
reviewer_bp = Blueprint('reviewer', __name__, 
    url_prefix='/',
    template_folder='templates/reviewer_signup')
    
# Import routes at the bottom to avoid circular imports
from . import routes
