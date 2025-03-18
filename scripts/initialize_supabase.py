import os
import logging
import argparse
import sys
import time
import json
import requests

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import Config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("dopcast.initialize_supabase")

def create_storage_buckets():
    """Create necessary storage buckets in Supabase."""
    try:
        logger.info("Creating storage buckets...")
        
        # List existing buckets to check if they exist
        url = f"{Config.SUPABASE_URL}/storage/v1/bucket"
        headers = {
            "apikey": Config.SERVICE_ROLE_KEY,
            "Authorization": f"Bearer {Config.SERVICE_ROLE_KEY}"
        }
        
        try:
            # List existing buckets
            buckets_response = requests.get(url, headers=headers)
            existing_buckets = []
            if buckets_response.status_code == 200:
                existing_buckets = [bucket["name"] for bucket in buckets_response.json()]
                logger.info(f"Existing buckets: {existing_buckets}")
            else:
                logger.error(f"Failed to list buckets: {buckets_response.text}")
                return False
            
            # Create each bucket if it doesn't exist
            for bucket_name, is_public in [
                ("audio", True),
                ("scripts", True),
                ("user_uploads", False)
            ]:
                if bucket_name not in existing_buckets:
                    logger.info(f"Creating '{bucket_name}' bucket...")
                    create_response = requests.post(
                        url,
                        headers={
                            "apikey": Config.SERVICE_ROLE_KEY,
                            "Authorization": f"Bearer {Config.SERVICE_ROLE_KEY}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "name": bucket_name,
                            "public": is_public
                        }
                    )
                    
                    if create_response.status_code in [200, 201]:
                        logger.info(f"Successfully created '{bucket_name}' bucket")
                    else:
                        logger.error(f"Failed to create '{bucket_name}' bucket: {create_response.text}")
                        return False
                else:
                    logger.info(f"Bucket '{bucket_name}' already exists")
            
            logger.info("All required storage buckets are available")
            return True
        except Exception as e:
            logger.error(f"Error accessing/creating buckets: {str(e)}")
            return False
            
    except Exception as e:
        logger.error(f"Error creating storage buckets: {str(e)}")
        return False

def wait_for_supabase():
    """Wait for Supabase to be ready."""
    max_retries = 10
    retry_interval = 5  # seconds
    
    for i in range(max_retries):
        try:
            logger.info(f"Attempt {i+1}/{max_retries}: Checking if Supabase is ready...")
            
            # Try to connect to the REST API
            url = f"{Config.SUPABASE_URL}/rest/v1/"
            headers = {
                "apikey": Config.SUPABASE_KEY
            }
            
            response = requests.get(url, headers=headers)
            
            if response.status_code in [200, 201]:
                logger.info("Supabase REST API is ready!")
                return True
        except Exception as e:
            logger.warning(f"Supabase not ready yet: {str(e)}")
        
        if i < max_retries - 1:
            logger.info(f"Waiting {retry_interval} seconds before next attempt...")
            time.sleep(retry_interval)
    
    logger.error("Timed out waiting for Supabase to be ready")
    return False

def main():
    parser = argparse.ArgumentParser(description='Initialize Supabase storage buckets for DopCast')
    parser.add_argument('--wait', action='store_true', help='Wait for Supabase to be ready')
    args = parser.parse_args()
    
    if args.wait:
        if not wait_for_supabase():
            logger.error("Supabase is not available. Exiting.")
            return 1
    
    if not create_storage_buckets():
        logger.error("Failed to create storage buckets. Exiting.")
        return 1
    
    logger.info("""
    ✅ Storage buckets created successfully!
    
    ⚠️ IMPORTANT: To complete the setup, you need to run the SQL commands in scripts/create_tables.sql
    
    You can do this by:
    1. Go to the Supabase dashboard
    2. Click on the SQL Editor
    3. Paste the contents of scripts/create_tables.sql
    4. Run the SQL commands to create the necessary tables
    
    Once the tables are created, your Supabase integration will be ready to use.
    """)
    return 0

if __name__ == "__main__":
    sys.exit(main()) 