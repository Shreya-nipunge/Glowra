from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any
import hashlib
import logging

logger = logging.getLogger(__name__)

def get_current_utc_time():
    """Get current UTC timestamp"""
    return datetime.now(timezone.utc)

def parse_iso_date(date_string: str) -> datetime:
    """Parse ISO date string to datetime object"""
    try:
        return datetime.fromisoformat(date_string.replace('Z', '+00:00'))
    except ValueError:
        # Fallback parsing
        return datetime.strptime(date_string, '%Y-%m-%d')

def get_date_range(days_back: int = 7):
    """Get date range for the last N days"""
    end_date = get_current_utc_time()
    start_date = end_date - timedelta(days=days_back)
    return start_date, end_date

def hash_user_id(user_id: str) -> str:
    """Hash user ID for privacy in analytics"""
    return hashlib.sha256(user_id.encode()).hexdigest()[:16]

def calculate_streak(activity_dates: List[datetime]) -> int:
    """Calculate current streak from list of activity dates"""
    if not activity_dates:
        return 0
    
    # Sort dates in descending order
    sorted_dates = sorted(activity_dates, reverse=True)
    
    # Start from today and count consecutive days
    current_date = get_current_utc_time().date()
    streak = 0
    
    for activity_date in sorted_dates:
        activity_day = activity_date.date()
        
        # Check if this activity was on the expected date
        expected_date = current_date - timedelta(days=streak)
        
        if activity_day == expected_date:
            streak += 1
        elif activity_day < expected_date:
            # Gap in activities, streak broken
            break
    
    return streak

def calculate_mood_average(mood_logs: List[Dict[str, Any]]) -> Dict[str, float]:
    """Calculate average mood metrics from mood logs"""
    if not mood_logs:
        return {"mood_score": 0, "energy": 0, "stress": 0}
    
    # Convert mood to numeric scores
    mood_scores = {
        "happy": 5,
        "neutral": 3,
        "sad": 2,
        "stressed": 2,
        "anxious": 1
    }
    
    total_mood = 0
    total_energy = 0
    total_stress = 0
    count = len(mood_logs)
    
    for log in mood_logs:
        mood = log.get("mood", "neutral")
        total_mood += mood_scores.get(mood, 3)
        total_energy += log.get("energy", 0)
        total_stress += log.get("stress", 0)
    
    return {
        "mood_score": round(total_mood / count, 2),
        "energy": round(total_energy / count, 2),
        "stress": round(total_stress / count, 2)
    }

def get_wellness_insights(mood_logs: List[Dict[str, Any]], journal_entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate wellness insights from user data"""
    insights = {
        "total_entries": len(mood_logs) + len(journal_entries),
        "recent_mood_trend": "stable",
        "key_challenges": [],
        "positive_patterns": []
    }
    
    if mood_logs:
        # Analyze mood trend
        recent_moods = mood_logs[:7]  # Last 7 entries
        if len(recent_moods) >= 3:
            mood_scores = []
            for log in recent_moods:
                mood = log.get("mood", "neutral")
                if mood == "happy":
                    mood_scores.append(5)
                elif mood == "neutral":
                    mood_scores.append(3)
                else:
                    mood_scores.append(2)
            
            avg_recent = sum(mood_scores[:3]) / 3
            avg_older = sum(mood_scores[3:]) / max(1, len(mood_scores[3:]))
            
            if avg_recent > avg_older + 0.5:
                insights["recent_mood_trend"] = "improving"
            elif avg_recent < avg_older - 0.5:
                insights["recent_mood_trend"] = "declining"
    
    if journal_entries:
        # Analyze journal insights for patterns
        categories = []
        for entry in journal_entries[:10]:  # Last 10 entries
            ai_insight = entry.get("ai_insight", {})
            categories.extend(ai_insight.get("categories", []))
        
        # Count category frequency
        category_counts = {}
        for category in categories:
            category_counts[category] = category_counts.get(category, 0) + 1
        
        # Identify top challenges
        top_challenges = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        insights["key_challenges"] = [challenge[0] for challenge in top_challenges]
    
    return insights

def format_response(data: Any, success: bool = True, message: str = None) -> Dict[str, Any]:
    """Format consistent API response structure"""
    response = {
        "success": success,
        "data": data
    }
    
    if message:
        response["message"] = message
    
    return response
