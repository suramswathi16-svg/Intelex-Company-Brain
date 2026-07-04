from fastapi import APIRouter

router = APIRouter()

@router.get("/weekly-report")
def weekly_report():
    return {
        "new_documents": 45,
        "ai_queries": 850,
        "active_users": 160,
        "top_department": "Engineering",
        "knowledge_growth": "12%"
    }