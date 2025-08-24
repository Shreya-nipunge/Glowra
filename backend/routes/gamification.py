from flask import Blueprint, request, jsonify, g
from services.firestore_service import firestore_service
from utils.decorators import require_auth, handle_errors
from utils.helpers import format_response, get_current_utc_time, get_date_range
from datetime import datetime, timezone, timedelta
import logging

logger = logging.getLogger(__name__)

gamification_bp = Blueprint('gamification', __name__)

def calculate_user_level(points):
    """Calculate user level based on points"""
    if points < 100:
        return 1
    elif points < 300:
        return 2
    elif points < 600:
        return 3
    elif points < 1000:
        return 4
    elif points < 1500:
        return 5
    else:
        return min(10, 5 + (points - 1500) // 500)

def get_available_badges():
    """Define available badges and their criteria"""
    return {
        'first_check_in': {
            'name': 'First Check-in',
            'description': 'Logged your first mood',
            'icon': '🎯',
            'points': 10
        },
        'journal_starter': {
            'name': 'Journal Starter',
            'description': 'Created your first journal entry',
            'icon': '📝',
            'points': 15
        },
        'week_warrior': {
            'name': 'Week Warrior',
            'description': 'Maintained a 7-day activity streak',
            'icon': '🔥',
            'points': 50
        },
        'mood_tracker': {
            'name': 'Mood Tracker',
            'description': 'Logged mood 10 times',
            'icon': '📊',
            'points': 25
        },
        'reflection_master': {
            'name': 'Reflection Master',
            'description': 'Wrote 20 journal entries',
            'icon': '🧠',
            'points': 75
        },
        'task_champion': {
            'name': 'Task Champion',
            'description': 'Completed 25 daily tasks',
            'icon': '🏆',
            'points': 60
        },
        'mindful_minute': {
            'name': 'Mindful Minute',
            'description': 'Completed first mindfulness task',
            'icon': '🧘',
            'points': 20
        },
        'consistency_king': {
            'name': 'Consistency King',
            'description': 'Maintained a 30-day streak',
            'icon': '👑',
            'points': 150
        },
        'wellness_explorer': {
            'name': 'Wellness Explorer',
            'description': 'Tried 5 different activity types',
            'icon': '🗺️',
            'points': 40
        },
        'point_collector': {
            'name': 'Point Collector',
            'description': 'Earned 500 points',
            'icon': '💎',
            'points': 30
        }
    }

def check_badge_eligibility(uid, user_stats, mood_logs, journal_entries, daily_plans):
    """Check which badges user is eligible for"""
    available_badges = get_available_badges()
    current_badges = user_stats.get('badges', [])
    new_badges = []
    
    # Badge criteria checks
    criteria_checks = {
        'first_check_in': len(mood_logs) >= 1,
        'journal_starter': len(journal_entries) >= 1,
        'week_warrior': user_stats.get('streak_days', 0) >= 7,
        'mood_tracker': len(mood_logs) >= 10,
        'reflection_master': len(journal_entries) >= 20,
        'task_champion': user_stats.get('completed_tasks', 0) >= 25,
        'mindful_minute': any(
            any(task.get('type') == 'breathing' and task.get('status') == 'completed' 
                for task in plan.get('tasks', []))
            for plan in daily_plans
        ),
        'consistency_king': user_stats.get('streak_days', 0) >= 30,
        'wellness_explorer': len(set(
            task.get('type', 'general') 
            for plan in daily_plans 
            for task in plan.get('tasks', []) 
            if task.get('status') == 'completed'
        )) >= 5,
        'point_collector': user_stats.get('points', 0) >= 500
    }
    
    # Award new badges
    for badge_id, earned in criteria_checks.items():
        if earned and badge_id not in current_badges:
            badge_info = available_badges[badge_id]
            new_badges.append({
                'id': badge_id,
                'name': badge_info['name'],
                'description': badge_info['description'],
                'icon': badge_info['icon'],
                'earned_at': get_current_utc_time(),
                'points': badge_info['points']
            })
            current_badges.append(badge_id)
    
    return new_badges, current_badges

@gamification_bp.route('/badges', methods=['GET'])
@require_auth
@handle_errors
def get_user_badges():
    """Get user's earned badges and available badges"""
    try:
        uid = g.current_user['uid']
        
        # Get user stats
        user_stats = firestore_service.get_user_stats(uid)
        
        # Get user activity data for badge calculation
        start_date, end_date = get_date_range(90)  # Last 90 days for comprehensive check
        mood_logs = firestore_service.get_mood_logs(uid, start_date, end_date)
        journal_entries = firestore_service.get_journal_entries(uid, 50)
        
        # Get daily plans for activity type analysis
        daily_plans = []
        current_date = datetime.now(timezone.utc).date()
        for i in range(30):  # Last 30 days
            date_str = (current_date - timedelta(days=i)).isoformat()
            plan = firestore_service.get_daily_plan(uid, date_str)
            if plan:
                daily_plans.append(plan)
        
        # Check for new badges
        new_badges, updated_badge_list = check_badge_eligibility(
            uid, user_stats, mood_logs, journal_entries, daily_plans
        )
        
        # Update user stats if new badges were earned
        if new_badges:
            badge_points = sum(badge['points'] for badge in new_badges)
            updated_stats = {
                'badges': updated_badge_list,
                'points': user_stats.get('points', 0) + badge_points
            }
            firestore_service.update_user_stats(uid, updated_stats)
            user_stats.update(updated_stats)
        
        # Get earned badge details
        available_badges = get_available_badges()
        earned_badges = []
        
        for badge_id in user_stats.get('badges', []):
            if badge_id in available_badges:
                badge_info = available_badges[badge_id]
                earned_badges.append({
                    'id': badge_id,
                    'name': badge_info['name'],
                    'description': badge_info['description'],
                    'icon': badge_info['icon'],
                    'earned_at': get_current_utc_time()  # Would be actual earn date in production
                })
        
        # Calculate user level
        total_points = user_stats.get('points', 0)
        current_level = calculate_user_level(total_points)
        
        # Calculate points needed for next level
        level_thresholds = [0, 100, 300, 600, 1000, 1500]
        if current_level < len(level_thresholds):
            points_for_next = level_thresholds[current_level] - total_points
        else:
            points_for_next = ((current_level - 4) * 500 + 1500) - total_points
        
        response_data = {
            'earned_badges': earned_badges,
            'new_badges': new_badges,
            'total_badges': len(earned_badges),
            'available_badges': len(available_badges),
            'user_level': {
                'current_level': current_level,
                'total_points': total_points,
                'points_for_next_level': max(0, points_for_next)
            },
            'stats': {
                'streak_days': user_stats.get('streak_days', 0),
                'completed_tasks': user_stats.get('completed_tasks', 0),
                'total_journal_entries': len(journal_entries),
                'total_mood_logs': len(mood_logs)
            }
        }
        
        logger.info(f"Retrieved badges for user {uid}: {len(earned_badges)} earned, {len(new_badges)} new")
        return jsonify(format_response(response_data))
        
    except Exception as e:
        logger.error(f"Get user badges error: {e}")
        return jsonify(format_response(None, False, "Failed to get user badges")), 500

@gamification_bp.route('/leaderboard', methods=['GET'])
@require_auth
@handle_errors
def get_leaderboard():
    """Get wellness leaderboard (anonymized)"""
    try:
        # Note: In a production app, you'd want to implement proper privacy controls
        # This is a simplified version for demonstration
        
        uid = g.current_user['uid']
        
        # For privacy, we'll create a mock leaderboard
        # In production, you'd aggregate anonymized stats from BigQuery
        
        # Get current user's stats for context
        user_stats = firestore_service.get_user_stats(uid)
        user_points = user_stats.get('points', 0)
        user_level = calculate_user_level(user_points)
        
        # Generate anonymized leaderboard (mock data for demo)
        leaderboard = [
            {'rank': 1, 'username': 'WellnessWarrior', 'points': 2500, 'level': 8},
            {'rank': 2, 'username': 'MindfulMover', 'points': 2200, 'level': 7},
            {'rank': 3, 'username': 'ZenMaster', 'points': 1950, 'level': 7},
            {'rank': 4, 'username': 'PositiveVibes', 'points': 1800, 'level': 6},
            {'rank': 5, 'username': 'GrowthSeeker', 'points': 1650, 'level': 6}
        ]
        
        # Find user's approximate rank
        user_rank = len([entry for entry in leaderboard if entry['points'] > user_points]) + 1
        
        # Add current user to leaderboard if they have points
        if user_points > 0:
            current_user_entry = {
                'rank': user_rank,
                'username': 'You',
                'points': user_points,
                'level': user_level,
                'is_current_user': True
            }
            
            # Insert user in appropriate position
            if user_rank <= len(leaderboard):
                leaderboard.insert(user_rank - 1, current_user_entry)
            else:
                leaderboard.append(current_user_entry)
        
        response_data = {
            'leaderboard': leaderboard[:10],  # Top 10
            'user_rank': user_rank,
            'user_stats': {
                'points': user_points,
                'level': user_level,
                'badges': len(user_stats.get('badges', []))
            },
            'weekly_challenge': {
                'name': 'Mindful Moments',
                'description': 'Complete 5 mindfulness tasks this week',
                'progress': min(user_stats.get('completed_tasks', 0) % 7, 5),
                'target': 5,
                'reward_points': 100
            }
        }
        
        return jsonify(format_response(response_data))
        
    except Exception as e:
        logger.error(f"Get leaderboard error: {e}")
        return jsonify(format_response(None, False, "Failed to get leaderboard")), 500

@gamification_bp.route('/stats', methods=['GET'])
@require_auth
@handle_errors
def get_user_stats():
    """Get comprehensive user statistics"""
    try:
        uid = g.current_user['uid']
        
        # Get user stats
        user_stats = firestore_service.get_user_stats(uid)
        
        # Get activity data
        start_date, end_date = get_date_range(30)  # Last 30 days
        mood_logs = firestore_service.get_mood_logs(uid, start_date, end_date)
        journal_entries = firestore_service.get_journal_entries(uid, 30)
        
        # Calculate additional metrics
        total_points = user_stats.get('points', 0)
        current_level = calculate_user_level(total_points)
        
        # Activity frequency
        activity_frequency = {
            'daily_avg_mood_logs': len(mood_logs) / 30 if mood_logs else 0,
            'daily_avg_journal_entries': len([e for e in journal_entries if e.get('timestamp') >= start_date]) / 30,
            'weekly_active_days': len(set(
                log['timestamp'].date() for log in mood_logs if log.get('timestamp')
            )) if mood_logs else 0
        }
        
        # Personal bests
        personal_bests = {
            'longest_streak': user_stats.get('longest_streak', user_stats.get('streak_days', 0)),
            'most_tasks_per_day': max([
                len(plan.get('tasks', [])) for plan in [
                    firestore_service.get_daily_plan(uid, 
                        (datetime.now(timezone.utc).date() - timedelta(days=i)).isoformat()
                    ) for i in range(7)
                ] if plan
            ], default=0),
            'highest_energy_level': max([log.get('energy', 0) for log in mood_logs], default=0),
            'lowest_stress_level': min([log.get('stress', 10) for log in mood_logs], default=10)
        }
        
        # Weekly progress
        week_start = datetime.now(timezone.utc) - timedelta(days=datetime.now(timezone.utc).weekday())
        weekly_mood_logs = [
            log for log in mood_logs 
            if log.get('timestamp') and log['timestamp'] >= week_start
        ]
        
        weekly_progress = {
            'mood_logs_this_week': len(weekly_mood_logs),
            'points_this_week': sum([
                5 for log in weekly_mood_logs  # 5 points per mood log
            ]) + len([
                entry for entry in journal_entries
                if entry.get('timestamp') and entry['timestamp'] >= week_start
            ]) * 10,  # 10 points per journal entry
            'streak_this_week': min(user_stats.get('streak_days', 0), 7)
        }
        
        response_data = {
            'overview': {
                'total_points': total_points,
                'current_level': current_level,
                'current_streak': user_stats.get('streak_days', 0),
                'total_badges': len(user_stats.get('badges', [])),
                'member_since': user_stats.get('created_at', get_current_utc_time()).isoformat()
            },
            'activity_stats': {
                'total_mood_logs': len(mood_logs),
                'total_journal_entries': len(journal_entries),
                'total_completed_tasks': user_stats.get('completed_tasks', 0),
                'activity_frequency': activity_frequency
            },
            'personal_bests': personal_bests,
            'weekly_progress': weekly_progress,
            'achievements': {
                'badges_earned': len(user_stats.get('badges', [])),
                'points_from_badges': sum([
                    get_available_badges().get(badge_id, {}).get('points', 0)
                    for badge_id in user_stats.get('badges', [])
                ]),
                'completion_rate': round(
                    (user_stats.get('completed_tasks', 0) / max(user_stats.get('total_tasks_assigned', 1), 1)) * 100, 
                    1
                ) if user_stats.get('total_tasks_assigned') else 0
            }
        }
        
        return jsonify(format_response(response_data))
        
    except Exception as e:
        logger.error(f"Get user stats error: {e}")
        return jsonify(format_response(None, False, "Failed to get user stats")), 500
