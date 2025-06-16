from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, validator
from enum import Enum

class MetricType(str, Enum):
    SLEEP = "sleep"
    HEART_RATE = "heart_rate"
    WEIGHT = "weight"

class SleepPhase(BaseModel):
    deep: int = Field(..., description="Deep sleep duration in minutes")
    light: int = Field(..., description="Light sleep duration in minutes")
    rem: int = Field(..., description="REM sleep duration in minutes")
    awake: int = Field(..., description="Awake duration in minutes")

    @validator('deep', 'light', 'rem', 'awake')
    def validate_duration(cls, v):
        if v < 0:
            raise ValueError("Duration cannot be negative")
        return v

class SleepData(BaseModel):
    start_time: datetime = Field(..., description="Sleep start time")
    end_time: datetime = Field(..., description="Sleep end time")
    quality: int = Field(..., ge=0, le=100, description="Sleep quality score (0-100)")
    phases: SleepPhase = Field(..., description="Sleep phases")
    source: str = Field(..., description="Data source (e.g., 'mobile_app', 'manual')")
    
    @validator('end_time')
    def validate_times(cls, v, values):
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError("end_time must be after start_time")
        return v

class HeartRateData(BaseModel):
    timestamp: datetime = Field(..., description="Measurement timestamp")
    value: int = Field(..., ge=30, le=220, description="Heart rate in BPM")
    resting_rate: Optional[int] = Field(None, ge=30, le=100, description="Resting heart rate in BPM")
    activity_type: Optional[str] = Field(None, description="Type of activity during measurement")
    source: str = Field(..., description="Data source")

class BodyComposition(BaseModel):
    body_fat: float = Field(..., ge=0, le=100, description="Body fat percentage")
    muscle_mass: float = Field(..., ge=0, le=100, description="Muscle mass percentage")
    water_percentage: float = Field(..., ge=0, le=100, description="Water percentage")
    bone_mass: Optional[float] = Field(None, ge=0, description="Bone mass in kg")

class WeightData(BaseModel):
    timestamp: datetime = Field(..., description="Measurement timestamp")
    value: float = Field(..., gt=0, description="Weight in kg")
    bmi: Optional[float] = Field(None, gt=0, description="Body Mass Index")
    body_composition: Optional[BodyComposition] = Field(None, description="Body composition metrics")
    source: str = Field(..., description="Data source")

class HealthDataResponse(BaseModel):
    status: str = Field(..., description="Response status")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")
    message: Optional[str] = Field(None, description="Response message")
    insights: Optional[Dict[str, Any]] = Field(None, description="AI-generated insights")

class HealthDataError(Exception):
    """Custom exception for health data errors"""
    def __init__(self, error: str, details: Optional[Dict[str, Any]] = None):
        self.error = error
        self.details = details
        super().__init__(self.error)
    
    def dict(self):
        return {
            "status": "error",
            "error": self.error,
            "details": self.details
        } 