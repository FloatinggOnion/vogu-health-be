from datetime import datetime, timedelta
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
                user_id TEXT NOT NULL,
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
                user_id TEXT NOT NULL,
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
                user_id TEXT NOT NULL,
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
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sleep_user_time ON sleep(user_id, start_time)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_hr_user_time ON heart_rate(user_id, timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_weight_user_time ON weight(user_id, timestamp)')
            
            conn.commit()
    
    async def store_sleep_data(self, data: SleepData) -> HealthDataResponse:
        """Store sleep data in the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                INSERT INTO sleep (
                    user_id, start_time, end_time, quality,
                    deep_sleep, light_sleep, rem_sleep, awake_time,
                    source
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    data.user_id,
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
                    user_id, timestamp, value,
                    resting_rate, activity_type, source
                ) VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    data.user_id,
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
                    user_id, timestamp, value, bmi,
                    body_fat, muscle_mass, water_percentage,
                    bone_mass, source
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    data.user_id,
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
        user_id: str,
        metric_type: MetricType,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """Get recent health data for a specific metric type"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                if metric_type == MetricType.SLEEP:
                    cursor.execute('''
                    SELECT * FROM sleep
                    WHERE user_id = ? AND start_time >= ?
                    ORDER BY start_time DESC
                    ''', (user_id, start_date.isoformat()))
                    
                    return [dict(row) for row in cursor.fetchall()]
                
                elif metric_type == MetricType.HEART_RATE:
                    cursor.execute('''
                    SELECT * FROM heart_rate
                    WHERE user_id = ? AND timestamp >= ?
                    ORDER BY timestamp DESC
                    ''', (user_id, start_date.isoformat()))
                    
                    return [dict(row) for row in cursor.fetchall()]
                
                elif metric_type == MetricType.WEIGHT:
                    cursor.execute('''
                    SELECT * FROM weight
                    WHERE user_id = ? AND timestamp >= ?
                    ORDER BY timestamp DESC
                    ''', (user_id, start_date.isoformat()))
                    
                    return [dict(row) for row in cursor.fetchall()]
                
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
        user_id: str,
        date: datetime
    ) -> Dict[str, Any]:
        """Get a summary of health metrics for a specific day"""
        try:
            end_date = date + timedelta(days=1)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Get sleep data
                cursor.execute('''
                SELECT * FROM sleep
                WHERE user_id = ? AND start_time >= ? AND start_time < ?
                ''', (user_id, date.isoformat(), end_date.isoformat()))
                sleep_data = [dict(row) for row in cursor.fetchall()]
                
                # Get heart rate data
                cursor.execute('''
                SELECT * FROM heart_rate
                WHERE user_id = ? AND timestamp >= ? AND timestamp < ?
                ''', (user_id, date.isoformat(), end_date.isoformat()))
                heart_rate_data = [dict(row) for row in cursor.fetchall()]
                
                # Get weight data
                cursor.execute('''
                SELECT * FROM weight
                WHERE user_id = ? AND timestamp >= ? AND timestamp < ?
                ''', (user_id, date.isoformat(), end_date.isoformat()))
                weight_data = [dict(row) for row in cursor.fetchall()]
                
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