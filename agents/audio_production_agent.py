import os
import json
import asyncio
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
import pyttsx3
import shutil
import wave
import numpy as np

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
            },
            "timeouts": {
                "process": 120,  # seconds
                "produce_podcast": 60,  # seconds
                "tts_generation": 30  # seconds
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
        
        # Initialize TTS engine for intro/outro
        try:
            self.engine = pyttsx3.init()
        except Exception as e:
            self.logger.error(f"Failed to initialize TTS engine: {str(e)}")
            self.engine = None
    
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
        start_time = time.time()
        process_timeout = self.config.get("timeouts", {}).get("process", 120)  # 2 minute default timeout
        
        audio_metadata = input_data.get("audio_metadata", {})
        script = input_data.get("script", {})
        custom_parameters = input_data.get("custom_parameters", {})
        
        # Validate input data
        if not audio_metadata:
            self.logger.error("No audio metadata provided")
            return {"error": "No audio metadata provided"}
        
        # Apply any custom parameters
        output_formats = custom_parameters.get("output_formats", self.config["output_formats"])
        
        try:
            # Create a task with timeout for the produce_podcast method
            produce_task = asyncio.create_task(self._produce_podcast(audio_metadata, script, output_formats))
            
            # Set a timeout for the production process
            try:
                production_data = await asyncio.wait_for(produce_task, timeout=process_timeout)
                self.logger.info(f"Audio production completed in {time.time() - start_time:.2f} seconds")
            except asyncio.TimeoutError:
                self.logger.error(f"Audio production timed out after {process_timeout} seconds")
                # Create fallback production data
                production_data = self._create_fallback_production(script)
                self.logger.info("Created fallback audio production data")
            
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
            
            metadata_path = os.path.join(self.content_dir, "audio", "final", f"{filename_base}_production.json")
            with open(metadata_path, "w") as f:
                json.dump(metadata, f, indent=2)
            
            self.logger.info(f"Audio production metadata saved to {metadata_path}")
            return metadata
            
        except Exception as e:
            elapsed_time = time.time() - start_time
            self.logger.error(f"Error in audio production after {elapsed_time:.2f} seconds: {str(e)}")
            # Return a basic error response with any available audio data
            return {
                "error": f"Audio production failed: {str(e)}",
                "partial_data": True,
                "duration": audio_metadata.get("total_duration", 0),
                "main_file": audio_metadata.get("main_file", "")
            }
    
    def _create_fallback_production(self, script: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create fallback production data when the normal process times out.
        
        Args:
            script: Original script
            
        Returns:
            Basic production data with available information
        """
        title = script.get("title", "Untitled Episode")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{title.lower().replace(' ', '_').replace(':', '')}_{timestamp}.mp3"
        filepath = os.path.join(self.content_dir, "audio", "final", filename)
        
        # Create a simple fallback message file if possible
        try:
            if self.engine:
                fallback_text = f"This is a fallback audio for {title}. The full production process timed out."
                self.engine.save_to_file(fallback_text, filepath)
                self.engine.runAndWait()
                duration = len(fallback_text.split()) / 150 * 60  # Rough estimate
                file_exists = os.path.exists(filepath)
            else:
                # Create an empty file if TTS is not available
                with open(filepath, 'w') as f:
                    f.write("")
                duration = 0
                file_exists = True
        except Exception as e:
            self.logger.error(f"Could not create fallback audio: {str(e)}")
            duration = 0
            file_exists = False
        
        return {
            "duration": duration,
            "output_files": [
                {
                    "filename": filename,
                    "format": "mp3",
                    "filepath": filepath if file_exists else "",
                    "size_estimate": self._estimate_file_size(duration, {"format": "mp3", "bitrate": "128k"}),
                    "actual_size": os.path.getsize(filepath) if file_exists and os.path.exists(filepath) else 0,
                    "note": "Fallback audio due to timeout"
                }
            ]
        }
    
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
        start_time = time.time()
        produce_timeout = self.config.get("timeouts", {}).get("produce_podcast", 60)  # 1 minute default timeout
        
        title = script.get("title", "Untitled Episode")
        segment_files = audio_metadata.get("segment_files", [])
        total_duration = audio_metadata.get("total_duration", 0)
        main_file = audio_metadata.get("main_file", "")
        
        # Create a simple intro and outro with longer pauses
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        intro_filename = f"intro_{timestamp}.mp3"
        outro_filename = f"outro_{timestamp}.mp3"
        
        intro_path = os.path.join(self.content_dir, "audio", "segments", intro_filename)
        outro_path = os.path.join(self.content_dir, "audio", "segments", outro_filename)
        
        # Ensure the TTS engine is available
        if not self.engine:
            self.logger.warning("TTS engine not available, skipping intro/outro generation")
        else:
            try:
                # Generate intro and outro with timeout
                tts_timeout = self.config.get("timeouts", {}).get("tts_generation", 30)
                
                # Save current rate
                rate = self.engine.getProperty('rate')
                self.engine.setProperty('rate', int(rate * 0.4))  # 40% of normal speed
                
                # Create intro with music mention
                intro_text = f"Welcome to {title}. Today we'll be exploring the latest developments in the world of motorsport. Let's get started."
                
                tts_task = asyncio.to_thread(self._tts_save_to_file, intro_text, intro_path)
                try:
                    await asyncio.wait_for(tts_task, timeout=tts_timeout)
                    self.logger.info(f"Created intro audio: {intro_path}")
                except asyncio.TimeoutError:
                    self.logger.warning(f"Intro generation timed out after {tts_timeout} seconds")
                
                # Create outro with longer thank you message
                outro_text = f"Thank you for listening to {title}. We hope you enjoyed this episode and gained valuable insights. Please subscribe for more episodes, and join us next time for more exciting discussions. This has been a DopCast production."
                
                tts_task = asyncio.to_thread(self._tts_save_to_file, outro_text, outro_path)
                try:
                    await asyncio.wait_for(tts_task, timeout=tts_timeout)
                    self.logger.info(f"Created outro audio: {outro_path}")
                except asyncio.TimeoutError:
                    self.logger.warning(f"Outro generation timed out after {tts_timeout} seconds")
                
                # Reset rate to normal
                self.engine.setProperty('rate', rate)
                
                # Add intro and outro to segment files list if they were created
                if os.path.exists(intro_path):
                    intro_duration = len(intro_text.split()) / 150 * 60 * 2.5  # 2.5x longer for pauses
                    segment_files.insert(0, {
                        "filename": intro_filename, 
                        "type": "intro", 
                        "duration": intro_duration, 
                        "path": intro_path
                    })
                    total_duration += intro_duration
                
                if os.path.exists(outro_path):
                    outro_duration = len(outro_text.split()) / 150 * 60 * 2.5  # 2.5x longer for pauses
                    segment_files.append({
                        "filename": outro_filename, 
                        "type": "outro", 
                        "duration": outro_duration, 
                        "path": outro_path
                    })
                    total_duration += outro_duration
            except Exception as e:
                self.logger.error(f"Error generating intro/outro: {str(e)}")
        
        # Check if we're approaching the timeout, skip non-essential processing if needed
        elapsed_time = time.time() - start_time
        remaining_time = produce_timeout - elapsed_time
        
        if remaining_time < 10:  # If less than 10 seconds remaining
            self.logger.warning(f"Approaching timeout, skipping audio processing (remaining: {remaining_time:.2f}s)")
        
        # Generate output files for each format
        output_files = []
        
        for format_spec in output_formats:
            format_type = format_spec.get("format", "mp3")
            filename = f"{title.lower().replace(' ', '_').replace(':', '')}_{timestamp}.{format_type}"
            filepath = os.path.join(self.content_dir, "audio", "final", filename)
            
            # For this implementation, we'll use the main file from voice synthesis if available,
            # otherwise we'll use the most substantial segment file
            main_file_path = os.path.join(self.content_dir, "audio", main_file) if main_file else ""
            
            if os.path.exists(main_file_path) and os.path.getsize(main_file_path) > 0:
                self.logger.info(f"Using main file for final podcast: {main_file}")
                shutil.copy(main_file_path, filepath)
                output_files.append({
                    "filename": filename,
                    "format": format_type,
                    "filepath": filepath,
                    "size_estimate": self._estimate_file_size(total_duration, format_spec),
                    "actual_size": os.path.getsize(filepath) if os.path.exists(filepath) else 0
                })
            elif segment_files:
                self.logger.info(f"Creating podcast file from best available segment: {filename}")
                
                # Find the most substantial segment file (largest file size)
                best_segment = None
                largest_size = 0
                
                for segment in segment_files:
                    path = segment.get("path", "")
                    if os.path.exists(path):
                        size = os.path.getsize(path)
                        if size > largest_size:
                            largest_size = size
                            best_segment = segment
                
                if best_segment:
                    self.logger.info(f"Using segment: {best_segment.get('filename')} as final podcast")
                    shutil.copy(best_segment.get("path"), filepath)
                    
                    output_files.append({
                        "filename": filename,
                        "format": format_type,
                        "filepath": filepath,
                        "size_estimate": self._estimate_file_size(total_duration, format_spec),
                        "actual_size": os.path.getsize(filepath) if os.path.exists(filepath) else 0,
                        "note": f"Using best available segment: {best_segment.get('filename')}"
                    })
                else:
                    self.logger.warning(f"No valid segments found")
                    
                    # Create a placeholder file
                    placeholder_text = f"Welcome to {title}. This is a placeholder for the full podcast episode about {script.get('description', 'motorsport topics')}. The complete episode will feature in-depth discussions, expert analysis, and the latest news from the world of motorsport."
                    
                    if self.engine:
                        self.engine.save_to_file(placeholder_text, filepath)
                        self.engine.runAndWait()
                    else:
                        # Create an empty file if TTS is not available
                        with open(filepath, 'w') as f:
                            f.write("")
                    
                    placeholder_duration = len(placeholder_text.split()) / 150 * 60 * 1.2  # 20% longer for pauses
                    
                    output_files.append({
                        "filename": filename,
                        "format": format_type,
                        "filepath": filepath,
                        "size_estimate": self._estimate_file_size(placeholder_duration, format_spec),
                        "actual_size": os.path.getsize(filepath) if os.path.exists(filepath) else 0,
                        "note": "Placeholder audio file created"
                    })
            else:
                self.logger.warning(f"No audio sources available, creating placeholder")
                
                # Create a text placeholder file
                placeholder_text = f"Welcome to {title}. This is a placeholder for the full podcast episode. No audio segments were available for production."
                
                if self.engine:
                    self.engine.save_to_file(placeholder_text, filepath)
                    self.engine.runAndWait()
                else:
                    # Create an empty file if TTS is not available
                    with open(filepath, 'w') as f:
                        f.write("")
                
                placeholder_duration = len(placeholder_text.split()) / 150 * 60
                
                output_files.append({
                    "filename": filename,
                    "format": format_type,
                    "filepath": filepath,
                    "size_estimate": self._estimate_file_size(placeholder_duration, format_spec),
                    "actual_size": os.path.getsize(filepath) if os.path.exists(filepath) else 0,
                    "note": "Placeholder audio (no segments available)"
                })
        
        final_duration = total_duration if total_duration > 0 else (audio_metadata.get("total_duration", 0) or 60)  # Default to 1 minute
        
        self.logger.info(f"Audio production completed in {time.time() - start_time:.2f} seconds")
        return {
            "duration": final_duration,
            "output_files": output_files
        }
    
    def _tts_save_to_file(self, text: str, file_path: str) -> None:
        """
        Helper method to save TTS to file for async execution.
        
        Args:
            text: Text to convert to speech
            file_path: Output file path
        """
        self.engine.save_to_file(text, file_path)
        self.engine.runAndWait()
    
    def _estimate_file_size(self, duration: float, format_spec: Dict[str, Any]) -> int:
        """
        Estimate the file size based on duration and format.
        
        Args:
            duration: Duration in seconds
            format_spec: Format specification
            
        Returns:
            Estimated file size in bytes
        """
        # Default size estimate is around 16KB per second for good quality MP3
        bytes_per_second = 16 * 1024
        
        # Adjust based on format
        format_type = format_spec.get("format", "mp3").lower()
        
        if format_type == "mp3":
            # Parse bitrate
            bitrate_str = format_spec.get("bitrate", "192k")
            try:
                if bitrate_str.endswith("k"):
                    bitrate = int(bitrate_str[:-1]) * 1000
                else:
                    bitrate = int(bitrate_str)
                
                # MP3 bitrate is roughly bytes per second * 8
                bytes_per_second = bitrate / 8
            except (ValueError, AttributeError):
                pass
        elif format_type == "ogg":
            # Vorbis quality settings (0-10)
            quality = format_spec.get("quality", 6)
            # Map quality to approximate bitrate
            quality_to_kbps = {
                0: 48, 1: 64, 2: 80, 3: 96, 4: 112,
                5: 128, 6: 160, 7: 192, 8: 224, 9: 256, 10: 320
            }
            bitrate = quality_to_kbps.get(quality, 160) * 1000 / 8
            bytes_per_second = bitrate
        elif format_type == "wav":
            # Uncompressed audio
            sample_rate = format_spec.get("sample_rate", 44100)
            bit_depth = format_spec.get("bit_depth", 16)
            channels = format_spec.get("channels", 2)
            bytes_per_second = (sample_rate * bit_depth * channels) / 8
        
        return int(duration * bytes_per_second)
    
    def _generate_metadata_tags(self, script: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate metadata tags for the audio file.
        
        Args:
            script: Script data
            
        Returns:
            Metadata tags dictionary
        """
        base_tags = self.config["metadata_tags"].copy()
        
        # Add script-specific metadata
        base_tags.update({
            "title": script.get("title", "Untitled Episode"),
            "year": datetime.now().year,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "copyright": f"© {datetime.now().year} DopCast AI"
        })
        
        # Add description if available
        if "description" in script:
            base_tags["comment"] = script["description"]
        
        return base_tags
