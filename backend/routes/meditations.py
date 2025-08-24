from flask import Blueprint, request, jsonify, g
from services.storage_service import storage_service
from services.firestore_service import firestore_service
from utils.decorators import require_auth, handle_errors
from utils.helpers import format_response, get_current_utc_time
import logging

logger = logging.getLogger(__name__)

meditations_bp = Blueprint('meditations', __name__)

@meditations_bp.route('/', methods=['GET'])
@require_auth
@handle_errors
def get_meditations():
    """Get list of available meditation resources"""
    try:
        uid = g.current_user['uid']
        
        # Get meditation files from Cloud Storage
        meditation_files = storage_service.list_meditation_files()
        
        # Categorize meditations
        categorized_meditations = {
            'breathing': [],
            'sleep': [],
            'stress_relief': [],
            'focus': [],
            'general': []
        }
        
        for file_info in meditation_files:
            filename = file_info['name'].lower()
            
            # Categorize based on filename
            if any(keyword in filename for keyword in ['breath', 'breathing']):
                category = 'breathing'
            elif any(keyword in filename for keyword in ['sleep', 'bedtime', 'night']):
                category = 'sleep'
            elif any(keyword in filename for keyword in ['stress', 'anxiety', 'calm']):
                category = 'stress_relief'
            elif any(keyword in filename for keyword in ['focus', 'concentration', 'study']):
                category = 'focus'
            else:
                category = 'general'
            
            # Add meditation metadata
            meditation = {
                'id': file_info['path'].replace('/', '_'),
                'name': file_info['name'].replace('.mp3', '').replace('.wav', '').replace('.m4a', ''),
                'file_name': file_info['name'],
                'url': file_info['url'],
                'size_mb': round(file_info['size'] / (1024 * 1024), 2) if file_info['size'] else 0,
                'category': category,
                'duration': file_info.get('duration', 'Unknown'),
                'description': get_meditation_description(filename)
            }
            
            categorized_meditations[category].append(meditation)
        
        # Get user's meditation history
        user_stats = firestore_service.get_user_stats(uid)
        completed_meditations = user_stats.get('completed_meditations', [])
        
        # Add completion status to meditations
        for category in categorized_meditations:
            for meditation in categorized_meditations[category]:
                meditation['completed'] = meditation['id'] in completed_meditations
        
        response_data = {
            'categories': categorized_meditations,
            'total_meditations': len(meditation_files),
            'user_completed': len(completed_meditations),
            'featured_meditation': get_featured_meditation(categorized_meditations, uid)
        }
        
        logger.info(f"Retrieved {len(meditation_files)} meditations for user {uid}")
        return jsonify(format_response(response_data))
        
    except Exception as e:
        logger.error(f"Get meditations error: {e}")
        return jsonify(format_response(None, False, "Failed to get meditations")), 500

@meditations_bp.route('/<meditation_id>/start', methods=['POST'])
@require_auth
@handle_errors
def start_meditation(meditation_id):
    """Start a meditation session"""
    try:
        uid = g.current_user['uid']
        
        # Create meditation session record
        session_data = {
            'meditation_id': meditation_id,
            'started_at': get_current_utc_time(),
            'status': 'started'
        }
        
        # Save session to Firestore
        session_ref = firestore_service.db.collection('meditation_sessions').document()
        session_ref.set({**session_data, 'user_id': uid})
        
        response_data = {
            'session_id': session_ref.id,
            'meditation_id': meditation_id,
            'started_at': session_data['started_at'].isoformat()
        }
        
        logger.info(f"Meditation session started for user {uid}")
        return jsonify(format_response(response_data, True, "Meditation session started"))
        
    except Exception as e:
        logger.error(f"Start meditation error: {e}")
        return jsonify(format_response(None, False, "Failed to start meditation")), 500

@meditations_bp.route('/sessions/<session_id>/complete', methods=['POST'])
@require_auth
@handle_errors
def complete_meditation(session_id):
    """Complete a meditation session"""
    try:
        uid = g.current_user['uid']
        data = request.get_json()
        
        duration_minutes = data.get('duration_minutes', 0)
        rating = data.get('rating', 5)  # 1-5 rating
        notes = data.get('notes', '')
        
        # Update session record
        session_ref = firestore_service.db.collection('meditation_sessions').document(session_id)
        session_doc = session_ref.get()
        
        if not session_doc.exists:
            return jsonify(format_response(None, False, "Session not found")), 404
        
        session_data = session_doc.to_dict()
        if session_data.get('user_id') != uid:
            return jsonify(format_response(None, False, "Unauthorized")), 403
        
        # Update session with completion data
        completion_data = {
            'completed_at': get_current_utc_time(),
            'duration_minutes': duration_minutes,
            'rating': rating,
            'notes': notes,
            'status': 'completed'
        }
        
        session_ref.update(completion_data)
        
        # Update user stats
        user_stats = firestore_service.get_user_stats(uid)
        meditation_id = session_data.get('meditation_id')
        completed_meditations = user_stats.get('completed_meditations', [])
        
        # Add to completed list if not already there
        if meditation_id and meditation_id not in completed_meditations:
            completed_meditations.append(meditation_id)
        
        # Calculate points (1 point per minute, bonus for completion)
        points_earned = duration_minutes + 10  # Base 10 points for completion
        
        updated_stats = {
            'completed_meditations': completed_meditations,
            'total_meditation_minutes': user_stats.get('total_meditation_minutes', 0) + duration_minutes,
            'meditation_sessions': user_stats.get('meditation_sessions', 0) + 1,
            'points': user_stats.get('points', 0) + points_earned,
            'last_meditation_date': get_current_utc_time()
        }
        
        firestore_service.update_user_stats(uid, updated_stats)
        
        response_data = {
            'session_id': session_id,
            'points_earned': points_earned,
            'total_meditation_minutes': updated_stats['total_meditation_minutes'],
            'completed_meditations_count': len(completed_meditations)
        }
        
        logger.info(f"Meditation session completed for user {uid}")
        return jsonify(format_response(response_data, True, "Meditation session completed"))
        
    except Exception as e:
        logger.error(f"Complete meditation error: {e}")
        return jsonify(format_response(None, False, "Failed to complete meditation")), 500

@meditations_bp.route('/history', methods=['GET'])
@require_auth
@handle_errors
def get_meditation_history():
    """Get user's meditation session history"""
    try:
        uid = g.current_user['uid']
        
        # Get query parameters
        limit = request.args.get('limit', 20, type=int)
        limit = min(limit, 100)  # Max 100 sessions
        
        # Get meditation sessions from Firestore
        sessions_ref = (firestore_service.db.collection('meditation_sessions')
                       .where('user_id', '==', uid)
                       .where('status', '==', 'completed')
                       .order_by('completed_at', direction=firestore_service.db.DESCENDING)
                       .limit(limit))
        
        sessions = []
        total_minutes = 0
        
        for doc in sessions_ref.stream():
            data = doc.to_dict()
            session = {
                'id': doc.id,
                'meditation_id': data.get('meditation_id'),
                'duration_minutes': data.get('duration_minutes', 0),
                'rating': data.get('rating'),
                'notes': data.get('notes', ''),
                'started_at': data.get('started_at').isoformat() if data.get('started_at') else None,
                'completed_at': data.get('completed_at').isoformat() if data.get('completed_at') else None
            }
            sessions.append(session)
            total_minutes += session['duration_minutes']
        
        # Calculate stats
        avg_duration = round(total_minutes / len(sessions), 1) if sessions else 0
        avg_rating = round(sum(s['rating'] for s in sessions if s['rating']) / len([s for s in sessions if s['rating']]), 1) if sessions else 0
        
        response_data = {
            'sessions': sessions,
            'stats': {
                'total_sessions': len(sessions),
                'total_minutes': total_minutes,
                'average_duration': avg_duration,
                'average_rating': avg_rating
            }
        }
        
        return jsonify(format_response(response_data))
        
    except Exception as e:
        logger.error(f"Get meditation history error: {e}")
        return jsonify(format_response(None, False, "Failed to get meditation history")), 500

@meditations_bp.route('/recommendations', methods=['GET'])
@require_auth
@handle_errors
def get_meditation_recommendations():
    """Get personalized meditation recommendations"""
    try:
        uid = g.current_user['uid']
        
        # Get user's recent mood and stress data
        from utils.helpers import get_date_range
        start_date, end_date = get_date_range(7)
        recent_moods = firestore_service.get_mood_logs(uid, start_date, end_date)
        user_stats = firestore_service.get_user_stats(uid)
        
        # Analyze patterns to suggest meditations
        recommendations = []
        
        if recent_moods:
            # Calculate average stress and mood
            avg_stress = sum(log.get('stress', 0) for log in recent_moods) / len(recent_moods)
            latest_mood = recent_moods[0].get('mood', 'neutral')
            
            # High stress - recommend stress relief
            if avg_stress > 6:
                recommendations.append({
                    'category': 'stress_relief',
                    'reason': 'Your recent stress levels suggest focusing on stress relief techniques',
                    'priority': 'high'
                })
            
            # Anxious or stressed mood - breathing exercises
            if latest_mood in ['anxious', 'stressed']:
                recommendations.append({
                    'category': 'breathing',
                    'reason': 'Breathing exercises can help with current feelings of stress or anxiety',
                    'priority': 'high'
                })
            
            # Low energy - focus meditations
            avg_energy = sum(log.get('energy', 0) for log in recent_moods) / len(recent_moods)
            if avg_energy < 4:
                recommendations.append({
                    'category': 'focus',
                    'reason': 'Focus meditations can help boost energy and concentration',
                    'priority': 'medium'
                })
        
        # Based on completion history
        completed_meditations = user_stats.get('completed_meditations', [])
        meditation_sessions = user_stats.get('meditation_sessions', 0)
        
        if meditation_sessions == 0:
            recommendations.append({
                'category': 'general',
                'reason': 'Start with beginner-friendly meditations to build your practice',
                'priority': 'high'
            })
        elif len(completed_meditations) < 5:
            recommendations.append({
                'category': 'breathing',
                'reason': 'Continue building your foundation with breathing exercises',
                'priority': 'medium'
            })
        
        # Time-based recommendations
        from datetime import datetime, timezone
        current_hour = datetime.now(timezone.utc).hour
        
        if 22 <= current_hour or current_hour <= 6:  # Evening/night
            recommendations.append({
                'category': 'sleep',
                'reason': 'Evening meditations can help prepare for restful sleep',
                'priority': 'medium'
            })
        
        # Remove duplicates and sort by priority
        unique_recommendations = []
        seen_categories = set()
        
        for rec in recommendations:
            if rec['category'] not in seen_categories:
                unique_recommendations.append(rec)
                seen_categories.add(rec['category'])
        
        # Sort by priority
        priority_order = {'high': 3, 'medium': 2, 'low': 1}
        unique_recommendations.sort(key=lambda x: priority_order.get(x['priority'], 0), reverse=True)
        
        response_data = {
            'recommendations': unique_recommendations[:3],  # Top 3 recommendations
            'user_context': {
                'recent_avg_stress': round(avg_stress, 1) if recent_moods else 0,
                'recent_avg_energy': round(avg_energy, 1) if recent_moods else 0,
                'latest_mood': latest_mood if recent_moods else 'unknown',
                'total_sessions': meditation_sessions,
                'completed_count': len(completed_meditations)
            }
        }
        
        return jsonify(format_response(response_data))
        
    except Exception as e:
        logger.error(f"Get meditation recommendations error: {e}")
        return jsonify(format_response(None, False, "Failed to get recommendations")), 500

def get_meditation_description(filename):
    """Generate description based on filename"""
    descriptions = {
        'breath': 'Focus on your breathing rhythm to center your mind and reduce stress',
        'sleep': 'Gentle meditation to help you relax and prepare for restful sleep',
        'stress': 'Targeted techniques to help manage and reduce stress levels',
        'anxiety': 'Calming practices to ease anxious thoughts and feelings',
        'focus': 'Improve concentration and mental clarity for better productivity',
        'calm': 'Find inner peace and tranquility through mindful awareness',
        'study': 'Enhance your learning capacity and retention through focused meditation',
        'morning': 'Start your day with positive intention and mindful awareness',
        'evening': 'Wind down and reflect on your day with peaceful meditation'
    }
    
    for keyword, description in descriptions.items():
        if keyword in filename:
            return description
    
    return 'A mindfulness meditation to support your mental wellness journey'

def get_featured_meditation(categorized_meditations, uid):
    """Get a featured meditation recommendation for the user"""
    # Simple logic to feature a meditation
    for category in ['breathing', 'stress_relief', 'general']:
        if categorized_meditations[category]:
            meditation = categorized_meditations[category][0]
            return {
                'id': meditation['id'],
                'name': meditation['name'],
                'category': meditation['category'],
                'description': meditation['description'],
                'url': meditation['url']
            }
    
    return None
