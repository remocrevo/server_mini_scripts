# bookcover/__init__.py
from flask import Blueprint

# Create the blueprint
bookcover_bp = Blueprint('bookcover', __name__,
    url_prefix='/bookcover',
    template_folder='templates/bookcover')
    
# Import routes at the bottom to avoid circular imports
from . import routes
