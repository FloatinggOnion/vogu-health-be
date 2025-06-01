from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any
import os
from dotenv import load_dotenv
import logging
import json
from pathlib import Path

load_dotenv()

logger = logging.getLogger(__name__)

class GarminService:
    def __init__(self):
        # Initialize data paths
        self.data_path = Path("HealthData")
        self.storage_path = self.data_path / "Storage"
        self.temp_path = self.data_path / "Temp"
        
        # Create directories if they don't exist
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.temp_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize file paths
        self.sleep_file = self.temp_path / 'sleep.json'
        self.weight_file = self.temp_path / 'weight.json'
        self.heart_rate_file = self.temp_path / 'heart_rate.json'
        
        # Storage file paths
        self.storage_files = {
            'sleep': self.storage_path / 'sleep_data.json',
            'weight': self.storage_path / 'weight_data.json',
            'heart_rate': self.storage_path / 'heart_rate_data.json'
        }

    def _load_json_data(self, file_path: Path) -> List[Dict]:
        """Load and parse JSON data from file"""
        try:
            if not file_path.exists():
                logger.warning(f"File not found: {file_path}")
                return []
            
            with open(file_path, 'r') as f:
                data = json.load(f)
                return data if isinstance(data, list) else [data]
        except Exception as e:
            logger.error(f"Error loading JSON data from {file_path}: {str(e)}")
            return []

    def _save_to_storage(self, collection_name: str, data: List[Dict]):
        """Save data to JSON file with proper error handling"""
        try:
            if data:
                storage_file = self.storage_files[collection_name]
                
                # Load existing data if file exists
                existing_data = []
                if storage_file.exists():
                    existing_data = self._load_json_data(storage_file)
                
                # Convert datetime objects to strings for JSON serialization
                for item in data:
                    if isinstance(item, dict):
                        for key, value in item.items():
                            if isinstance(value, datetime):
                                item[key] = value.isoformat()
                
                # Merge new data with existing data, using timestamp as key
                merged_data = {item.get('_id', str(i)): item for i, item in enumerate(existing_data)}
                for item in data:
                    key = item.get('_id', str(len(merged_data)))
                    merged_data[key] = item
                
                # Save merged data
                with open(storage_file, 'w') as f:
                    json.dump(list(merged_data.values()), f, indent=2)
                
                logger.info(f"Successfully saved {len(data)} items to {collection_name}")
        except Exception as e:
            logger.error(f"Error saving data to {collection_name}: {str(e)}")
            raise

    async def get_recent_metrics(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get health metrics from the last N days"""
        try:
            metrics = []
            
            # Load all data first to find the most recent date
            sleep_data = self._load_json_data(self.sleep_file)
            weight_data = self._load_json_data(self.weight_file)
            heart_rate_data = self._load_json_data(self.heart_rate_file)
            
            # Find the most recent date across all data
            all_dates = []
            for data in [sleep_data, weight_data, heart_rate_data]:
                for item in data:
                    if 'startTime' in item:
                        all_dates.append(datetime.fromisoformat(item['startTime'].replace('Z', '+00:00')))
                    elif 'timestamp' in item:
                        all_dates.append(datetime.fromisoformat(item['timestamp'].replace('Z', '+00:00')))
            
            if not all_dates:
                logger.warning("No dates found in the data")
                return []
            
            # Use the most recent date as the reference point
            end_date = max(all_dates)
            start_date = end_date - timedelta(days=days)
            
            # Process sleep data
            for sleep in sleep_data:
                if 'startTime' in sleep:
                    sleep_time = datetime.fromisoformat(sleep['startTime'].replace('Z', '+00:00'))
                    if start_date <= sleep_time <= end_date:
                        metrics.append({
                            "timestamp": sleep_time,
                            "metric_type": "sleep",
                            "value": sleep.get('totalSleepTime', 0),
                            "unit": "minutes",
                            "quality": sleep.get('sleepQuality'),
                            "deep_sleep_minutes": sleep.get('deepSleepTime'),
                            "light_sleep_minutes": sleep.get('lightSleepTime'),
                            "rem_sleep_minutes": sleep.get('remSleepTime'),
                            "awake_minutes": sleep.get('awakeTime'),
                            "sleep_score": sleep.get('sleepScore')
                        })
            
            # Process weight data
            for weight in weight_data:
                if 'timestamp' in weight:
                    weight_time = datetime.fromisoformat(weight['timestamp'].replace('Z', '+00:00'))
                    if start_date <= weight_time <= end_date:
                        metrics.append({
                            "timestamp": weight_time,
                            "metric_type": "weight",
                            "value": weight.get('weight'),
                            "unit": "kg",
                            "bmi": weight.get('bmi'),
                            "body_fat": weight.get('bodyFat'),
                            "body_water": weight.get('bodyWater'),
                            "muscle_mass": weight.get('muscleMass'),
                            "bone_mass": weight.get('boneMass')
                        })
            
            # Process heart rate data
            for hr in heart_rate_data:
                if 'timestamp' in hr:
                    hr_time = datetime.fromisoformat(hr['timestamp'].replace('Z', '+00:00'))
                    if start_date <= hr_time <= end_date:
                        metrics.append({
                            "timestamp": hr_time,
                            "metric_type": "heart_rate",
                            "value": hr.get('heartRate'),
                            "unit": "bpm",
                            "resting_heart_rate": hr.get('restingHeartRate'),
                            "max_heart_rate": hr.get('maxHeartRate'),
                            "min_heart_rate": hr.get('minHeartRate')
                        })
            
            # Save to storage
            self._save_to_storage('sleep', sleep_data)
            self._save_to_storage('weight', weight_data)
            self._save_to_storage('heart_rate', heart_rate_data)
            
            logger.info(f"Found {len(metrics)} metrics between {start_date} and {end_date}")
            return metrics
            
        except Exception as e:
            logger.error(f"Error fetching Garmin data: {str(e)}")
            raise

    async def get_daily_summary(self, date: datetime) -> Dict[str, Any]:
        """Get a summary of health metrics for a specific day"""
        try:
            # Ensure date is timezone-aware
            if date.tzinfo is None:
                date = date.replace(tzinfo=timezone.utc)
            
            end_date = date + timedelta(days=1)
            
            # Load all data from storage
            sleep_data = self._load_json_data(self.storage_files['sleep'])
            weight_data = self._load_json_data(self.storage_files['weight'])
            heart_rate_data = self._load_json_data(self.storage_files['heart_rate'])
            
            # Filter data for the specific day
            daily_sleep = [
                sleep for sleep in sleep_data
                if 'startTime' in sleep and date <= datetime.fromisoformat(sleep['startTime'].replace('Z', '+00:00')) < end_date
            ]
            
            daily_weight = [
                weight for weight in weight_data
                if 'timestamp' in weight and date <= datetime.fromisoformat(weight['timestamp'].replace('Z', '+00:00')) < end_date
            ]
            
            daily_heart_rate = [
                hr for hr in heart_rate_data
                if 'timestamp' in hr and date <= datetime.fromisoformat(hr['timestamp'].replace('Z', '+00:00')) < end_date
            ]
            
            # Calculate averages
            avg_heart_rate = sum(hr.get('heartRate', 0) for hr in daily_heart_rate) / len(daily_heart_rate) if daily_heart_rate else None
            
            return {
                "date": date,
                "sleep": daily_sleep,
                "heart_rate": {
                    "data": daily_heart_rate,
                    "average": avg_heart_rate
                },
                "weight": daily_weight
            }
            
        except Exception as e:
            logger.error(f"Error fetching daily summary: {str(e)}")
            raise

    async def get_health_trends(self, days: int = 30) -> Dict[str, Any]:
        """Get health trends over a period of time"""
        try:
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=days)
            
            # Get all metrics for the period
            metrics = await self.get_recent_metrics(days)
            
            # Calculate trends
            trends = {
                "sleep": {
                    "average_duration": 0,
                    "average_quality": 0,
                    "best_day": None,
                    "worst_day": None
                },
                "heart_rate": {
                    "average": 0,
                    "highest": None,
                    "lowest": None
                },
                "weight": {
                    "average": 0,
                    "trend": []
                }
            }
            
            # Process metrics to calculate trends
            for metric in metrics:
                if metric["metric_type"] == "sleep":
                    trends["sleep"]["average_duration"] += metric["value"]
                    if "quality" in metric:
                        trends["sleep"]["average_quality"] += metric["quality"]
                
                elif metric["metric_type"] == "heart_rate":
                    trends["heart_rate"]["average"] += metric["value"]
                    # Update highest and lowest only if we have a value
                    if trends["heart_rate"]["highest"] is None or metric["value"] > trends["heart_rate"]["highest"]:
                        trends["heart_rate"]["highest"] = metric["value"]
                    if trends["heart_rate"]["lowest"] is None or metric["value"] < trends["heart_rate"]["lowest"]:
                        trends["heart_rate"]["lowest"] = metric["value"]
                
                elif metric["metric_type"] == "weight":
                    trends["weight"]["average"] += metric["value"]
                    trends["weight"]["trend"].append({
                        "date": metric["timestamp"].isoformat(),
                        "weight": metric["value"]
                    })
            
            # Calculate averages
            days_count = len(set(m["timestamp"].date() for m in metrics))
            if days_count > 0:
                trends["sleep"]["average_duration"] /= days_count
                trends["sleep"]["average_quality"] /= days_count
                heart_rate_count = len([m for m in metrics if m["metric_type"] == "heart_rate"])
                if heart_rate_count > 0:
                    trends["heart_rate"]["average"] /= heart_rate_count
                weight_count = len([m for m in metrics if m["metric_type"] == "weight"])
                if weight_count > 0:
                    trends["weight"]["average"] /= weight_count
            
            return trends
            
        except Exception as e:
            logger.error(f"Error calculating health trends: {str(e)}")
            raise 