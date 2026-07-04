from fastapi import APIRouter

router = APIRouter()

@router.get("/employee-analysis")
def employee_analysis():
    return {
        "total_employees": 180,
        "active_today": 145,
        "inactive_today": 35,
        "top_contributors": [
            "Rahul",
            "Priya",
            "Sneha"
        ]
    }