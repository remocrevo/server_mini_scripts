# address_to_library_card_type/__init__.py
from flask import Blueprint

# Create the blueprint
address_to_library_card_type_bp = Blueprint('address_to_library_card_type', __name__,
    url_prefix='/address_to_library_card_type',
    template_folder='templates/address_to_library_card_type')
    
# Import routes at the bottom to avoid circular imports
from . import routes
