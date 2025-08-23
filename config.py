import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask Configuration
    SECRET_KEY = os.environ.get('SESSION_SECRET', 'dev-secret-key')
    FLASK_ENV = os.environ.get('FLASK_ENV', 'development')
    
    # Firebase Configuration
    FIREBASE_PROJECT_ID = os.environ.get('FIREBASE_PROJECT_ID')
    FIREBASE_API_KEY = os.environ.get('FIREBASE_API_KEY')
    FIREBASE_APP_ID = os.environ.get('FIREBASE_APP_ID')
    GOOGLE_APPLICATION_CREDENTIALS = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
    
    # Google Cloud Configuration
    GCP_PROJECT = os.environ.get('GCP_PROJECT')
    GCP_LOCATION = os.environ.get('GCP_LOCATION', 'us-central1')
    
    # AI Configuration
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    
    # BigQuery Configuration
    BQ_DATASET = os.environ.get('BQ_DATASET', 'glowra_analytics')
    BQ_MOOD_TABLE = os.environ.get('BQ_MOOD_TABLE', 'mood_logs')
    BQ_JOURNAL_TABLE = os.environ.get('BQ_JOURNAL_TABLE', 'journal_insights')
    
    # Cloud Storage Configuration
    GCS_BUCKET = os.environ.get('GCS_BUCKET', 'glowra-assets')
    
    # Development Configuration
    DEV_MODE = os.environ.get('DEV_MODE', 'false').lower() == 'true'
    FRONTEND_ORIGIN = os.environ.get('FRONTEND_ORIGIN', 'http://localhost:5000')
