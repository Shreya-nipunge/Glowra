from flask import Blueprint, request, jsonify, g
from services.firestore_service import firestore_service
from utils.decorators import require_auth, handle_errors
from utils.helpers import format_response, get_date_range, calculate_mood_average, calculate_streak, get_wellness_insights
from datetime import datetime, timezone, timedelta
import logging

logger = logging.getLogger(__name__)

progress_bp = Blueprint('progress', __name__)

@progress_bp.route('/weekly', methods=['GET'])
@require_auth
@handle_errors
def get_weekly_progress():
    """Get user's weekly progress summary"""
    try:
        uid = g.current_user['uid']
        
        # Get date range for last 7 days
        start_date, end_date = get_date_range(7)
        
        # Get mood logs for the week
        mood_logs = firestore_service.get_mood_logs(uid, start_date, end_date)
        
        # Get journal entries for the week
        journal_entries = firestore_service.get_journal_entries(uid, 20)  # Get more to filter by date
        weekly_journals = [
            entry for entry in journal_entries 
            if entry.get('timestamp') and entry['timestamp'] >= start_date
        ]
        
        # Get user stats
        user_stats = firestore_service.get_user_stats(uid)
        
        # Calculate mood averages
        mood_averages = calculate_mood_average(mood_logs)
        
        # Calculate activity dates for streak
        activity_dates = []
        
        # Add mood log dates
        for log in mood_logs:
            if log.get('timestamp'):
                activity_dates.append(log['timestamp'])
        
        # Add journal entry dates
        for entry in weekly_journals:
            if entry.get('timestamp'):
                activity_dates.append(entry['timestamp'])
        
        # Calculate current streak
        current_streak = calculate_streak(activity_dates)
        
        # Get daily plan completion stats
        plan_stats = []
        current_date = datetime.now(timezone.utc).date()
        
        for i in range(7):
            date_str = (current_date - timedelta(days=i)).isoformat()
            daily_plan = firestore_service.get_daily_plan(uid, date_str)
            
            if daily_plan:
                completed = sum(1 for task in daily_plan.get('tasks', []) if task['status'] == 'completed')
                total = len(daily_plan.get('tasks', []))
                plan_stats.append({
                    'date': date_str,
                    'completed_tasks': completed,
                    'total_tasks': total
                })
        
        total_completed_tasks = sum(day['completed_tasks'] for day in plan_stats)
        
        # Analyze mood trend
        mood_trend = "stable"
        if len(mood_logs) >= 4:
            recent_moods = mood_logs[:3]  # Most recent 3
            older_moods = mood_logs[3:6]  # Previous 3
            
            recent_avg = calculate_mood_average(recent_moods)['mood_score']
            older_avg = calculate_mood_average(older_moods)['mood_score']
            
            if recent_avg > older_avg + 0.5:
                mood_trend = "improving"
            elif recent_avg < older_avg - 0.5:
                mood_trend = "declining"
        
        # Build response
        progress_data = {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'days': 7
            },
            'mood_metrics': {
                'average_mood_score': mood_averages['mood_score'],
                'average_energy': mood_averages['energy'],
                'average_stress': mood_averages['stress'],
                'mood_trend': mood_trend,
                'total_mood_logs': len(mood_logs)
            },
            'activity_metrics': {
                'streak_days': current_streak,
                'completed_tasks': total_completed_tasks,
                'total_journal_entries': len(weekly_journals),
                'daily_plan_stats': plan_stats
            },
            'user_stats': {
                'total_points': user_stats.get('points', 0),
                'current_level': user_stats.get('level', 1),
                'total_completed_tasks': user_stats.get('completed_tasks', 0),
                'badges_count': len(user_stats.get('badges', []))
            }
        }
        
        logger.info(f"Weekly progress calculated for user {uid}")
        return jsonify(format_response(progress_data))
        
    except Exception as e:
        logger.error(f"Get weekly progress error: {e}")
        return jsonify(format_response(None, False, "Failed to get weekly progress")), 500

@progress_bp.route('/insights', methods=['GET'])
@require_auth
@handle_errors
def get_progress_insights():
    """Get detailed wellness insights and patterns"""
    try:
        uid = g.current_user['uid']
        
        # Get date range (configurable via query param)
        days = request.args.get('days', 30, type=int)
        days = min(days, 90)  # Max 90 days
        
        start_date, end_date = get_date_range(days)
        
        # Get data for analysis
        mood_logs = firestore_service.get_mood_logs(uid, start_date, end_date)
        journal_entries = firestore_service.get_journal_entries(uid, 50)  # Get more entries
        
        # Filter journal entries by date
        period_journals = [
            entry for entry in journal_entries 
            if entry.get('timestamp') and entry['timestamp'] >= start_date
        ]
        
        # Generate wellness insights
        insights = get_wellness_insights(mood_logs, period_journals)
        
        # Analyze mood patterns by day of week
        mood_by_day = {}
        for log in mood_logs:
            if log.get('timestamp'):
                day_of_week = log['timestamp'].strftime('%A')
                if day_of_week not in mood_by_day:
                    mood_by_day[day_of_week] = []
                mood_by_day[day_of_week].append(log)
        
        # Calculate averages by day of week
        daily_patterns = {}
        for day, logs in mood_by_day.items():
            daily_patterns[day] = calculate_mood_average(logs)
        
        # Analyze journal categories over time
        category_trends = {}
        for entry in period_journals:
            ai_insight = entry.get('ai_insight', {})
            categories = ai_insight.get('categories', [])
            entry_date = entry.get('timestamp')
            
            if entry_date:
                week_start = entry_date - timedelta(days=entry_date.weekday())
                week_key = week_start.strftime('%Y-%W')
                
                if week_key not in category_trends:
                    category_trends[week_key] = {}
                
                for category in categories:
                    category_trends[week_key][category] = category_trends[week_key].get(category, 0) + 1
        
        # Calculate improvement metrics
        if len(mood_logs) >= 10:
            first_half = mood_logs[len(mood_logs)//2:]  # Older entries
            second_half = mood_logs[:len(mood_logs)//2]  # Newer entries
            
            first_avg = calculate_mood_average(first_half)
            second_avg = calculate_mood_average(second_half)
            
            improvements = {
                'mood_improvement': round(second_avg['mood_score'] - first_avg['mood_score'], 2),
                'energy_improvement': round(second_avg['energy'] - first_avg['energy'], 2),
                'stress_reduction': round(first_avg['stress'] - second_avg['stress'], 2)  # Lower is better
            }
        else:
            improvements = {
                'mood_improvement': 0,
                'energy_improvement': 0,
                'stress_reduction': 0
            }
        
        # Build comprehensive insights response
        insights_data = {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'days_analyzed': days
            },
            'summary': insights,
            'patterns': {
                'daily_mood_patterns': daily_patterns,
                'category_trends': category_trends,
                'improvement_metrics': improvements
            },
            'recommendations': [
                "Continue your journaling practice to maintain self-awareness",
                "Focus on activities that boost your energy levels",
                "Practice stress management techniques during high-stress periods"
            ]
        }
        
        # Add personalized recommendations based on patterns
        if insights['recent_mood_trend'] == 'declining':
            insights_data['recommendations'].insert(0, 
                "Consider reaching out to friends or engaging in mood-boosting activities")
        elif insights['recent_mood_trend'] == 'improving':
            insights_data['recommendations'].insert(0, 
                "Great progress! Keep up the positive habits that are working for you")
        
        logger.info(f"Progress insights generated for user {uid}")
        return jsonify(format_response(insights_data))
        
    except Exception as e:
        logger.error(f"Get progress insights error: {e}")
        return jsonify(format_response(None, False, "Failed to get progress insights")), 500

@progress_bp.route('/mood-logs', methods=['POST'])
@require_auth
@handle_errors
def create_mood_log():
    """Create a new mood log entry"""
    try:
        uid = g.current_user['uid']
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['mood', 'energy', 'stress']
        for field in required_fields:
            if field not in data:
                return jsonify(format_response(None, False, f"Missing required field: {field}")), 400
        
        # Validate mood value
        valid_moods = ['happy', 'sad', 'stressed', 'anxious', 'neutral']
        if data['mood'] not in valid_moods:
            return jsonify(format_response(None, False, f"Invalid mood. Must be one of: {valid_moods}")), 400
        
        # Validate numeric ranges
        if not (0 <= data['energy'] <= 10):
            return jsonify(format_response(None, False, "Energy must be between 0 and 10")), 400
        
        if not (0 <= data['stress'] <= 10):
            return jsonify(format_response(None, False, "Stress must be between 0 and 10")), 400
        
        # Prepare mood log data
        mood_data = {
            'mood': data['mood'],
            'energy': data['energy'],
            'stress': data['stress'],
            'note': data.get('note', '').strip()[:500]  # Max 500 characters
        }
        
        # Save to Firestore
        log_id = firestore_service.save_mood_log(uid, mood_data)
        
        # Stream to BigQuery
        from services.bigquery_service import bigquery_service
        bigquery_service.stream_mood_log({**mood_data, 'user_id': uid})
        
        # Update user stats
        user_stats = firestore_service.get_user_stats(uid)
        updated_stats = {
            'points': user_stats.get('points', 0) + 5,  # 5 points for mood logging
            'last_mood_log_date': get_current_utc_time()
        }
        firestore_service.update_user_stats(uid, updated_stats)
        
        response_data = {
            'log_id': log_id,
            'mood': mood_data['mood'],
            'energy': mood_data['energy'],
            'stress': mood_data['stress'],
            'points_earned': 5,
            'timestamp': get_current_utc_time().isoformat()
        }
        
        logger.info(f"Mood log created for user {uid}")
        return jsonify(format_response(response_data, True, "Mood log created successfully"))
        
    except Exception as e:
        logger.error(f"Create mood log error: {e}")
        return jsonify(format_response(None, False, "Failed to create mood log")), 500

@progress_bp.route('/mood-logs', methods=['GET'])
@require_auth
@handle_errors
def get_mood_logs():
    """Get user's mood logs with optional date filtering"""
    try:
        uid = g.current_user['uid']
        
        # Get query parameters
        from_date_str = request.args.get('from')
        to_date_str = request.args.get('to')
        limit = request.args.get('limit', 50, type=int)
        limit = min(limit, 100)  # Max 100 logs
        
        # Parse dates if provided
        from_date = None
        to_date = None
        
        if from_date_str:
            try:
                from_date = datetime.fromisoformat(from_date_str.replace('Z', '+00:00'))
            except ValueError:
                return jsonify(format_response(None, False, "Invalid 'from' date format")), 400
        
        if to_date_str:
            try:
                to_date = datetime.fromisoformat(to_date_str.replace('Z', '+00:00'))
            except ValueError:
                return jsonify(format_response(None, False, "Invalid 'to' date format")), 400
        
        # Get mood logs
        mood_logs = firestore_service.get_mood_logs(uid, from_date, to_date)
        
        # Limit results
        mood_logs = mood_logs[:limit]
        
        # Format response
        formatted_logs = []
        for log in mood_logs:
            formatted_log = {
                'id': log.get('id'),
                'mood': log['mood'],
                'energy': log['energy'],
                'stress': log['stress'],
                'note': log.get('note', ''),
                'timestamp': log['timestamp'].isoformat()
            }
            formatted_logs.append(formatted_log)
        
        response_data = {
            'logs': formatted_logs,
            'total': len(formatted_logs),
            'period': {
                'from': from_date.isoformat() if from_date else None,
                'to': to_date.isoformat() if to_date else None
            }
        }
        
        return jsonify(format_response(response_data))
        
    except Exception as e:
        logger.error(f"Get mood logs error: {e}")
        return jsonify(format_response(None, False, "Failed to get mood logs")), 500
