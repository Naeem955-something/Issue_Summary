from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime
import uuid

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    github_id = Column(String(100), unique=True, nullable=False)
    username = Column(String(100), nullable=False)
    avatar_url = Column(String(500))
    availability_hours = Column(Integer, default=10)
    preferred_domains = Column(Text)
    learning_goals = Column(Text)
    new_skills_detected = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    summaries = relationship("IssueSummary", back_populates="user")
    skills = relationship("DeveloperSkill", back_populates="user", cascade="all, delete-orphan")
    match_scores = relationship("MatchScore", back_populates="user", cascade="all, delete-orphan")

class IssueSummary(Base):
    __tablename__ = "issue_summaries"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    repo_owner = Column(String(100), nullable=False)
    repo_name = Column(String(100), nullable=False)
    github_issue_id = Column(Integer, nullable=False)
    issue_title = Column(String(500), nullable=False)
    issue_url = Column(String(500), nullable=False)
    summary = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="summaries")

class DeveloperSkill(Base):
    __tablename__ = "developer_skills"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    skill_name = Column(String(100), nullable=False)
    category = Column(String(100), nullable=False)
    proficiency = Column(String(50), nullable=False)
    source = Column(Text, nullable=False)
    is_confirmed = Column(Boolean, default=False)
    is_manually_added = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)
    last_detected_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="skills")

class ProjectAnalysis(Base):
    __tablename__ = "project_analysis"

    id = Column(Integer, primary_key=True, autoincrement=True)
    repo_owner = Column(String(100), nullable=False)
    repo_name = Column(String(100), nullable=False)
    github_repo_id = Column(Integer, unique=True)
    stars = Column(Integer, default=0)
    forks = Column(Integer, default=0)
    open_issues_count = Column(Integer, default=0)
    license = Column(String(100))
    last_pushed_at = Column(DateTime)
    primary_language = Column(String(100))
    languages_json = Column(Text)
    architecture_type = Column(String(100))
    platform = Column(String(100))
    has_contributing = Column(Boolean, default=False)
    has_code_of_conduct = Column(Boolean, default=False)
    has_issue_template = Column(Boolean, default=False)
    has_pr_template = Column(Boolean, default=False)
    activity_score = Column(Integer, default=0)
    beginner_score = Column(Integer, default=0)
    domain_primary = Column(String(100))
    domain_secondary = Column(String(100))
    health_summary = Column(Text)
    last_synced_at = Column(DateTime, default=datetime.utcnow)

    issues = relationship("Issue", back_populates="project", cascade="all, delete-orphan")

class Issue(Base):
    __tablename__ = "issues"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("project_analysis.id", ondelete="CASCADE"), nullable=False)
    github_issue_id = Column(Integer, unique=True, nullable=False)
    issue_title = Column(String(500), nullable=False)
    issue_url = Column(String(500), nullable=False)
    issue_type = Column(String(100))
    plain_summary = Column(Text)
    required_skills = Column(Text)
    helpful_skills = Column(Text)
    difficulty = Column(String(50))
    estimated_hours = Column(Integer)
    coding_required = Column(Boolean, default=True)
    learning_takeaways = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("ProjectAnalysis", back_populates="issues")
    match_scores = relationship("MatchScore", back_populates="issue", cascade="all, delete-orphan")

class MatchScore(Base):
    __tablename__ = "match_scores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    issue_id = Column(Integer, ForeignKey("issues.id", ondelete="CASCADE"), nullable=False)
    score = Column(Integer, nullable=False)
    fit_explanation = Column(Text)
    last_calculated_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="match_scores")
    issue = relationship("Issue", back_populates="match_scores")

