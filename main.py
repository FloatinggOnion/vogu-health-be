from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging
from services.health_data.service import HealthDataService
from services.health_data.models import (
    MetricType, SleepData, HeartRateData, WeightData,
    HealthDataResponse, HealthDataError
)
from services.llm_service import LLMService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Health Data API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update this with your Flutter app's domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
health_data_service = HealthDataService()
llm_service = LLMService()

# Mock user authentication (replace with your actual auth system)
async def get_current_user() -> str:
    """Mock function to get current user ID"""
    return "user_123"  # Replace with actual user ID from your auth system

@app.post("/api/v1/health-data/sleep")
async def submit_sleep_data(
    data: SleepData,
    user_id: str = Depends(get_current_user)
) -> HealthDataResponse:
    """Submit sleep data"""
    try:
        data.user_id = user_id  # Ensure user_id is set
        return await health_data_service.store_sleep_data(data)
    except HealthDataError as e:
        raise HTTPException(status_code=400, detail=e.dict())
    except Exception as e:
        logger.error(f"Error submitting sleep data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/health-data/heart-rate")
async def submit_heart_rate_data(
    data: HeartRateData,
    user_id: str = Depends(get_current_user)
) -> HealthDataResponse:
    """Submit heart rate data"""
    try:
        data.user_id = user_id
        return await health_data_service.store_heart_rate_data(data)
    except HealthDataError as e:
        raise HTTPException(status_code=400, detail=e.dict())
    except Exception as e:
        logger.error(f"Error submitting heart rate data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/health-data/weight")
async def submit_weight_data(
    data: WeightData,
    user_id: str = Depends(get_current_user)
) -> HealthDataResponse:
    """Submit weight data"""
    try:
        data.user_id = user_id
        return await health_data_service.store_weight_data(data)
    except HealthDataError as e:
        raise HTTPException(status_code=400, detail=e.dict())
    except Exception as e:
        logger.error(f"Error submitting weight data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/health-data/{metric_type}")
async def get_health_data(
    metric_type: MetricType,
    days: int = Query(7, ge=1, le=30),
    user_id: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get health data for a specific metric type"""
    try:
        data = await health_data_service.get_recent_data(user_id, metric_type, days)
        return {
            "status": "success",
            "data": data
        }
    except HealthDataError as e:
        raise HTTPException(status_code=400, detail=e.dict())
    except Exception as e:
        logger.error(f"Error retrieving health data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/health-data/daily/{date}")
async def get_daily_summary(
    date: datetime,
    user_id: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get daily health summary"""
    try:
        summary = await health_data_service.get_daily_summary(user_id, date)
        return {
            "status": "success",
            "data": summary
        }
    except HealthDataError as e:
        raise HTTPException(status_code=400, detail=e.dict())
    except Exception as e:
        logger.error(f"Error retrieving daily summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/insights/recent")
async def get_recent_insights(
    days: int = Query(7, ge=1, le=30),
    user_id: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get AI-powered health insights for recent data"""
    try:
        # Get data for all metric types
        metrics = []
        for metric_type in MetricType:
            data = await health_data_service.get_recent_data(user_id, metric_type, days)
            metrics.extend(data)
        
        # Generate insights using LLM
        insights = await llm_service.get_health_insights(metrics)
        return {
            "status": "success",
            "insights": insights
        }
    except Exception as e:
        logger.error(f"Error generating insights: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/insights/daily/{date}")
async def get_daily_insights(
    date: datetime,
    user_id: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get AI-powered health insights for a specific day"""
    try:
        # Get daily summary
        summary = await health_data_service.get_daily_summary(user_id, date)
        
        # Convert summary to metrics format
        metrics = []
        for sleep in summary.get("sleep", []):
            metrics.append({
                "timestamp": datetime.fromisoformat(sleep["start_time"]),
                "metric_type": "sleep",
                "value": sleep["deep_sleep"] + sleep["light_sleep"] + sleep["rem_sleep"],
                "quality": sleep["quality"],
                "deep_sleep_minutes": sleep["deep_sleep"],
                "light_sleep_minutes": sleep["light_sleep"],
                "rem_sleep_minutes": sleep["rem_sleep"],
                "awake_minutes": sleep["awake_time"]
            })
        
        for hr in summary.get("heart_rate", []):
            metrics.append({
                "timestamp": datetime.fromisoformat(hr["timestamp"]),
                "metric_type": "heart_rate",
                "value": hr["value"],
                "resting_heart_rate": hr.get("resting_rate"),
                "activity_type": hr.get("activity_type")
            })
        
        for weight in summary.get("weight", []):
            metrics.append({
                "timestamp": datetime.fromisoformat(weight["timestamp"]),
                "metric_type": "weight",
                "value": weight["value"],
                "bmi": weight.get("bmi"),
                "body_fat": weight.get("body_fat"),
                "muscle_mass": weight.get("muscle_mass"),
                "water_percentage": weight.get("water_percentage"),
                "bone_mass": weight.get("bone_mass")
            })
        
        # Generate insights
        insights = await llm_service.get_health_insights(metrics)
        return {
            "status": "success",
            "insights": insights
        }
    except Exception as e:
        logger.error(f"Error generating daily insights: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 