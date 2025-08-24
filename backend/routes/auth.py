from flask import Blueprint, request, jsonify, g
from services.firebase_service import firebase_service
from services.firestore_service import firestore_service
from utils.decorators import require_auth, handle_errors
from utils.helpers import format_response, get_current_utc_time
import logging

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/signup', methods=['POST'])
@handle_errors
def signup():
    """Create user profile after Firebase registration"""
    try:
        data = request.get_json()
        
        # Get required fields
        uid = data.get('uid')
        email = data.get('email')
        name = data.get('name', '')
        
        if not uid or not email:
            return jsonify(format_response(None, False, "UID and email are required")), 400
        
        # Create user profile in Firestore
        user_data = {
            'uid': uid,
            'email': email,
            'name': name,
            'onboarding_completed': False,
            'preferences': {
                'notifications': True,
                'daily_reminders': True,
                'wellness_tips': True
            }
        }
        
        success = firestore_service.create_user(uid, user_data)
        
        if success:
            logger.info(f"User profile created for {uid}")
            return jsonify(format_response(user_data, True, "User profile created successfully"))
        else:
            return jsonify(format_response(None, False, "Failed to create user profile")), 500
            
    except Exception as e:
        logger.error(f"Signup error: {e}")
        return jsonify(format_response(None, False, "Signup failed")), 500

@auth_bp.route('/profile', methods=['GET'])
@require_auth
@handle_errors
def get_profile():
    """Get current user's profile"""
    try:
        uid = g.current_user['uid']
        
        # Get user profile from Firestore
        user_profile = firestore_service.get_user(uid)
        
        if not user_profile:
            # Create profile if it doesn't exist
            user_data = {
                'uid': uid,
                'email': g.current_user.get('email', ''),
                'name': g.current_user.get('name', ''),
                'onboarding_completed': False,
                'preferences': {}
            }
            firestore_service.create_user(uid, user_data)
            user_profile = user_data
        
        return jsonify(format_response(user_profile))
        
    except Exception as e:
        logger.error(f"Get profile error: {e}")
        return jsonify(format_response(None, False, "Failed to get profile")), 500

@auth_bp.route('/profile', methods=['PUT'])
@require_auth
@handle_errors
def update_profile():
    """Update user profile"""
    try:
        uid = g.current_user['uid']
        data = request.get_json()
        
        # Allowed fields to update
        allowed_fields = ['name', 'preferences', 'onboarding_completed']
        update_data = {k: v for k, v in data.items() if k in allowed_fields}
        
        if not update_data:
            return jsonify(format_response(None, False, "No valid fields to update")), 400
        
        update_data['updated_at'] = get_current_utc_time()
        
        success = firestore_service.create_user(uid, update_data)  # Using merge=True
        
        if success:
            updated_profile = firestore_service.get_user(uid)
            return jsonify(format_response(updated_profile, True, "Profile updated successfully"))
        else:
            return jsonify(format_response(None, False, "Failed to update profile")), 500
            
    except Exception as e:
        logger.error(f"Update profile error: {e}")
        return jsonify(format_response(None, False, "Update failed")), 500

@auth_bp.route('/verify', methods=['POST'])
@handle_errors
def verify_token():
    """Verify Firebase ID token"""
    try:
        data = request.get_json()
        token = data.get('token')
        
        if not token:
            return jsonify(format_response(None, False, "Token is required")), 400
        
        user_info = firebase_service.verify_token(token)
        
        if user_info:
            return jsonify(format_response(user_info, True, "Token verified successfully"))
        else:
            return jsonify(format_response(None, False, "Invalid token")), 401
            
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        return jsonify(format_response(None, False, "Verification failed")), 500

@auth_bp.route('/logout', methods=['POST'])
@require_auth
@handle_errors
def logout():
    """Logout user (client-side token removal)"""
    try:
        # In Firebase, logout is primarily handled client-side
        # Server can log the logout event for analytics
        uid = g.current_user['uid']
        logger.info(f"User {uid} logged out")
        
        return jsonify(format_response(None, True, "Logged out successfully"))
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        return jsonify(format_response(None, False, "Logout failed")), 500
