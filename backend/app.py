import os
import logging
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from config import Config

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
    
    # Enable CORS
    CORS(app, origins=[Config.FRONTEND_ORIGIN])
    
    # Register Blueprints
    from routes.auth import auth_bp
    from routes.journal import journal_bp
    from routes.planner import planner_bp
    from routes.progress import progress_bp
    from routes.gamification import gamification_bp
    from routes.chat import chat_bp
    from routes.meditations import meditations_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(journal_bp, url_prefix='/api/journal')
    app.register_blueprint(planner_bp, url_prefix='/api/planner')
    app.register_blueprint(progress_bp, url_prefix='/api/progress')
    app.register_blueprint(gamification_bp, url_prefix='/api/gamification')
    app.register_blueprint(chat_bp, url_prefix='/api/chat')
    app.register_blueprint(meditations_bp, url_prefix='/api/meditations')
    
    @app.route('/')
    def index():
        return render_template('index.html',
                             firebase_api_key=Config.FIREBASE_API_KEY,
                             firebase_project_id=Config.FIREBASE_PROJECT_ID,
                             firebase_app_id=Config.FIREBASE_APP_ID)
    
    @app.route('/dashboard')
    def dashboard():
        return render_template('dashboard.html',
                             firebase_api_key=Config.FIREBASE_API_KEY,
                             firebase_project_id=Config.FIREBASE_PROJECT_ID,
                             firebase_app_id=Config.FIREBASE_APP_ID)
    
    @app.route('/health')
    def health():
        return jsonify({
            "status": "ok",
            "service": "glowra-backend",
            "environment": Config.FLASK_ENV
        })
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Not found"}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {error}")
        return jsonify({"error": "Internal server error"}), 500
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
