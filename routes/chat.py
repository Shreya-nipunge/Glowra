from flask import Blueprint, request, jsonify, g
from services.ai_service import ai_service
from services.firestore_service import firestore_service
from utils.decorators import require_auth, handle_errors
from utils.helpers import format_response, get_current_utc_time
from models.schemas import ChatIn, ChatOut
from pydantic import ValidationError
import logging
import uuid

logger = logging.getLogger(__name__)

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/', methods=['POST'])
@require_auth
@handle_errors
def chat_with_ai():
    """Chat with AI wellness companion"""
    try:
        uid = g.current_user['uid']
        data = request.get_json()
        
        # Validate input
        try:
            chat_input = ChatIn(**data)
        except ValidationError as e:
            return jsonify(format_response(None, False, f"Validation error: {e}")), 400
        
        # Get or create conversation ID
        conversation_id = chat_input.conversation_id or str(uuid.uuid4())
        
        # Get conversation history
        conversation_history = []
        if chat_input.conversation_id:
            # In production, you'd fetch from database
            # For now, we'll work with current message only
            conversation_history = []
        
        logger.info(f"Processing chat message for user {uid}")
        
        # Get AI response
        ai_response = ai_service.chat_response(
            message=chat_input.message,
            conversation_history=conversation_history
        )
        
        # Save conversation turn to Firestore
        conversation_data = {
            'conversation_id': conversation_id,
            'user_message': chat_input.message,
            'ai_response': ai_response['response'],
            'mood_detected': ai_response.get('mood_detected', 'neutral'),
            'suggestions': ai_response.get('suggestions', []),
            'timestamp': get_current_utc_time()
        }
        
        # Save to conversations collection
        try:
            conversation_ref = firestore_service.db.collection('conversations').document()
            conversation_ref.set({**conversation_data, 'user_id': uid})
            logger.info(f"Conversation turn saved for user {uid}")
        except Exception as e:
            logger.warning(f"Failed to save conversation: {e}")
        
        # Update user stats (engagement points)
        user_stats = firestore_service.get_user_stats(uid)
        updated_stats = {
            'points': user_stats.get('points', 0) + 2,  # 2 points for chat interaction
            'chat_messages': user_stats.get('chat_messages', 0) + 1,
            'last_chat_date': get_current_utc_time()
        }
        firestore_service.update_user_stats(uid, updated_stats)
        
        # Prepare response
        response_data = {
            'conversation_id': conversation_id,
            'response': ai_response['response'],
            'mood_detected': ai_response.get('mood_detected', 'neutral'),
            'suggestions': ai_response.get('suggestions', []),
            'points_earned': 2,
            'timestamp': get_current_utc_time().isoformat()
        }
        
        logger.info(f"Chat response generated for user {uid}")
        return jsonify(format_response(response_data, True, "Chat response generated"))
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return jsonify(format_response(None, False, "Failed to process chat message")), 500

@chat_bp.route('/conversations', methods=['GET'])
@require_auth
@handle_errors
def get_conversations():
    """Get user's recent conversations"""
    try:
        uid = g.current_user['uid']
        
        # Get query parameters
        limit = request.args.get('limit', 10, type=int)
        limit = min(limit, 50)  # Max 50 conversations
        
        # Get conversations from Firestore
        try:
            conversations_ref = (firestore_service.db.collection('conversations')
                               .where('user_id', '==', uid)
                               .order_by('timestamp', direction=firestore_service.db.DESCENDING)
                               .limit(limit))
            
            conversations = []
            for doc in conversations_ref.stream():
                data = doc.to_dict()
                conversation = {
                    'id': doc.id,
                    'conversation_id': data.get('conversation_id'),
                    'user_message': data.get('user_message'),
                    'ai_response': data.get('ai_response'),
                    'mood_detected': data.get('mood_detected'),
                    'timestamp': data.get('timestamp').isoformat() if data.get('timestamp') else None
                }
                conversations.append(conversation)
            
        except Exception as e:
            logger.warning(f"Failed to fetch conversations: {e}")
            conversations = []
        
        # Group by conversation_id
        grouped_conversations = {}
        for conv in conversations:
            conv_id = conv['conversation_id']
            if conv_id not in grouped_conversations:
                grouped_conversations[conv_id] = []
            grouped_conversations[conv_id].append(conv)
        
        # Format for response
        conversation_summaries = []
        for conv_id, messages in grouped_conversations.items():
            latest_message = max(messages, key=lambda x: x['timestamp'] or '')
            conversation_summaries.append({
                'conversation_id': conv_id,
                'message_count': len(messages),
                'latest_message': latest_message['user_message'][:100] + '...' if len(latest_message['user_message']) > 100 else latest_message['user_message'],
                'latest_timestamp': latest_message['timestamp'],
                'last_mood': latest_message['mood_detected']
            })
        
        # Sort by latest timestamp
        conversation_summaries.sort(key=lambda x: x['latest_timestamp'] or '', reverse=True)
        
        response_data = {
            'conversations': conversation_summaries,
            'total': len(conversation_summaries)
        }
        
        return jsonify(format_response(response_data))
        
    except Exception as e:
        logger.error(f"Get conversations error: {e}")
        return jsonify(format_response(None, False, "Failed to get conversations")), 500

@chat_bp.route('/conversations/<conversation_id>', methods=['GET'])
@require_auth
@handle_errors
def get_conversation_history(conversation_id):
    """Get full conversation history"""
    try:
        uid = g.current_user['uid']
        
        # Get conversation messages
        try:
            messages_ref = (firestore_service.db.collection('conversations')
                          .where('user_id', '==', uid)
                          .where('conversation_id', '==', conversation_id)
                          .order_by('timestamp'))
            
            messages = []
            for doc in messages_ref.stream():
                data = doc.to_dict()
                message = {
                    'id': doc.id,
                    'user_message': data.get('user_message'),
                    'ai_response': data.get('ai_response'),
                    'mood_detected': data.get('mood_detected'),
                    'suggestions': data.get('suggestions', []),
                    'timestamp': data.get('timestamp').isoformat() if data.get('timestamp') else None
                }
                messages.append(message)
            
        except Exception as e:
            logger.warning(f"Failed to fetch conversation {conversation_id}: {e}")
            messages = []
        
        if not messages:
            return jsonify(format_response(None, False, "Conversation not found")), 404
        
        # Calculate conversation insights
        mood_trends = [msg['mood_detected'] for msg in messages if msg['mood_detected']]
        all_suggestions = []
        for msg in messages:
            all_suggestions.extend(msg.get('suggestions', []))
        
        conversation_insights = {
            'total_messages': len(messages),
            'duration_minutes': None,  # Could calculate from first/last timestamp
            'mood_progression': mood_trends,
            'common_suggestions': list(set(all_suggestions))[:5],  # Top 5 unique suggestions
            'started_at': messages[0]['timestamp'] if messages else None,
            'last_updated': messages[-1]['timestamp'] if messages else None
        }
        
        response_data = {
            'conversation_id': conversation_id,
            'messages': messages,
            'insights': conversation_insights
        }
        
        return jsonify(format_response(response_data))
        
    except Exception as e:
        logger.error(f"Get conversation history error: {e}")
        return jsonify(format_response(None, False, "Failed to get conversation history")), 500

@chat_bp.route('/suggestions', methods=['GET'])
@require_auth
@handle_errors
def get_chat_suggestions():
    """Get suggested conversation starters based on user's recent mood/journal data"""
    try:
        uid = g.current_user['uid']
        
        # Get user's recent data for context
        from utils.helpers import get_date_range
        start_date, end_date = get_date_range(7)
        recent_moods = firestore_service.get_mood_logs(uid, start_date, end_date)
        recent_journals = firestore_service.get_journal_entries(uid, 3)
        
        # Generate contextual suggestions
        suggestions = []
        
        # Default suggestions
        default_suggestions = [
            "How are you feeling today?",
            "What's been on your mind lately?",
            "I'd like some tips for managing stress",
            "Can you help me with study motivation?",
            "I want to talk about my goals"
        ]
        
        # Add context-based suggestions
        if recent_moods:
            latest_mood = recent_moods[0].get('mood', 'neutral')
            if latest_mood in ['stressed', 'anxious']:
                suggestions.extend([
                    "I'm feeling stressed about upcoming exams",
                    "Can you suggest some relaxation techniques?",
                    "How can I manage my anxiety better?"
                ])
            elif latest_mood == 'sad':
                suggestions.extend([
                    "I've been feeling down lately",
                    "How can I boost my mood?",
                    "I need some encouragement today"
                ])
            elif latest_mood == 'happy':
                suggestions.extend([
                    "I'm having a great day! How can I maintain this?",
                    "What are some ways to spread positivity?",
                    "I want to celebrate my progress"
                ])
        
        # Add journal-based suggestions
        if recent_journals:
            latest_categories = recent_journals[0].get('ai_insight', {}).get('categories', [])
            if 'exam_anxiety' in latest_categories:
                suggestions.append("I need help preparing for exams")
            if 'sleep' in latest_categories:
                suggestions.append("I'm having trouble with my sleep schedule")
            if 'loneliness' in latest_categories:
                suggestions.append("I've been feeling lonely lately")
        
        # Remove duplicates and limit
        unique_suggestions = list(dict.fromkeys(suggestions + default_suggestions))[:8]
        
        response_data = {
            'suggestions': unique_suggestions,
            'context': {
                'recent_mood': recent_moods[0].get('mood') if recent_moods else None,
                'recent_categories': recent_journals[0].get('ai_insight', {}).get('categories', []) if recent_journals else []
            }
        }
        
        return jsonify(format_response(response_data))
        
    except Exception as e:
        logger.error(f"Get chat suggestions error: {e}")
        return jsonify(format_response(None, False, "Failed to get chat suggestions")), 500
