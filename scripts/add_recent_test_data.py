#!/usr/bin/env python3
"""
Script to add recent test data for sleep, heart rate, and weight over the last 7 days.
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
import os
import random

# Add the parent directory to the path so we can import our services
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.health_data.service import HealthDataService
from services.health_data.models import SleepData, HeartRateData, WeightData, SleepPhase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestDataGenerator:
    def __init__(self):
        self.health_service = HealthDataService()
    
    def generate_sleep_data(self, date: datetime) -> SleepData:
        """Generate realistic sleep data for a given date"""
        # Sleep from 10 PM to 6 AM (8 hours)
        start_time = date.replace(hour=22, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(hours=8)
        
        # Generate realistic sleep phases (total should be ~480 minutes)
        total_sleep = 480
        deep_sleep = random.randint(60, 120)  # 1-2 hours
        rem_sleep = random.randint(90, 150)   # 1.5-2.5 hours
        light_sleep = total_sleep - deep_sleep - rem_sleep
        awake_time = random.randint(10, 30)   # 10-30 minutes awake
        
        quality = random.randint(70, 95)  # Sleep quality 70-95
        
        return SleepData(
            start_time=start_time,
            end_time=end_time,
            quality=quality,
            phases=SleepPhase(
                deep=deep_sleep,
                light=light_sleep,
                rem=rem_sleep,
                awake=awake_time
            ),
            source="test_data"
        )
    
    def generate_heart_rate_data(self, date: datetime) -> list[HeartRateData]:
        """Generate heart rate data for a given date (multiple readings)"""
        heart_rate_data = []
        
        # Generate 24 readings (one per hour)
        for hour in range(24):
            timestamp = date.replace(hour=hour, minute=random.randint(0, 59), second=0, microsecond=0)
            
            # Different heart rates based on time of day
            if 6 <= hour <= 8:  # Morning
                value = random.randint(65, 85)
            elif 12 <= hour <= 14:  # Afternoon
                value = random.randint(70, 90)
            elif 18 <= hour <= 20:  # Evening
                value = random.randint(75, 95)
            else:  # Night
                value = random.randint(55, 75)
            
            resting_rate = random.randint(50, 65)
            activity_type = random.choice([None, "resting", "walking", "sleeping"])
            
            heart_rate_data.append(HeartRateData(
                timestamp=timestamp,
                value=value,
                resting_rate=resting_rate,
                activity_type=activity_type,
                source="test_data"
            ))
        
        return heart_rate_data
    
    def generate_weight_data(self, date: datetime) -> WeightData:
        """Generate weight data for a given date"""
        # Base weight around 70kg with small daily variations
        base_weight = 70.0
        daily_variation = random.uniform(-0.5, 0.5)
        weight = base_weight + daily_variation
        
        # Calculate BMI (assuming height of 1.75m)
        height = 1.75
        bmi = weight / (height * height)
        
        timestamp = date.replace(hour=8, minute=0, second=0, microsecond=0)
        
        return WeightData(
            timestamp=timestamp,
            value=weight,
            bmi=bmi,
            body_composition=None,  # Keep it simple for test data
            source="test_data"
        )
    
    async def add_test_data_for_date(self, date: datetime):
        """Add test data for a specific date"""
        try:
            # Add sleep data
            sleep_data = self.generate_sleep_data(date)
            await self.health_service.store_sleep_data(sleep_data)
            logger.info(f"Added sleep data for {date.date()}")
            
            # Add heart rate data (multiple readings)
            heart_rate_data_list = self.generate_heart_rate_data(date)
            for hr_data in heart_rate_data_list:
                await self.health_service.store_heart_rate_data(hr_data)
            logger.info(f"Added {len(heart_rate_data_list)} heart rate readings for {date.date()}")
            
            # Add weight data
            weight_data = self.generate_weight_data(date)
            await self.health_service.store_weight_data(weight_data)
            logger.info(f"Added weight data for {date.date()}")
            
        except Exception as e:
            logger.error(f"Error adding test data for {date.date()}: {e}")
    
    async def add_recent_test_data(self, days: int = 7):
        """Add test data for the last N days"""
        logger.info(f"Adding test data for the last {days} days...")
        
        end_date = datetime.now(timezone.utc)
        
        for i in range(days):
            date = end_date - timedelta(days=i)
            await self.add_test_data_for_date(date)
        
        logger.info(f"Successfully added test data for {days} days")

async def main():
    """Main function to run the test data generation"""
    generator = TestDataGenerator()
    await generator.add_recent_test_data(7)

if __name__ == "__main__":
    asyncio.run(main()) 