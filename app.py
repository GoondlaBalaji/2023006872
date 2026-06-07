from fastapi import FastAPI
import uvicorn

# Import our refactored scripts
from vehicle_scheduler.main import get_schedule
from notification_app_be.priority_inbox import get_top_notifications

app = FastAPI(title="AffordMed Backend Assessment API")

@app.get("/api/vehicle-scheduler", summary="Get optimal vehicle maintenance schedule")
def vehicle_scheduler_endpoint():
    """
    Solves the 0/1 Knapsack problem to maximize impact within mechanic hour budgets.
    """
    return get_schedule()

@app.get("/api/priority-inbox", summary="Get Top 10 Priority Notifications")
def priority_inbox_endpoint():
    """
    Uses a Min-Heap to return the exact Top 10 notifications based on Weight and Recency.
    """
    return get_top_notifications()

if __name__ == "__main__":
    print("Starting API Server... You can test this in Postman!")
    uvicorn.run(app, host="127.0.0.1", port=8000)
