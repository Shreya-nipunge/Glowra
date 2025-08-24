from flask import Blueprint, request, jsonify, g
from services.ai_service import ai_service
from services.firestore_service import firestore_service
from utils.decorators import require_auth, handle_errors
from utils.helpers import format_response, get_current_utc_time, get_date_range
from datetime import datetime, timezone
import logging
import uuid

logger = logging.getLogger(__name__)

planner_bp = Blueprint('planner', __name__)

@planner_bp.route('/today', methods=['GET'])
@require_auth
@handle_errors
def get_daily_plan():
    """Get or generate daily plan for today"""
    try:
        uid = g.current_user['uid']
        today = datetime.now(timezone.utc).date().isoformat()
        
        # Check if plan already exists for today
        existing_plan = firestore_service.get_daily_plan(uid, today)
        
        if existing_plan:
            logger.info(f"Retrieved existing daily plan for user {uid}")
            return jsonify(format_response(existing_plan))
        
        # Generate new plan based on user's recent data
        logger.info(f"Generating new daily plan for user {uid}")
        
        # Get user's recent mood logs and journal insights
        start_date, end_date = get_date_range(7)  # Last 7 days
        recent_moods = firestore_service.get_mood_logs(uid, start_date, end_date)
        recent_journals = firestore_service.get_journal_entries(uid, 5)  # Last 5 entries
        user_stats = firestore_service.get_user_stats(uid)
        
        # Prepare data for AI recommendation generation
        user_data = {
            'recent_moods': [
                {
                    'mood': log.get('mood'),
                    'energy': log.get('energy'),
                    'stress': log.get('stress'),
                    'timestamp': log.get('timestamp').isoformat() if log.get('timestamp') else None
                } for log in recent_moods[-7:]  # Last 7 mood logs
            ],
            'recent_insights': [
                {
                    'categories': entry.get('ai_insight', {}).get('categories', []),
                    'mood': entry.get('ai_insight', {}).get('mood'),
                    'risk': entry.get('ai_insight', {}).get('risk')
                } for entry in recent_journals
            ],
            'preferences': firestore_service.get_user(uid).get('preferences', {}),
            'stats': user_stats
        }
        
        # Generate AI recommendations
        recommendations = ai_service.generate_daily_recommendations(user_data)
        
        # Create tasks from recommendations
        tasks = []
        for i, rec in enumerate(recommendations):
            task = {
                'id': str(uuid.uuid4()),
                'title': rec.get('title', f'Activity {i+1}'),
                'cta_type': rec.get('cta_type', 'activity'),
                'estimated_minutes': rec.get('estimated_minutes', 10),
                'description': rec.get('description', ''),
                'type': rec.get('type', 'general'),
                'status': 'pending'
            }
            tasks.append(task)
        
        # Create daily plan
        daily_plan = {
            'date': today,
            'tasks': tasks,
            'generated_at': get_current_utc_time(),
            'total_estimated_minutes': sum(task['estimated_minutes'] for task in tasks),
            'completed_tasks': 0
        }
        
        # Save plan to Firestore
        firestore_service.save_daily_plan(uid, today, daily_plan)
        
        logger.info(f"Generated daily plan with {len(tasks)} tasks for user {uid}")
        return jsonify(format_response(daily_plan, True, "Daily plan generated successfully"))
        
    except Exception as e:
        logger.error(f"Get daily plan error: {e}")
        return jsonify(format_response(None, False, "Failed to get daily plan")), 500

@planner_bp.route('/task/<task_id>/complete', methods=['POST'])
@require_auth
@handle_errors
def complete_task(task_id):
    """Mark a task as completed"""
    try:
        uid = g.current_user['uid']
        today = datetime.now(timezone.utc).date().isoformat()
        
        # Get today's plan
        daily_plan = firestore_service.get_daily_plan(uid, today)
        
        if not daily_plan:
            return jsonify(format_response(None, False, "No daily plan found for today")), 404
        
        # Find and update the task
        task_found = False
        for task in daily_plan.get('tasks', []):
            if task['id'] == task_id:
                task['status'] = 'completed'
                task['completed_at'] = get_current_utc_time().isoformat()
                task_found = True
                break
        
        if not task_found:
            return jsonify(format_response(None, False, "Task not found")), 404
        
        # Update completed tasks count
        completed_count = sum(1 for task in daily_plan['tasks'] if task['status'] == 'completed')
        daily_plan['completed_tasks'] = completed_count
        
        # Save updated plan
        firestore_service.save_daily_plan(uid, today, daily_plan)
        
        # Update user stats and award points
        user_stats = firestore_service.get_user_stats(uid)
        points_earned = 5  # 5 points per completed task
        
        updated_stats = {
            'completed_tasks': user_stats.get('completed_tasks', 0) + 1,
            'points': user_stats.get('points', 0) + points_earned,
            'last_activity_date': get_current_utc_time()
        }
        
        # Check for streak update
        if completed_count == 1:  # First task of the day
            last_activity = user_stats.get('last_activity_date')
            if last_activity:
                last_date = last_activity.date() if hasattr(last_activity, 'date') else datetime.fromisoformat(str(last_activity)).date()
                today_date = datetime.now(timezone.utc).date()
                
                if (today_date - last_date).days == 1:
                    # Consecutive day - increment streak
                    updated_stats['streak_days'] = user_stats.get('streak_days', 0) + 1
                elif (today_date - last_date).days > 1:
                    # Streak broken - reset
                    updated_stats['streak_days'] = 1
            else:
                # First activity ever
                updated_stats['streak_days'] = 1
        
        firestore_service.update_user_stats(uid, updated_stats)
        
        response_data = {
            'task_id': task_id,
            'status': 'completed',
            'points_earned': points_earned,
            'total_completed': completed_count,
            'streak_days': updated_stats.get('streak_days', 0)
        }
        
        logger.info(f"Task {task_id} completed by user {uid}")
        return jsonify(format_response(response_data, True, "Task marked as completed"))
        
    except Exception as e:
        logger.error(f"Complete task error: {e}")
        return jsonify(format_response(None, False, "Failed to complete task")), 500

@planner_bp.route('/task/<task_id>/skip', methods=['POST'])
@require_auth
@handle_errors
def skip_task(task_id):
    """Mark a task as skipped"""
    try:
        uid = g.current_user['uid']
        today = datetime.now(timezone.utc).date().isoformat()
        
        # Get today's plan
        daily_plan = firestore_service.get_daily_plan(uid, today)
        
        if not daily_plan:
            return jsonify(format_response(None, False, "No daily plan found for today")), 404
        
        # Find and update the task
        task_found = False
        for task in daily_plan.get('tasks', []):
            if task['id'] == task_id:
                task['status'] = 'skipped'
                task['skipped_at'] = get_current_utc_time().isoformat()
                task_found = True
                break
        
        if not task_found:
            return jsonify(format_response(None, False, "Task not found")), 404
        
        # Save updated plan
        firestore_service.save_daily_plan(uid, today, daily_plan)
        
        logger.info(f"Task {task_id} skipped by user {uid}")
        return jsonify(format_response({'task_id': task_id, 'status': 'skipped'}, True, "Task marked as skipped"))
        
    except Exception as e:
        logger.error(f"Skip task error: {e}")
        return jsonify(format_response(None, False, "Failed to skip task")), 500

@planner_bp.route('/history', methods=['GET'])
@require_auth
@handle_errors
def get_plan_history():
    """Get user's daily plan history"""
    try:
        uid = g.current_user['uid']
        
        # Get query parameters
        days = request.args.get('days', 7, type=int)
        days = min(days, 30)  # Max 30 days
        
        # Generate date list for the last N days
        history = []
        current_date = datetime.now(timezone.utc).date()
        
        for i in range(days):
            date_str = (current_date - datetime.timedelta(days=i)).isoformat()
            plan = firestore_service.get_daily_plan(uid, date_str)
            
            if plan:
                # Calculate completion rate
                total_tasks = len(plan.get('tasks', []))
                completed_tasks = sum(1 for task in plan.get('tasks', []) if task['status'] == 'completed')
                completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
                
                history_item = {
                    'date': date_str,
                    'total_tasks': total_tasks,
                    'completed_tasks': completed_tasks,
                    'completion_rate': round(completion_rate, 1),
                    'total_minutes': plan.get('total_estimated_minutes', 0)
                }
            else:
                history_item = {
                    'date': date_str,
                    'total_tasks': 0,
                    'completed_tasks': 0,
                    'completion_rate': 0,
                    'total_minutes': 0
                }
            
            history.append(history_item)
        
        # Calculate overall stats
        total_plans = len([h for h in history if h['total_tasks'] > 0])
        avg_completion = sum(h['completion_rate'] for h in history) / len(history) if history else 0
        total_completed = sum(h['completed_tasks'] for h in history)
        
        response_data = {
            'history': history,
            'stats': {
                'total_plans_generated': total_plans,
                'average_completion_rate': round(avg_completion, 1),
                'total_tasks_completed': total_completed
            }
        }
        
        return jsonify(format_response(response_data))
        
    except Exception as e:
        logger.error(f"Get plan history error: {e}")
        return jsonify(format_response(None, False, "Failed to get plan history")), 500
