"""
Simple test script to fetch a transcript for a specific YouTube video.
"""

import os
import sys
import json

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from agents.research.tools.youtube_transcript_tool import YouTubeTranscriptTool

def main():
    # Create output directory if it doesn't exist
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    data_dir = os.path.join(output_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    
    # Initialize the YouTube transcript tool
    youtube_tool = YouTubeTranscriptTool(data_dir)
    
    # The video URL to test - an F1 interview that should have a transcript
    video_url = "https://www.youtube.com/watch?v=YXsOvs_eqQE"
    
    print(f"Fetching transcript for video: {video_url}")
    
    # Extract the transcript
    transcript = youtube_tool.get_transcript(video_url)
    
    if transcript:
        print("\nTranscript found!")
        print(f"Video ID: {transcript['video_id']}")
        print(f"Language: {transcript['language']}")
        print(f"Fetched at: {transcript['fetched_at']}")
        print(f"Transcript length: {len(transcript['full_text'])} characters")
        print(f"Number of segments: {len(transcript['segments'])}")
        print(f"Is fallback: {transcript.get('is_fallback', False)}")
        
        # Print a sample of the transcript
        print("\nSample of transcript:")
        sample_length = min(500, len(transcript['full_text']))
        print(transcript['full_text'][:sample_length] + "...")
        
        # Save the transcript to a file
        output_file = os.path.join(output_dir, f"transcript_{transcript['video_id']}.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(transcript, f, ensure_ascii=False, indent=2)
        
        print(f"\nFull transcript saved to: {output_file}")
    else:
        print("\nNo transcript found for this video.")

if __name__ == "__main__":
    main()
