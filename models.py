"""
models.py
-------------
SQLAlchemy ORM models for the Company Brain platform.

Tables:
- users              -> accounts + role (admin / employee / analyst)
- uploads            -> metadata for files uploaded (for RAG ingestion)
- chat_messages      -> chat history between a user and the assistant
- alerts             -> system / workflow alerts shown on the dashboard
- employee_analyses  -> analytics rows used by /employee-analysis
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    DateTime,
    ForeignKey,
    Enum,
    Text,
)
from sqlalchemy.orm import relationship

from database import Base


class RoleEnum(str, enum.Enum):
    """Roles used for Role-Based Access Control (RBAC)."""
    ADMIN = "admin"
    EMPLOYEE = "employee"
    ANALYST = "analyst"


def gen_uuid() -> str:
    """Generate a string UUID primary key."""
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=gen_uuid)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(RoleEnum), nullable=False, default=RoleEnum.EMPLOYEE)
    created_at = Column(DateTime, default=datetime.utcnow)

    uploads = relationship("Upload", back_populates="owner")
    chats = relationship("ChatMessage", back_populates="user")
    analyses = relationship(
        "EmployeeAnalysis",
        back_populates="employee",
        foreign_keys="EmployeeAnalysis.employee_id",
    )


class Upload(Base):
    __tablename__ = "uploads"

    id = Column(String, primary_key=True, default=gen_uuid)
    filename = Column(String(255), nullable=False)
    content_type = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    uploaded_by = Column(String, ForeignKey("users.id"), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="uploads")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    message = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="chats")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(String, primary_key=True, default=gen_uuid)
    title = Column(String(150), nullable=False)
    message = Column(Text, nullable=False)
    severity = Column(String(20), default="info")  # info | warning | critical
    created_by = Column(String, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class EmployeeAnalysis(Base):
    __tablename__ = "employee_analyses"

    id = Column(String, primary_key=True, default=gen_uuid)
    employee_id = Column(String, ForeignKey("users.id"), nullable=False)
    metric_name = Column(String(100), nullable=False)   # e.g. "productivity_score"
    metric_value = Column(Float, nullable=False)
    period = Column(String(20), nullable=False)          # e.g. "2026-Q2"
    created_at = Column(DateTime, default=datetime.utcnow)

    employee = relationship(
        "User", back_populates="analyses", foreign_keys=[employee_id]
    )
