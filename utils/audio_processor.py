import os
import logging
import tempfile
from typing import Dict, Any, List, Optional, Tuple
from pydub import AudioSegment
import librosa
import numpy as np
from datetime import datetime

from config import Config

logger = logging.getLogger("dopcast.audio")

class AudioProcessor:
    """
    Utility class for audio processing operations in the DopCast system.
    Handles audio manipulation, effects, and format conversions.
    """
    
    def __init__(self):
        """
        Initialize the audio processor.
        """
        self.content_dir = Config.CONTENT_DIR
        self.audio_dir = os.path.join(self.content_dir, "audio")
        os.makedirs(self.audio_dir, exist_ok=True)
    
    def merge_audio_segments(self, segments: List[Dict[str, Any]], 
                          output_path: Optional[str] = None,
                          add_effects: bool = True) -> str:
        """
        Merge multiple audio segments into a single audio file.
        
        Args:
            segments: List of audio segment dictionaries with paths and metadata
            output_path: Optional output file path
            add_effects: Whether to add sound effects and transitions
            
        Returns:
            Path to the merged audio file
        """
        if not segments:
            raise ValueError("No audio segments provided")
        
        # Generate output path if not provided
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(self.audio_dir, f"merged_{timestamp}.{Config.DEFAULT_AUDIO_FORMAT}")
        
        # Create an empty audio segment
        merged = AudioSegment.silent(duration=0)
        
        # Add each segment with crossfade between speakers
        prev_speaker = None
        for i, segment in enumerate(segments):
            audio_path = segment["audio_file"]
            speaker = segment.get("speaker")
            
            # Load the audio segment
            audio = AudioSegment.from_file(audio_path)
            
            # Add a small crossfade between different speakers
            if add_effects and prev_speaker is not None and speaker != prev_speaker:
                crossfade_ms = 300  # 300ms crossfade
                merged = merged.append(audio, crossfade=crossfade_ms)
            else:
                merged = merged + audio
            
            prev_speaker = speaker
        
        # Add intro/outro music if effects are enabled
        if add_effects:
            try:
                # Check for intro music
                intro_path = os.path.join(self.content_dir, "audio", "assets", "intro_music.mp3")
                if os.path.exists(intro_path):
                    intro = AudioSegment.from_file(intro_path)
                    # Fade in the intro and fade out at the end
                    intro = intro.fade_in(2000).fade_out(2000)
                    # Reduce volume of intro music
                    intro = intro - 6  # -6 dB
                    # Add intro to the beginning with crossfade
                    merged = intro.append(merged, crossfade=2000)
                
                # Check for outro music
                outro_path = os.path.join(self.content_dir, "audio", "assets", "outro_music.mp3")
                if os.path.exists(outro_path):
                    outro = AudioSegment.from_file(outro_path)
                    # Fade in the outro and fade out at the end
                    outro = outro.fade_in(2000).fade_out(2000)
                    # Reduce volume of outro music
                    outro = outro - 6  # -6 dB
                    # Add outro to the end with crossfade
                    merged = merged.append(outro, crossfade=2000)
            except Exception as e:
                logger.warning(f"Could not add intro/outro music: {str(e)}")
        
        # Export the merged audio
        merged.export(output_path, format=os.path.splitext(output_path)[1][1:])
        logger.info(f"Merged {len(segments)} audio segments into {output_path}")
        
        return output_path
    
    def add_sound_effects(self, audio_path: str, effects: List[Dict[str, Any]]) -> str:
        """
        Add sound effects to an audio file.
        
        Args:
            audio_path: Path to the audio file
            effects: List of effect dictionaries with timestamp, effect type, and duration
            
        Returns:
            Path to the modified audio file
        """
        # Load the base audio
        audio = AudioSegment.from_file(audio_path)
        
        # Add each effect
        for effect in effects:
            effect_type = effect["effect"]
            timestamp_ms = effect["timestamp"] * 1000  # Convert to milliseconds
            duration_ms = effect.get("duration", 3) * 1000  # Default 3 seconds
            
            # Load the effect audio
            effect_path = os.path.join(self.content_dir, "audio", "assets", f"{effect_type}.mp3")
            if not os.path.exists(effect_path):
                logger.warning(f"Sound effect not found: {effect_path}")
                continue
            
            effect_audio = AudioSegment.from_file(effect_path)
            
            # Trim effect to the specified duration if needed
            if len(effect_audio) > duration_ms:
                effect_audio = effect_audio[:duration_ms]
            
            # Reduce volume of effect
            effect_audio = effect_audio - 10  # -10 dB
            
            # Overlay the effect at the specified timestamp
            position = min(timestamp_ms, len(audio))
            audio = audio.overlay(effect_audio, position=position)
        
        # Generate output path
        output_path = os.path.join(
            os.path.dirname(audio_path),
            f"{os.path.splitext(os.path.basename(audio_path))[0]}_with_effects{os.path.splitext(audio_path)[1]}"
        )
        
        # Export the modified audio
        audio.export(output_path, format=os.path.splitext(output_path)[1][1:])
        logger.info(f"Added {len(effects)} sound effects to {output_path}")
        
        return output_path
    
    def convert_format(self, audio_path: str, output_format: str, bitrate: Optional[str] = None) -> str:
        """
        Convert an audio file to a different format.
        
        Args:
            audio_path: Path to the audio file
            output_format: Target format (mp3, wav, ogg, etc.)
            bitrate: Optional bitrate for the output file
            
        Returns:
            Path to the converted audio file
        """
        # Load the audio
        audio = AudioSegment.from_file(audio_path)
        
        # Generate output path
        output_path = os.path.join(
            os.path.dirname(audio_path),
            f"{os.path.splitext(os.path.basename(audio_path))[0]}.{output_format}"
        )
        
        # Export with the new format
        export_params = {}
        if bitrate:
            export_params["bitrate"] = bitrate
        
        audio.export(output_path, format=output_format, **export_params)
        logger.info(f"Converted {audio_path} to {output_format} format at {output_path}")
        
        return output_path
    
    def normalize_audio(self, audio_path: str, target_db: float = -14.0) -> str:
        """
        Normalize the volume of an audio file.
        
        Args:
            audio_path: Path to the audio file
            target_db: Target dB level
            
        Returns:
            Path to the normalized audio file
        """
        # Load the audio
        audio = AudioSegment.from_file(audio_path)
        
        # Normalize
        change_in_db = target_db - audio.dBFS
        normalized = audio.apply_gain(change_in_db)
        
        # Generate output path
        output_path = os.path.join(
            os.path.dirname(audio_path),
            f"{os.path.splitext(os.path.basename(audio_path))[0]}_normalized{os.path.splitext(audio_path)[1]}"
        )
        
        # Export the normalized audio
        normalized.export(output_path, format=os.path.splitext(output_path)[1][1:])
        logger.info(f"Normalized {audio_path} to {target_db} dB at {output_path}")
        
        return output_path
    
    def add_chapter_markers(self, audio_path: str, chapters: List[Dict[str, Any]]) -> str:
        """
        Add chapter markers to an audio file (for podcast players that support chapters).
        
        Args:
            audio_path: Path to the audio file
            chapters: List of chapter dictionaries with title, start_time, and end_time
            
        Returns:
            Path to the audio file with chapter markers
        """
        # This is a simplified implementation that would need to be expanded
        # based on the specific format and requirements
        
        # For MP3 files, we could use mutagen to add chapter markers
        if audio_path.lower().endswith(".mp3"):
            try:
                from mutagen.mp3 import MP3
                from mutagen.id3 import ID3, CTOC, CHAP, TIT2, CTOCFlags
                
                # Load the MP3 file
                audio = MP3(audio_path)
                
                # Add ID3 tags if not present
                if not audio.tags:
                    audio.add_tags()
                
                # Create a table of contents
                audio.tags.add(CTOC(
                    element_id="toc",
                    flags=CTOCFlags.TOP_LEVEL | CTOCFlags.ORDERED,
                    child_element_ids=[f"chp{i}" for i in range(len(chapters))],
                    sub_frames=[TIT2(text=["Chapters"])]
                ))
                
                # Add each chapter
                for i, chapter in enumerate(chapters):
                    # Convert times to milliseconds
                    start_time = int(chapter["start_time"] * 1000)
                    end_time = int(chapter["end_time"] * 1000)
                    
                    # Add the chapter frame
                    audio.tags.add(CHAP(
                        element_id=f"chp{i}",
                        start_time=start_time,
                        end_time=end_time,
                        sub_frames=[TIT2(text=[chapter["title"]])]
                    ))
                
                # Save the file
                audio.save()
                logger.info(f"Added {len(chapters)} chapter markers to {audio_path}")
                
                return audio_path
            except ImportError:
                logger.warning("Could not add chapter markers: mutagen library not available")
            except Exception as e:
                logger.warning(f"Could not add chapter markers: {str(e)}")
        
        # For other formats, we might need different approaches
        logger.warning(f"Chapter markers not supported for format: {os.path.splitext(audio_path)[1]}")
        return audio_path
    
    def analyze_audio(self, audio_path: str) -> Dict[str, Any]:
        """
        Analyze an audio file to extract metadata and quality metrics.
        
        Args:
            audio_path: Path to the audio file
            
        Returns:
            Dictionary of audio analysis results
        """
        try:
            # Load the audio file with librosa for analysis
            y, sr = librosa.load(audio_path, sr=None)
            
            # Get duration
            duration = librosa.get_duration(y=y, sr=sr)
            
            # Calculate RMS energy
            rms = librosa.feature.rms(y=y)[0]
            rms_mean = np.mean(rms)
            rms_std = np.std(rms)
            
            # Calculate spectral centroid
            cent = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
            cent_mean = np.mean(cent)
            
            # Get file size
            file_size = os.path.getsize(audio_path)
            
            # Load with pydub to get format info
            audio = AudioSegment.from_file(audio_path)
            
            return {
                "path": audio_path,
                "duration": duration,
                "sample_rate": sr,
                "channels": audio.channels,
                "format": os.path.splitext(audio_path)[1][1:],
                "bit_depth": audio.sample_width * 8,
                "file_size_bytes": file_size,
                "rms_energy": {
                    "mean": float(rms_mean),
                    "std": float(rms_std)
                },
                "spectral_centroid": float(cent_mean),
                "perceived_loudness": float(audio.dBFS)
            }
        except Exception as e:
            logger.error(f"Error analyzing audio {audio_path}: {str(e)}")
            return {
                "path": audio_path,
                "error": str(e)
            }

# Singleton instance
audio_processor = AudioProcessor()
