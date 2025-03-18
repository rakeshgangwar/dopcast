import os
import logging
import requests
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
import json

from supabase import create_client, Client
from config import Config

logger = logging.getLogger("dopcast.supabase")

class SupabaseClient:
    """
    Supabase client for DopCast system.
    Provides database, auth, storage, and real-time functionality.
    """
    
    def __init__(self):
        """
        Initialize the Supabase client.
        """
        self.url = Config.SUPABASE_URL
        self.key = Config.SUPABASE_KEY
        self.service_key = Config.SERVICE_ROLE_KEY
        self.client = None
        
        try:
            # Initialize with anonymous key by default
            self.client = create_client(self.url, self.key)
            logger.info(f"Connected to Supabase at {self.url}")
        except Exception as e:
            logger.error(f"Failed to connect to Supabase: {str(e)}")
    
    def get_admin_client(self) -> Client:
        """
        Get an admin client using the service role key.
        
        Returns:
            Supabase client with admin privileges
        """
        try:
            return create_client(self.url, self.service_key)
        except Exception as e:
            logger.error(f"Failed to create admin Supabase client: {str(e)}")
            return None
    
    def is_connected(self) -> bool:
        """
        Check if Supabase connection is active.
        
        Returns:
            True if connected, False otherwise
        """
        if not self.client:
            return False
        
        try:
            # Just check the API connection, don't worry about specific tables
            response = requests.get(
                f"{self.url}/rest/v1/",
                headers={
                    "apikey": self.key
                }
            )
            return response.status_code in [200, 201]
        except Exception as e:
            logger.error(f"Failed to connect to Supabase: {str(e)}")
            return False
    
    def check_tables_exist(self) -> bool:
        """
        Check if required tables exist.
        
        Returns:
            True if all required tables exist, False otherwise
        """
        required_tables = ["podcasts", "generation_logs", "health_check"]
        missing_tables = []
        
        for table in required_tables:
            try:
                # Try to access the table
                self.client.table(table).select("*").limit(1).execute()
            except Exception as e:
                error_msg = str(e)
                if "relation" in error_msg and "does not exist" in error_msg:
                    missing_tables.append(table)
        
        if missing_tables:
            logger.error(f"Missing tables: {', '.join(missing_tables)}")
            logger.error("Please run the SQL script at scripts/create_tables.sql to create the missing tables")
            return False
        
        logger.info("All required tables exist")
        return True

    # Podcast management methods
    def store_podcast(self, podcast_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Store podcast data in the database or update if already exists.
        
        Args:
            podcast_data: Podcast data including id if updating
            
        Returns:
            Stored podcast data or None if failed
        """
        try:
            logger.info(f"Attempting to store podcast data: {podcast_data.get('id', 'new podcast')}")
            
            # Make a copy of the data to avoid modifying the original
            data_to_store = podcast_data.copy()
            
            # Get podcast ID - need this for fallback logging
            podcast_id = data_to_store.get('id', 'unknown')
            
            # Handle metadata field - the most common source of errors
            # For Supabase PostgreSQL JSONB type, metadata must be a dict not a string
            if 'metadata' in data_to_store:
                if isinstance(data_to_store['metadata'], str):
                    # If it's a string, try to parse it to a dict
                    try:
                        data_to_store['metadata'] = json.loads(data_to_store['metadata'])
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid JSON in metadata: {data_to_store['metadata']}")
                        # If it can't be parsed, set to empty object to avoid errors
                        data_to_store['metadata'] = {}
                elif data_to_store['metadata'] is None:
                    # If metadata is None, set to empty object
                    data_to_store['metadata'] = {}
            else:
                # Ensure metadata field exists
                data_to_store['metadata'] = {}
            
            # Use direct API approach first as it's more reliable
            logger.debug("Using direct API approach to store podcast")
            if 'id' in data_to_store:
                # Update existing podcast
                url = f"{self.url}/rest/v1/podcasts?id=eq.{data_to_store['id']}"
                method = requests.patch
            else:
                # Create new podcast
                url = f"{self.url}/rest/v1/podcasts"
                method = requests.post
            
            headers = {
                "apikey": self.service_key,
                "Authorization": f"Bearer {self.service_key}",
                "Content-Type": "application/json",
                "Prefer": "return=representation"
            }
            
            response = method(url, headers=headers, json=data_to_store)
            
            if response.status_code in [200, 201]:
                logger.info(f"Successfully stored podcast {podcast_id} via direct API")
                try:
                    result_data = response.json()
                    if isinstance(result_data, list) and result_data:
                        return result_data[0]
                    elif isinstance(result_data, dict):
                        return result_data
                    else:
                        # Empty response but success status
                        return data_to_store
                except Exception as json_err:
                    logger.warning(f"Error parsing direct API response: {str(json_err)}")
                    # Return original data since operation succeeded
                    return data_to_store
            
            logger.warning(f"Direct API request failed: {response.status_code}. Trying client...")
            
            # Fall back to client library approach
            admin_client = self.get_admin_client()
            
            if 'id' in data_to_store:
                # Update existing podcast
                logger.info(f"Updating existing podcast with ID: {data_to_store['id']}")
                if admin_client:
                    # Try with admin privileges first
                    result = admin_client.table('podcasts').update(data_to_store).eq('id', data_to_store['id']).execute()
                else:
                    # Fall back to regular client
                    result = self.client.table('podcasts').update(data_to_store).eq('id', data_to_store['id']).execute()
            else:
                # Create new podcast entry
                logger.info("Creating new podcast entry")
                if admin_client:
                    # Try with admin privileges first
                    result = admin_client.table('podcasts').insert(data_to_store).execute()
                else:
                    # Fall back to regular client
                    result = self.client.table('podcasts').insert(data_to_store).execute()
            
            if result and result.data:
                logger.info(f"Successfully stored podcast: {result.data[0].get('id', 'unknown')}")
                return result.data[0]
            
            # If we get here, all approaches failed
            logger.error(f"Failed to store podcast {podcast_id} after trying all methods")
            return None
                
        except Exception as e:
            logger.error(f"Error storing podcast data: {str(e)}", exc_info=True)
            return None
    
    def get_podcast(self, podcast_id: str) -> Optional[Dict[str, Any]]:
        """
        Get podcast data from the database.
        
        Args:
            podcast_id: Podcast ID
            
        Returns:
            Podcast data or None if not found
        """
        try:
            result = self.client.table('podcasts').select('*').eq('id', podcast_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error getting podcast {podcast_id}: {str(e)}")
            return None
    
    def get_recent_podcasts(self, sport: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent podcasts, optionally filtered by sport.
        
        Args:
            sport: Optional sport filter
            limit: Maximum number of podcasts to return
            
        Returns:
            List of podcast data
        """
        try:
            query = self.client.table('podcasts').select('*').order('created_at', desc=True).limit(limit)
            
            if sport:
                query = query.eq('sport', sport)
                
            result = query.execute()
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Error getting recent podcasts: {str(e)}")
            return []
    
    def log_podcast_generation(self, podcast_id: str, agent_name: str, message: str, level: str = "info") -> bool:
        """
        Log a message during podcast generation.
        
        Args:
            podcast_id: Podcast ID
            agent_name: Name of the agent
            message: Log message
            level: Log level (info, warning, error)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Verify podcast exists first to handle foreign key constraint
            podcast = self.get_podcast(podcast_id)
            if not podcast:
                logger.warning(f"Cannot log for podcast {podcast_id} - podcast not found in database")
                # Log to stdout/stderr instead
                print(f"LOG [{level.upper()}] - {agent_name}: {message}")
                return False
            
            log_data = {
                "podcast_id": podcast_id,
                "agent_name": agent_name,
                "message": message,
                "level": level,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.debug(f"Logging message for podcast {podcast_id}: {message}")
            
            # Use direct API approach as it's more reliable
            url = f"{self.url}/rest/v1/generation_logs"
            headers = {
                "apikey": self.service_key,
                "Authorization": f"Bearer {self.service_key}",
                "Content-Type": "application/json",
                "Prefer": "return=representation"
            }
            
            response = requests.post(url, headers=headers, json=log_data)
            
            if response.status_code in [200, 201]:
                logger.debug(f"Successfully logged message via direct API")
                return True
            
            # If direct API failed, try the client library
            logger.warning(f"Direct API logging failed: {response.status_code}. Trying client...")
            admin_client = self.get_admin_client()
            
            if admin_client:
                result = admin_client.table('generation_logs').insert(log_data).execute()
            else:
                result = self.client.table('generation_logs').insert(log_data).execute()
            
            if result and result.data:
                logger.debug(f"Successfully logged message via client: {result.data[0].get('id')}")
                return True
            
            # If all database methods failed, log to stdout at least
            logger.error(f"Failed to log message to database. Falling back to console.")
            print(f"LOG [{level.upper()}] - {agent_name}: {message}")
            return False
            
        except Exception as e:
            logger.error(f"Error logging podcast generation: {str(e)}", exc_info=True)
            # Log to stdout as fallback
            print(f"LOG [{level.upper()}] - {agent_name}: {message}")
            return False
    
    # Storage methods
    def upload_file(self, bucket: str, path: str, file_path: str) -> Optional[str]:
        """
        Upload a file to Supabase storage.
        
        Args:
            bucket: Storage bucket name
            path: Path within bucket
            file_path: Local file path
            
        Returns:
            Public URL or None if failed
        """
        try:
            with open(file_path, 'rb') as f:
                result = self.client.storage.from_(bucket).upload(path, f)
                if result and result.get('Key'):
                    # Get public URL
                    file_url = self.client.storage.from_(bucket).get_public_url(path)
                    return file_url
                return None
        except Exception as e:
            logger.error(f"Error uploading file {file_path}: {str(e)}")
            return None
    
    def upload_audio(self, podcast_id: str, file_path: str) -> Optional[str]:
        """
        Upload podcast audio file to Supabase storage.
        
        Args:
            podcast_id: Podcast ID
            file_path: Path to audio file
            
        Returns:
            Public URL or None if failed
        """
        file_name = os.path.basename(file_path)
        storage_path = f"{podcast_id}/{file_name}"
        return self.upload_file('audio', storage_path, file_path)
    
    def upload_script(self, podcast_id: str, file_path: str) -> Optional[str]:
        """
        Upload podcast script file to Supabase storage.
        
        Args:
            podcast_id: Podcast ID
            file_path: Path to script file
            
        Returns:
            Public URL or None if failed
        """
        file_name = os.path.basename(file_path)
        storage_path = f"{podcast_id}/{file_name}"
        return self.upload_file('scripts', storage_path, file_path)
    
    def download_file(self, bucket: str, path: str, destination_path: str) -> bool:
        """
        Download a file from Supabase storage.
        
        Args:
            bucket: Storage bucket name
            path: Path within bucket
            destination_path: Local destination path
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = self.client.storage.from_(bucket).download(path)
            
            if result:
                os.makedirs(os.path.dirname(destination_path), exist_ok=True)
                with open(destination_path, 'wb') as f:
                    f.write(result)
                return True
            return False
        except Exception as e:
            logger.error(f"Error downloading file {path}: {str(e)}")
            return False 