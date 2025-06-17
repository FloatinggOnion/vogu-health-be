from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
import json
import logging
from pathlib import Path
import sqlite3
from .models import (
    MetricType, SleepData, HeartRateData, WeightData,
    HealthDataResponse, HealthDataError
)

logger = logging.getLogger(__name__)

class HealthDataService:
    def __init__(self, db_path: str = "HealthData/health_data.db"):
        """Initialize the health data service"""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Initialize the SQLite database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create sleep table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS sleep (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP NOT NULL,
                quality INTEGER NOT NULL,
                deep_sleep INTEGER NOT NULL,
                light_sleep INTEGER NOT NULL,
                rem_sleep INTEGER NOT NULL,
                awake_time INTEGER NOT NULL,
                source TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # Create heart rate table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS heart_rate (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP NOT NULL,
                value INTEGER NOT NULL,
                resting_rate INTEGER,
                activity_type TEXT,
                source TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # Create weight table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS weight (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP NOT NULL,
                value REAL NOT NULL,
                bmi REAL,
                body_fat REAL,
                muscle_mass REAL,
                water_percentage REAL,
                bone_mass REAL,
                source TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # Create indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sleep_time ON sleep(start_time)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_hr_time ON heart_rate(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_weight_time ON weight(timestamp)')
            
            conn.commit()
    
    async def store_sleep_data(self, data: SleepData) -> HealthDataResponse:
        """Store sleep data in the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                INSERT INTO sleep (
                    start_time, end_time, quality,
                    deep_sleep, light_sleep, rem_sleep, awake_time,
                    source
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    data.start_time.isoformat(),
                    data.end_time.isoformat(),
                    data.quality,
                    data.phases.deep,
                    data.phases.light,
                    data.phases.rem,
                    data.phases.awake,
                    data.source
                ))
                conn.commit()
            
            return HealthDataResponse(
                status="success",
                message="Sleep data stored successfully"
            )
        except Exception as e:
            logger.error(f"Error storing sleep data: {str(e)}")
            raise HealthDataError(
                error="Failed to store sleep data",
                details={"error": str(e)}
            )
    
    async def store_heart_rate_data(self, data: HeartRateData) -> HealthDataResponse:
        """Store heart rate data in the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                INSERT INTO heart_rate (
                    timestamp, value,
                    resting_rate, activity_type, source
                ) VALUES (?, ?, ?, ?, ?)
                ''', (
                    data.timestamp.isoformat(),
                    data.value,
                    data.resting_rate,
                    data.activity_type,
                    data.source
                ))
                conn.commit()
            
            return HealthDataResponse(
                status="success",
                message="Heart rate data stored successfully"
            )
        except Exception as e:
            logger.error(f"Error storing heart rate data: {str(e)}")
            raise HealthDataError(
                error="Failed to store heart rate data",
                details={"error": str(e)}
            )
    
    async def store_weight_data(self, data: WeightData) -> HealthDataResponse:
        """Store weight data in the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                INSERT INTO weight (
                    timestamp, value, bmi,
                    body_fat, muscle_mass, water_percentage,
                    bone_mass, source
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    data.timestamp.isoformat(),
                    data.value,
                    data.bmi,
                    data.body_composition.body_fat if data.body_composition else None,
                    data.body_composition.muscle_mass if data.body_composition else None,
                    data.body_composition.water_percentage if data.body_composition else None,
                    data.body_composition.bone_mass if data.body_composition else None,
                    data.source
                ))
                conn.commit()
            
            return HealthDataResponse(
                status="success",
                message="Weight data stored successfully"
            )
        except Exception as e:
            logger.error(f"Error storing weight data: {str(e)}")
            raise HealthDataError(
                error="Failed to store weight data",
                details={"error": str(e)}
            )
    
    async def get_recent_data(
        self,
        metric_type: MetricType,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """Get recent health data for a specific metric type"""
        try:
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=days)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                if metric_type == MetricType.SLEEP:
                    cursor.execute('''
                    SELECT 
                        id,
                        start_time,
                        end_time,
                        quality,
                        deep_sleep,
                        light_sleep,
                        rem_sleep,
                        awake_time,
                        source,
                        created_at
                    FROM sleep
                    WHERE start_time >= ?
                    ORDER BY start_time DESC
                    ''', (start_date.isoformat(),))
                    
                    rows = cursor.fetchall()
                    return [{
                        "id": row["id"],
                        "start_time": row["start_time"],
                        "end_time": row["end_time"],
                        "quality": row["quality"],
                        "phases": {
                            "deep": row["deep_sleep"],
                            "light": row["light_sleep"],
                            "rem": row["rem_sleep"],
                            "awake": row["awake_time"]
                        },
                        "source": row["source"],
                        "created_at": row["created_at"]
                    } for row in rows]
                
                elif metric_type == MetricType.HEART_RATE:
                    cursor.execute('''
                    SELECT 
                        id,
                        timestamp,
                        value,
                        resting_rate,
                        activity_type,
                        source,
                        created_at
                    FROM heart_rate
                    WHERE timestamp >= ?
                    ORDER BY timestamp DESC
                    ''', (start_date.isoformat(),))
                    
                    rows = cursor.fetchall()
                    return [{
                        "id": row["id"],
                        "timestamp": row["timestamp"],
                        "value": row["value"],
                        "resting_rate": row["resting_rate"],
                        "activity_type": row["activity_type"],
                        "source": row["source"],
                        "created_at": row["created_at"]
                    } for row in rows]
                
                elif metric_type == MetricType.WEIGHT:
                    cursor.execute('''
                    SELECT 
                        id,
                        timestamp,
                        value,
                        bmi,
                        body_fat,
                        muscle_mass,
                        water_percentage,
                        bone_mass,
                        source,
                        created_at
                    FROM weight
                    WHERE timestamp >= ?
                    ORDER BY timestamp DESC
                    ''', (start_date.isoformat(),))
                    
                    rows = cursor.fetchall()
                    return [{
                        "id": row["id"],
                        "timestamp": row["timestamp"],
                        "value": row["value"],
                        "bmi": row["bmi"],
                        "body_composition": {
                            "body_fat": row["body_fat"],
                            "muscle_mass": row["muscle_mass"],
                            "water_percentage": row["water_percentage"],
                            "bone_mass": row["bone_mass"]
                        } if row["body_fat"] is not None else None,
                        "source": row["source"],
                        "created_at": row["created_at"]
                    } for row in rows]
                
                else:
                    raise ValueError(f"Unsupported metric type: {metric_type}")
        
        except Exception as e:
            logger.error(f"Error retrieving {metric_type} data: {str(e)}")
            raise HealthDataError(
                error=f"Failed to retrieve {metric_type} data",
                details={"error": str(e)}
            )
    
    async def get_daily_summary(
        self,
        date: datetime
    ) -> Dict[str, Any]:
        """Get a summary of health metrics for a specific day"""
        try:
            # Ensure date is UTC-aware
            if date.tzinfo is None:
                date = date.replace(tzinfo=timezone.utc)
            end_date = date + timedelta(days=1)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Get sleep data
                cursor.execute('''
                SELECT 
                    id,
                    start_time,
                    end_time,
                    quality,
                    deep_sleep,
                    light_sleep,
                    rem_sleep,
                    awake_time,
                    source,
                    created_at
                FROM sleep
                WHERE start_time >= ? AND start_time < ?
                ''', (date.isoformat(), end_date.isoformat()))
                sleep_rows = cursor.fetchall()
                sleep_data = [{
                    "id": row["id"],
                    "start_time": row["start_time"],
                    "end_time": row["end_time"],
                    "quality": row["quality"],
                    "phases": {
                        "deep": row["deep_sleep"],
                        "light": row["light_sleep"],
                        "rem": row["rem_sleep"],
                        "awake": row["awake_time"]
                    },
                    "source": row["source"],
                    "created_at": row["created_at"]
                } for row in sleep_rows]
                
                # Get heart rate data
                cursor.execute('''
                SELECT 
                    id,
                    timestamp,
                    value,
                    resting_rate,
                    activity_type,
                    source,
                    created_at
                FROM heart_rate
                WHERE timestamp >= ? AND timestamp < ?
                ''', (date.isoformat(), end_date.isoformat()))
                hr_rows = cursor.fetchall()
                heart_rate_data = [{
                    "id": row["id"],
                    "timestamp": row["timestamp"],
                    "value": row["value"],
                    "resting_rate": row["resting_rate"],
                    "activity_type": row["activity_type"],
                    "source": row["source"],
                    "created_at": row["created_at"]
                } for row in hr_rows]
                
                # Get weight data
                cursor.execute('''
                SELECT 
                    id,
                    timestamp,
                    value,
                    bmi,
                    body_fat,
                    muscle_mass,
                    water_percentage,
                    bone_mass,
                    source,
                    created_at
                FROM weight
                WHERE timestamp >= ? AND timestamp < ?
                ''', (date.isoformat(), end_date.isoformat()))
                weight_rows = cursor.fetchall()
                weight_data = [{
                    "id": row["id"],
                    "timestamp": row["timestamp"],
                    "value": row["value"],
                    "bmi": row["bmi"],
                    "body_composition": {
                        "body_fat": row["body_fat"],
                        "muscle_mass": row["muscle_mass"],
                        "water_percentage": row["water_percentage"],
                        "bone_mass": row["bone_mass"]
                    } if row["body_fat"] is not None else None,
                    "source": row["source"],
                    "created_at": row["created_at"]
                } for row in weight_rows]
                
                return {
                    "date": date.isoformat(),
                    "sleep": sleep_data,
                    "heart_rate": heart_rate_data,
                    "weight": weight_data
                }
        
        except Exception as e:
            logger.error(f"Error retrieving daily summary: {str(e)}")
            raise HealthDataError(
                error="Failed to retrieve daily summary",
                details={"error": str(e)}
            ) 