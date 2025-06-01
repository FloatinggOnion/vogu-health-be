#!/usr/bin/env python3
from datetime import datetime, timedelta, timezone
import json
import random
import numpy as np
from pathlib import Path
import logging
from typing import List, Dict, Any
import math

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HealthDataGenerator:
    def __init__(self, start_date: datetime = None, days: int = 30):
        """Initialize the health data generator"""
        self.start_date = start_date or (datetime.now(timezone.utc) - timedelta(days=days))
        self.days = days
        
        # Base metrics (can be adjusted for different profiles)
        self.base_metrics = {
            'sleep': {
                'total_sleep': 420,  # 7 hours in minutes
                'deep_sleep_ratio': 0.2,  # 20% of total sleep
                'rem_sleep_ratio': 0.25,  # 25% of total sleep
                'light_sleep_ratio': 0.5,  # 50% of total sleep
                'awake_ratio': 0.05,  # 5% of total sleep
                'quality_base': 75,  # Base sleep quality score
                'score_base': 80,  # Base sleep score
            },
            'heart_rate': {
                'resting': 60,  # Base resting heart rate
                'max': 180,  # Maximum heart rate
                'min': 45,  # Minimum heart rate
                'variation': 15,  # Daily variation
            },
            'weight': {
                'base': 70.0,  # Base weight in kg
                'trend': -0.1,  # Weight trend per day (negative for weight loss)
                'variation': 0.3,  # Daily variation
            }
        }
        
        # Create output directory
        self.output_dir = Path("HealthData/Temp")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _generate_sleep_metrics(self, date: datetime, previous_quality: float = None) -> Dict:
        """Generate realistic sleep metrics for a given date"""
        # Add some randomness to total sleep time (±30 minutes)
        total_sleep = self.base_metrics['sleep']['total_sleep'] + random.randint(-30, 30)
        
        # Calculate sleep phases
        deep_sleep = int(total_sleep * self.base_metrics['sleep']['deep_sleep_ratio'])
        rem_sleep = int(total_sleep * self.base_metrics['sleep']['rem_sleep_ratio'])
        light_sleep = int(total_sleep * self.base_metrics['sleep']['light_sleep_ratio'])
        awake_time = int(total_sleep * self.base_metrics['sleep']['awake_ratio'])
        
        # Adjust for total
        remaining = total_sleep - (deep_sleep + rem_sleep + light_sleep + awake_time)
        light_sleep += remaining  # Add any remainder to light sleep
        
        # Generate sleep quality (correlated with previous day)
        if previous_quality is None:
            quality = self.base_metrics['sleep']['quality_base']
        else:
            # Quality tends to stay similar but can change
            quality = previous_quality + random.randint(-10, 10)
            quality = max(0, min(100, quality))  # Clamp between 0-100
        
        # Calculate sleep score based on quality and duration
        duration_score = min(100, (total_sleep / 480) * 100)  # 8 hours = 100
        score = int((quality * 0.7 + duration_score * 0.3) + random.randint(-5, 5))
        score = max(0, min(100, score))
        
        # Generate sleep times
        sleep_time = date.replace(hour=23, minute=random.randint(0, 30))
        wake_time = sleep_time + timedelta(minutes=total_sleep)
        
        return {
            "startTime": sleep_time.isoformat(),
            "endTime": wake_time.isoformat(),
            "totalSleepTime": total_sleep,
            "deepSleepTime": deep_sleep,
            "lightSleepTime": light_sleep,
            "remSleepTime": rem_sleep,
            "awakeTime": awake_time,
            "sleepQuality": quality,
            "sleepScore": score
        }

    def _generate_heart_rate_metrics(self, date: datetime, sleep_quality: float) -> List[Dict]:
        """Generate realistic heart rate metrics for a given date"""
        # Base resting heart rate varies with sleep quality
        resting_hr = self.base_metrics['heart_rate']['resting']
        if sleep_quality < 50:
            resting_hr += random.randint(2, 5)  # Higher resting HR with poor sleep
        elif sleep_quality > 80:
            resting_hr -= random.randint(1, 3)  # Lower resting HR with good sleep
        
        # Generate 24 hours of heart rate data (one reading every 15 minutes)
        heart_rates = []
        for hour in range(24):
            for minute in range(0, 60, 15):
                timestamp = date.replace(hour=hour, minute=minute)
                
                # Heart rate varies throughout the day
                if 2 <= hour <= 5:  # Deep sleep hours
                    hr = resting_hr + random.randint(-5, 5)
                elif 6 <= hour <= 8:  # Morning hours
                    hr = resting_hr + random.randint(10, 20)
                elif 12 <= hour <= 14:  # Afternoon
                    hr = resting_hr + random.randint(5, 15)
                elif 18 <= hour <= 20:  # Evening
                    hr = resting_hr + random.randint(15, 25)
                else:  # Other hours
                    hr = resting_hr + random.randint(0, 10)
                
                # Add some random variation
                hr += random.randint(-3, 3)
                hr = max(self.base_metrics['heart_rate']['min'],
                        min(self.base_metrics['heart_rate']['max'], hr))
                
                heart_rates.append({
                    "timestamp": timestamp.isoformat(),
                    "heartRate": hr,
                    "restingHeartRate": resting_hr,
                    "maxHeartRate": self.base_metrics['heart_rate']['max'],
                    "minHeartRate": self.base_metrics['heart_rate']['min']
                })
        
        return heart_rates

    def _generate_weight_metrics(self, date: datetime, previous_weight: float = None) -> Dict:
        """Generate realistic weight metrics for a given date"""
        if previous_weight is None:
            weight = self.base_metrics['weight']['base']
        else:
            # Weight follows a trend with daily variation
            weight = previous_weight + self.base_metrics['weight']['trend']
            weight += random.uniform(-self.base_metrics['weight']['variation'],
                                  self.base_metrics['weight']['variation'])
        
        # Calculate BMI (assuming height of 1.75m)
        height = 1.75
        bmi = weight / (height * height)
        
        # Calculate body composition metrics
        body_fat = 20 + (bmi - 22) * 2 + random.uniform(-1, 1)  # Rough estimate
        body_water = 60 - (body_fat * 0.5) + random.uniform(-1, 1)  # Rough estimate
        muscle_mass = (weight * 0.4) + random.uniform(-1, 1)  # Rough estimate
        bone_mass = (weight * 0.15) + random.uniform(-0.1, 0.1)  # Rough estimate
        
        return {
            "timestamp": date.replace(hour=8, minute=0).isoformat(),  # Morning weight
            "weight": round(weight, 1),
            "bmi": round(bmi, 1),
            "bodyFat": round(body_fat, 1),
            "bodyWater": round(body_water, 1),
            "muscleMass": round(muscle_mass, 1),
            "boneMass": round(bone_mass, 1)
        }

    def generate_data(self) -> None:
        """Generate and save all health metrics data"""
        try:
            sleep_data = []
            heart_rate_data = []
            weight_data = []
            
            previous_quality = None
            previous_weight = None
            
            # Generate data for each day
            for day in range(self.days):
                current_date = self.start_date + timedelta(days=day)
                
                # Generate sleep data
                sleep_metrics = self._generate_sleep_metrics(current_date, previous_quality)
                sleep_data.append(sleep_metrics)
                previous_quality = sleep_metrics['sleepQuality']
                
                # Generate heart rate data
                heart_rate_data.extend(self._generate_heart_rate_metrics(current_date, previous_quality))
                
                # Generate weight data
                weight_metrics = self._generate_weight_metrics(current_date, previous_weight)
                weight_data.append(weight_metrics)
                previous_weight = weight_metrics['weight']
            
            # Save data to files
            with open(self.output_dir / 'sleep.json', 'w') as f:
                json.dump(sleep_data, f, indent=2)
            
            with open(self.output_dir / 'heart_rate.json', 'w') as f:
                json.dump(heart_rate_data, f, indent=2)
            
            with open(self.output_dir / 'weight.json', 'w') as f:
                json.dump(weight_data, f, indent=2)
            
            logger.info(f"Generated {len(sleep_data)} days of health data")
            logger.info(f"Sleep data: {len(sleep_data)} records")
            logger.info(f"Heart rate data: {len(heart_rate_data)} records")
            logger.info(f"Weight data: {len(weight_data)} records")
            
        except Exception as e:
            logger.error(f"Error generating health data: {str(e)}")
            raise

def main():
    """Main function to generate health data"""
    # Generate 30 days of data starting from 30 days ago
    generator = HealthDataGenerator(days=30)
    generator.generate_data()

if __name__ == "__main__":
    main() 