import os
import shutil
import sqlite3
from datetime import datetime, timedelta
import random

def clear_databases():
    """Clear existing database files"""
    db_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "HealthData", "DBs")
    if os.path.exists(db_dir):
        shutil.rmtree(db_dir)
    os.makedirs(db_dir, exist_ok=True)
    print("Cleared existing databases")

def create_mock_database():
    """Create a new SQLite database with mock data"""
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "HealthData", "DBs", "garmin.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create tables
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS activities (
        id INTEGER PRIMARY KEY,
        start_time TIMESTAMP,
        activity_type TEXT,
        distance REAL,
        duration INTEGER,
        calories INTEGER
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sleep (
        id INTEGER PRIMARY KEY,
        start_time TIMESTAMP,
        total_sleep_minutes INTEGER,
        sleep_quality INTEGER,
        deep_sleep_minutes INTEGER,
        light_sleep_minutes INTEGER,
        rem_sleep_minutes INTEGER,
        awake_minutes INTEGER
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS heart_rate (
        id INTEGER PRIMARY KEY,
        timestamp TIMESTAMP,
        heart_rate INTEGER
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS weight (
        id INTEGER PRIMARY KEY,
        timestamp TIMESTAMP,
        weight REAL,
        bmi REAL,
        body_fat REAL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS steps (
        id INTEGER PRIMARY KEY,
        timestamp TIMESTAMP,
        steps INTEGER,
        distance REAL,
        calories INTEGER
    )
    ''')

    # Generate mock data for the last 30 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    # Generate activities
    activity_types = ['running', 'cycling', 'swimming', 'walking']
    for i in range(30):
        date = start_date + timedelta(days=i)
        for _ in range(random.randint(0, 2)):  # 0-2 activities per day
            activity_type = random.choice(activity_types)
            distance = random.uniform(1, 20)
            duration = int(distance * random.uniform(5, 10) * 60)  # 5-10 min per km
            calories = int(distance * random.uniform(50, 100))
            
            cursor.execute('''
            INSERT INTO activities (start_time, activity_type, distance, duration, calories)
            VALUES (?, ?, ?, ?, ?)
            ''', (date, activity_type, distance, duration, calories))

    # Generate sleep data
    for i in range(30):
        date = start_date + timedelta(days=i)
        total_sleep = random.randint(360, 540)  # 6-9 hours
        quality = random.randint(1, 100)
        deep_sleep = int(total_sleep * random.uniform(0.1, 0.3))
        light_sleep = int(total_sleep * random.uniform(0.4, 0.6))
        rem_sleep = int(total_sleep * random.uniform(0.1, 0.3))
        awake = random.randint(10, 30)
        
        cursor.execute('''
        INSERT INTO sleep (start_time, total_sleep_minutes, sleep_quality, 
                         deep_sleep_minutes, light_sleep_minutes, rem_sleep_minutes, awake_minutes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (date, total_sleep, quality, deep_sleep, light_sleep, rem_sleep, awake))

    # Generate heart rate data (every 15 minutes)
    for i in range(30):
        date = start_date + timedelta(days=i)
        for hour in range(24):
            for minute in range(0, 60, 15):
                timestamp = date + timedelta(hours=hour, minutes=minute)
                heart_rate = random.randint(50, 180)
                cursor.execute('''
                INSERT INTO heart_rate (timestamp, heart_rate)
                VALUES (?, ?)
                ''', (timestamp, heart_rate))

    # Generate weight data (daily)
    base_weight = 70.0  # kg
    for i in range(30):
        date = start_date + timedelta(days=i)
        weight = base_weight + random.uniform(-0.5, 0.5)
        height = 1.75  # meters
        bmi = weight / (height * height)
        body_fat = random.uniform(15, 25)
        
        cursor.execute('''
        INSERT INTO weight (timestamp, weight, bmi, body_fat)
        VALUES (?, ?, ?, ?)
        ''', (date, weight, bmi, body_fat))

    # Generate steps data (hourly)
    for i in range(30):
        date = start_date + timedelta(days=i)
        for hour in range(24):
            timestamp = date + timedelta(hours=hour)
            steps = random.randint(0, 1000)
            distance = steps * 0.0007  # Rough estimate: 0.7 meters per step
            calories = int(steps * 0.04)  # Rough estimate: 0.04 calories per step
            
            cursor.execute('''
            INSERT INTO steps (timestamp, steps, distance, calories)
            VALUES (?, ?, ?, ?)
            ''', (timestamp, steps, distance, calories))

    conn.commit()
    conn.close()
    print("Created mock database with sample data")

if __name__ == "__main__":
    clear_databases()
    create_mock_database()
    print("Database seeding complete!") 