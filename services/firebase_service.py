import firebase_admin
from firebase_admin import credentials, auth
from config import Config
import logging

logger = logging.getLogger(__name__)

class FirebaseService:
    def __init__(self):
        if not firebase_admin._apps:
            try:
                if Config.GOOGLE_APPLICATION_CREDENTIALS:
                    cred = credentials.Certificate(Config.GOOGLE_APPLICATION_CREDENTIALS)
                else:
                    # Use default credentials in Cloud environment
                    cred = credentials.ApplicationDefault()
                
                firebase_admin.initialize_app(cred, {
                    'projectId': Config.FIREBASE_PROJECT_ID
                })
                logger.info("Firebase Admin SDK initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Firebase Admin SDK: {e}")
                raise
    
    def verify_token(self, id_token):
        """Verify Firebase ID token and return user info"""
        try:
            decoded_token = auth.verify_id_token(id_token)
            return {
                'uid': decoded_token['uid'],
                'email': decoded_token.get('email'),
                'name': decoded_token.get('name'),
                'picture': decoded_token.get('picture')
            }
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            return None
    
    def get_user(self, uid):
        """Get user information by UID"""
        try:
            user = auth.get_user(uid)
            return {
                'uid': user.uid,
                'email': user.email,
                'display_name': user.display_name,
                'photo_url': user.photo_url,
                'email_verified': user.email_verified
            }
        except Exception as e:
            logger.error(f"Failed to get user {uid}: {e}")
            return None

firebase_service = FirebaseService()
