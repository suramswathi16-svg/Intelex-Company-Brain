"""
schemas.py
-------------
Pydantic models used for request validation and JSON responses.
Keeping these separate from the SQLAlchemy models (models.py) is a
best practice: it decouples the DB schema from the public API contract.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field

from models import RoleEnum


# ---------- Auth ----------

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)
    role: RoleEnum = RoleEnum.EMPLOYEE  # defaults to "employee" if not supplied


class UserLogin(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: str
    username: str
    email: EmailStr
    role: RoleEnum
    created_at: datetime

    class Config:
        from_attributes = True  # allows creation from ORM objects


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: RoleEnum


# ---------- Upload ----------

class UploadOut(BaseModel):
    id: str
    filename: str
    content_type: Optional[str]
    description: Optional[str]
    uploaded_by: str
    uploaded_at: datetime

    class Config:
        from_attributes = True


# ---------- Chat ----------

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)


class ChatResponse(BaseModel):
    id: str
    message: str
    response: str
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- Alerts ----------

class AlertCreate(BaseModel):
    title: str
    message: str
    severity: str = "info"  # info | warning | critical


class AlertOut(BaseModel):
    id: str
    title: str
    message: str
    severity: str
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- Analytics ----------

class EmployeeAnalysisOut(BaseModel):
    id: str
    employee_id: str
    metric_name: str
    metric_value: float
    period: str
    created_at: datetime

    class Config:
        from_attributes = True


class DashboardOut(BaseModel):
    total_users: int
    total_uploads: int
    total_chats: int
    active_alerts: int
    users_by_role: dict
    recent_alerts: List[AlertOut]
