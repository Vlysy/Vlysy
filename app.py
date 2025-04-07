import os
import sys
import logging
import io
import tempfile
import json
import traceback
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
from werkzeug.utils import secure_filename
from werkzeug.middleware.proxy_fix import ProxyFix
from resume_parser import parse_resume_file, parse_resume_text
from ai_analyzer import analyze_resume, generate_anschreiben, score_resume
from models import db, Resume, ResumeScore, ResumeCorrection, CoverLetter, Testimonial

# Configure logging
logging.basicConfig(
    level=logging.DEBUG, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default-secret-key")
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
db.init_app(app)

# Setup ProxyFix (needed for url_for to generate with https)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Store session data in files instead of cookies to handle larger data
try:
    from flask_session import Session
    app.config['SESSION_TYPE'] = 'filesystem'
    temp_dir = os.path.join(tempfile.gettempdir(), 'flask_sessions')
    app.config['SESSION_FILE_DIR'] = temp_dir
    
    # Ensure session directory exists and is writable
    os.makedirs(temp_dir, exist_ok=True)
    if not os.access(temp_dir, os.W_OK):
        logging.warning(f"Session directory {temp_dir} is not writable, using default")
        app.config['SESSION_TYPE'] = 'null'
    
    Session(app)
    logging.info(f"Flask-Session initialized with directory: {temp_dir}")
except Exception as e:
    logging.error(f"Error initializing Flask-Session: {str(e)}")
    logging.error(traceback.format_exc())
    # Continue with cookie sessions as fallback
    pass

# Configure upload settings
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt'}
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
TEMP_FOLDER = UPLOAD_FOLDER

# Ensure upload folder exists
try:
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    logging.info(f"Upload folder created at {UPLOAD_FOLDER}")
except Exception as e:
    logging.warning(f"Failed to create upload folder: {str(e)}")
    # Use temp directory as fallback
    UPLOAD_FOLDER = tempfile.gettempdir()
    TEMP_FOLDER = UPLOAD_FOLDER
    logging.info(f"Using temporary directory instead: {TEMP_FOLDER}")

# Create database tables
with app.app_context():
    db.create_all()
    logging.info("Database tables created")

# Import routes (must be after app creation to avoid circular imports)
from routes import *

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)