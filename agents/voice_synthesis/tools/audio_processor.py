"""
Audio processor tool for the Voice Synthesis Agent.
Provides enhanced audio processing capabilities.
"""

import logging
import os
import shutil
import subprocess
import time
from typing import Dict, Any, List, Optional

class AudioProcessorTool:
    """
    Enhanced audio processor tool for processing and combining audio segments.
    """

    def __init__(self, audio_dir: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the audio processor tool.

        Args:
            audio_dir: Directory to store audio files
            config: Configuration parameters
        """
        self.logger = logging.getLogger("dopcast.voice_synthesis.audio_processor")
        self.audio_dir = audio_dir
        self.config = config or {}

    def combine_audio_segments(self, intro_audio: Dict[str, Any],
                             section_audio: List[Dict[str, Any]],
                             title: str, audio_format: str) -> Dict[str, Any]:
        """
        Combine audio segments into a complete episode.

        Args:
            intro_audio: Intro audio information
            section_audio: List of section audio information
            title: Episode title
            audio_format: Audio format

        Returns:
            Information about the combined audio
        """
        # We'll use ffmpeg directly for audio concatenation

        # Generate filename for the episode
        timestamp = int(time.time())
        episode_filename = f"{title.lower().replace(' ', '_')}_{timestamp}.{audio_format}"
        episode_path = os.path.join(self.audio_dir, episode_filename)

        try:
            # Collect all audio files to combine
            all_audio_files = []
            if os.path.exists(intro_audio.get("path", "")):
                all_audio_files.append(intro_audio["path"])

            # Add all section audio files
            for section in section_audio:
                for segment in section.get("segment_files", []):
                    if os.path.exists(segment.get("path", "")):
                        all_audio_files.append(segment["path"])

            self.logger.info(f"Combining {len(all_audio_files)} audio files into {episode_path}")

            if len(all_audio_files) == 0:
                self.logger.warning("No audio files to combine")
                # Create an empty file
                with open(episode_path, "w") as f:
                    f.write("")
                return {
                    "main_file": episode_filename,
                    "segment_files": [],
                    "total_duration": 0
                }

            if len(all_audio_files) == 1:
                # Just copy the single file
                shutil.copy(all_audio_files[0], episode_path)
                self.logger.info(f"Copied single audio file to {episode_path}")
            else:
                # Use ffmpeg to concatenate all audio files
                try:
                    # Create a temporary file list for ffmpeg
                    file_list_path = os.path.join(self.audio_dir, f"filelist_{timestamp}.txt")

                    # Check which files actually exist
                    existing_files = []
                    for audio_file in all_audio_files:
                        if os.path.exists(audio_file) and os.path.getsize(audio_file) > 0:
                            # Use absolute path to avoid issues
                            abs_path = os.path.abspath(audio_file)
                            existing_files.append(abs_path)
                        else:
                            self.logger.warning(f"Audio file not found or empty: {audio_file}")

                    # If no files exist, create a dummy file
                    if not existing_files:
                        self.logger.error("No valid audio files found for combining")
                        # Create a dummy file with silence
                        dummy_path = os.path.join(self.audio_dir, f"dummy_{timestamp}.mp3")
                        try:
                            # Create a 1-second silent MP3 using ffmpeg
                            subprocess.run([
                                "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
                                "-t", "1", "-q:a", "9", "-acodec", "libmp3lame", dummy_path
                            ], check=True, capture_output=True)
                            existing_files.append(dummy_path)
                            self.logger.info(f"Created dummy silent audio file: {dummy_path}")
                        except Exception as e:
                            self.logger.error(f"Failed to create dummy audio file: {e}")

                    # Write the file list
                    with open(file_list_path, "w") as f:
                        for audio_file in existing_files:
                            f.write(f"file '{audio_file}'\n")

                    # Use ffmpeg to concatenate the files
                    cmd = [
                        "ffmpeg",
                        "-y",  # Overwrite output file if it exists
                        "-f", "concat",
                        "-safe", "0",
                        "-i", file_list_path,
                        "-c", "copy",
                        episode_path
                    ]

                    self.logger.info(f"Running ffmpeg command: {' '.join(cmd)}")
                    subprocess.run(cmd, check=True)

                    # Clean up the temporary file
                    os.remove(file_list_path)

                    self.logger.info(f"Successfully combined {len(all_audio_files)} audio files to {episode_path}")
                except Exception as e:
                    self.logger.error(f"Error combining audio with ffmpeg: {e}")
                    # Fallback to using the first file
                    shutil.copy(all_audio_files[0], episode_path)
                    self.logger.info(f"Fallback: Copied first audio file to {episode_path}")

            # Calculate total duration
            total_duration = intro_audio.get("duration", 0)
            segment_files = []

            for section in section_audio:
                for segment in section.get("segment_files", []):
                    segment_files.append(segment)
                    total_duration += segment.get("duration", 0)

            return {
                "main_file": episode_filename,
                "segment_files": segment_files,
                "total_duration": total_duration
            }

        except Exception as e:
            self.logger.error(f"Error combining audio segments: {e}")
            # Create an empty file as fallback
            with open(episode_path, "w") as f:
                f.write("")

            return {
                "main_file": episode_filename,
                "segment_files": [],
                "total_duration": 0
            }

    def adjust_audio_parameters(self, voice_profile: Dict[str, Any],
                              emotion: str) -> Dict[str, Any]:
        """
        Adjust voice parameters based on detected emotion.

        Args:
            voice_profile: Base voice profile
            emotion: Detected emotion

        Returns:
            Adjusted voice profile
        """
        adjusted_profile = voice_profile.copy()

        # Apply emotion-specific adjustments
        emotion_adjustments = self.config.get("emotion_mapping", {}).get(emotion, {})

        for param, value in emotion_adjustments.items():
            if param in adjusted_profile:
                adjusted_profile[param] += value

        return adjusted_profile
