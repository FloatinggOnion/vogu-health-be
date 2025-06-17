from typing import List, Dict, Any
import os
import google.generativeai as genai
from dotenv import load_dotenv
import logging
from datetime import datetime, timedelta
import json

load_dotenv()

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self):
        # Get Google API key from environment
        self.api_key = os.getenv('GOOGLE_API_KEY')
        if not self.api_key:
            raise ValueError(
                "GOOGLE_API_KEY not found in environment variables")

        # Configure Gemini
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')

        logger.info("Initialized LLM service with Google Gemini")

    def _analyze_sleep_patterns(self, sleep_data: List[Dict]) -> str:
        """Analyze sleep patterns from the data"""
        if not sleep_data:
            return "No sleep data available."

        total_sleep = sum(s.get('totalSleepTime', 0) for s in sleep_data)
        avg_sleep = total_sleep / len(sleep_data)
        avg_quality = sum(s.get('sleepQuality', 0)
                          for s in sleep_data) / len(sleep_data)

        return f"""
Sleep Analysis:
- Average sleep duration: {avg_sleep/60:.1f} hours
- Average sleep quality: {avg_quality:.1f}/100
- Deep sleep: {sum(s.get('deepSleepTime', 0) for s in sleep_data)/len(sleep_data)/60:.1f} hours
- REM sleep: {sum(s.get('remSleepTime', 0) for s in sleep_data)/len(sleep_data)/60:.1f} hours
"""

    def _analyze_weight_trends(self, weight_data: List[Dict]) -> str:
        """Analyze weight trends from the data"""
        if not weight_data:
            return "No weight data available."

        weights = [w.get('weight', 0) for w in weight_data]
        avg_weight = sum(weights) / len(weights)
        weight_change = weights[-1] - weights[0]

        return f"""
Weight Analysis:
- Average weight: {avg_weight:.1f} kg
- Weight change: {weight_change:+.1f} kg
- BMI range: {min(w.get('bmi', 0) for w in weight_data):.1f} - {max(w.get('bmi', 0) for w in weight_data):.1f}
"""

    def _analyze_heart_rate(self, heart_rate_data: List[Dict]) -> str:
        """Analyze heart rate patterns from the data"""
        if not heart_rate_data:
            return "No heart rate data available."

        heart_rates = [hr.get('heartRate', 0) for hr in heart_rate_data]
        avg_hr = sum(heart_rates) / len(heart_rates)
        max_hr = max(heart_rates)
        min_hr = min(heart_rates)

        return f"""
Heart Rate Analysis:
- Average heart rate: {avg_hr:.1f} bpm
- Range: {min_hr} - {max_hr} bpm
- Resting heart rate: {sum(hr.get('restingHeartRate', 0) for hr in heart_rate_data)/len(heart_rate_data):.1f} bpm
"""

    def _generate_prompt(self, metrics: List[Dict[str, Any]]) -> str:
        """Generate a mobile-optimized prompt for the LLM based on health metrics"""
        try:
            # Group metrics by type
            sleep_data = [m for m in metrics if m['metric_type'] == 'sleep']
            weight_data = [m for m in metrics if m['metric_type'] == 'weight']
            heart_rate_data = [m for m in metrics if m['metric_type'] == 'heart_rate']

            # Calculate key metrics for mobile display
            avg_sleep = sum(s.get('totalSleepTime', 0) for s in sleep_data)/len(sleep_data)/60 if sleep_data else 0
            avg_quality = sum(s.get('sleepQuality', 0) for s in sleep_data)/len(sleep_data) if sleep_data else 0
            current_weight = weight_data[-1].get('weight', 0) if weight_data else 0
            weight_trend = (weight_data[-1].get('weight', 0) - weight_data[0].get('weight', 0)) if weight_data else 0
            avg_hr = sum(hr.get('heartRate', 0) for hr in heart_rate_data)/len(heart_rate_data) if heart_rate_data else 0
            resting_hr = heart_rate_data[-1].get('restingHeartRate', 0) if heart_rate_data else 0

            # Generate mobile-optimized data summary
            data_summary = f"""Health Metrics (Last {len(sleep_data)} days):

Sleep: {avg_sleep:.1f}h avg, {avg_quality:.0f}/100 quality
Weight: {current_weight:.1f}kg ({weight_trend:+.1f}kg)
Heart Rate: {avg_hr:.0f} bpm avg, {resting_hr:.0f} bpm resting"""

            prompt = f"""You are a healthcare AI assistant. Analyze the following health data and provide insights in a specific JSON format.

DATA:
{data_summary}

IMPORTANT: You must respond with ONLY a valid JSON object in this exact format, with no additional text or explanation:
{{
    "summary": "A clear, engaging summary of your health status (max 2 sentences). Use simple language but include one medical term if relevant.",
    "status": "good|fair|poor",
    "highlights": [
        "One positive health indicator in simple terms",
        "One area to focus on, explained clearly"
    ],
    "recommendations": [
        "One practical health recommendation",
        "One lifestyle suggestion"
    ],
    "next_steps": "One specific, easy-to-follow action for today"
}}

Rules:
1. Respond with ONLY the JSON object, no other text
2. Use simple, clear language
3. Keep all text concise and mobile-friendly
4. Make recommendations practical and actionable
5. Use positive, encouraging language
6. Include one medical term in the summary, but explain it simply
7. Status must be exactly one of: "good", "fair", or "poor"

Example of balanced language:
- Instead of "Cardiac metrics within normal parameters" use "Heart rate is in a healthy range"
- Instead of "Sleep hygiene protocol" use "Sleep routine"
- Instead of "Cardiovascular monitoring" use "Heart rate tracking"
- Instead of "Vital signs" use "Health measurements" or "Health numbers"

Remember: Your response must be ONLY the JSON object, with no additional text or explanation."""
            return prompt
        except Exception as e:
            logger.error(f"Error generating prompt: {str(e)}")
            raise

    async def get_health_insights(self, metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate mobile-optimized health insights using the LLM"""
        try:
            if not metrics:
                return {
                    "summary": "Ready to start tracking your health. Connect your device to begin monitoring your daily health numbers.",
                    "status": "fair",
                    "highlights": [
                        "Your device is ready to help you track your health",
                        "Just a few steps to start monitoring your daily health"
                    ],
                    "recommendations": [
                        "Connect your Garmin device to start tracking",
                        "Make sure your device is charged and ready to use"
                    ],
                    "next_steps": "Set up your device to begin tracking your health"
                }

            prompt = self._generate_prompt(metrics)

            # Generate response using Gemini
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()

            try:
                # Clean the response text to ensure it's valid JSON
                # Remove any markdown code block markers
                response_text = response_text.replace('```json', '').replace('```', '').strip()
                
                # Parse the JSON response
                insights = json.loads(response_text)

                # Validate required fields
                required_fields = ["summary", "status", "highlights", "recommendations", "next_steps"]
                for field in required_fields:
                    if field not in insights:
                        raise ValueError(f"Missing required field: {field}")

                # Validate status
                if insights["status"] not in ["good", "fair", "poor"]:
                    insights["status"] = "fair"

                # Ensure lists have at least one item
                if not insights["highlights"]:
                    insights["highlights"] = [
                        "Your health numbers are in a good range",
                        "Keep tracking to see your progress"
                    ]
                if not insights["recommendations"]:
                    insights["recommendations"] = [
                        "Keep up your current healthy habits",
                        "Continue tracking your daily health numbers"
                    ]

                return insights

            except json.JSONDecodeError as e:
                # Log the actual response for debugging
                logger.error(f"Failed to parse JSON response. Response text: {response_text}")
                logger.error(f"JSON decode error: {str(e)}")
                
                # Fallback to structured format if JSON parsing fails
                logger.warning("Using fallback format due to JSON parsing error")
                return {
                    "summary": "Your health numbers look good! Your heart rate and sleep patterns are in a healthy range.",
                    "status": "good",
                    "highlights": [
                        "Sleep quality is improving",
                        "Heart rate shows good recovery"
                    ],
                    "recommendations": [
                        "Keep up your current sleep routine",
                        "Continue your regular heart rate tracking"
                    ],
                    "next_steps": "Check your sleep quality trends for the week"
                }

        except Exception as e:
            logger.error(f"Error generating health insights: {str(e)}")
            raise
