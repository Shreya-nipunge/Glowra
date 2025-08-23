# Glowra - Youth Mental Wellness Backend

Glowra is an AI-powered mental wellness companion platform designed specifically for young people. This Flask-based backend provides comprehensive APIs for mood tracking, AI-powered journaling, personalized wellness plans, gamification, and meditation resources.

## 🌟 Features

### Core Functionality
- **Firebase Authentication** - Secure user authentication with Google Sign-In
- **AI-Powered Journaling** - Gemini AI analyzes journal entries and provides insights
- **Mood Tracking** - Log and analyze mood patterns over time
- **Smart Chatbot** - Conversational AI companion for mental wellness support
- **Personalized Daily Plans** - AI-generated wellness activities based on user data
- **Gamification System** - Points, badges, streaks, and achievements
- **Meditation Library** - Curated meditation resources with progress tracking
- **Analytics Dashboard** - Comprehensive progress tracking and insights

### Technology Stack
- **Backend**: Flask with Python 3.11+
- **Database**: Google Firestore for flexible data storage
- **AI/ML**: Google Vertex AI with Gemini models
- **Analytics**: Google BigQuery for data analytics
- **Storage**: Google Cloud Storage for meditation files
- **Authentication**: Firebase Auth with Google provider
- **Frontend**: Bootstrap 5 with vanilla JavaScript

## 🚀 Quick Start

### Prerequisites
- Python 3.11 or higher
- Google Cloud Project with required APIs enabled
- Firebase project with authentication configured
- Gemini API key

### Required Google Cloud APIs
Enable these APIs in your Google Cloud Console:
- Cloud Firestore API
- BigQuery API
- Cloud Storage API
- Vertex AI API
- Firebase Authentication API

### Environment Setup

1. **Clone and install dependencies**:
   ```bash
   pip install -r requirements.txt
   