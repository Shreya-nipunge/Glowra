from flask import Blueprint, request, jsonify, g
from services.ai_service import ai_service
from services.firestore_service import firestore_service
from services.bigquery_service import bigquery_service
from utils.decorators import require_auth, handle_errors
from utils.helpers import format_response, get_current_utc_time
from models.schemas import JournalIn, InsightOut
from pydantic import ValidationError
import logging

logger = logging.getLogger(__name__)

journal_bp = Blueprint('journal', __name__)

@journal_bp.route('/', methods=['POST'])
@require_auth
@handle_errors
def create_journal_entry():
    """Create a new journal entry with AI analysis"""
    try:
        uid = g.current_user['uid']
        data = request.get_json()
        
        # Validate input
        try:
            journal_input = JournalIn(**data)
        except ValidationError as e:
            return jsonify(format_response(None, False, f"Validation error: {e}")), 400
        
        # Get AI analysis of journal text
        logger.info(f"Analyzing journal entry for user {uid}")
        ai_insight = ai_service.analyze_journal(journal_input.text)
        
        # Prepare journal entry data
        journal_data = {
            'text': journal_input.text,
            'ai_insight': ai_insight,
            'word_count': len(journal_input.text.split()),
            'character_count': len(journal_input.text)
        }
        
        # Save to Firestore
        entry_id = firestore_service.save_journal_entry(uid, journal_data)
        
        # Stream to BigQuery for analytics
        bigquery_service.stream_journal_insight(journal_data)
        
        # Update user stats
        firestore_service.update_user_stats(uid, {
            'journal_entries': firestore_service.get_user_stats(uid).get('journal_entries', 0) + 1,
            'points': firestore_service.get_user_stats(uid).get('points', 0) + 10,  # 10 points for journaling
            'last_journal_date': get_current_utc_time()
        })
        
        # Format response
        response_data = {
            'entry_id': entry_id,
            'insight': ai_insight,
            'points_earned': 10
        }
        
        logger.info(f"Journal entry created successfully for user {uid}")
        return jsonify(format_response(response_data, True, "Journal entry created and analyzed"))
        
    except Exception as e:
        logger.error(f"Journal creation error: {e}")
        return jsonify(format_response(None, False, "Failed to create journal entry")), 500

@journal_bp.route('/', methods=['GET'])
@require_auth
@handle_errors
def get_journal_entries():
    """Get user's journal entries"""
    try:
        uid = g.current_user['uid']
        
        # Get query parameters
        limit = request.args.get('limit', 10, type=int)
        limit = min(limit, 50)  # Max 50 entries
        
        # Get journal entries from Firestore
        entries = firestore_service.get_journal_entries(uid, limit)
        
        # Format entries for response
        formatted_entries = []
        for entry in entries:
            formatted_entry = {
                'id': entry['id'],
                'text': entry['text'],
                'word_count': entry.get('word_count', 0),
                'timestamp': entry['timestamp'].isoformat(),
                'ai_insight': entry.get('ai_insight', {}),
                'mood': entry.get('ai_insight', {}).get('mood', 'neutral')
            }
            formatted_entries.append(formatted_entry)
        
        logger.info(f"Retrieved {len(formatted_entries)} journal entries for user {uid}")
        return jsonify(format_response({
            'entries': formatted_entries,
            'total': len(formatted_entries)
        }))
        
    except Exception as e:
        logger.error(f"Get journal entries error: {e}")
        return jsonify(format_response(None, False, "Failed to get journal entries")), 500

@journal_bp.route('/<entry_id>', methods=['GET'])
@require_auth
@handle_errors
def get_journal_entry(entry_id):
    """Get specific journal entry"""
    try:
        uid = g.current_user['uid']
        
        # Get specific entry (would need to implement in firestore_service)
        # For now, get all entries and filter
        entries = firestore_service.get_journal_entries(uid, 100)
        
        entry = None
        for e in entries:
            if e['id'] == entry_id:
                entry = e
                break
        
        if not entry:
            return jsonify(format_response(None, False, "Journal entry not found")), 404
        
        # Check if entry belongs to current user
        if entry.get('user_id') != uid:
            return jsonify(format_response(None, False, "Unauthorized")), 403
        
        formatted_entry = {
            'id': entry['id'],
            'text': entry['text'],
            'word_count': entry.get('word_count', 0),
            'character_count': entry.get('character_count', 0),
            'timestamp': entry['timestamp'].isoformat(),
            'ai_insight': entry.get('ai_insight', {})
        }
        
        return jsonify(format_response(formatted_entry))
        
    except Exception as e:
        logger.error(f"Get journal entry error: {e}")
        return jsonify(format_response(None, False, "Failed to get journal entry")), 500

@journal_bp.route('/insights/summary', methods=['GET'])
@require_auth
@handle_errors
def get_insights_summary():
    """Get summary of recent insights and patterns"""
    try:
        uid = g.current_user['uid']
        
        # Get recent journal entries
        recent_entries = firestore_service.get_journal_entries(uid, 30)  # Last 30 entries
        
        if not recent_entries:
            return jsonify(format_response({
                'total_entries': 0,
                'mood_distribution': {},
                'top_categories': [],
                'average_confidence': 0,
                'risk_levels': {}
            }))
        
        # Analyze patterns
        moods = []
        categories = []
        confidences = []
        risks = []
        
        for entry in recent_entries:
            insight = entry.get('ai_insight', {})
            if insight:
                moods.append(insight.get('mood', 'neutral'))
                categories.extend(insight.get('categories', []))
                confidences.append(insight.get('confidence', 0))
                risks.append(insight.get('risk', 'low'))
        
        # Calculate distributions
        mood_dist = {}
        for mood in moods:
            mood_dist[mood] = mood_dist.get(mood, 0) + 1
        
        category_dist = {}
        for category in categories:
            category_dist[category] = category_dist.get(category, 0) + 1
        
        risk_dist = {}
        for risk in risks:
            risk_dist[risk] = risk_dist.get(risk, 0) + 1
        
        top_categories = sorted(category_dist.items(), key=lambda x: x[1], reverse=True)[:5]
        
        summary = {
            'total_entries': len(recent_entries),
            'mood_distribution': mood_dist,
            'top_categories': [cat[0] for cat in top_categories],
            'average_confidence': round(sum(confidences) / len(confidences), 2) if confidences else 0,
            'risk_levels': risk_dist
        }
        
        return jsonify(format_response(summary))
        
    except Exception as e:
        logger.error(f"Get insights summary error: {e}")
        return jsonify(format_response(None, False, "Failed to get insights summary")), 500
