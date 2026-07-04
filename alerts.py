from fastapi import APIRouter

router = APIRouter()

@router.get("/alerts")
def get_alerts():
    return {
        "critical_alerts": [
            "12 outdated documents",
            "8 unanswered AI queries",
            "5 inactive employees"
        ],
        "status": "Attention Required"
    }