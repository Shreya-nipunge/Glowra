from functools import wraps
from flask import request, jsonify, g
from services.firebase_service import firebase_service
from config import Config
import logging

logger = logging.getLogger(__name__)

def require_auth(f):
    """Decorator to require Firebase authentication for API endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check for development mode bypass
        if Config.DEV_MODE:
            dev_user_id = request.headers.get('X-Dev-User-Id')
            if dev_user_id:
                g.current_user = {
                    'uid': dev_user_id,
                    'email': f"{dev_user_id}@dev.local",
                    'name': f"Dev User {dev_user_id}"
                }
                logger.info(f"DEV MODE: Using dev user {dev_user_id}")
                return f(*args, **kwargs)
        
        # Get authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Missing or invalid authorization header'}), 401
        
        # Extract token
        token = auth_header.split(' ')[1]
        
        # Verify token with Firebase
        user_info = firebase_service.verify_token(token)
        if not user_info:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        # Store user info in g for use in route handlers
        g.current_user = user_info
        logger.info(f"Authenticated user: {user_info['uid']}")
        
        return f(*args, **kwargs)
    
    return decorated_function

def handle_errors(f):
    """Decorator to handle common errors in API endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValueError as e:
            logger.error(f"Validation error in {f.__name__}: {e}")
            return jsonify({'error': f'Validation error: {str(e)}'}), 400
        except KeyError as e:
            logger.error(f"Missing required field in {f.__name__}: {e}")
            return jsonify({'error': f'Missing required field: {str(e)}'}), 400
        except Exception as e:
            logger.error(f"Unexpected error in {f.__name__}: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    return decorated_function
