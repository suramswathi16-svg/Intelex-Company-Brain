from fastapi import APIRouter

router = APIRouter()

@router.get("/dashboard")
def get_dashboard():
    return {
        "total_documents": 1250,
        "active_employees": 180,
        "ai_queries_today": 950
    }