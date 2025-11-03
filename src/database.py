"""Database models and connection management for CAB Agent (SQL Server)."""

import sys
import os
from sqlalchemy import (
    create_engine,
    Column,
    String,
    Text,
    DateTime,
    Integer,
    Index,
    UniqueConstraint,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.types import JSON
from datetime import datetime
import urllib

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.utils import Config, get_logger

logger = get_logger(__name__)

Base = declarative_base()


class ChangeRequest(Base):
    """Change Request model - stores current state of CRs."""

    __tablename__ = "change_requests"

    cr_id = Column(String(50), primary_key=True)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    state = Column(String(100), index=True)
    work_item_type = Column(String(100))
    created_by = Column(String(255))
    created_by_email = Column(String(255), index=True)
    assigned_to = Column(String(255), index=True)
    scheduled_start_date = Column(DateTime)
    scheduled_end_date = Column(DateTime)
    approval_status = Column(String(100))
    priority = Column(String(50))
    risk_level = Column(String(50))
    last_synced_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<ChangeRequest(cr_id='{self.cr_id}', title='{self.title}', state='{self.state}')>"


class CRStateHistory(Base):
    """CR State History model - tracks all changes to CRs."""

    __tablename__ = "cr_state_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cr_id = Column(String(50), nullable=False, index=True)
    field_name = Column(String(100), nullable=False, index=True)
    old_value = Column(Text)
    new_value = Column(Text)
    changed_by = Column(String(255))
    changed_at = Column(DateTime, default=datetime.utcnow, index=True)
    revision_number = Column(Integer)

    def __repr__(self):
        return f"<CRStateHistory(cr_id='{self.cr_id}', field='{self.field_name}', {self.old_value}->{self.new_value})>"


class UserConversationReference(Base):
    """User conversation reference for Teams proactive messaging."""

    __tablename__ = "user_conversation_references"

    user_id = Column(String(255), primary_key=True)
    email = Column(String(255), index=True)
    aad_object_id = Column(String(255), index=True)
    name = Column(String(255))
    conversation_reference = Column(Text, nullable=False)  # Store JSON as TEXT for SQL Server
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_interaction_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<UserConversationReference(user_id='{self.user_id}', email='{self.email}')>"


class CRNotificationSent(Base):
    """Track sent notifications to prevent duplicates."""

    __tablename__ = "cr_notifications_sent"
    __table_args__ = (
        UniqueConstraint("cr_id", "event_type", "recipient_email", name="unique_notification"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    cr_id = Column(String(50), nullable=False, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    recipient_email = Column(String(255), nullable=False, index=True)
    sent_at = Column(DateTime, default=datetime.utcnow)
    notification_status = Column(String(50), default="sent")

    def __repr__(self):
        return f"<CRNotificationSent(cr_id='{self.cr_id}', event='{self.event_type}', to='{self.recipient_email}')>"


class PIRTracking(Base):
    """Track PIR (Post Implementation Review) status and completion."""

    __tablename__ = "pir_tracking"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cr_id = Column(String(50), nullable=False, unique=True, index=True)
    cr_title = Column(String(500))
    requester_email = Column(String(255), index=True)
    status = Column(String(50), nullable=False, index=True)  # pending, escalated, completed
    reviewer_count = Column(Integer, default=0)
    
    # Timestamps
    initiated_at = Column(DateTime, default=datetime.utcnow, index=True)
    reminder_due_at = Column(DateTime, index=True)
    escalation_due_at = Column(DateTime, index=True)
    reminder_sent = Column(Integer, default=0)  # Using Integer as Boolean for SQL Server compatibility
    reminder_sent_at = Column(DateTime)
    escalation_sent = Column(Integer, default=0)  # Using Integer as Boolean
    escalation_sent_at = Column(DateTime)
    completed_at = Column(DateTime, index=True)
    completed_by = Column(String(255))
    
    # Metrics
    completion_time_hours = Column(Integer)
    pir_comments = Column(Text)
    
    def __repr__(self):
        return f"<PIRTracking(cr_id='{self.cr_id}', status='{self.status}')>"


# Database connection functions


def get_database_url():
    """Get database URL from configuration."""
    return Config.DATABASE_URL


def create_db_engine():
    """Create database engine with connection pooling."""
    database_url = get_database_url()
    
    # URL encode the connection string for special characters
    if "?" in database_url:
        base_url, params = database_url.split("?", 1)
        # Parse and re-encode parameters
        params_encoded = urllib.parse.quote_plus(params)
        database_url = f"{base_url}?{params}"
    
    logger.info("Creating database engine", database_type="SQL Server")
    
    engine = create_engine(
        database_url,
        pool_pre_ping=True,  # Verify connections before using
        pool_recycle=3600,  # Recycle connections after 1 hour
        pool_size=10,  # Connection pool size
        max_overflow=20,  # Max overflow connections
        echo=False,  # Set to True for SQL debugging
    )
    return engine


def init_database():
    """Initialize database - create all tables."""
    logger.info("Initializing database - creating tables")
    
    try:
        engine = create_db_engine()
        Base.metadata.create_all(engine)
        logger.info("Database tables created successfully")
        return engine
    except Exception as e:
        logger.error("Failed to initialize database", error=str(e))
        raise


def get_session():
    """Get database session for queries."""
    engine = create_db_engine()
    Session = sessionmaker(bind=engine)
    return Session()


def drop_all_tables():
    """Drop all tables - USE WITH CAUTION (for development only)."""
    logger.warning("Dropping all database tables")
    engine = create_db_engine()
    Base.metadata.drop_all(engine)
    logger.info("All tables dropped")
