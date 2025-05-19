from pymongo import MongoClient
from dotenv import load_dotenv
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_mongodb_connection():
    """Test MongoDB connection and basic operations"""
    try:
        # Load environment variables
        load_dotenv()
        
        # Get MongoDB URI
        mongo_uri = os.getenv('MONGODB_URI')
        print(mongo_uri)
        if not mongo_uri:
            raise ValueError("MONGODB_URI not found in environment variables")
        
        # Connect to MongoDB
        client = MongoClient(mongo_uri)
        
        # Test connection
        client.admin.command('ping')
        logger.info("Successfully connected to MongoDB!")
        
        # Test database operations
        db = client['garmin_health']
        
        # Create a test collection
        test_collection = db['test_collection']
        
        # Insert a test document
        test_doc = {
            'test': 'data',
            'timestamp': '2024-01-01T00:00:00'
        }
        result = test_collection.insert_one(test_doc)
        logger.info(f"Successfully inserted test document with ID: {result.inserted_id}")
        
        # Query the test document
        retrieved_doc = test_collection.find_one({'test': 'data'})
        logger.info(f"Successfully retrieved test document: {retrieved_doc}")
        
        # Clean up
        test_collection.delete_one({'test': 'data'})
        logger.info("Successfully cleaned up test data")
        
        return True
        
    except Exception as e:
        logger.error(f"Error testing MongoDB connection: {str(e)}")
        return False

if __name__ == "__main__":
    test_mongodb_connection() 