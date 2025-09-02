"""
Unified web application
통합 웹 애플리케이션
"""

from src.web.api import register_api_routes
from src.web.app import create_app
from src.web.routes import register_routes

__all__ = [
    'create_app',
    'register_routes',
    'register_api_routes'
]
