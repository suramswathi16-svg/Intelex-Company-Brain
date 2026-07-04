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