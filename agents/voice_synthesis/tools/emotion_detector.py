"""
Emotion detector tool for the Voice Synthesis Agent.
Provides enhanced emotion detection capabilities.
"""

import logging
import re
from typing import Dict, Any, Optional

class EmotionDetectorTool:
    """
    Enhanced emotion detector tool for detecting emotions in text.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the emotion detector tool.
        
        Args:
            config: Configuration parameters
        """
        self.logger = logging.getLogger("dopcast.voice_synthesis.emotion_detector")
        self.config = config or {}
        
        # Initialize emotion keywords
        self._initialize_emotion_keywords()
    
    def _initialize_emotion_keywords(self):
        """Initialize emotion keywords for detection."""
        self.emotion_keywords = {
            "excited": ["wow", "amazing", "incredible", "fantastic", "awesome", "exciting", "thrilled", "!"],
            "happy": ["happy", "glad", "pleased", "delighted", "joy", "smile", "great", "good"],
            "sad": ["sad", "unfortunate", "disappointing", "regret", "sorry", "upset", "shame"],
            "angry": ["angry", "frustrated", "annoyed", "outrageous", "unacceptable", "terrible"],
            "surprised": ["surprised", "unexpected", "shocking", "astonishing", "remarkable", "sudden"],
            "analytical": ["analyze", "consider", "examine", "data", "evidence", "statistics", "technical"],
            "neutral": []  # Default
        }
    
    def detect_emotion(self, text: str) -> str:
        """
        Detect the primary emotion in a text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Detected emotion
        """
        # Convert to lowercase for case-insensitive matching
        text_lower = text.lower()
        
        # Count occurrences of emotion keywords
        emotion_scores = {emotion: 0 for emotion in self.emotion_keywords.keys()}
        
        for emotion, keywords in self.emotion_keywords.items():
            for keyword in keywords:
                # Count occurrences of the keyword
                count = len(re.findall(r'\b' + re.escape(keyword) + r'\b', text_lower))
                # For exclamation marks, count them directly
                if keyword == "!":
                    count = text.count("!")
                
                emotion_scores[emotion] += count
        
        # Check for punctuation indicators
        if text.count("!") > 2:
            emotion_scores["excited"] += 2
        
        if text.count("?") > 2:
            emotion_scores["surprised"] += 2
        
        # Determine the primary emotion
        max_score = 0
        primary_emotion = "neutral"
        
        for emotion, score in emotion_scores.items():
            if score > max_score:
                max_score = score
                primary_emotion = emotion
        
        return primary_emotion
