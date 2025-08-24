import json
import logging
import os
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import List, Literal
from tenacity import retry, stop_after_attempt, wait_exponential
from config import Config

logger = logging.getLogger(__name__)

# Initialize Gemini client
client = genai.Client(api_key=Config.GEMINI_API_KEY)

class JournalInsight(BaseModel):
    mood: Literal["happy", "sad", "stressed", "anxious", "neutral"]
    categories: List[str] = Field(description="List of relevant categories like exam_anxiety, procrastination, sleep, loneliness, burnout")
    confidence: float = Field(ge=0, le=1, description="Confidence score between 0 and 1")
    recommendations: List[dict] = Field(description="List of recommendation objects with type, title, duration_min, and resource_url")
    risk: Literal["low", "moderate", "high"]
    message: str = Field(description="Kind, validating reflection in 1-2 sentences")

class ChatResponse(BaseModel):
    response: str = Field(description="Supportive and empathetic response to user's message")
    mood_detected: str = Field(description="Detected mood from the conversation")
    suggestions: List[str] = Field(description="Helpful suggestions or coping strategies")

class AIService:
    def __init__(self):
        self.model_name = "gemini-2.5-pro"
        logger.info("AI Service initialized with Gemini")
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def analyze_journal(self, text: str) -> dict:
        """Analyze journal text and return structured insights"""
        try:
            system_prompt = """
            You are a compassionate mental health AI assistant for young people. 
            Analyze the journal entry and provide insights in the exact JSON format requested.
            
            For recommendations, suggest practical activities like:
            - breathing exercises (5-10 minutes)
            - light physical activity (10-30 minutes)
            - journaling prompts
            - mindfulness exercises
            - study techniques
            - social connection activities
            
            Always provide supportive, non-diagnostic language. If you detect high risk (thoughts of self-harm, 
            severe depression symptoms), set risk to "high" and include encouraging message about seeking support.
            
            Respond ONLY with valid JSON matching the schema.
            """
            
            response = client.models.generate_content(
                model=self.model_name,
                contents=[
                    types.Content(role="user", parts=[types.Part(text=f"Analyze this journal entry: {text}")])
                ],
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    response_mime_type="application/json",
                    response_schema=JournalInsight,
                ),
            )
            
            if response.text:
                result = json.loads(response.text)
                
                # Add escalation advice for high risk cases
                if result.get("risk") == "high":
                    result["escalation_advice"] = (
                        "Please consider reaching out to a trusted adult, counselor, or mental health helpline. "
                        "You don't have to go through this alone - support is available."
                    )
                
                logger.info("Journal analysis completed successfully")
                return result
            else:
                raise ValueError("Empty response from AI model")
                
        except Exception as e:
            logger.error(f"Journal analysis failed: {e}")
            # Return safe fallback response
            return {
                "mood": "neutral",
                "categories": ["general"],
                "confidence": 0.5,
                "recommendations": [
                    {
                        "type": "breathing",
                        "title": "5-minute deep breathing",
                        "duration_min": 5,
                        "resource_url": ""
                    }
                ],
                "risk": "low",
                "message": "Thank you for sharing your thoughts. Remember that every feeling is valid."
            }
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def chat_response(self, message: str, conversation_history: List[dict] = None) -> dict:
        """Generate contextual chat response for mental wellness guidance"""
        try:
            # Build conversation context
            context = ""
            if conversation_history:
                for turn in conversation_history[-5:]:  # Last 5 turns for context
                    context += f"User: {turn.get('user', '')}\nAssistant: {turn.get('assistant', '')}\n"
            
            system_prompt = """
            You are Glowra, a compassionate AI companion for young people's mental wellness.
            
            Guidelines:
            - Be warm, empathetic, and supportive
            - Use age-appropriate language for teens/young adults
            - Provide practical coping strategies and encouragement
            - Never provide medical diagnosis or replace professional help
            - If someone mentions self-harm or severe distress, gently encourage seeking help
            - Focus on strengths, resilience, and growth mindset
            - Validate emotions while offering hope and practical next steps
            
            Respond with helpful suggestions and maintain a caring, non-judgmental tone.
            """
            
            prompt = f"""
            Previous conversation:
            {context}
            
            Current message: {message}
            
            Provide a supportive response that acknowledges their feelings and offers helpful guidance.
            """
            
            response = client.models.generate_content(
                model=self.model_name,
                contents=[
                    types.Content(role="user", parts=[types.Part(text=prompt)])
                ],
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    response_mime_type="application/json",
                    response_schema=ChatResponse,
                ),
            )
            
            if response.text:
                result = json.loads(response.text)
                logger.info("Chat response generated successfully")
                return result
            else:
                raise ValueError("Empty response from AI model")
                
        except Exception as e:
            logger.error(f"Chat response generation failed: {e}")
            # Return safe fallback response
            return {
                "response": "I'm here to listen and support you. Sometimes talking through our feelings can really help. What's on your mind today?",
                "mood_detected": "neutral",
                "suggestions": [
                    "Take a few deep breaths",
                    "Consider journaling about your feelings",
                    "Reach out to someone you trust"
                ]
            }
    
    def generate_daily_recommendations(self, user_data: dict) -> List[dict]:
        """Generate personalized daily recommendations based on user's recent data"""
        try:
            # Analyze recent mood patterns and journal insights
            mood_trends = user_data.get("recent_moods", [])
            journal_insights = user_data.get("recent_insights", [])
            user_preferences = user_data.get("preferences", {})
            
            prompt = f"""
            Based on this user's recent mental wellness data, suggest 3-5 personalized daily activities:
            
            Recent moods: {mood_trends}
            Recent journal insights: {journal_insights}
            User preferences: {user_preferences}
            
            Suggest a mix of:
            - Mindfulness/breathing exercises (5-15 min)
            - Physical activity (10-30 min)
            - Creative/journaling activities (10-20 min)
            - Social connection activities
            - Study/productivity techniques
            
            Format as JSON array with objects containing: type, title, estimated_minutes, description, cta_type
            """
            
            response = client.models.generate_content(
                model="gemini-2.5-flash",  # Use faster model for recommendations
                contents=prompt
            )
            
            if response.text:
                # Parse and validate recommendations
                recommendations = json.loads(response.text)
                logger.info("Daily recommendations generated successfully")
                return recommendations
            else:
                # Return default recommendations
                return self._get_default_recommendations()
                
        except Exception as e:
            logger.error(f"Failed to generate daily recommendations: {e}")
            return self._get_default_recommendations()
    
    def _get_default_recommendations(self) -> List[dict]:
        """Return default daily recommendations as fallback"""
        return [
            {
                "type": "breathing",
                "title": "Morning mindfulness",
                "estimated_minutes": 5,
                "description": "Start your day with 5 minutes of deep breathing",
                "cta_type": "timer"
            },
            {
                "type": "journaling",
                "title": "Gratitude reflection",
                "estimated_minutes": 10,
                "description": "Write down three things you're grateful for today",
                "cta_type": "prompt"
            },
            {
                "type": "movement",
                "title": "Energizing walk",
                "estimated_minutes": 15,
                "description": "Take a short walk outside or around your space",
                "cta_type": "activity"
            }
        ]

ai_service = AIService()
