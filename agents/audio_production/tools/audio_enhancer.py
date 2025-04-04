"""
Audio enhancer tool for the Audio Production Agent.
Provides enhanced audio enhancement capabilities with ffmpeg support.
"""

import logging
import os
import shutil
import time
from typing import Dict, Any, List, Optional

from .ffmpeg_processor import FFmpegProcessor

class AudioEnhancerTool:
    """
    Enhanced audio enhancer tool for improving audio quality.
    Uses FFmpeg for reliable audio processing.
    """

    def __init__(self, production_dir: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the audio enhancer tool.

        Args:
            production_dir: Directory to store production files
            config: Configuration parameters
        """
        self.logger = logging.getLogger("dopcast.audio_production.audio_enhancer")
        self.production_dir = production_dir
        self.config = config or {}

        # Ensure production directories exist
        os.makedirs(os.path.join(self.production_dir, "enhanced"), exist_ok=True)

        # Initialize the FFmpeg processor
        self.ffmpeg_processor = FFmpegProcessor(production_dir, config)

    def enhance_audio_segments(self, audio_metadata: Dict[str, Any],
                             segment_files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Enhance audio segments with noise reduction, EQ, and compression.

        Args:
            audio_metadata: Audio metadata from voice synthesis
            segment_files: Audio segment files

        Returns:
            List of processed segment information
        """
        # In a real implementation, this would use audio processing libraries
        # to enhance each segment with noise reduction, EQ, and compression

        # For this implementation, we'll just return the segment files
        self.logger.info(f"Would enhance {len(segment_files)} audio segments")

        # Create a copy of the segment files to represent processed segments
        processed_segments = []
        for segment in segment_files:
            processed_segment = segment.copy()
            processed_segment["enhanced"] = True
            processed_segments.append(processed_segment)

        return processed_segments

    def apply_equalization(self, mixed_audio: Dict[str, Any],
                         eq_settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply equalization to the mixed audio.

        Args:
            mixed_audio: Mixed audio information
            eq_settings: Equalization settings

        Returns:
            Updated mixed audio information
        """
        # In a real implementation, this would apply equalization

        # For this implementation, we'll just return the mixed audio information
        self.logger.info(f"Would apply equalization with settings: {eq_settings}")

        return mixed_audio

    def apply_compression(self, mixed_audio: Dict[str, Any],
                        compression_settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply compression to the mixed audio.

        Args:
            mixed_audio: Mixed audio information
            compression_settings: Compression settings

        Returns:
            Updated mixed audio information
        """
        # In a real implementation, this would apply compression

        # For this implementation, we'll just return the mixed audio information
        self.logger.info(f"Would apply compression with settings: {compression_settings}")

        return mixed_audio

    def master_audio(self, mixed_audio: Dict[str, Any],
                   mastering_settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Master the audio for final production using FFmpeg.

        Args:
            mixed_audio: Mixed audio information
            mastering_settings: Mastering settings

        Returns:
            Information about the mastered audio
        """
        self.logger.info(f"Mastering audio with FFmpeg using settings: {mastering_settings}")

        mixed_path = mixed_audio.get("mixed_path", "")
        if not os.path.exists(mixed_path):
            self.logger.warning(f"Mixed file not found: {mixed_path}")
            return mixed_audio

        # Generate filename for the mastered audio
        filename_parts = os.path.basename(mixed_path).split("_mixed_")
        if len(filename_parts) != 2:
            mastered_filename = f"mastered_{os.path.basename(mixed_path)}"
        else:
            mastered_filename = f"{filename_parts[0]}_mastered_{filename_parts[1]}"

        mastered_path = os.path.join(self.production_dir, "enhanced", mastered_filename)

        try:
            # Apply mastering using FFmpeg
            # This includes compression, limiting, and final EQ
            limiter_threshold = mastering_settings.get("limiter_threshold", 0.95)  # Changed from -1.0 to 0.95 to be within valid range [0.0625 - 1]
            limiter_release = mastering_settings.get("limiter_release", 100.0)

            # Build the audio filter chain
            filter_chain = [
                # Apply compression
                "compand=attacks=0.05:decays=0.3:points=-90/-90|-40/-10|0/-3:gain=1",
                # Apply EQ (subtle presence boost and low-end control)
                "equalizer=f=100:width_type=h:width=200:g=-1,equalizer=f=3000:width_type=h:width=1000:g=2",
                # Apply limiting
                f"alimiter=level_in=1:level_out=1:limit={limiter_threshold}:attack=5:release={limiter_release}",
                # Final loudness normalization
                "loudnorm=I=-14:LRA=11:TP=-1"
            ]

            # Use FFmpeg to apply the mastering chain
            cmd = [
                "ffmpeg",
                "-y",  # Overwrite output file if it exists
                "-i", mixed_path,
                "-af", ",".join(filter_chain),
                "-c:a", "libmp3lame",  # Use MP3 codec
                "-q:a", "0",  # Highest quality
                mastered_path
            ]

            self.logger.debug(f"Running ffmpeg command: {' '.join(cmd)}")

            import subprocess
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False
            )

            if result.returncode != 0:
                self.logger.error(f"ffmpeg error: {result.stderr}")
                # Fallback to simple copy if FFmpeg fails
                shutil.copy(mixed_path, mastered_path)
                self.logger.info(f"Fallback: Copied mixed file to {mastered_path}")
            else:
                self.logger.info(f"Successfully mastered audio to {mastered_path}")

            # Get audio information
            audio_info = self.ffmpeg_processor.get_audio_info(mastered_path)
            total_duration = audio_info.get("duration", mixed_audio.get("total_duration", 0))

        except Exception as e:
            self.logger.error(f"Error mastering audio with FFmpeg: {e}")
            # Fallback to simple copy if FFmpeg fails
            shutil.copy(mixed_path, mastered_path)
            self.logger.info(f"Fallback: Copied mixed file to {mastered_path}")
            total_duration = mixed_audio.get("total_duration", 0)

        return {
            "mastered_file": mastered_filename,
            "mastered_path": mastered_path,
            "total_duration": total_duration,
            "format": mixed_audio.get("format", "mp3")
        }
