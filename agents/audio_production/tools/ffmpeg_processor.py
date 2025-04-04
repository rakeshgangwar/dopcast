"""
FFmpeg-based audio processor for the Audio Production Agent.
Provides reliable audio file stitching and processing using direct ffmpeg commands.
Falls back to pydub when ffmpeg is not directly available.
"""

import logging
import os
import subprocess
import tempfile
import json
import shutil
from typing import Dict, Any, List, Optional, Tuple

# Try to import pydub for fallback implementation
try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False

class FFmpegProcessor:
    """
    FFmpeg-based audio processor for reliable audio file operations.
    """

    def __init__(self, production_dir: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the FFmpeg processor.

        Args:
            production_dir: Directory to store production files
            config: Configuration parameters
        """
        self.logger = logging.getLogger("dopcast.audio_production.ffmpeg_processor")
        self.production_dir = production_dir
        self.config = config or {}
        self.ffmpeg_available = False
        self.ffprobe_available = False

        # Check if ffmpeg is available
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False
            )
            if result.returncode == 0:
                self.ffmpeg_available = True
                self.logger.info(f"ffmpeg found: {result.stdout.splitlines()[0]}")
            else:
                self.logger.warning("ffmpeg not found or not working properly")
        except Exception as e:
            self.logger.warning(f"Error checking ffmpeg: {e}")

        # Check if ffprobe is available
        try:
            result = subprocess.run(
                ["ffprobe", "-version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False
            )
            if result.returncode == 0:
                self.ffprobe_available = True
                self.logger.info(f"ffprobe found: {result.stdout.splitlines()[0]}")
            else:
                self.logger.warning("ffprobe not found or not working properly")
        except Exception as e:
            self.logger.warning(f"Error checking ffprobe: {e}")

        # Log fallback availability
        if not self.ffmpeg_available:
            if PYDUB_AVAILABLE:
                self.logger.info("Using pydub as fallback for audio processing")
            else:
                self.logger.warning("Neither ffmpeg nor pydub is available for audio processing")

    def stitch_audio_files(self,
                         audio_files: List[str],
                         output_path: str,
                         crossfade_duration: float = 0.3) -> str:
        """
        Stitch multiple audio files together using ffmpeg or pydub as fallback.

        Args:
            audio_files: List of audio file paths to stitch
            output_path: Path for the output file
            crossfade_duration: Duration of crossfade between files in seconds

        Returns:
            Path to the stitched audio file
        """
        if not audio_files:
            raise ValueError("No audio files provided for stitching")

        self.logger.info(f"Stitching {len(audio_files)} audio files")

        # Check if any of the input files exist
        existing_files = [f for f in audio_files if os.path.exists(f)]
        if not existing_files:
            self.logger.error("None of the input audio files exist")
            raise FileNotFoundError("No input audio files found")

        # If some files don't exist, log a warning
        if len(existing_files) < len(audio_files):
            self.logger.warning(f"Only {len(existing_files)} out of {len(audio_files)} audio files exist")
            audio_files = existing_files

        # If only one file exists, just copy it to the output path
        if len(audio_files) == 1:
            self.logger.info(f"Only one audio file available, copying to output")
            shutil.copy(audio_files[0], output_path)
            return output_path

        # Try using ffmpeg if available
        if self.ffmpeg_available:
            # Create a temporary file list for ffmpeg
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                file_list_path = f.name
                for audio_file in audio_files:
                    f.write(f"file '{os.path.abspath(audio_file)}'\n")

            try:
                # Use ffmpeg to concatenate the files
                cmd = [
                    "ffmpeg",
                    "-y",  # Overwrite output file if it exists
                    "-f", "concat",
                    "-safe", "0",
                    "-i", file_list_path,
                    "-c", "copy",  # Copy codec (fast)
                    output_path
                ]

                self.logger.debug(f"Running ffmpeg command: {' '.join(cmd)}")

                result = subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=False
                )

                if result.returncode != 0:
                    self.logger.error(f"ffmpeg error: {result.stderr}")
                    # Fall back to pydub if ffmpeg fails
                    if PYDUB_AVAILABLE:
                        self.logger.info("Falling back to pydub for audio stitching")
                        return self._stitch_with_pydub(audio_files, output_path, crossfade_duration)
                    else:
                        raise RuntimeError(f"ffmpeg failed and pydub is not available")

                self.logger.info(f"Successfully stitched audio files with ffmpeg to {output_path}")
                return output_path

            finally:
                # Clean up the temporary file
                try:
                    os.unlink(file_list_path)
                except Exception as e:
                    self.logger.warning(f"Error removing temporary file: {e}")

        # Fall back to pydub if ffmpeg is not available
        elif PYDUB_AVAILABLE:
            self.logger.info("Using pydub for audio stitching")
            return self._stitch_with_pydub(audio_files, output_path, crossfade_duration)

        # If neither ffmpeg nor pydub is available, just copy the first file
        else:
            self.logger.warning("Neither ffmpeg nor pydub is available, copying first file")
            shutil.copy(audio_files[0], output_path)
            return output_path

    def _stitch_with_pydub(self, audio_files: List[str], output_path: str, crossfade_duration: float = 0.3) -> str:
        """
        Stitch audio files using pydub as a fallback method.

        Args:
            audio_files: List of audio file paths to stitch
            output_path: Path for the output file
            crossfade_duration: Duration of crossfade between files in seconds

        Returns:
            Path to the stitched audio file
        """
        try:
            # Create an empty audio segment
            merged = AudioSegment.silent(duration=0)

            # Add each segment with crossfade
            for i, audio_file in enumerate(audio_files):
                # Load the audio segment
                audio = AudioSegment.from_file(audio_file)

                # Add with crossfade if not the first file
                if i > 0 and crossfade_duration > 0:
                    crossfade_ms = int(crossfade_duration * 1000)  # Convert to milliseconds
                    merged = merged.append(audio, crossfade=crossfade_ms)
                else:
                    merged = merged + audio

            # Export the merged audio
            merged.export(output_path, format=os.path.splitext(output_path)[1][1:])
            self.logger.info(f"Successfully stitched {len(audio_files)} audio files with pydub to {output_path}")

            return output_path
        except Exception as e:
            self.logger.error(f"Error stitching with pydub: {e}")
            # Last resort: copy the first file
            shutil.copy(audio_files[0], output_path)
            self.logger.warning(f"Fallback to copying first file to {output_path}")
            return output_path

    def mix_audio_with_background(self,
                                main_audio_path: str,
                                background_audio_path: str,
                                output_path: str,
                                background_volume: float = 0.2) -> str:
        """
        Mix main audio with background audio (e.g., music) using ffmpeg.

        Args:
            main_audio_path: Path to the main audio file
            background_audio_path: Path to the background audio file
            output_path: Path for the output file
            background_volume: Volume level for the background (0.0-1.0)

        Returns:
            Path to the mixed audio file
        """
        self.logger.info(f"Mixing audio with background using ffmpeg")

        cmd = [
            "ffmpeg",
            "-y",  # Overwrite output file if it exists
            "-i", main_audio_path,
            "-i", background_audio_path,
            "-filter_complex", f"[1:a]volume={background_volume}[bg]; [0:a][bg]amix=inputs=2:duration=longest",
            "-c:a", "libmp3lame",  # Use MP3 codec
            "-q:a", "2",  # Quality setting
            output_path
        ]

        self.logger.debug(f"Running ffmpeg command: {' '.join(cmd)}")

        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )

        if result.returncode != 0:
            self.logger.error(f"ffmpeg error: {result.stderr}")
            raise RuntimeError(f"ffmpeg failed: {result.stderr}")

        self.logger.info(f"Successfully mixed audio with background to {output_path}")
        return output_path

    def normalize_audio(self,
                      input_path: str,
                      output_path: str,
                      target_level: float = -16.0) -> str:
        """
        Normalize audio levels using ffmpeg or pydub as fallback.

        Args:
            input_path: Path to the input audio file
            output_path: Path for the output file
            target_level: Target loudness level in dB LUFS

        Returns:
            Path to the normalized audio file
        """
        if not os.path.exists(input_path):
            self.logger.error(f"Input file not found: {input_path}")
            raise FileNotFoundError(f"Input file not found: {input_path}")

        self.logger.info(f"Normalizing audio to {target_level} dB LUFS")

        # Try using ffmpeg if available
        if self.ffmpeg_available:
            self.logger.info("Using ffmpeg for normalization")
            cmd = [
                "ffmpeg",
                "-y",  # Overwrite output file if it exists
                "-i", input_path,
                "-af", f"loudnorm=I={target_level}:LRA=11:TP=-1.5",
                "-c:a", "libmp3lame",  # Use MP3 codec
                "-q:a", "2",  # Quality setting
                output_path
            ]

            self.logger.debug(f"Running ffmpeg command: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False
            )

            if result.returncode != 0:
                self.logger.error(f"ffmpeg error: {result.stderr}")
                # Fall back to pydub if ffmpeg fails
                if PYDUB_AVAILABLE:
                    self.logger.info("Falling back to pydub for normalization")
                    return self._normalize_with_pydub(input_path, output_path, target_level)
                else:
                    # If pydub is not available, just copy the file
                    self.logger.warning("Falling back to copying the file without normalization")
                    shutil.copy(input_path, output_path)
                    return output_path

            self.logger.info(f"Successfully normalized audio with ffmpeg to {output_path}")
            return output_path

        # Fall back to pydub if ffmpeg is not available
        elif PYDUB_AVAILABLE:
            self.logger.info("Using pydub for normalization")
            return self._normalize_with_pydub(input_path, output_path, target_level)

        # If neither ffmpeg nor pydub is available, just copy the file
        else:
            self.logger.warning("Neither ffmpeg nor pydub is available, copying file without normalization")
            shutil.copy(input_path, output_path)
            return output_path

    def _normalize_with_pydub(self, input_path: str, output_path: str, target_level: float = -16.0) -> str:
        """
        Normalize audio using pydub as a fallback method.

        Args:
            input_path: Path to the input audio file
            output_path: Path for the output file
            target_level: Target loudness level in dB

        Returns:
            Path to the normalized audio file
        """
        try:
            # Load the audio
            audio = AudioSegment.from_file(input_path)

            # Normalize (pydub uses dBFS not LUFS, but it's a reasonable approximation)
            change_in_db = target_level - audio.dBFS
            normalized = audio.apply_gain(change_in_db)

            # Export the normalized audio
            normalized.export(output_path, format=os.path.splitext(output_path)[1][1:])
            self.logger.info(f"Successfully normalized audio with pydub to {output_path}")

            return output_path
        except Exception as e:
            self.logger.error(f"Error normalizing with pydub: {e}")
            # Last resort: copy the file
            shutil.copy(input_path, output_path)
            self.logger.warning(f"Fallback to copying file without normalization to {output_path}")
            return output_path

    def get_audio_info(self, audio_path: str) -> Dict[str, Any]:
        """
        Get detailed information about an audio file using ffprobe or pydub as fallback.

        Args:
            audio_path: Path to the audio file

        Returns:
            Dictionary with audio file information
        """
        if not os.path.exists(audio_path):
            self.logger.error(f"Audio file not found: {audio_path}")
            return {
                "path": audio_path,
                "error": "File not found",
                "duration": 0,
                "format": os.path.splitext(audio_path)[1][1:] if '.' in audio_path else "",
                "size_bytes": 0
            }

        self.logger.info(f"Getting audio information for {audio_path}")

        # Try using ffprobe if available
        if self.ffprobe_available:
            self.logger.info("Using ffprobe for audio info")
            cmd = [
                "ffprobe",
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                audio_path
            ]

            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False
            )

            if result.returncode == 0:
                try:
                    info = json.loads(result.stdout)

                    # Extract relevant information
                    audio_info = {
                        "path": audio_path,
                        "format": info.get("format", {}).get("format_name", ""),
                        "duration": float(info.get("format", {}).get("duration", 0)),
                        "size_bytes": int(info.get("format", {}).get("size", 0)),
                        "bit_rate": int(info.get("format", {}).get("bit_rate", 0)),
                    }

                    # Get audio stream info
                    for stream in info.get("streams", []):
                        if stream.get("codec_type") == "audio":
                            audio_info.update({
                                "codec": stream.get("codec_name", ""),
                                "sample_rate": int(stream.get("sample_rate", 0)),
                                "channels": int(stream.get("channels", 0)),
                                "channel_layout": stream.get("channel_layout", ""),
                            })
                            break

                    return audio_info

                except json.JSONDecodeError as e:
                    self.logger.error(f"Error parsing ffprobe output: {e}")
            else:
                self.logger.error(f"ffprobe error: {result.stderr}")

        # Fall back to pydub if ffprobe is not available or failed
        if PYDUB_AVAILABLE:
            self.logger.info("Using pydub for audio info")
            return self._get_info_with_pydub(audio_path)

        # If neither ffprobe nor pydub is available, return basic file info
        self.logger.warning("Neither ffprobe nor pydub is available, returning basic file info")
        return self._get_basic_file_info(audio_path)

    def _get_info_with_pydub(self, audio_path: str) -> Dict[str, Any]:
        """
        Get audio information using pydub as a fallback method.

        Args:
            audio_path: Path to the audio file

        Returns:
            Dictionary with audio file information
        """
        try:
            # Load the audio file
            audio = AudioSegment.from_file(audio_path)

            # Get file size
            size_bytes = os.path.getsize(audio_path)

            # Get format from file extension
            file_format = os.path.splitext(audio_path)[1][1:] if '.' in audio_path else ""

            # Calculate duration in seconds
            duration_seconds = len(audio) / 1000.0

            return {
                "path": audio_path,
                "format": file_format,
                "duration": duration_seconds,
                "size_bytes": size_bytes,
                "bit_rate": int((size_bytes * 8) / duration_seconds) if duration_seconds > 0 else 0,
                "channels": audio.channels,
                "sample_rate": audio.frame_rate,
                "sample_width": audio.sample_width * 8,  # Convert to bits
                "perceived_loudness": float(audio.dBFS)
            }
        except Exception as e:
            self.logger.error(f"Error getting audio info with pydub: {e}")
            return self._get_basic_file_info(audio_path)

    def _get_basic_file_info(self, audio_path: str) -> Dict[str, Any]:
        """
        Get basic file information when no audio processing libraries are available.

        Args:
            audio_path: Path to the audio file

        Returns:
            Dictionary with basic file information
        """
        try:
            # Get file size
            size_bytes = os.path.getsize(audio_path)

            # Get format from file extension
            file_format = os.path.splitext(audio_path)[1][1:] if '.' in audio_path else ""

            return {
                "path": audio_path,
                "format": file_format,
                "duration": 0,  # Unknown duration
                "size_bytes": size_bytes,
                "bit_rate": 0,  # Unknown bit rate
            }
        except Exception as e:
            self.logger.error(f"Error getting basic file info: {e}")
            return {
                "path": audio_path,
                "error": str(e),
                "duration": 0,
                "format": os.path.splitext(audio_path)[1][1:] if '.' in audio_path else "",
                "size_bytes": 0
            }
