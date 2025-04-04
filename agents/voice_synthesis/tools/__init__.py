"""
Tools for the DopCast Voice Synthesis Agent.
This package contains specialized tools for voice synthesis.
"""

from .voice_generator import VoiceGeneratorTool
from .audio_processor import AudioProcessorTool
from .emotion_detector import EmotionDetectorTool

__all__ = [
    "VoiceGeneratorTool",
    "AudioProcessorTool",
    "EmotionDetectorTool",
]
