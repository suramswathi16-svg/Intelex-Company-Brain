"""
routes.py
-------------
All API endpoints for Company Brain, grouped into a single APIRouter
for simplicity (easy to split into per-feature routers later, e.g.
auth_router, upload_router, chat_router, analytics_router).

Endpoints:
  POST /register            -> create a new user account
  POST /login                -> authenticate, get a JWT
  GET  /users                -> list all users (admin only)
  POST /upload                -> upload a file's metadata (admin/employee)
  POST /chat                 -> send a message to the AI assistant (any role)
  GET  /dashboard             -> aggregated stats (admin/analyst)
  GET  /alerts                -> list alerts (any authenticated role)
  POST /alerts                -> create an alert (admin only)
  GET  /employee-analysis     -> analytics data (analyst/admin)
"""

from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import get_db
from models import User, RoleEnum, Upload, ChatMessage, Alert, EmployeeAnalysis
from schemas import (
    UserCreate,
    UserOut,
    UserLogin,
    Token,
    UploadOut,
    ChatRequest,
    ChatResponse,
    AlertCreate,
    AlertOut,
    EmployeeAnalysisOut,
    DashboardOut,
)
from auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
    require_role,
)

router = APIRouter()


# =====================================================================
# AUTH
# =====================================================================

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    """Create a new user. Username & email must be unique."""
    existing = (
        db.query(User)
        .filter((User.username == payload.username) | (User.email == payload.email))
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Username or email already registered")

    user = User(
        username=payload.username,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=payload.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    """Validate credentials and return a signed JWT access token."""
    user = db.query(User).filter(User.username == payload.username).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    # `sub` (subject) holds the user id; `role` is embedded for convenience
    # on the client side (do not rely on it server-side for authorization --
    # every protected route re-checks the role from the DB via get_current_user).
    token = create_access_token(data={"sub": user.id, "role": user.role.value})
    return Token(access_token=token, role=user.role)


# =====================================================================
# USERS (Admin only)
# =====================================================================

@router.get("/users", response_model=List[UserOut])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(RoleEnum.ADMIN)),
):
    """Admin-only: list every registered user."""
    return db.query(User).order_by(User.created_at.desc()).all()


# =====================================================================
# UPLOAD (Admin + Employee)
# =====================================================================

@router.post("/upload", response_model=UploadOut, status_code=status.HTTP_201_CREATED)
def upload_file(
    file: UploadFile = File(...),
    description: str = Form(default=""),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(RoleEnum.ADMIN, RoleEnum.EMPLOYEE)),
):
    """
    Accepts a file upload and stores its metadata (filename, content type,
    uploader, description). In a full implementation this is also where
    you'd push the file to object storage (S3 etc.) and kick off the RAG
    ingestion / embedding pipeline.
    """
    record = Upload(
        filename=file.filename,
        content_type=file.content_type,
        description=description,
        uploaded_by=current_user.id,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


# =====================================================================
# CHAT (any authenticated role)
# =====================================================================

@router.post("/chat", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Sends a message to the (mocked) AI assistant and stores the exchange.
    Replace `generate_mock_response` with a call into your RAG / multi-agent
    pipeline (e.g. retrieve relevant docs, then call the LLM).
    """
    reply_text = generate_mock_response(payload.message)

    record = ChatMessage(
        user_id=current_user.id,
        message=payload.message,
        response=reply_text,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def generate_mock_response(message: str) -> str:
    """Placeholder for the real RAG/LLM call."""
    return (
        f"[Company Brain Assistant] I received your message: '{message}'. "
        "In production this would be answered using retrieved company "
        "knowledge via the RAG pipeline."
    )


# =====================================================================
# DASHBOARD (Admin + Analyst)
# =====================================================================

@router.get("/dashboard", response_model=DashboardOut)
def dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(RoleEnum.ADMIN, RoleEnum.ANALYST)),
):
    """Aggregated platform stats for the admin/analyst dashboard."""
    total_users = db.query(func.count(User.id)).scalar()
    total_uploads = db.query(func.count(Upload.id)).scalar()
    total_chats = db.query(func.count(ChatMessage.id)).scalar()
    active_alerts = db.query(func.count(Alert.id)).scalar()

    users_by_role = {
        role.value: db.query(func.count(User.id)).filter(User.role == role).scalar()
        for role in RoleEnum
    }

    recent_alerts = (
        db.query(Alert).order_by(Alert.created_at.desc()).limit(5).all()
    )

    return DashboardOut(
        total_users=total_users,
        total_uploads=total_uploads,
        total_chats=total_chats,
        active_alerts=active_alerts,
        users_by_role=users_by_role,
        recent_alerts=recent_alerts,
    )


# =====================================================================
# ALERTS (GET: any authenticated role | POST: Admin only)
# =====================================================================

@router.get("/alerts", response_model=List[AlertOut])
def list_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Any authenticated user can view alerts."""
    return db.query(Alert).order_by(Alert.created_at.desc()).all()


@router.post("/alerts", response_model=AlertOut, status_code=status.HTTP_201_CREATED)
def create_alert(
    payload: AlertCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(RoleEnum.ADMIN)),
):
    """Admin-only: create a new alert (e.g. triggered by a workflow)."""
    alert = Alert(
        title=payload.title,
        message=payload.message,
        severity=payload.severity,
        created_by=current_user.id,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


# =====================================================================
# EMPLOYEE ANALYSIS (Admin + Analyst)
# =====================================================================

@router.get("/employee-analysis", response_model=List[EmployeeAnalysisOut])
def employee_analysis(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(RoleEnum.ADMIN, RoleEnum.ANALYST)),
):
    """Returns raw analytics rows (e.g. productivity/engagement metrics)."""
    return db.query(EmployeeAnalysis).order_by(EmployeeAnalysis.created_at.desc()).all()
