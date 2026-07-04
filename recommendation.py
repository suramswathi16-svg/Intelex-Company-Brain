from fastapi import APIRouter

router = APIRouter()

@router.get("/recommendations")
def get_recommendations():
    return {
        "recommendations": [
            "Upload missing HR policies",
            "Update outdated technical documentation",
            "Encourage inactive employees to contribute",
            "Review frequently searched documents"
        ]
    }