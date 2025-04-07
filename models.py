from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

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