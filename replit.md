# Overview

Glowra is an AI-powered mental wellness companion platform specifically designed for young people. The backend provides comprehensive APIs for mood tracking, AI-powered journaling, personalized daily planning, gamification, meditation resources, and analytics. The system leverages Google Cloud services and Vertex AI (Gemini) to deliver intelligent insights and personalized mental health support while maintaining user privacy and safety.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Framework and Structure
- **Framework**: Flask-based REST API with Blueprint architecture for modular route organization
- **Entry Point**: `main.py` serving on port 5000 with CORS enabled for frontend communication
- **Route Organization**: Separate blueprints for auth, journal, planner, progress, gamification, chat, and meditations

## Authentication System
- **Primary Auth**: Firebase Authentication with Google Sign-In provider
- **Token Verification**: Firebase Admin SDK for ID token validation
- **Development Mode**: Bypass mechanism using `X-Dev-User-Id` header for local development
- **Authorization**: Decorator-based authentication (`@require_auth`) for API endpoint protection

## Data Storage Strategy
- **Primary Database**: Google Firestore for flexible document storage of user profiles, mood logs, journal entries, and gamification data
- **Analytics Storage**: Google BigQuery for data analytics and insights with separate tables for mood logs and journal insights
- **File Storage**: Google Cloud Storage for meditation audio files with signed URL generation for secure access

## AI Integration Architecture
- **AI Provider**: Google Vertex AI with Gemini 2.5 Pro model for natural language processing
- **Journal Analysis**: Structured response generation using Pydantic schemas for mood detection, categorization, and recommendations
- **Chat System**: Conversational AI with mood detection and supportive responses
- **Retry Logic**: Tenacity-based retry mechanism for AI service reliability

## Gamification System
- **Points System**: Activity-based point accumulation with level calculation algorithms
- **Badges**: Achievement system with predefined criteria for user engagement
- **Streaks**: Consecutive activity day tracking for motivation
- **Progress Tracking**: Weekly and monthly analytics with mood pattern analysis

## Data Validation and Error Handling
- **Input Validation**: Pydantic models for request/response schema validation
- **Error Handling**: Centralized error handling decorators with logging
- **Response Format**: Standardized JSON response structure with success/error states

## Development Features
- **Environment Configuration**: Environment-based configuration with .env support
- **Logging**: Comprehensive logging throughout the application
- **CORS**: Cross-origin resource sharing for frontend integration
- **Development Tools**: Debug mode and development user bypass for testing

# External Dependencies

## Google Cloud Platform Services
- **Firestore**: Document database for primary data storage
- **BigQuery**: Analytics and data warehousing service
- **Cloud Storage**: File storage for meditation audio resources
- **Vertex AI**: Machine learning platform for Gemini AI integration
- **Firebase Admin SDK**: Server-side authentication and user management

## AI and Machine Learning
- **Gemini API**: Google's generative AI for journal analysis and conversational responses
- **Vertex AI Client**: Integration with Google's AI platform for model access

## Development and Utilities
- **Flask**: Web framework with CORS support
- **Pydantic**: Data validation and serialization
- **python-dotenv**: Environment variable management
- **Tenacity**: Retry logic for external service calls

## Frontend Dependencies
- **Firebase JavaScript SDK**: Client-side authentication
- **Bootstrap 5**: UI framework with dark theme support
- **Chart.js**: Data visualization for progress tracking
- **Feather Icons**: Icon library for user interface

## Configuration Requirements
- Firebase project configuration (API keys, project ID, app ID)
- Google Cloud project with enabled APIs (Firestore, BigQuery, Storage, Vertex AI)
- Gemini API key for AI functionality
- Environment-specific configuration for development vs production