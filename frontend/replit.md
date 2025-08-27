# Glowra - Mental Wellness Platform

## Overview

Glowra is a comprehensive mental wellness platform designed to help users track their mental health through mood monitoring, journaling, task management, and meditation. The application provides a holistic approach to mental wellness with AI-powered insights and gamification elements to encourage consistent engagement.

The platform features a modern web interface built with Flask and Bootstrap, offering users tools for daily mood tracking, reflective journaling with AI analysis, task management with point-based rewards, meditation library, and analytics dashboard for progress visualization.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
The frontend uses a traditional server-side rendered approach with Flask templates enhanced by client-side JavaScript modules. The UI is built with Bootstrap 5 for responsive design and Font Awesome for icons. The architecture follows a modular JavaScript pattern with separate classes for different features:

- **Dashboard.js**: Main navigation and section management
- **MoodTracker.js**: Mood slider interface and mood entry management
- **JournalManager.js**: Journal entry creation and AI insights display
- **MeditationLibrary.js**: Audio meditation player and library management
- **AnalyticsManager.js**: Chart.js integration for data visualization
- **AuthManager.js**: Authentication state management and token handling

### Backend Architecture
The backend uses Flask with SQLAlchemy ORM following a simple MVC pattern. The application is structured with:

- **app.py**: Main Flask application configuration and route definitions
- **models.py**: SQLAlchemy database models for users, mood entries, journal entries, and tasks
- **main.py**: Application entry point

The backend supports both SQLite (for development) and PostgreSQL (for production) through environment-based configuration. Database operations are handled through SQLAlchemy with automatic table creation on startup.

### Authentication System
Authentication is implemented using Firebase Auth for user management, providing:
- Google OAuth integration for seamless sign-in
- JWT token-based API authentication
- User session management with localStorage backup
- Secure user identification through Firebase UIDs

### Data Storage
The application uses a relational database design with four main entities:
- **User**: Stores Firebase UID, email, name, and creation timestamp
- **MoodEntry**: Tracks daily mood ratings (1-10 scale) with optional notes
- **JournalEntry**: Stores journal content with AI-generated insights
- **Task**: Manages user tasks with completion status and point values

The database schema supports user relationships through foreign keys and includes timestamp tracking for all entries.

### API Design
The application follows a RESTful API pattern with endpoints for:
- Mood tracking and analytics
- Journal entry management
- Task CRUD operations
- Meditation library access
- User analytics and progress data

API responses use JSON format with consistent error handling and authentication middleware.

## External Dependencies

### Authentication Services
- **Firebase Authentication**: Provides OAuth integration, user management, and JWT token generation
- **Google OAuth**: Primary authentication method for user sign-in

### Frontend Libraries
- **Bootstrap 5.3.0**: CSS framework for responsive UI components
- **Font Awesome 6.4.0**: Icon library for UI elements
- **Chart.js**: JavaScript charting library for analytics visualization

### Backend Dependencies
- **Flask**: Python web framework for server-side logic
- **SQLAlchemy**: ORM for database operations and model definitions
- **Werkzeug**: WSGI utilities and proxy fix middleware

### Database Systems
- **SQLite**: Default database for development and local testing
- **PostgreSQL**: Production database (configurable via DATABASE_URL environment variable)

### Development Environment
- **Python**: Backend runtime environment
- **HTML5/CSS3/JavaScript**: Frontend technologies
- **Environment Variables**: Configuration for Firebase credentials, database URLs, and session secrets

The application is designed to be deployment-ready with environment-based configuration and supports both development and production environments through conditional database selection and credential management.