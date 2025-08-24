from pydantic import BaseModel, Field, validator
from typing import List, Optional, Literal
from datetime import datetime

class MoodLogIn(BaseModel):
    mood: Literal["happy", "sad", "stressed", "anxious", "neutral"]
    energy: int = Field(ge=0, le=10, description="Energy level from 0 to 10")
    stress: int = Field(ge=0, le=10, description="Stress level from 0 to 10")
    note: Optional[str] = Field(None, max_length=500)

class MoodLogOut(BaseModel):
    id: str
    mood: str
    energy: int
    stress: int
    note: Optional[str]
    timestamp: datetime
    user_id: str

class JournalIn(BaseModel):
    text: str = Field(min_length=10, max_length=2000, description="Journal entry text")

class RecommendationOut(BaseModel):
    type: str
    title: str
    duration_min: int
    resource_url: Optional[str]

class InsightOut(BaseModel):
    mood: str
    categories: List[str]
    confidence: float
    recommendations: List[RecommendationOut]
    risk: str
    message: str
    escalation_advice: Optional[str] = None

class TaskOut(BaseModel):
    id: str
    title: str
    cta_type: str
    estimated_minutes: int
    status: Literal["pending", "completed", "skipped"] = "pending"
    description: Optional[str] = None

class DailyPlanOut(BaseModel):
    date: str
    tasks: List[TaskOut]
    generated_at: datetime

class ProgressWeeklyOut(BaseModel):
    average_mood: float
    average_energy: float
    average_stress: float
    streak_days: int
    completed_tasks: int
    total_journal_entries: int
    mood_trend: str

class BadgeOut(BaseModel):
    id: str
    name: str
    description: str
    earned_at: datetime
    icon: str

class BadgesOut(BaseModel):
    badges: List[BadgeOut]
    total_points: int
    current_level: int

class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    conversation_id: Optional[str] = None

class ChatOut(BaseModel):
    response: str
    mood_detected: str
    suggestions: List[str]
    conversation_id: str

class MeditationFile(BaseModel):
    name: str
    path: str
    size: int
    duration: Optional[str] = None
    category: Optional[str] = None
    url: str

class UserProfile(BaseModel):
    uid: str
    email: str
    name: str
    created_at: datetime
    preferences: Optional[dict] = {}
    onboarding_completed: bool = False

class UserStatsOut(BaseModel):
    points: int
    streak_days: int
    completed_tasks: int
    level: int
    badges_count: int
    journal_entries: int
    mood_logs: int
