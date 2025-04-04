"""
Audio mixer tool for the Audio Production Agent.
Provides enhanced audio mixing capabilities with ffmpeg support.
"""

import logging
import os
import shutil
import time
from typing import Dict, Any, List, Optional

from .ffmpeg_processor import FFmpegProcessor

class AudioMixerTool:
    """
    Enhanced audio mixer tool for mixing and balancing audio segments.
    Uses FFmpeg for reliable audio processing.
    """

    def __init__(self, production_dir: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the audio mixer tool.

        Args:
            production_dir: Directory to store production files
            config: Configuration parameters
        """
        self.logger = logging.getLogger("dopcast.audio_production.audio_mixer")
        self.production_dir = production_dir
        self.config = config or {}

        # Ensure production directories exist
        os.makedirs(os.path.join(self.production_dir, "mixed"), exist_ok=True)

        # Initialize the FFmpeg processor
        self.ffmpeg_processor = FFmpegProcessor(production_dir, config)

    def mix_audio_segments(self, audio_metadata: Dict[str, Any],
                         processed_segments: List[Dict[str, Any]],
                         output_format: str) -> Dict[str, Any]:
        """
        Mix audio segments with proper transitions and balancing using FFmpeg.

        Args:
            audio_metadata: Audio metadata from voice synthesis
            processed_segments: Processed audio segments
            output_format: Output audio format

        Returns:
            Information about the mixed audio
        """
        self.logger.info(f"Mixing audio segments with FFmpeg for {audio_metadata.get('title', 'Untitled Episode')}")

        # Generate filename for the mixed audio
        title = audio_metadata.get("title", "untitled").lower().replace(" ", "_")
        timestamp = int(time.time())
        mixed_filename = f"{title}_mixed_{timestamp}.{output_format}"
        mixed_path = os.path.join(self.production_dir, "mixed", mixed_filename)

        # Collect all audio files to be mixed
        audio_files = []

        # First check if we have a main file from voice synthesis
        main_file_path = os.path.join(os.path.dirname(self.production_dir), "audio", audio_metadata.get("main_file", ""))
        # If file doesn't exist, try the output directory structure
        if not os.path.exists(main_file_path):
            main_file_path = os.path.join(os.path.dirname(os.path.dirname(self.production_dir)), "output", "audio", audio_metadata.get("main_file", ""))

        if os.path.exists(main_file_path):
            audio_files.append(main_file_path)
            self.logger.info(f"Using main audio file: {main_file_path}")

        # Add segment files if available
        for segment in processed_segments:
            segment_path = segment.get("audio_file")
            if segment_path and os.path.exists(segment_path):
                audio_files.append(segment_path)
                self.logger.info(f"Adding segment: {segment_path}")

        # If we have segment files from audio_metadata, add those too
        for segment in audio_metadata.get("segments", []):
            segment_path = segment.get("path")
            if segment_path and os.path.exists(segment_path):
                audio_files.append(segment_path)
                self.logger.info(f"Adding segment from metadata: {segment_path}")

        # If we have no audio files, create an empty file
        if not audio_files:
            self.logger.warning("No audio files found to mix")
            with open(mixed_path, "w") as f:
                f.write("")
            total_duration = 0
        else:
            try:
                # Use FFmpeg to stitch the audio files
                self.ffmpeg_processor.stitch_audio_files(audio_files, mixed_path)

                # Get audio information
                audio_info = self.ffmpeg_processor.get_audio_info(mixed_path)
                total_duration = audio_info.get("duration", 0)

                self.logger.info(f"Successfully mixed {len(audio_files)} audio files with total duration: {total_duration} seconds")
            except Exception as e:
                self.logger.error(f"Error mixing audio with FFmpeg: {e}")
                # Fallback to simple copy if FFmpeg fails
                if os.path.exists(main_file_path):
                    shutil.copy(main_file_path, mixed_path)
                    self.logger.info(f"Fallback: Copied main file to {mixed_path}")
                    total_duration = audio_metadata.get("total_duration", 0)
                else:
                    with open(mixed_path, "w") as f:
                        f.write("")
                    total_duration = 0

        return {
            "mixed_file": mixed_filename,
            "mixed_path": mixed_path,
            "total_duration": total_duration,
            "format": output_format
        }

    def apply_transitions(self, mixed_audio: Dict[str, Any],
                        transition_points: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Apply transitions between sections.

        Args:
            mixed_audio: Mixed audio information
            transition_points: List of transition points

        Returns:
            Updated mixed audio information
        """
        # In a real implementation, this would apply transitions at specified points

        # For this implementation, we'll just return the mixed audio information
        self.logger.info(f"Would apply {len(transition_points)} transitions to the mixed audio")

        return mixed_audio

    def normalize_audio_levels(self, mixed_audio: Dict[str, Any],
                             target_level: float) -> Dict[str, Any]:
        """
        Normalize audio levels to a target level using FFmpeg.

        Args:
            mixed_audio: Mixed audio information
            target_level: Target audio level in dB LUFS

        Returns:
            Updated mixed audio information
        """
        self.logger.info(f"Normalizing audio levels to {target_level} dB LUFS")

        mixed_path = mixed_audio.get("mixed_path", "")
        if not os.path.exists(mixed_path):
            self.logger.warning(f"Mixed file not found: {mixed_path}")
            return mixed_audio

        try:
            # Generate filename for the normalized audio
            filename_parts = os.path.basename(mixed_path).split(".")
            if len(filename_parts) < 2:
                normalized_filename = f"{filename_parts[0]}_normalized.mp3"
            else:
                extension = filename_parts[-1]
                base_name = ".".join(filename_parts[:-1])
                normalized_filename = f"{base_name}_normalized.{extension}"

            normalized_path = os.path.join(os.path.dirname(mixed_path), normalized_filename)

            # Use FFmpeg to normalize the audio
            self.ffmpeg_processor.normalize_audio(mixed_path, normalized_path, target_level)

            # Update the mixed audio information
            mixed_audio["mixed_path"] = normalized_path
            mixed_audio["mixed_file"] = normalized_filename

            # Get updated audio information
            audio_info = self.ffmpeg_processor.get_audio_info(normalized_path)
            mixed_audio["total_duration"] = audio_info.get("duration", mixed_audio.get("total_duration", 0))

            self.logger.info(f"Successfully normalized audio to {target_level} dB LUFS")
        except Exception as e:
            self.logger.error(f"Error normalizing audio with FFmpeg: {e}")
            # Keep the original file if normalization fails

        return mixed_audio
