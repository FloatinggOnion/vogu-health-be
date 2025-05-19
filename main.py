from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
from dotenv import load_dotenv
from datetime import datetime
from services.garmin_service import GarminService
from services.llm_service import LLMService

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Garmin Health Insights API",
    description="API for ingesting Garmin health data and providing AI-powered insights",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
garmin_service = GarminService()
llm_service = LLMService()

# Models
class HealthMetric(BaseModel):
    timestamp: datetime
    metric_type: str
    value: float
    unit: str
    additional_data: Optional[Dict[str, Any]] = None

class HealthInsight(BaseModel):
    summary: str
    recommendations: List[str]
    concerns: List[str]

@app.get("/")
async def root():
    return {"message": "Garmin Health Insights API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/metrics/recent")
async def get_recent_metrics(days: int = 7):
    """Get recent health metrics from the last N days"""
    try:
        metrics = await garmin_service.get_recent_metrics(days)
        return {"metrics": metrics}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics/daily/{date}")
async def get_daily_metrics(date: datetime):
    """Get health metrics for a specific day"""
    try:
        summary = await garmin_service.get_daily_summary(date)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/trends")
async def get_health_trends(days: int = 30):
    """Get health trends over a period of time"""
    try:
        trends = await garmin_service.get_health_trends(days)
        return trends
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/insights/recent")
async def get_recent_insights(days: int = 7):
    """Get AI-powered health insights for recent metrics"""
    try:
        # Get recent metrics
        metrics = await garmin_service.get_recent_metrics(days)
        
        # Generate insights
        insights = await llm_service.get_health_insights(metrics)
        
        return insights
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/insights/daily/{date}")
async def get_daily_insights(date: datetime):
    """Get AI-powered health insights for a specific day"""
    try:
        # Get daily metrics
        summary = await garmin_service.get_daily_summary(date)
        
        # Convert summary to metrics format
        metrics = []
        
        if "sleep" in summary:
            for sleep in summary["sleep"]:
                metrics.append({
                    "timestamp": datetime.fromisoformat(sleep["startTime"].replace('Z', '+00:00')),
                    "metric_type": "sleep",
                    "value": sleep["totalSleepTime"],
                    "unit": "minutes",
                    "additional_data": {
                        "quality": sleep.get("sleepQuality"),
                        "deep_sleep_minutes": sleep.get("deepSleepTime"),
                        "light_sleep_minutes": sleep.get("lightSleepTime"),
                        "rem_sleep_minutes": sleep.get("remSleepTime"),
                        "awake_minutes": sleep.get("awakeTime"),
                        "sleep_score": sleep.get("sleepScore")
                    }
                })
        
        if "heart_rate" in summary:
            for hr in summary["heart_rate"]["data"]:
                metrics.append({
                    "timestamp": datetime.fromisoformat(hr["timestamp"].replace('Z', '+00:00')),
                    "metric_type": "heart_rate",
                    "value": hr["heartRate"],
                    "unit": "bpm",
                    "additional_data": {
                        "resting_heart_rate": hr.get("restingHeartRate"),
                        "max_heart_rate": hr.get("maxHeartRate"),
                        "min_heart_rate": hr.get("minHeartRate")
                    }
                })
        
        if "weight" in summary:
            for weight in summary["weight"]:
                metrics.append({
                    "timestamp": datetime.fromisoformat(weight["timestamp"].replace('Z', '+00:00')),
                    "metric_type": "weight",
                    "value": weight["weight"],
                    "unit": "kg",
                    "additional_data": {
                        "bmi": weight.get("bmi"),
                        "body_fat": weight.get("bodyFat"),
                        "body_water": weight.get("bodyWater"),
                        "muscle_mass": weight.get("muscleMass"),
                        "bone_mass": weight.get("boneMass")
                    }
                })
        
        # Generate insights
        insights = await llm_service.get_health_insights(metrics)
        
        return insights
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 