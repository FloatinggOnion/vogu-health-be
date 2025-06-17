from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta, timezone
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

@app.get("/")
def hello_world():
    return {"message": "Hello World"}

@app.post("/api/v1/health-data/sleep")
async def submit_sleep_data(
    data: SleepData
) -> HealthDataResponse:
    """Submit sleep data"""
    try:
        return await health_data_service.store_sleep_data(data)
    except HealthDataError as e:
        raise HTTPException(status_code=400, detail=e.dict())
    except Exception as e:
        logger.error(f"Error submitting sleep data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/health-data/heart-rate")
async def submit_heart_rate_data(
    data: HeartRateData
) -> HealthDataResponse:
    """Submit heart rate data"""
    try:
        return await health_data_service.store_heart_rate_data(data)
    except HealthDataError as e:
        raise HTTPException(status_code=400, detail=e.dict())
    except Exception as e:
        logger.error(f"Error submitting heart rate data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/health-data/weight")
async def submit_weight_data(
    data: WeightData
) -> HealthDataResponse:
    """Submit weight data"""
    try:
        return await health_data_service.store_weight_data(data)
    except HealthDataError as e:
        raise HTTPException(status_code=400, detail=e.dict())
    except Exception as e:
        logger.error(f"Error submitting weight data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/health-data/{metric_type}")
async def get_health_data(
    metric_type: MetricType,
    days: int = Query(7, ge=1, le=30)
) -> Dict[str, Any]:
    """Get health data for a specific metric type"""
    try:
        data = await health_data_service.get_recent_data(metric_type, days)
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
    date: datetime
) -> Dict[str, Any]:
    """Get daily health summary"""
    try:
        # Ensure date is UTC-aware
        if date.tzinfo is None:
            date = date.replace(tzinfo=timezone.utc)
        summary = await health_data_service.get_daily_summary(date)
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
    days: int = Query(7, ge=1, le=30)
) -> Dict[str, Any]:
    """Get AI-powered health insights for recent data"""
    try:
        # Get data for all metric types
        metrics = []
        for metric_type in MetricType:
            try:
                data = await health_data_service.get_recent_data(metric_type, days)
                if not data:
                    logger.info(f"No {metric_type.value} data available for the last {days} days")
                    continue

                if metric_type == MetricType.SLEEP:
                    for sleep in data:
                        try:
                            if not isinstance(sleep.get("phases"), dict):
                                logger.warning(f"Invalid sleep phases data: {sleep}")
                                continue
                            
                            phases = sleep["phases"]
                            total_sleep = phases.get("deep", 0) + phases.get("light", 0) + phases.get("rem", 0)
                            metrics.append({
                                "metric_type": metric_type.value,
                                "totalSleepTime": total_sleep,
                                "sleepQuality": sleep.get("quality", 0),
                                "deepSleepTime": phases.get("deep", 0),
                                "remSleepTime": phases.get("rem", 0)
                            })
                        except Exception as e:
                            logger.error(f"Error processing sleep data: {str(e)}")
                            continue

                elif metric_type == MetricType.HEART_RATE:
                    for hr in data:
                        try:
                            metrics.append({
                                "metric_type": metric_type.value,
                                "heartRate": hr.get("value", 0),
                                "restingHeartRate": hr.get("resting_rate", 0),
                                "activityType": hr.get("activity_type", "unknown")
                            })
                        except Exception as e:
                            logger.error(f"Error processing heart rate data: {str(e)}")
                            continue

                elif metric_type == MetricType.WEIGHT:
                    for weight in data:
                        try:
                            body_comp = weight.get("body_composition", {}) or {}
                            metrics.append({
                                "metric_type": metric_type.value,
                                "weight": weight.get("value", 0),
                                "bmi": weight.get("bmi", 0),
                                "bodyFat": body_comp.get("body_fat", 0),
                                "muscleMass": body_comp.get("muscle_mass", 0),
                                "waterPercentage": body_comp.get("water_percentage", 0)
                            })
                        except Exception as e:
                            logger.error(f"Error processing weight data: {str(e)}")
                            continue

            except Exception as e:
                logger.error(f"Error retrieving {metric_type.value} data: {str(e)}")
                continue

        if not metrics:
            logger.info("No health data available for insights")
            return {
                "status": "success",
                "insights": {
                    "summary": "No health data available for the selected period. Start tracking your health metrics to get personalized insights.",
                    "status": "fair",
                    "highlights": [
                        "Ready to start tracking your health",
                        "Connect your device to begin monitoring"
                    ],
                    "recommendations": [
                        "Set up your health tracking device",
                        "Start recording your daily health metrics"
                    ],
                    "next_steps": "Begin tracking your health metrics today"
                }
            }

        # Generate insights using LLM
        insights = await llm_service.get_health_insights(metrics)
        return {
            "status": "success",
            "insights": insights
        }
    except Exception as e:
        logger.error(f"Error generating insights: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate insights: {str(e)}"
        )

@app.get("/api/v1/insights/daily/{date}")
async def get_daily_insights(
    date: datetime
) -> Dict[str, Any]:
    """Get AI-powered health insights for a specific day"""
    try:
        # Ensure date is UTC-aware
        if date.tzinfo is None:
            date = date.replace(tzinfo=timezone.utc)
        
        # Get daily summary
        summary = await health_data_service.get_daily_summary(date)
        if not summary:
            logger.info(f"No health data available for {date.isoformat()}")
            return {
                "status": "success",
                "insights": {
                    "summary": f"No health data available for {date.date()}. Start tracking your health metrics to get personalized insights.",
                    "status": "fair",
                    "highlights": [
                        "Ready to start tracking your health",
                        "Connect your device to begin monitoring"
                    ],
                    "recommendations": [
                        "Set up your health tracking device",
                        "Start recording your daily health metrics"
                    ],
                    "next_steps": "Begin tracking your health metrics today"
                }
            }
        
        # Convert summary to metrics format
        metrics = []
        
        # Process sleep data
        for sleep in summary.get("sleep", []):
            try:
                if not isinstance(sleep.get("phases"), dict):
                    logger.warning(f"Invalid sleep phases data: {sleep}")
                    continue
                
                phases = sleep["phases"]
                total_sleep = phases.get("deep", 0) + phases.get("light", 0) + phases.get("rem", 0)
                metrics.append({
                    "metric_type": MetricType.SLEEP.value,
                    "totalSleepTime": total_sleep,
                    "sleepQuality": sleep.get("quality", 0),
                    "deepSleepTime": phases.get("deep", 0),
                    "remSleepTime": phases.get("rem", 0)
                })
            except Exception as e:
                logger.error(f"Error processing sleep data: {str(e)}")
                continue
        
        # Process heart rate data
        for hr in summary.get("heart_rate", []):
            try:
                metrics.append({
                    "metric_type": MetricType.HEART_RATE.value,
                    "heartRate": hr.get("value", 0),
                    "restingHeartRate": hr.get("resting_rate", 0),
                    "activityType": hr.get("activity_type", "unknown")
                })
            except Exception as e:
                logger.error(f"Error processing heart rate data: {str(e)}")
                continue
        
        # Process weight data
        for weight in summary.get("weight", []):
            try:
                body_comp = weight.get("body_composition", {}) or {}
                metrics.append({
                    "metric_type": MetricType.WEIGHT.value,
                    "weight": weight.get("value", 0),
                    "bmi": weight.get("bmi", 0),
                    "bodyFat": body_comp.get("body_fat", 0),
                    "muscleMass": body_comp.get("muscle_mass", 0),
                    "waterPercentage": body_comp.get("water_percentage", 0)
                })
            except Exception as e:
                logger.error(f"Error processing weight data: {str(e)}")
                continue
        
        if not metrics:
            logger.info(f"No valid health data available for {date.isoformat()}")
            return {
                "status": "success",
                "insights": {
                    "summary": f"No valid health data available for {date.date()}. Please ensure your health tracking device is properly connected.",
                    "status": "fair",
                    "highlights": [
                        "Device connection needed",
                        "Health tracking ready to start"
                    ],
                    "recommendations": [
                        "Check your device connection",
                        "Verify your health tracking settings"
                    ],
                    "next_steps": "Connect your health tracking device"
                }
            }
        
        # Generate insights
        insights = await llm_service.get_health_insights(metrics)
        return {
            "status": "success",
            "insights": insights
        }
    except Exception as e:
        logger.error(f"Error generating daily insights: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate daily insights: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 