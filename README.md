# Garmin Health Insights API

A FastAPI backend that integrates with Garmin health data and provides AI-powered health insights using the Meditron LLM.

## Features

- Ingest health metrics from Garmin devices
- Generate AI-powered health insights
- Daily and historical health data analysis
- RESTful API endpoints for easy integration

## Prerequisites

- Python 3.12
- Garmin Connect account
- Garmin device with health tracking capabilities
- CUDA-capable GPU (recommended for LLM inference)

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
GARMIN_DB_PATH=garmin.db
API_HOST=0.0.0.0
API_PORT=8000
LLM_MODEL_NAME=epfl-llm/meditron-7b
LLM_DEVICE=cuda  # or cpu
```

## Usage

1. Start the API server:
```bash
pipenv run uvicorn main:app --reload
```

2. Access the API documentation at `http://localhost:8000/docs`

## API Endpoints

- `GET /`: Root endpoint
- `GET /health`: Health check endpoint
- `GET /metrics/recent`: Get recent health metrics (default: last 7 days)
- `GET /metrics/daily/{date}`: Get daily health metrics
- `GET /insights/recent`: Get AI insights for recent health metrics
- `GET /insights/daily/{date}`: Get AI insights for specific day

## Example Usage

Get recent health insights:
```bash
curl "http://localhost:8000/insights/recent?days=7"
```

Get daily insights for a specific date:
```bash
curl "http://localhost:8000/insights/daily/2024-05-01"
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 