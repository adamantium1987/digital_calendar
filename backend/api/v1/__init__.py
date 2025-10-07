"""
API Version 1

This module provides the v1 API blueprint.
"""

from flask import Blueprint

# Create v1 blueprint
api_v1 = Blueprint('api_v1', __name__, url_prefix='/api/v1')

# Import routes to register them
from . import routes  # noqa: E402, F401
