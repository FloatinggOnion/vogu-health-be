from typing import List, Dict, Any
import os
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
from dotenv import load_dotenv
import logging
from datetime import datetime, timedelta

load_dotenv()

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.model_name = "epfl-llm/meditron-7b"
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(self.device)
        
        # Get Hugging Face token from environment
        self.hf_token = os.getenv('HF_TOKEN')
        if not self.hf_token:
            raise ValueError("HF_TOKEN not found in environment variables")
        
        logger.info(f"Initializing LLM service with model: {self.model_name}")
        logger.info(f"Using device: {self.device}")
        
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                token=self.hf_token,
                trust_remote_code=True
            )
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                token=self.hf_token,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                device_map="auto",
                trust_remote_code=True
            )
            logger.info("Successfully loaded model and tokenizer")
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            raise

    def _analyze_sleep_patterns(self, sleep_data: List[Dict]) -> str:
        """Analyze sleep patterns from the data"""
        if not sleep_data:
            return "No sleep data available."
        
        total_sleep = sum(s.get('totalSleepTime', 0) for s in sleep_data)
        avg_sleep = total_sleep / len(sleep_data)
        avg_quality = sum(s.get('sleepQuality', 0) for s in sleep_data) / len(sleep_data)
        
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
        """Generate a detailed prompt for the LLM based on health metrics"""
        # Group metrics by type
        sleep_data = [m for m in metrics if m['metric_type'] == 'sleep']
        weight_data = [m for m in metrics if m['metric_type'] == 'weight']
        heart_rate_data = [m for m in metrics if m['metric_type'] == 'heart_rate']
        
        # Generate analysis sections
        sleep_analysis = self._analyze_sleep_patterns(sleep_data)
        weight_analysis = self._analyze_weight_trends(weight_data)
        heart_rate_analysis = self._analyze_heart_rate(heart_rate_data)
        
        prompt = f"""You are a health AI assistant analyzing Garmin health data. Based on the following analysis, provide detailed insights and recommendations:

{sleep_analysis}

{weight_analysis}

{heart_rate_analysis}

Please provide a comprehensive health analysis with the following sections:

1. Key Insights:
   - Analyze patterns and trends in the data
   - Identify correlations between different metrics
   - Highlight significant changes or anomalies

2. Health Recommendations:
   - Provide specific, actionable recommendations for improvement
   - Focus on sleep quality, weight management, and heart health
   - Include both short-term and long-term goals

3. Health Concerns:
   - Identify any potential health concerns
   - Suggest when to consult a healthcare professional
   - Provide preventive measures

Format your response in a clear, structured way with these three sections. Be specific and evidence-based in your analysis.
"""
        return prompt

    async def get_health_insights(self, metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate health insights using the LLM"""
        try:
            prompt = self._generate_prompt(metrics)
            
            # Tokenize and generate
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
            outputs = self.model.generate(
                **inputs,
                max_length=1000,
                num_return_sequences=1,
                temperature=0.7,
                top_p=0.9,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id
            )
            
            # Decode the response
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Parse the response into structured format
            insights = {
                "summary": response,
                "recommendations": [],
                "concerns": []
            }
            
            # Parse the response into sections
            current_section = None
            for line in response.split('\n'):
                line = line.strip()
                if not line:
                    continue
                    
                if "Key Insights" in line:
                    current_section = "insights"
                elif "Health Recommendations" in line:
                    current_section = "recommendations"
                elif "Health Concerns" in line:
                    current_section = "concerns"
                elif current_section == "recommendations" and line.startswith("-"):
                    insights["recommendations"].append(line[1:].strip())
                elif current_section == "concerns" and line.startswith("-"):
                    insights["concerns"].append(line[1:].strip())
            
            return insights
            
        except Exception as e:
            logger.error(f"Error generating health insights: {str(e)}")
            raise 