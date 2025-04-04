"""
Script formatter tool for the Script Generation Agent.
Provides enhanced script formatting capabilities.
"""

import logging
import os
import json
import markdown
from typing import Dict, Any, List, Optional
from datetime import datetime

# For PDF generation
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
except ImportError:
    # Add a note that reportlab needs to be installed for PDF generation
    pass

class ScriptFormatterTool:
    """
    Enhanced script formatter tool for creating different script formats.
    """
    
    def __init__(self, content_dir: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the script formatter tool.
        
        Args:
            content_dir: Directory to store scripts
            config: Configuration parameters
        """
        self.logger = logging.getLogger("dopcast.script_generation.script_formatter")
        self.content_dir = content_dir
        self.config = config or {}
        
        # Ensure script directories exist
        os.makedirs(os.path.join(self.content_dir, "scripts"), exist_ok=True)
        os.makedirs(os.path.join(self.content_dir, "scripts", "markdown"), exist_ok=True)
        os.makedirs(os.path.join(self.content_dir, "scripts", "pdf"), exist_ok=True)
    
    def save_script(self, script: Dict[str, Any]) -> Dict[str, str]:
        """
        Save the script in multiple formats.
        
        Args:
            script: Complete podcast script
            
        Returns:
            Dictionary of file paths
        """
        # Generate filenames
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        sport = script.get("sport", script.get("title", "").split(":")[0] if ":" in script.get("title", "") else "unknown")
        episode_type = script.get("episode_type", "unknown")
        basename = f"{sport.lower()}_{episode_type}_{timestamp}"
        
        # Save as JSON (original format)
        json_filename = f"{basename}.json"
        json_path = os.path.join(self.content_dir, "scripts", json_filename)
        
        with open(json_path, "w") as f:
            json.dump(script, f, indent=2)
        
        # Generate and save Markdown version
        md_content = self.generate_markdown(script)
        md_filename = f"{basename}.md"
        md_path = os.path.join(self.content_dir, "scripts", "markdown", md_filename)
        
        with open(md_path, "w") as f:
            f.write(md_content)
        
        # Generate and save PDF version
        pdf_filename = f"{basename}.pdf"
        pdf_path = os.path.join(self.content_dir, "scripts", "pdf", pdf_filename)
        self.generate_pdf(script, pdf_path)
        
        # Return file paths
        return {
            "json": os.path.join("scripts", json_filename),
            "markdown": os.path.join("scripts", "markdown", md_filename),
            "pdf": os.path.join("scripts", "pdf", pdf_filename)
        }
    
    def generate_markdown(self, script: Dict[str, Any]) -> str:
        """
        Generate a markdown representation of the script.
        
        Args:
            script: The complete podcast script
            
        Returns:
            Markdown formatted string of the script
        """
        md = []
        
        # Add title and metadata
        md.append(f"# {script['title']}\n")
        md.append(f"*{script['description']}*\n")
        md.append(f"**Hosts:** {', '.join(script['hosts'])}\n")
        md.append(f"**Created:** {script['created_at']}\n")
        md.append(f"**Duration:** {script['total_duration']} seconds\n")
        md.append(f"**Word Count:** {script['word_count']} words\n\n")
        
        # Add each section
        for section in script['sections']:
            md.append(f"## {section['name'].replace('_', ' ').title()}\n")
            
            # Add dialogue
            for line in section['dialogue']:
                speaker = line['speaker']
                text = line['text']
                
                # Format special lines differently
                if speaker in ["INTRO", "OUTRO", "TRANSITION"]:
                    md.append(f"*{text}*\n\n")
                else:
                    md.append(f"**{speaker}:** {text}\n\n")
            
            # Add sound effects as notes
            if section['sound_effects']:
                md.append("### Sound Effects\n")
                for effect in section['sound_effects']:
                    md.append(f"- *{effect['description']}* (at line {effect['position'] + 1})\n")
                md.append("\n")
        
        return "".join(md)
    
    def generate_pdf(self, script: Dict[str, Any], output_path: str) -> None:
        """
        Generate a PDF version of the script.
        
        Args:
            script: The complete podcast script
            output_path: Path to save the PDF file
        """
        try:
            # Create PDF document
            doc = SimpleDocTemplate(output_path, pagesize=letter)
            styles = getSampleStyleSheet()
            
            # Create custom styles
            title_style = ParagraphStyle(
                'Title',
                parent=styles['Title'],
                spaceAfter=0.25*inch
            )
            
            heading_style = ParagraphStyle(
                'Heading',
                parent=styles['Heading2'],
                spaceAfter=0.15*inch,
                spaceBefore=0.25*inch
            )
            
            speaker_style = ParagraphStyle(
                'Speaker',
                parent=styles['Normal'],
                fontName='Helvetica-Bold'
            )
            
            normal_style = styles['Normal']
            
            note_style = ParagraphStyle(
                'Note',
                parent=styles['Italic'],
                leftIndent=0.25*inch,
                fontName='Helvetica-Oblique'
            )
            
            # Build the document content
            content = []
            
            # Add title and metadata
            content.append(Paragraph(script['title'], title_style))
            content.append(Paragraph(f"<i>{script['description']}</i>", normal_style))
            content.append(Spacer(1, 0.1*inch))
            content.append(Paragraph(f"<b>Hosts:</b> {', '.join(script['hosts'])}", normal_style))
            content.append(Paragraph(f"<b>Created:</b> {script['created_at']}", normal_style))
            content.append(Paragraph(f"<b>Duration:</b> {script['total_duration']} seconds", normal_style))
            content.append(Paragraph(f"<b>Word Count:</b> {script['word_count']} words", normal_style))
            content.append(Spacer(1, 0.2*inch))
            
            # Add each section
            for section in script['sections']:
                content.append(Paragraph(section['name'].replace('_', ' ').title(), heading_style))
                
                # Add dialogue
                for line in section['dialogue']:
                    speaker = line['speaker']
                    text = line['text']
                    
                    # Format special lines differently
                    if speaker in ["INTRO", "OUTRO", "TRANSITION"]:
                        content.append(Paragraph(f"<i>{text}</i>", note_style))
                    else:
                        content.append(Paragraph(f"<b>{speaker}:</b> {text}", normal_style))
                    content.append(Spacer(1, 0.05*inch))
                
                # Add sound effects as notes
                if section['sound_effects']:
                    content.append(Paragraph("Sound Effects:", speaker_style))
                    for effect in section['sound_effects']:
                        content.append(Paragraph(
                            f"- <i>{effect['description']}</i> (at line {effect['position'] + 1})", 
                            note_style
                        ))
                    content.append(Spacer(1, 0.1*inch))
            
            # Build the PDF
            doc.build(content)
            self.logger.info(f"Generated PDF script at {output_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to generate PDF: {str(e)}")
            self.logger.info("PDF generation requires reportlab package. Install with: pip install reportlab")
    
    def calculate_script_metrics(self, script_sections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate metrics for the script.
        
        Args:
            script_sections: List of script sections
            
        Returns:
            Dictionary of script metrics
        """
        # Calculate total duration
        total_duration = sum(section.get("duration", 0) for section in script_sections)
        
        # Calculate word count
        word_count = sum(section.get("word_count", 0) for section in script_sections)
        
        # Calculate dialogue count
        dialogue_count = sum(len(section.get("dialogue", [])) for section in script_sections)
        
        # Calculate sound effect count
        sound_effect_count = sum(len(section.get("sound_effects", [])) for section in script_sections)
        
        # Calculate average words per minute
        words_per_minute = (word_count / (total_duration / 60)) if total_duration > 0 else 0
        
        return {
            "total_duration": total_duration,
            "word_count": word_count,
            "dialogue_count": dialogue_count,
            "sound_effect_count": sound_effect_count,
            "words_per_minute": words_per_minute
        }
