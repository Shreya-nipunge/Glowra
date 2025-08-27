from dotenv import load_dotenv
load_dotenv()


import os
import logging
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from datetime import datetime

logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///glowra.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# initialize the app with the extension
db.init_app(app)

with app.app_context():
    import models
    db.create_all()

@app.route("/")
def index():
    return render_template(
        "index.html",
        firebase_api_key=os.environ.get("FIREBASE_API_KEY", ""),
        firebase_project_id=os.environ.get("FIREBASE_PROJECT_ID", ""),
        firebase_app_id=os.environ.get("FIREBASE_APP_ID", ""),
    )

@app.route("/login")
def login():
    return render_template(
        "login.html",
        firebase_api_key=os.environ.get("FIREBASE_API_KEY", ""),
        firebase_project_id=os.environ.get("FIREBASE_PROJECT_ID", ""),
        firebase_app_id=os.environ.get("FIREBASE_APP_ID", ""),
    )

@app.route("/dashboard")
def dashboard():
    return render_template(
        "dashboard.html",
        firebase_api_key=os.environ.get("FIREBASE_API_KEY", ""),
        firebase_project_id=os.environ.get("FIREBASE_PROJECT_ID", ""),
        firebase_app_id=os.environ.get("FIREBASE_APP_ID", ""),
    )

# API Routes
@app.route("/api/mood", methods=["GET", "POST"])
def mood_api():
    if request.method == "POST":
        data = request.get_json()
        # Store mood data
        return jsonify({"status": "success", "message": "Mood recorded"})
    else:
        # Return mood history
        return jsonify({"moods": []})

@app.route("/api/journal", methods=["GET", "POST"])
def journal_api():
    if request.method == "POST":
        data = request.get_json()
        # Store journal entry and return AI insights
        return jsonify({
            "status": "success", 
            "insights": "Your entry shows positive emotional growth and self-awareness."
        })
    else:
        # Return journal entries
        return jsonify({"entries": []})

@app.route("/api/tasks", methods=["GET", "POST", "PUT"])
def tasks_api():
    if request.method == "POST":
        data = request.get_json()
        # Create new task
        return jsonify({"status": "success", "task_id": 1})
    elif request.method == "PUT":
        data = request.get_json()
        # Update task completion
        return jsonify({"status": "success", "points_earned": 10})
    else:
        # Return daily tasks
        return jsonify({"tasks": [], "streak": 0, "points": 0})

@app.route("/api/meditation")
def meditation_api():
    # Return meditation resources
    return jsonify({"meditations": []})

@app.route("/api/analytics")
def analytics_api():
    # Return analytics data
    return jsonify({
        "mood_trends": [],
        "streaks": [],
        "achievements": []
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
