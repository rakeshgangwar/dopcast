import os
from dotenv import load_dotenv
from typing import Dict, Any, Optional
import json

# Load environment variables from .env file
load_dotenv()

class Config:
    """
    Configuration manager for the DopCast system.
    Handles loading settings from environment variables and config files.
    """
    
    # Base configuration
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    CONTENT_DIR = os.path.join(BASE_DIR, "content")
    DATA_DIR = os.path.join(BASE_DIR, "data")
    LOGS_DIR = os.path.join(BASE_DIR, "logs")
    
    # Ensure directories exist
    os.makedirs(CONTENT_DIR, exist_ok=True)
    os.makedirs(os.path.join(CONTENT_DIR, "scripts"), exist_ok=True)
    os.makedirs(os.path.join(CONTENT_DIR, "audio"), exist_ok=True)
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(os.path.join(DATA_DIR, "cache"), exist_ok=True)
    os.makedirs(LOGS_DIR, exist_ok=True)
    
    # API settings
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", "8000"))
    
    # Web UI settings
    WEB_HOST = os.getenv("WEB_HOST", "0.0.0.0")
    WEB_PORT = int(os.getenv("WEB_PORT", "8501"))
    
    # Redis settings
    REDIS_ENABLED = os.getenv("REDIS_ENABLED", "false").lower() == "true"
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB = int(os.getenv("REDIS_DB", "0"))
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
    
    # OpenAI API settings
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4")
    
    # Audio settings
    DEFAULT_AUDIO_FORMAT = os.getenv("DEFAULT_AUDIO_FORMAT", "mp3")
    DEFAULT_SAMPLE_RATE = int(os.getenv("DEFAULT_SAMPLE_RATE", "44100"))
    DEFAULT_BITRATE = os.getenv("DEFAULT_BITRATE", "192k")
    
    # Agent-specific settings
    RESEARCH_SOURCES = os.getenv("RESEARCH_SOURCES", "official,news,social")
    MAX_RESEARCH_DEPTH = int(os.getenv("MAX_RESEARCH_DEPTH", "3"))
    
    @classmethod
    def get_agent_config(cls, agent_name: str) -> Dict[str, Any]:
        """
        Get configuration for a specific agent.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Configuration dictionary for the agent
        """
        config_path = os.path.join(cls.BASE_DIR, "config", f"{agent_name}.json")
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                return json.load(f)
        return {}
    
    @classmethod
    def save_agent_config(cls, agent_name: str, config: Dict[str, Any]) -> None:
        """
        Save configuration for a specific agent.
        
        Args:
            agent_name: Name of the agent
            config: Configuration dictionary to save
        """
        os.makedirs(os.path.join(cls.BASE_DIR, "config"), exist_ok=True)
        config_path = os.path.join(cls.BASE_DIR, "config", f"{agent_name}.json")
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)
    
    @classmethod
    def get_voice_profile(cls, profile_name: str) -> Optional[Dict[str, Any]]:
        """
        Get a voice profile configuration.
        
        Args:
            profile_name: Name of the voice profile
            
        Returns:
            Voice profile configuration or None if not found
        """
        profiles_path = os.path.join(cls.BASE_DIR, "config", "voice_profiles.json")
        if os.path.exists(profiles_path):
            with open(profiles_path, "r") as f:
                profiles = json.load(f)
                return profiles.get(profile_name)
        return None
    
    @classmethod
    def get_sport_config(cls, sport: str) -> Dict[str, Any]:
        """
        Get configuration for a specific sport.
        
        Args:
            sport: Sport identifier (e.g., "f1", "motogp")
            
        Returns:
            Sport-specific configuration
        """
        config_path = os.path.join(cls.BASE_DIR, "config", "sports", f"{sport}.json")
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                return json.load(f)
        return {}

# Create default configuration files if they don't exist
def create_default_configs():
    config_dir = os.path.join(Config.BASE_DIR, "config")
    os.makedirs(config_dir, exist_ok=True)
    os.makedirs(os.path.join(config_dir, "sports"), exist_ok=True)
    
    # Default voice profiles
    voice_profiles = {
        "host_male_1": {
            "name": "Alex",
            "gender": "male",
            "accent": "american",
            "style": "enthusiastic",
            "pitch": 1.0,
            "rate": 1.0
        },
        "host_female_1": {
            "name": "Maria",
            "gender": "female",
            "accent": "british",
            "style": "professional",
            "pitch": 1.0,
            "rate": 1.0
        },
        "host_male_2": {
            "name": "James",
            "gender": "male",
            "accent": "british",
            "style": "analytical",
            "pitch": 0.95,
            "rate": 0.98
        },
        "host_female_2": {
            "name": "Sophia",
            "gender": "female",
            "accent": "american",
            "style": "conversational",
            "pitch": 1.05,
            "rate": 1.02
        }
    }
    
    profiles_path = os.path.join(config_dir, "voice_profiles.json")
    if not os.path.exists(profiles_path):
        with open(profiles_path, "w") as f:
            json.dump(voice_profiles, f, indent=2)
    
    # Default F1 configuration
    f1_config = {
        "name": "Formula 1",
        "short_name": "F1",
        "data_sources": [
            "https://www.formula1.com",
            "https://www.autosport.com/f1",
            "https://www.motorsport.com/f1"
        ],
        "teams": [
            "Red Bull Racing",
            "Mercedes",
            "Ferrari",
            "McLaren",
            "Aston Martin",
            "Alpine",
            "Williams",
            "AlphaTauri",
            "Sauber",
            "Haas"
        ],
        "event_types": [
            "race",
            "qualifying",
            "sprint",
            "practice"
        ],
        "podcast_intro": "Welcome to F1 Insider, your ultimate source for Formula 1 analysis and insights."
    }
    
    f1_path = os.path.join(config_dir, "sports", "f1.json")
    if not os.path.exists(f1_path):
        with open(f1_path, "w") as f:
            json.dump(f1_config, f, indent=2)
    
    # Default MotoGP configuration
    motogp_config = {
        "name": "MotoGP",
        "short_name": "MotoGP",
        "data_sources": [
            "https://www.motogp.com",
            "https://www.crash.net/motogp",
            "https://www.motorsport.com/motogp"
        ],
        "teams": [
            "Ducati Lenovo Team",
            "Monster Energy Yamaha MotoGP",
            "Repsol Honda Team",
            "Red Bull KTM Factory Racing",
            "Aprilia Racing",
            "Gresini Racing MotoGP",
            "Prima Pramac Racing",
            "LCR Honda",
            "Tech3 GasGas Factory Racing",
            "VR46 Racing Team"
        ],
        "event_types": [
            "race",
            "qualifying",
            "practice"
        ],
        "podcast_intro": "Welcome to MotoGP Insider, your ultimate source for MotoGP analysis and insights."
    }
    
    motogp_path = os.path.join(config_dir, "sports", "motogp.json")
    if not os.path.exists(motogp_path):
        with open(motogp_path, "w") as f:
            json.dump(motogp_config, f, indent=2)

# Create default configs when module is imported
create_default_configs()
