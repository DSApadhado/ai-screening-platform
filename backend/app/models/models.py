import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database import Base


class Job(Base):
    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    candidates = relationship("Candidate", back_populates="job", cascade="all, delete-orphan")


class Candidate(Base):
    __tablename__ = "candidates"
    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    s_no = Column(Integer)
    name = Column(String(255))
    email = Column(String(255))
    college = Column(String(255))
    branch = Column(String(255))
    cgpa = Column(Float)
    best_ai_project = Column(Text)
    research_work = Column(Text)
    github_url = Column(String(512))
    resume_url = Column(String(512))
    resume_text = Column(Text)
    github_analysis = Column(Text)
    ai_evaluation = Column(Text)
    ai_score = Column(Float, default=0.0)
    resume_score = Column(Float, default=0.0)
    github_score = Column(Float, default=0.0)
    jd_match_score = Column(Float, default=0.0)
    project_score = Column(Float, default=0.0)
    research_score = Column(Float, default=0.0)
    total_score = Column(Float, default=0.0)
    test_la = Column(Float)
    test_code = Column(Float)
    test_total = Column(Float)
    final_score = Column(Float, default=0.0)
    status = Column(String(50), default="uploaded")  # uploaded, evaluated, shortlisted, test_sent, test_scored, interview_scheduled, rejected
    interview_time = Column(DateTime)
    meet_link = Column(String(512))
    email_sent = Column(Boolean, default=False)
    score_breakdown = Column(JSON)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    job = relationship("Job", back_populates="candidates")
