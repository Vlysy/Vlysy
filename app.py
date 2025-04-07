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
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from flask_sqlalchemy import SQLAlchemy

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
# Use a SQLite database as fallback if DATABASE_URL is not set
database_url = os.environ.get("DATABASE_URL")
if not database_url:
    # Log warning about missing database URL
    logging.warning("DATABASE_URL not set. Using SQLite database as fallback.")
    # Use SQLite as fallback (will be in-memory if path is not writable)
    try:
        db_path = os.path.join(os.getcwd(), 'resume_analyzer.db')
        database_url = f'sqlite:///{db_path}'
    except:
        database_url = 'sqlite:///:memory:'
        
app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize SQLAlchemy
db = SQLAlchemy(app)

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

# Database models
class Resume(db.Model):
    """Model for storing user resumes"""
    __tablename__ = 'resumes'
    
    id = Column(Integer, primary_key=True)
    text = Column(Text, nullable=False)
    language = Column(String(10), default='en')
    file_name = Column(String(255), nullable=True)
    file_type = Column(String(10), nullable=True)  # pdf, docx, txt
    created_at = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    scores = relationship("ResumeScore", back_populates="resume", cascade="all, delete-orphan")
    corrections = relationship("ResumeCorrection", back_populates="resume", cascade="all, delete-orphan")
    cover_letters = relationship("CoverLetter", back_populates="resume", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Resume {self.id}: {self.file_name or 'Text input'}>"


class ResumeScore(db.Model):
    """Model for storing resume scores"""
    __tablename__ = 'resume_scores'
    
    id = Column(Integer, primary_key=True)
    resume_id = Column(Integer, ForeignKey('resumes.id'), nullable=False)
    
    overall_score = Column(Float, nullable=False)
    content_score = Column(Float, nullable=True)
    format_score = Column(Float, nullable=True)
    language_score = Column(Float, nullable=True)
    conciseness_score = Column(Float, nullable=True)
    summary = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    resume = relationship("Resume", back_populates="scores")
    
    def __repr__(self):
        return f"<ResumeScore {self.id}: {self.overall_score}>"


class ResumeCorrection(db.Model):
    """Model for storing resume corrections"""
    __tablename__ = 'resume_corrections'
    
    id = Column(Integer, primary_key=True)
    resume_id = Column(Integer, ForeignKey('resumes.id'), nullable=False)
    
    original_text = Column(Text, nullable=False)
    suggested_text = Column(Text, nullable=False)
    explanation = Column(Text, nullable=True)
    category = Column(String(50), nullable=True)  # grammar, content, formatting, etc.
    position_start = Column(Integer, nullable=True)
    position_end = Column(Integer, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    applied = Column(Boolean, default=False)
    
    # Relationships
    resume = relationship("Resume", back_populates="corrections")
    
    def __repr__(self):
        return f"<ResumeCorrection {self.id}: {self.category}>"


class CoverLetter(db.Model):
    """Model for storing generated cover letters"""
    __tablename__ = 'cover_letters'
    
    id = Column(Integer, primary_key=True)
    resume_id = Column(Integer, ForeignKey('resumes.id'), nullable=False)
    
    text = Column(Text, nullable=False)
    job_description = Column(Text, nullable=False)
    job_title = Column(String(255), nullable=True)
    company_name = Column(String(255), nullable=True)
    language = Column(String(10), default='de')  # Usually German
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    resume = relationship("Resume", back_populates="cover_letters")
    
    def __repr__(self):
        return f"<CoverLetter {self.id}: {self.job_title or 'Untitled'}>"


class Testimonial(db.Model):
    """Model for storing user testimonials/feedback"""
    __tablename__ = 'testimonials'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    position = Column(String(255), nullable=True)
    company = Column(String(255), nullable=True)
    text = Column(Text, nullable=False)
    rating = Column(Integer, nullable=True)  # 1-5 star rating
    
    approved = Column(Boolean, default=False)  # Admin approval flag
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Testimonial {self.id}: {self.name}>"

# Create database tables
with app.app_context():
    db.create_all()
    logging.info("Database tables created")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    # Clear any previous CV data from session
    for key in ['resume_text', 'corrections', 'anschreiben', 'job_description', 'resume_score']:
        if key in session:
            session.pop(key)
    
    logging.info("Rendering index page")
    # Get some example testimonials for display
    testimonials = Testimonial.query.filter_by(approved=True).order_by(Testimonial.created_at.desc()).limit(3).all()
    return render_template('index.html', testimonials=testimonials)

@app.route('/analyze', methods=['POST'])
def analyze():
    resume_text = ""
    file_name = None
    file_type = None
    
    # Check if the user uploaded a file or pasted text
    if 'resume_file' in request.files and request.files['resume_file'].filename:
        file = request.files['resume_file']
        
        logging.debug(f"File upload detected: {file.filename}")
        
        if not allowed_file(file.filename):
            flash('Invalid file type. Please upload a PDF, DOCX, or TXT file.', 'danger')
            return redirect(url_for('index'))
        
        try:
            filename = secure_filename(file.filename)
            file_path = os.path.join(TEMP_FOLDER, filename)
            logging.debug(f"Saving file to: {file_path}")
            file.save(file_path)
            
            # Save file info for database
            file_name = filename
            file_type = filename.rsplit('.', 1)[1].lower()
            
            # Parse the CV file
            logging.debug(f"Parsing file: {file_path}")
            resume_text = parse_resume_file(file_path)
            logging.debug(f"File parsed successfully, text length: {len(resume_text)}")
            
            # Remove the temporary file
            try:
                os.remove(file_path)
                logging.debug(f"Removed temporary file: {file_path}")
            except Exception as e:
                logging.warning(f"Could not remove temporary file: {str(e)}")
            
        except Exception as e:
            flash(f'Error parsing file: {str(e)}', 'danger')
            logging.error(f"File parsing error: {str(e)}")
            logging.error(traceback.format_exc())
            return redirect(url_for('index'))
    
    elif request.form.get('resume_text'):
        resume_text = request.form.get('resume_text')
        resume_text = parse_resume_text(resume_text)
    
    else:
        flash('Please upload a file or paste your CV text.', 'warning')
        return redirect(url_for('index'))
    
    # Check if CV text is too short
    if len(resume_text) < 50:
        flash('The CV content is too short or could not be properly extracted. Please try again.', 'warning')
        return redirect(url_for('index'))
    
    try:
        # Get language preference from form
        language = request.form.get('language', 'en')
        
        # Save resume to database
        resume = Resume(
            text=resume_text,
            language=language,
            file_name=file_name,
            file_type=file_type
        )
        db.session.add(resume)
        db.session.commit()
        
        # Store resume ID in session
        session['resume_id'] = resume.id
        
        # Analyze the CV with AI using specified language
        logging.info(f"Analyzing resume with language: {language}")
        corrections = analyze_resume(resume_text, language)
        
        # Save corrections to database
        for correction in corrections:
            db_correction = ResumeCorrection(
                resume_id=resume.id,
                original_text=correction.get('original', ''),
                suggested_text=correction.get('suggestion', ''),
                explanation=correction.get('explanation', ''),
                category=correction.get('category', ''),
                position_start=correction.get('position', {}).get('start'),
                position_end=correction.get('position', {}).get('end')
            )
            db.session.add(db_correction)
        
        db.session.commit()
        logging.info(f"Saved {len(corrections)} corrections to database")
        
        # Limit the number of corrections to prevent session size issues
        max_corrections = 20
        if len(corrections) > max_corrections:
            logging.warning(f"Limiting corrections from {len(corrections)} to {max_corrections} to prevent session overflow")
            corrections = corrections[:max_corrections]
            
        session['resume_text'] = resume_text
        session['corrections'] = corrections
        session['language'] = language
        
        return redirect(url_for('results'))
        
    except Exception as e:
        flash(f'Error analyzing CV: {str(e)}', 'danger')
        logging.error(f"AI analysis error: {str(e)}")
        logging.error(traceback.format_exc())
        return redirect(url_for('index'))

@app.route('/results')
def results():
    # Check if CV and corrections are in session
    if 'resume_text' not in session or 'corrections' not in session:
        flash('Please submit a CV for analysis first.', 'warning')
        return redirect(url_for('index'))
    
    resume_text = session['resume_text']
    corrections = session['corrections']
    resume_id = session.get('resume_id')
    
    # Get CV score if not already in session
    score_data = session.get('resume_score', None)
    if not score_data:
        try:
            # Get the language preference from the session
            language = session.get('language', 'en')
            score_data = score_resume(resume_text, language)
            session['resume_score'] = score_data
            
            # Save score to database if we have resume_id
            if resume_id:
                # Create the score record
                score_record = ResumeScore(
                    resume_id=resume_id,
                    overall_score=score_data.get('overall', 0),
                    content_score=score_data.get('categories', {}).get('content', 0),
                    format_score=score_data.get('categories', {}).get('format', 0),
                    language_score=score_data.get('categories', {}).get('language', 0),
                    conciseness_score=score_data.get('categories', {}).get('conciseness', 0),
                    summary=score_data.get('summary', '')
                )
                db.session.add(score_record)
                db.session.commit()
                logging.info(f"Saved resume score to database, overall: {score_data.get('overall', 0)}")
                
        except Exception as e:
            logging.error(f"Error scoring CV: {str(e)}")
            logging.error(traceback.format_exc())
            score_data = {
                "overall": 0,
                "categories": {
                    "content": 0,
                    "format": 0,
                    "language": 0,
                    "conciseness": 0
                },
                "summary": "Error in evaluation" if 'language' in locals() and language == 'en' else "Fehler bei der Bewertung"
            }
    
    return render_template('result.html', resume_text=resume_text, corrections=corrections, score=score_data)

@app.route('/download', methods=['POST'])
def download():
    if 'resume_text' not in session:
        flash('No CV data available for download.', 'warning')
        return redirect(url_for('index'))
    
    # Get the corrected CV text from the form
    corrected_text = request.form.get('corrected_text', '')
    
    if not corrected_text:
        flash('No content to download.', 'warning')
        return redirect(url_for('results'))
    
    # Create a temporary file with the corrected CV
    format_type = request.form.get('format', 'txt')
    
    if format_type == 'txt':
        # Create a text file
        file_buffer = io.BytesIO()
        file_buffer.write(corrected_text.encode('utf-8'))
        file_buffer.seek(0)
        
        return send_file(
            file_buffer,
            as_attachment=True,
            download_name='corrected_cv.txt',
            mimetype='text/plain'
        )
    else:  # PDF
        try:
            from fpdf import FPDF
            
            # Create a PDF file
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            
            # Clean text of non-compatible characters 
            # Replace special characters with standard ASCII alternatives
            clean_text = corrected_text.replace('\u2013', '-')  # en-dash
            clean_text = clean_text.replace('\u2014', '--')     # em-dash
            clean_text = clean_text.replace('\u2018', "'")      # left single quote
            clean_text = clean_text.replace('\u2019', "'")      # right single quote
            clean_text = clean_text.replace('\u201c', '"')      # left double quote
            clean_text = clean_text.replace('\u201d', '"')      # right double quote
            
            # Split the text into lines and add to PDF
            for line in clean_text.split('\n'):
                # Handle potential Unicode errors with a general filter
                safe_line = ''.join(c if ord(c) < 128 else '-' for c in line)
                pdf.multi_cell(0, 10, safe_line)
            
            # Save the PDF to a memory buffer
            file_buffer = io.BytesIO()
            
            try:
                # Get the PDF as bytes
                pdf_data = pdf.output(dest='S')
                if isinstance(pdf_data, str):
                    pdf_data = pdf_data.encode('latin-1')
                
                file_buffer.write(pdf_data)
                file_buffer.seek(0)
            except UnicodeEncodeError:
                logging.warning("Unicode encode error when creating PDF, using ASCII fallback")
                # If still encountering unicode errors, fall back to ASCII only
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=12)
                
                # Use ASCII-only version
                ascii_text = corrected_text.encode('ascii', 'replace').decode('ascii')
                for line in ascii_text.split('\n'):
                    pdf.multi_cell(0, 10, line)
                
                pdf_data = pdf.output(dest='S')
                if isinstance(pdf_data, str):
                    pdf_data = pdf_data.encode('latin-1')
                
                file_buffer = io.BytesIO()
                file_buffer.write(pdf_data)
                file_buffer.seek(0)
            
            return send_file(
                file_buffer,
                as_attachment=True,
                download_name='corrected_cv.pdf',
                mimetype='application/pdf'
            )
        except Exception as e:
            flash(f'Error generating PDF: {str(e)}', 'danger')
            logging.error(f"PDF generation error: {str(e)}")
            logging.error(traceback.format_exc())
            return redirect(url_for('results'))

@app.route('/apply_corrections', methods=['POST'])
def apply_corrections():
    if request.method == 'POST':
        data = request.json
        if not data or 'selected_corrections' not in data or 'resume_text' not in data:
            return json.dumps({'error': 'Invalid data format'}), 400, {'ContentType': 'application/json'}
        
        selected_corrections = data['selected_corrections']
        resume_text = data['resume_text']
        
        # Apply selected corrections to the CV text
        # Sort corrections in reverse order to avoid offset issues
        sorted_corrections = sorted(selected_corrections, key=lambda x: x['position']['start'], reverse=True)
        
        for correction in sorted_corrections:
            start = correction['position']['start']
            end = correction['position']['end']
            resume_text = resume_text[:start] + correction['suggestion'] + resume_text[end:]
        
        return json.dumps({'corrected_text': resume_text}), 200, {'ContentType': 'application/json'}
    
    return json.dumps({'error': 'Invalid request method'}), 405, {'ContentType': 'application/json'}


@app.route('/anschreiben', methods=['GET', 'POST'])
def anschreiben_page():
    if request.method == 'GET':
        # Check if CV is in session
        if 'resume_text' not in session:
            flash('Please submit a CV for analysis first.', 'warning')
            return redirect(url_for('index'))
            
        # Get CV from session
        resume_text = session.get('resume_text', '')
        anschreiben_text = session.get('anschreiben', '')
        job_description = session.get('job_description', '')
        
        return render_template('anschreiben.html', 
                              resume_text=resume_text,
                              job_description=job_description,
                              anschreiben=anschreiben_text)
    
    elif request.method == 'POST':
        # Get CV and job description
        resume_text = session.get('resume_text', '')
        job_description = request.form.get('job_description', '')
        resume_id = session.get('resume_id')
        
        if not resume_text:
            flash('No CV found. Please upload your CV first.', 'warning')
            return redirect(url_for('index'))
            
        if not job_description or len(job_description) < 50:
            flash('Please provide a detailed job description to generate a personalized cover letter.', 'warning')
            return render_template('anschreiben.html', 
                                  resume_text=resume_text,
                                  job_description=job_description,
                                  anschreiben='')
        
        try:
            # Generate anschreiben using API
            logging.info("Generating cover letter (Anschreiben)")
            anschreiben_text = generate_anschreiben(resume_text, job_description)
            
            # Store in session
            session['anschreiben'] = anschreiben_text
            session['job_description'] = job_description
            
            # Save to database if we have resume_id
            if resume_id:
                # Get job title and company name
                from ai_analyzer import extract_job_title, extract_company_name
                job_title = extract_job_title(job_description)
                company_name = extract_company_name(job_description)
                
                # Save cover letter
                cover_letter = CoverLetter(
                    resume_id=resume_id,
                    text=anschreiben_text,
                    job_description=job_description,
                    job_title=job_title,
                    company_name=company_name,
                    language='de'  # Anschreiben is typically German
                )
                db.session.add(cover_letter)
                db.session.commit()
                logging.info(f"Saved cover letter to database for resume {resume_id}")
            
            return render_template('anschreiben.html', 
                                  resume_text=resume_text,
                                  job_description=job_description,
                                  anschreiben=anschreiben_text)
        except Exception as e:
            error_message = str(e)
            flash(f'Error generating cover letter: {error_message}', 'danger')
            logging.error(f"Anschreiben generation error: {error_message}")
            logging.error(traceback.format_exc())
            
            return render_template('anschreiben.html', 
                                 resume_text=resume_text,
                                 job_description=job_description,
                                 anschreiben='')

@app.route('/download_anschreiben', methods=['POST'])
def download_anschreiben():
    if 'anschreiben' not in session:
        flash('No cover letter available for download.', 'warning')
        return redirect(url_for('anschreiben_page'))
    
    # Get the anschreiben text from the form or session
    anschreiben_text = request.form.get('anschreiben_text', session.get('anschreiben', ''))
    
    if not anschreiben_text:
        flash('No content to download.', 'warning')
        return redirect(url_for('anschreiben_page'))
    
    # Create a text file
    file_buffer = io.BytesIO()
    file_buffer.write(anschreiben_text.encode('utf-8'))
    file_buffer.seek(0)
    
    return send_file(
        file_buffer,
        as_attachment=True,
        download_name='anschreiben.txt',
        mimetype='text/plain'
    )

@app.route('/donate', methods=['GET', 'POST'])
def donate():
    """Display the donation page with Ko-fi integration and testimonials."""
    if request.method == 'POST':
        # Handle testimonial submission
        try:
            name = request.form.get('name', '').strip()
            position = request.form.get('position', '').strip()
            company = request.form.get('company', '').strip()
            text = request.form.get('testimonial_text', '').strip()
            rating = request.form.get('rating')
            
            # Validate submission
            if not name or not text:
                flash('Please provide your name and testimonial text.', 'warning')
            else:
                # Convert rating to integer if provided
                rating_int = None
                if rating and rating.isdigit():
                    rating_int = int(rating)
                    if rating_int < 1 or rating_int > 5:
                        rating_int = None
                
                # Create new testimonial (pending approval)
                testimonial = Testimonial(
                    name=name,
                    position=position,
                    company=company,
                    text=text,
                    rating=rating_int,
                    approved=False  # Require admin approval
                )
                db.session.add(testimonial)
                db.session.commit()
                
                flash('Thank you for your feedback! Your testimonial has been submitted for review.', 'success')
                logging.info(f"New testimonial submitted by {name}")
                
        except Exception as e:
            flash('Error submitting testimonial. Please try again.', 'danger')
            logging.error(f"Error submitting testimonial: {str(e)}")
            logging.error(traceback.format_exc())
    
    # Get approved testimonials from database
    testimonials = Testimonial.query.filter_by(approved=True).order_by(Testimonial.created_at.desc()).limit(10).all()
    return render_template('donate.html', testimonials=testimonials)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    logging.error(f"Server error: {str(e)}")
    return render_template('500.html'), 500

# Error logging for uncaught exceptions
@app.errorhandler(Exception)
def handle_exception(e):
    logging.error(f"Unhandled exception: {str(e)}")
    logging.error(traceback.format_exc())
    return render_template('500.html'), 500

# New routes for additional features
@app.route('/faq')
def faq():
    """Display the FAQ page with common questions and answers."""
    return render_template('faq.html')

@app.route('/examples')
def examples():
    """Display example resumes that users can download as templates."""
    return render_template('examples.html')

@app.route('/recommendations')
def recommendations():
    """Display personalized recommendations based on resume analysis."""
    # Check if CV and score data are in session
    if 'resume_text' not in session or 'resume_score' not in session:
        flash('Please submit a CV for analysis first.', 'warning')
        return redirect(url_for('index'))
    
    resume_text = session.get('resume_text', '')
    score_data = session.get('resume_score', {})
    
    # Placeholder for industry-specific recommendations
    # In a full implementation, this would be generated using AI based on detected skills
    industry_recommendations = {
        'industry_tips': [
            {
                'title': 'Technology / IT',
                'description': 'If you\'re in the technology field:',
                'items': [
                    'List programming languages and technologies in order of proficiency',
                    'Include GitHub/GitLab repositories or portfolio website',
                    'Highlight specific technical problems you\'ve solved',
                    'Mention contributions to open-source projects or hackathons'
                ]
            },
            {
                'title': 'Business / Management',
                'description': 'If you\'re in business or management:',
                'items': [
                    'Highlight cost-saving initiatives and their financial impact',
                    'Emphasize leadership and team management experiences',
                    'Include metrics on team performance improvements',
                    'Showcase project management methodologies you\'re familiar with'
                ]
            }
        ]
    }
    
    return render_template('recommendations.html', 
                           score=score_data, 
                           recommendations=industry_recommendations)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
