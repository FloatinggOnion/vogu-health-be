# Health Data API

A FastAPI backend that provides a modern health data tracking and insights service, powered by Google's Gemini AI.

## Features

- Track sleep, heart rate, and weight metrics
- Store health data in SQLite database
- Generate AI-powered health insights using Google Gemini
- Daily and historical health data analysis
- RESTful API endpoints for easy integration
- User authentication and data privacy
- Offline-first data storage

## Prerequisites

- Python 3.12
- Google Cloud API key with Gemini API access

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd <repository-directory>
```

2. Install dependencies using Pipenv:
```bash
pipenv install
```

3. Create a `.env` file with the following configuration:
```
API_HOST=0.0.0.0
API_PORT=8000
GOOGLE_API_KEY=your_google_api_key_here
SECRET_KEY=your_secret_key_here  # For JWT token generation
```

## Usage

1. Start the API server:
```bash
pipenv run uvicorn main:app --reload
```

2. Access the API documentation at `http://localhost:8000/docs`

## API Endpoints

### Data Submission
- `POST /api/v1/health-data/sleep`: Submit sleep data
- `POST /api/v1/health-data/heart-rate`: Submit heart rate data
- `POST /api/v1/health-data/weight`: Submit weight data

### Data Retrieval
- `GET /api/v1/health-data/{metric_type}`: Get health data for a specific metric type
- `GET /api/v1/health-data/daily/{date}`: Get daily health summary

### Insights
- `GET /api/v1/insights/recent`: Get AI insights for recent health metrics
- `GET /api/v1/insights/daily/{date}`: Get AI insights for specific day

## Data Models

### Sleep Data
```json
{
    "start_time": "2024-03-20T22:00:00Z",
    "end_time": "2024-03-21T06:00:00Z",
    "quality": 85,
    "phases": {
        "deep": 120,
        "light": 240,
        "rem": 90,
        "awake": 30
    },
    "source": "mobile_app"
}
```

### Heart Rate Data
```json
{
    "timestamp": "2024-03-21T12:00:00Z",
    "value": 75,
    "resting_rate": 60,
    "activity_type": "walking",
    "source": "mobile_app"
}
```

### Weight Data
```json
{
    "timestamp": "2024-03-21T08:00:00Z",
    "value": 70.5,
    "bmi": 22.5,
    "body_composition": {
        "body_fat": 18.5,
        "muscle_mass": 40.2,
        "water_percentage": 55.0,
        "bone_mass": 3.2
    },
    "source": "mobile_app"
}
```

## Development

### Running Tests
```bash
pipenv run pytest
```

### Code Formatting
```bash
pipenv run black .
pipenv run isort .
```

### Type Checking
```bash
pipenv run mypy .
```

### Linting
```bash
pipenv run flake8
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 