import json
from datetime import datetime, timedelta
import random
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

def generate_mock_data(days: int = 30):
    """Generate mock Garmin data for the specified number of days"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # Initialize data structures
    sleep_data = []
    weight_data = []
    heart_rate_data = []
    
    current_date = start_date
    while current_date <= end_date:
        # Generate sleep data
        sleep_duration = random.randint(420, 540)  # 7-9 hours in minutes
        deep_sleep = random.randint(60, 120)  # 1-2 hours
        light_sleep = random.randint(180, 240)  # 3-4 hours
        rem_sleep = random.randint(60, 90)  # 1-1.5 hours
        awake_time = random.randint(10, 30)  # 10-30 minutes
        
        sleep_data.append({
            "startTime": current_date.isoformat() + "Z",
            "endTime": (current_date + timedelta(minutes=sleep_duration)).isoformat() + "Z",
            "totalSleepTime": sleep_duration,
            "deepSleepTime": deep_sleep,
            "lightSleepTime": light_sleep,
            "remSleepTime": rem_sleep,
            "awakeTime": awake_time,
            "sleepQuality": random.randint(1, 100),
            "sleepScore": random.randint(60, 95)
        })
        
        # Generate weight data (measure once per day)
        weight = random.uniform(69.0, 72.0)
        weight_data.append({
            "timestamp": current_date.isoformat() + "Z",
            "weight": round(weight, 1),
            "bmi": round(weight / (1.75 * 1.75), 1),  # Assuming height of 1.75m
            "bodyFat": round(random.uniform(15.0, 20.0), 1),
            "bodyWater": round(random.uniform(50.0, 55.0), 1),
            "muscleMass": round(random.uniform(35.0, 40.0), 1),
            "boneMass": round(random.uniform(3.0, 3.5), 1)
        })
        
        # Generate heart rate data (measure every 15 minutes)
        for hour in range(24):
            for minute in [0, 15, 30, 45]:
                timestamp = current_date + timedelta(hours=hour, minutes=minute)
                # Higher heart rate during day, lower during night
                if 6 <= hour <= 22:  # Daytime
                    heart_rate = random.randint(60, 100)
                else:  # Nighttime
                    heart_rate = random.randint(45, 65)
                
                heart_rate_data.append({
                    "timestamp": timestamp.isoformat() + "Z",
                    "heartRate": heart_rate,
                    "restingHeartRate": random.randint(45, 55),
                    "maxHeartRate": random.randint(160, 180),
                    "minHeartRate": random.randint(40, 50)
                })
        
        current_date += timedelta(days=1)
    
    return {
        "sleep": sleep_data,
        "weight": weight_data,
        "heart_rate": heart_rate_data
    }

def save_mock_data(data: dict, output_dir: str):
    """Save mock data to JSON files"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    for data_type, items in data.items():
        file_path = output_path / f"{data_type}.json"
        with open(file_path, 'w') as f:
            json.dump(items, f, indent=2)
        print(f"Saved {len(items)} {data_type} records to {file_path}")

def main():
    # Use HealthData/Temp/ directory
    output_dir = "HealthData/Temp"
    
    # Generate 30 days of mock data
    mock_data = generate_mock_data(days=30)
    
    # Save the data
    save_mock_data(mock_data, output_dir)
    print("Mock data generation complete!")

if __name__ == "__main__":
    main() 