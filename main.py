"""
main.py
-------------
FastAPI application entrypoint for "intelex Company Brain".

- Creates DB tables on startup (for hackathon speed; use Alembic
  migrations in a real production setup).
- Seeds a few realistic sample users / alerts / analytics rows so the
  frontend team has data to work with immediately.
- Registers CORS middleware and mounts all routes from routes.py.

Run with:
    uvicorn main:app --reload
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import Base, engine, SessionLocal
from models import User, RoleEnum, Alert, EmployeeAnalysis
from auth import hash_password
from routes import router


def seed_sample_data():
    """Populate the DB with demo users/alerts/analytics if it's empty."""
    db = SessionLocal()
    try:
        if db.query(User).count() > 0:
            return  # already seeded

        admin = User(
            username="admin",
            email="admin@intelex.com",
            hashed_password=hash_password("Admin@123"),
            role=RoleEnum.ADMIN,
        )
        employee = User(
            username="employee1",
            email="employee1@intelex.com",
            hashed_password=hash_password("Employee@123"),
            role=RoleEnum.EMPLOYEE,
        )
        analyst = User(
            username="analyst1",
            email="analyst1@intelex.com",
            hashed_password=hash_password("Analyst@123"),
            role=RoleEnum.ANALYST,
        )
        db.add_all([admin, employee, analyst])
        db.commit()
        db.refresh(admin)
        db.refresh(employee)

        alerts = [
            Alert(
                title="Storage nearing capacity",
                message="Document storage is at 85% capacity. Consider archiving old files.",
                severity="warning",
                created_by=admin.id,
            ),
            Alert(
                title="New RAG index deployed",
                message="The knowledge base index was refreshed with Q2 documents.",
                severity="info",
                created_by=admin.id,
            ),
            Alert(
                title="Failed login attempts detected",
                message="Multiple failed login attempts on account 'employee1'.",
                severity="critical",
                created_by=admin.id,
            ),
        ]
        db.add_all(alerts)

        analyses = [
            EmployeeAnalysis(
                employee_id=employee.id,
                metric_name="productivity_score",
                metric_value=87.5,
                period="2026-Q2",
            ),
            EmployeeAnalysis(
                employee_id=employee.id,
                metric_name="engagement_score",
                metric_value=72.0,
                period="2026-Q2",
            ),
            EmployeeAnalysis(
                employee_id=employee.id,
                metric_name="tickets_resolved",
                metric_value=134,
                period="2026-Q2",
            ),
        ]
        db.add_all(analyses)

        db.commit()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables + seed demo data
    Base.metadata.create_all(bind=engine)
    seed_sample_data()
    yield
    # Shutdown: nothing to clean up for this hackathon setup


app = FastAPI(
    title="intelex Company Brain API",
    description="Backend for an enterprise knowledge platform: RAG search, "
    "workflow automation, and multi-agent assistants.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS: open for hackathon/dev use. Lock this down to your real frontend
# origin(s) before shipping to production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount all API routes
app.include_router(router)


@app.get("/")
def root():
    """Simple health-check / welcome endpoint."""
    return {
        "status": "ok",
        "service": "intelex Company Brain API",
        "docs": "/docs",
    }
from fastapi import FastAPI
from dashboard import router as dashboard_router
from employee_analysis import router as employee_router
from alerts import router as alerts_router
from recommendation import router as recommendation_router
from weekly_report import router as weekly_router
app = FastAPI(title="AI Company Brain Dashboard")

app.include_router(dashboard_router)
app.include_router(employee_router)
app.include_router(alerts_router)
app.include_router(weekly_router)
app.include_router(recommendation_router)

@app.get("/")
def home():
    return {"message": "AI Company Brain Backend is Running!"}
