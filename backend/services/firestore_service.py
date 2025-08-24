from google.cloud import firestore
from google.cloud.firestore import FieldFilter
from config import Config
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class FirestoreService:
    def __init__(self):
        try:
            self.db = firestore.Client(project=Config.GCP_PROJECT)
            logger.info("Firestore client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Firestore client: {e}")
            raise
    
    # User operations
    def create_user(self, uid: str, user_data: Dict[str, Any]) -> bool:
        """Create or update user profile"""
        try:
            user_ref = self.db.collection('users').document(uid)
            user_data['created_at'] = datetime.now(timezone.utc)
            user_data['updated_at'] = datetime.now(timezone.utc)
            user_ref.set(user_data, merge=True)
            logger.info(f"User {uid} created/updated successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to create user {uid}: {e}")
            return False
    
    def get_user(self, uid: str) -> Optional[Dict[str, Any]]:
        """Get user profile"""
        try:
            user_ref = self.db.collection('users').document(uid)
            doc = user_ref.get()
            if doc.exists:
                return doc.to_dict()
            return None
        except Exception as e:
            logger.error(f"Failed to get user {uid}: {e}")
            return None
    
    # Mood logging operations
    def save_mood_log(self, uid: str, mood_data: Dict[str, Any]) -> str:
        """Save mood log entry"""
        try:
            mood_ref = self.db.collection('mood_logs').document()
            mood_data['user_id'] = uid
            mood_data['timestamp'] = datetime.now(timezone.utc)
            mood_ref.set(mood_data)
            logger.info(f"Mood log saved for user {uid}")
            return mood_ref.id
        except Exception as e:
            logger.error(f"Failed to save mood log for user {uid}: {e}")
            raise
    
    def get_mood_logs(self, uid: str, from_date: datetime = None, to_date: datetime = None) -> List[Dict[str, Any]]:
        """Get mood logs for user within date range"""
        try:
            query = self.db.collection('mood_logs').where(filter=FieldFilter('user_id', '==', uid))
            
            if from_date:
                query = query.where(filter=FieldFilter('timestamp', '>=', from_date))
            if to_date:
                query = query.where(filter=FieldFilter('timestamp', '<=', to_date))
            
            query = query.order_by('timestamp', direction=firestore.Query.DESCENDING)
            
            docs = query.stream()
            results = []
            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id
                results.append(data)
            
            return results
        except Exception as e:
            logger.error(f"Failed to get mood logs for user {uid}: {e}")
            return []
    
    # Journal operations
    def save_journal_entry(self, uid: str, journal_data: Dict[str, Any]) -> str:
        """Save journal entry with AI insights"""
        try:
            journal_ref = self.db.collection('journal_entries').document()
            journal_data['user_id'] = uid
            journal_data['timestamp'] = datetime.now(timezone.utc)
            journal_ref.set(journal_data)
            logger.info(f"Journal entry saved for user {uid}")
            return journal_ref.id
        except Exception as e:
            logger.error(f"Failed to save journal entry for user {uid}: {e}")
            raise
    
    def get_journal_entries(self, uid: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent journal entries for user"""
        try:
            query = (self.db.collection('journal_entries')
                    .where(filter=FieldFilter('user_id', '==', uid))
                    .order_by('timestamp', direction=firestore.Query.DESCENDING)
                    .limit(limit))
            
            docs = query.stream()
            results = []
            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id
                results.append(data)
            
            return results
        except Exception as e:
            logger.error(f"Failed to get journal entries for user {uid}: {e}")
            return []
    
    # Daily plan operations
    def save_daily_plan(self, uid: str, date: str, plan_data: Dict[str, Any]) -> bool:
        """Save daily plan for user"""
        try:
            plan_ref = self.db.collection('daily_plans').document(f"{uid}_{date}")
            plan_data['user_id'] = uid
            plan_data['date'] = date
            plan_data['created_at'] = datetime.now(timezone.utc)
            plan_ref.set(plan_data, merge=True)
            logger.info(f"Daily plan saved for user {uid} on {date}")
            return True
        except Exception as e:
            logger.error(f"Failed to save daily plan for user {uid}: {e}")
            return False
    
    def get_daily_plan(self, uid: str, date: str) -> Optional[Dict[str, Any]]:
        """Get daily plan for user and date"""
        try:
            plan_ref = self.db.collection('daily_plans').document(f"{uid}_{date}")
            doc = plan_ref.get()
            if doc.exists:
                return doc.to_dict()
            return None
        except Exception as e:
            logger.error(f"Failed to get daily plan for user {uid}: {e}")
            return None
    
    # Gamification operations
    def update_user_stats(self, uid: str, stats_update: Dict[str, Any]) -> bool:
        """Update user gamification stats"""
        try:
            stats_ref = self.db.collection('user_stats').document(uid)
            stats_update['updated_at'] = datetime.now(timezone.utc)
            stats_ref.set(stats_update, merge=True)
            logger.info(f"User stats updated for {uid}")
            return True
        except Exception as e:
            logger.error(f"Failed to update user stats for {uid}: {e}")
            return False
    
    def get_user_stats(self, uid: str) -> Optional[Dict[str, Any]]:
        """Get user gamification stats"""
        try:
            stats_ref = self.db.collection('user_stats').document(uid)
            doc = stats_ref.get()
            if doc.exists:
                return doc.to_dict()
            return {
                'points': 0,
                'streak_days': 0,
                'completed_tasks': 0,
                'badges': [],
                'level': 1
            }
        except Exception as e:
            logger.error(f"Failed to get user stats for {uid}: {e}")
            return None

firestore_service = FirestoreService()
