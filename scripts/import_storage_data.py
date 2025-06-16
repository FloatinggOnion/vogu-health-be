#!/usr/bin/env python3
"""
Script to import health data from Storage JSON files into the SQLite database.
Transforms the frontend format to the API format.
"""

import json
import asyncio
import logging
from datetime import datetime
from pathlib import Path
import sys
import os

# Add the parent directory to the path so we can import our services
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.health_data.service import HealthDataService
from services.health_data.models import SleepData, HeartRateData, WeightData, SleepPhase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StorageDataImporter:
    def __init__(self):
        self.health_service = HealthDataService()
        self.storage_path = Path("HealthData/Storage")
    
    def transform_sleep_data(self, storage_data):
        """Transform sleep data from storage format to API format"""
        transformed = []
        for item in storage_data:
            try:
                # Transform the data format
                sleep_data = SleepData(
                    start_time=datetime.fromisoformat(item["startTime"].replace("Z", "+00:00")),
                    end_time=datetime.fromisoformat(item["endTime"].replace("Z", "+00:00")),
                    quality=item["sleepQuality"],
                    phases=SleepPhase(
                        deep=item["deepSleepTime"],
                        light=item["lightSleepTime"],
                        rem=item["remSleepTime"],
                        awake=item["awakeTime"]
                    ),
                    source="storage_import"
                )
                transformed.append(sleep_data)
            except Exception as e:
                logger.warning(f"Failed to transform sleep data item: {e}")
                continue
        return transformed
    
    def transform_heart_rate_data(self, storage_data):
        """Transform heart rate data from storage format to API format"""
        transformed = []
        for item in storage_data:
            try:
                heart_rate_data = HeartRateData(
                    timestamp=datetime.fromisoformat(item["timestamp"].replace("Z", "+00:00")),
                    value=item["heartRate"],
                    resting_rate=item.get("restingHeartRate"),
                    activity_type=None,  # Not available in storage format
                    source="storage_import"
                )
                transformed.append(heart_rate_data)
            except Exception as e:
                logger.warning(f"Failed to transform heart rate data item: {e}")
                continue
        return transformed
    
    def transform_weight_data(self, storage_data):
        """Transform weight data from storage format to API format"""
        transformed = []
        for item in storage_data:
            try:
                weight_data = WeightData(
                    timestamp=datetime.fromisoformat(item["timestamp"].replace("Z", "+00:00")),
                    value=item["weight"],
                    bmi=item.get("bmi"),
                    body_composition=None,  # We'll handle this separately if needed
                    source="storage_import"
                )
                transformed.append(weight_data)
            except Exception as e:
                logger.warning(f"Failed to transform weight data item: {e}")
                continue
        return transformed
    
    async def import_sleep_data(self):
        """Import sleep data from storage"""
        sleep_file = self.storage_path / "sleep_data.json"
        if not sleep_file.exists():
            logger.warning(f"Sleep data file not found: {sleep_file}")
            return 0
        
        try:
            with open(sleep_file, 'r') as f:
                storage_data = json.load(f)
            
            transformed_data = self.transform_sleep_data(storage_data)
            logger.info(f"Transformed {len(transformed_data)} sleep records")
            
            imported_count = 0
            for sleep_data in transformed_data:
                try:
                    await self.health_service.store_sleep_data(sleep_data)
                    imported_count += 1
                except Exception as e:
                    logger.warning(f"Failed to import sleep data: {e}")
                    continue
            
            logger.info(f"Successfully imported {imported_count} sleep records")
            return imported_count
            
        except Exception as e:
            logger.error(f"Error importing sleep data: {e}")
            return 0
    
    async def import_heart_rate_data(self):
        """Import heart rate data from storage"""
        hr_file = self.storage_path / "heart_rate_data.json"
        if not hr_file.exists():
            logger.warning(f"Heart rate data file not found: {hr_file}")
            return 0
        
        try:
            with open(hr_file, 'r') as f:
                storage_data = json.load(f)
            
            transformed_data = self.transform_heart_rate_data(storage_data)
            logger.info(f"Transformed {len(transformed_data)} heart rate records")
            
            imported_count = 0
            for hr_data in transformed_data:
                try:
                    await self.health_service.store_heart_rate_data(hr_data)
                    imported_count += 1
                except Exception as e:
                    logger.warning(f"Failed to import heart rate data: {e}")
                    continue
            
            logger.info(f"Successfully imported {imported_count} heart rate records")
            return imported_count
            
        except Exception as e:
            logger.error(f"Error importing heart rate data: {e}")
            return 0
    
    async def import_weight_data(self):
        """Import weight data from storage"""
        weight_file = self.storage_path / "weight_data.json"
        if not weight_file.exists():
            logger.warning(f"Weight data file not found: {weight_file}")
            return 0
        
        try:
            with open(weight_file, 'r') as f:
                storage_data = json.load(f)
            
            transformed_data = self.transform_weight_data(storage_data)
            logger.info(f"Transformed {len(transformed_data)} weight records")
            
            imported_count = 0
            for weight_data in transformed_data:
                try:
                    await self.health_service.store_weight_data(weight_data)
                    imported_count += 1
                except Exception as e:
                    logger.warning(f"Failed to import weight data: {e}")
                    continue
            
            logger.info(f"Successfully imported {imported_count} weight records")
            return imported_count
            
        except Exception as e:
            logger.error(f"Error importing weight data: {e}")
            return 0
    
    async def import_all_data(self):
        """Import all data from storage files"""
        logger.info("Starting data import from Storage files...")
        
        sleep_count = await self.import_sleep_data()
        hr_count = await self.import_heart_rate_data()
        weight_count = await self.import_weight_data()
        
        total_count = sleep_count + hr_count + weight_count
        logger.info(f"Import completed! Total records imported: {total_count}")
        logger.info(f"  - Sleep: {sleep_count}")
        logger.info(f"  - Heart Rate: {hr_count}")
        logger.info(f"  - Weight: {weight_count}")
        
        return total_count

async def main():
    """Main function to run the import"""
    importer = StorageDataImporter()
    await importer.import_all_data()

if __name__ == "__main__":
    asyncio.run(main()) 