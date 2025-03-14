import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

from agents.base_agent import BaseAgent

class AudioProductionAgent(BaseAgent):
    """
    Agent responsible for enhancing raw audio with production elements.
    Adds intro/outro music, sound effects, and balances audio levels.
    """
    
    def __init__(self, name: str = "audio_production", config: Optional[Dict[str, Any]] = None):
        """
        Initialize the audio production agent.
        
        Args:
            name: Agent identifier
            config: Configuration parameters
        """
        default_config = {
            "audio_assets": {
                "intro_music": "assets/audio/intro_theme.mp3",
                "outro_music": "assets/audio/outro_theme.mp3",
                "transition_effects": [
                    "assets/audio/transition_1.mp3",
                    "assets/audio/transition_2.mp3"
                ],
                "sound_effects": {
                    "race": ["assets/audio/race_sounds.mp3"],
                    "crowd": ["assets/audio/crowd_sounds.mp3"],
                    "crash": ["assets/audio/crash_sound.mp3"]
                }
            },
            "audio_processing": {
                "normalize_volume": True,
                "target_loudness": -16.0,  # LUFS
                "dynamic_range": 8.0,      # dB
                "apply_eq": True,
                "apply_compression": True,
                "add_reverb": False
            },
            "output_formats": [
                {
                    "format": "mp3",
                    "bitrate": "192k",
                    "sample_rate": 44100
                },
                {
                    "format": "ogg",
                    "quality": 6,
                    "sample_rate": 44100
                }
            ],
            "metadata_tags": {
                "artist": "DopCast AI",
                "album": "Motorsport Podcasts",
                "genre": "Sports"
            }
        }
        
        # Merge default config with provided config
        merged_config = default_config.copy()
        if config:
            for key, value in config.items():
                if isinstance(value, dict) and key in merged_config and isinstance(merged_config[key], dict):
                    merged_config[key].update(value)
                else:
                    merged_config[key] = value
        
        super().__init__(name, merged_config)
        
        # Initialize content storage
        self.content_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "content")
        os.makedirs(os.path.join(self.content_dir, "audio", "final"), exist_ok=True)
        
        # Ensure assets directory exists
        assets_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "audio")
        os.makedirs(assets_dir, exist_ok=True)
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process raw audio and enhance with production elements.
        
        Args:
            input_data: Input data containing:
                - audio_metadata: Metadata from the voice synthesis agent
                - script: Original script for reference
                - custom_parameters: Any custom parameters for production
        
        Returns:
            Information about the produced podcast files
        """
        audio_metadata = input_data.get("audio_metadata", {})
        script = input_data.get("script", {})
        custom_parameters = input_data.get("custom_parameters", {})
        
        # Validate input data
        if not audio_metadata:
            self.logger.error("No audio metadata provided")
            return {"error": "No audio metadata provided"}
        
        # Apply any custom parameters
        output_formats = custom_parameters.get("output_formats", self.config["output_formats"])
        
        # Produce the final podcast
        production_data = await self._produce_podcast(
            audio_metadata, script, output_formats
        )
        
        # Save metadata
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        title = script.get("title", "Untitled Episode")
        filename_base = title.lower().replace(" ", "_").replace(":", "") + f"_{timestamp}"
        
        metadata = {
            "title": title,
            "description": script.get("description", ""),
            "produced_at": datetime.now().isoformat(),
            "duration": production_data["duration"],
            "output_files": production_data["output_files"],
            "audio_processing": self.config["audio_processing"],
            "metadata_tags": self._generate_metadata_tags(script)
        }
        
        with open(os.path.join(self.content_dir, "audio", "final", f"{filename_base}_production.json"), "w") as f:
            json.dump(metadata, f, indent=2)
        
        return metadata
    
    async def _produce_podcast(self, audio_metadata: Dict[str, Any], 
                            script: Dict[str, Any],
                            output_formats: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Produce the final podcast with all production elements.
        
        Args:
            audio_metadata: Metadata from voice synthesis
            script: Original script
            output_formats: List of output formats to generate
            
        Returns:
            Information about the produced podcast
        """
        title = script.get("title", "Untitled Episode")
        segment_files = audio_metadata.get("segment_files", [])
        
        # In a real implementation, this would use audio processing libraries
        # to combine segments, add music, balance levels, etc.
        
        # For this example, we'll simulate the process
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_files = []
        
        for format_spec in output_formats:
            format_type = format_spec.get("format", "mp3")
            filename = f"{title.lower().replace(' ', '_').replace(':', '')}_{timestamp}.{format_type}"
            filepath = os.path.join(self.content_dir, "audio", "final", filename)
            
            # Log what would happen in a real implementation
            self.logger.info(f"Would produce final podcast in {format_type} format: {filename}")
            self.logger.info(f"Would apply audio processing: normalization, EQ, compression")
            self.logger.info(f"Would add intro/outro music and sound effects")
            
            # Record the output file
            output_files.append({
                "filename": filename,
                "format": format_type,
                "filepath": filepath,
                "size_estimate": self._estimate_file_size(audio_metadata.get("total_duration", 0), format_spec)
            })
        
        # Return information about the production
        return {
            "duration": audio_metadata.get("total_duration", 0),
            "output_files": output_files
        }
    
    def _estimate_file_size(self, duration: float, format_spec: Dict[str, Any]) -> int:
        """
        Estimate file size based on duration and format.
        
        Args:
            duration: Audio duration in seconds
            format_spec: Format specification
            
        Returns:
            Estimated file size in bytes
        """
        # Simple estimation based on format and duration
        if format_spec.get("format") == "mp3":
            bitrate = format_spec.get("bitrate", "192k")
            bitrate_value = int(bitrate.replace("k", "")) * 1000
            return int((bitrate_value / 8) * duration)  # bytes per second * duration
        
        elif format_spec.get("format") == "ogg":
            # Rough estimate for Ogg Vorbis
            quality = format_spec.get("quality", 6)
            bitrate_estimate = 64000 + (quality * 32000)  # Rough mapping of quality to bitrate
            return int((bitrate_estimate / 8) * duration)  # bytes per second * duration
        
        else:
            # Default estimate for other formats
            return int(192000 / 8 * duration)  # Assume 192kbps
    
    def _generate_metadata_tags(self, script: Dict[str, Any]) -> Dict[str, str]:
        """
        Generate metadata tags for the podcast.
        
        Args:
            script: Original script
            
        Returns:
            Metadata tags
        """
        title = script.get("title", "Untitled Episode")
        description = script.get("description", "")
        
        # Start with default tags
        tags = self.config["metadata_tags"].copy()
        
        # Add episode-specific tags
        tags.update({
            "title": title,
            "comment": description,
            "date": datetime.now().strftime("%Y-%m-%d")
        })
        
        # Determine sport from title for more specific tagging
        if "F1" in title or "Formula 1" in title or "Formula One" in title:
            tags["album"] = "Formula 1 Podcasts"
        elif "MotoGP" in title:
            tags["album"] = "MotoGP Podcasts"
        
        return tags
