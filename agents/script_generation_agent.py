import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
import random
import markdown
import textwrap

# For PDF generation
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
except ImportError:
    # Add a note that reportlab needs to be installed for PDF generation
    pass

from agents.base_agent import BaseAgent

class ScriptGenerationAgent(BaseAgent):
    """
    Agent responsible for writing natural, engaging podcast scripts.
    Converts content outlines into conversational dialogue.
    """
    
    def __init__(self, name: str = "script_generation", config: Optional[Dict[str, Any]] = None):
        """
        Initialize the script generation agent.
        
        Args:
            name: Agent identifier
            config: Configuration parameters
        """
        default_config = {
            "host_personalities": [
                {
                    "name": "Mukesh",
                    "role": "lead_host",
                    "style": "enthusiastic",
                    "expertise": "general",
                    "catchphrases": ["Absolutely incredible!", "Let's dive into this.", "What a moment that was!"]
                },
                {
                    "name": "Rakesh",
                    "role": "technical_expert",
                    "style": "analytical",
                    "expertise": "technical",
                    "catchphrases": ["If we look at the data...", "Technically speaking...", "The numbers tell us..."]
                }
            ],
            "script_style": "conversational",
            "include_sound_effects": True,
            "include_transitions": True,
            "humor_level": "heavy"  # none, light, moderate, heavy
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
        os.makedirs(os.path.join(self.content_dir, "scripts"), exist_ok=True)
        os.makedirs(os.path.join(self.content_dir, "scripts", "markdown"), exist_ok=True)
        os.makedirs(os.path.join(self.content_dir, "scripts", "pdf"), exist_ok=True)
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process content outline and generate a podcast script.
        
        Args:
            input_data: Input data containing:
                - content_outline: Outline from the content planning agent
                - custom_parameters: Any custom parameters for this script
        
        Returns:
            Complete podcast script with dialogue and production notes
        """
        content_outline = input_data.get("content_outline", {})
        custom_parameters = input_data.get("custom_parameters", {})
        
        # Validate input data
        if not content_outline:
            self.logger.error("No content outline provided")
            return {"error": "No content outline provided"}
        
        # Apply any custom parameters
        script_style = custom_parameters.get("script_style", self.config["script_style"])
        humor_level = custom_parameters.get("humor_level", self.config["humor_level"])
        
        # Generate the script
        script = self._generate_script(content_outline, script_style, humor_level)
        
        # Save the script
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        sport = content_outline.get("sport", "unknown")
        episode_type = content_outline.get("episode_type", "unknown")
        basename = f"{sport}_{episode_type}_{timestamp}"
        
        # Save as JSON (original format)
        json_filename = f"{basename}.json"
        with open(os.path.join(self.content_dir, "scripts", json_filename), "w") as f:
            json.dump(script, f, indent=2)
        
        # Generate and save Markdown version
        md_content = self._generate_markdown(script)
        md_filename = f"{basename}.md"
        with open(os.path.join(self.content_dir, "scripts", "markdown", md_filename), "w") as f:
            f.write(md_content)
        
        # Generate and save PDF version
        pdf_path = os.path.join(self.content_dir, "scripts", "pdf", f"{basename}.pdf")
        self._generate_pdf(script, pdf_path)
        
        # Add file paths to the result
        script["file_paths"] = {
            "json": os.path.join("scripts", json_filename),
            "markdown": os.path.join("scripts", "markdown", md_filename),
            "pdf": os.path.join("scripts", "pdf", f"{basename}.pdf")
        }
        
        return script
    
    def _generate_markdown(self, script: Dict[str, Any]) -> str:
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
    
    def _generate_pdf(self, script: Dict[str, Any], output_path: str) -> None:
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
    
    def _generate_script(self, content_outline: Dict[str, Any], 
                        script_style: str, humor_level: str) -> Dict[str, Any]:
        """
        Generate a complete podcast script from the content outline.
        
        Args:
            content_outline: Content outline from planning agent
            script_style: Style of the script
            humor_level: Level of humor to include
            
        Returns:
            Complete podcast script
        """
        title = content_outline.get("title", "Untitled Episode")
        description = content_outline.get("description", "")
        sections = content_outline.get("sections", [])
        host_count = content_outline.get("host_count", len(self.config["host_personalities"]))
        
        # Ensure we have enough host personalities
        host_personalities = self.config["host_personalities"][:host_count]
        if len(host_personalities) < host_count:
            # Create generic hosts if needed
            for i in range(len(host_personalities), host_count):
                host_personalities.append({
                    "name": f"Host {i+1}",
                    "role": "co_host",
                    "style": "neutral",
                    "expertise": "general",
                    "catchphrases": []
                })
        
        # Create script sections
        script_sections = []
        for section in sections:
            script_section = self._generate_section_script(
                section, host_personalities, script_style, humor_level
            )
            script_sections.append(script_section)
        
        # Add intro and outro if not already included
        if not any(s.get("name") == "intro" for s in script_sections):
            intro = self._generate_intro_script(title, description, host_personalities)
            script_sections.insert(0, intro)
        
        if not any(s.get("name") == "outro" for s in script_sections):
            outro = self._generate_outro_script(host_personalities)
            script_sections.append(outro)
        
        # Assemble the complete script
        script = {
            "title": title,
            "description": description,
            "hosts": [host["name"] for host in host_personalities],
            "created_at": datetime.now().isoformat(),
            "script_style": script_style,
            "humor_level": humor_level,
            "sections": script_sections,
            "total_duration": sum(section.get("duration", 0) for section in script_sections),
            "word_count": sum(section.get("word_count", 0) for section in script_sections)
        }
        
        return script
    
    def _generate_section_script(self, section: Dict[str, Any], 
                               host_personalities: List[Dict[str, Any]],
                               script_style: str, humor_level: str) -> Dict[str, Any]:
        """
        Generate script for a single section.
        
        Args:
            section: Section from content outline
            host_personalities: List of host personality definitions
            script_style: Style of the script
            humor_level: Level of humor to include
            
        Returns:
            Script for the section
        """
        section_name = section.get("name", "unnamed_section")
        talking_points = section.get("talking_points", [])
        duration = section.get("duration", 60)  # Default 60 seconds
        
        # Import random at the top of the function to ensure it's available
        import random
        
        # Enhanced implementation to generate more detailed dialogue
        dialogue_lines = []
        sound_effects = []
        
        # Add section transition if enabled
        if self.config["include_transitions"] and section_name != "intro":
            dialogue_lines.append({
                "speaker": "TRANSITION",
                "text": f"[Transition to {section_name.replace('_', ' ').title()} section]"
            })
            sound_effects.append({
                "type": "transition",
                "description": "Short transition sound",
                "position": len(dialogue_lines) - 1
            })
        
        # Add section introduction by the primary host
        if len(host_personalities) > 0 and section_name not in ["intro", "outro"]:
            primary_host = host_personalities[0]
            section_intro = f"Let's move on to {section_name.replace('_', ' ').title()}. "
            
            if section_name == "headlines":
                section_intro += "Here are the top stories making news in the motorsport world this week."
            elif section_name == "detailed_stories":
                section_intro += "Now let's dive deeper into some of these stories and explore their implications."
            elif section_name == "analysis":
                section_intro += "I think it's time we analyze what these developments mean for the sport going forward."
            elif section_name == "key_moments":
                section_intro += "There were several defining moments that shaped the outcome of this event."
            elif section_name == "driver_performances":
                section_intro += "Let's take a closer look at how some of the drivers performed under pressure."
            elif section_name == "team_strategies":
                section_intro += "The strategic decisions made by the teams played a crucial role in the final results."
            
            dialogue_lines.append({
                "speaker": primary_host["name"],
                "text": section_intro
            })
        
        # Generate dialogue for each talking point with expanded content
        for i, point in enumerate(talking_points):
            point_content = point.get("content", "")
            host_index = point.get("host", i % len(host_personalities))
            host = host_personalities[host_index]
            
            # Convert talking point to natural dialogue
            dialogue = self._talking_point_to_dialogue(
                point_content, host, script_style, humor_level
            )
            
            dialogue_lines.append({
                "speaker": host["name"],
                "text": dialogue
            })
            
            # Add interaction between hosts
            if i < len(talking_points) - 1 and script_style == "conversational":
                next_host_index = talking_points[i+1].get("host", (i+1) % len(host_personalities))
                if next_host_index != host_index:
                    # Add a detailed response or handoff
                    next_host = host_personalities[next_host_index]
                    handoff = self._generate_handoff(host, next_host, point_content)
                    
                    dialogue_lines.append({
                        "speaker": next_host["name"],
                        "text": handoff
                    })
                else:
                    # Even if the same host continues, add a transitional line
                    dialogue_lines.append({
                        "speaker": host["name"],
                        "text": f"Building on that point, I'd also like to discuss another important aspect of this topic..."
                    })
            
            # Add follow-up questions and responses to create more depth
            # This significantly increases the dialogue content
            if i < len(talking_points) - 1 and random.random() < 0.7:  # 70% chance for follow-up
                # Determine who asks the follow-up question
                if len(host_personalities) > 1:
                    question_host_index = (host_index + 1) % len(host_personalities)
                    question_host = host_personalities[question_host_index]
                    
                    # Generate a follow-up question
                    follow_up_questions = [
                        f"That's fascinating. Could you elaborate on how this specifically affects the championship standings?",
                        f"I'm curious about your take on the long-term implications. Do you think this will change how teams approach similar situations in the future?",
                        f"That raises an interesting point about the technical regulations. How do you see this influencing development strategies for the rest of the season?",
                        f"The fans have been very vocal about this online. What do you think has been the most surprising reaction from the community?",
                        f"If you were in the team principal's position, how would you have handled this situation differently?"
                    ]
                    
                    dialogue_lines.append({
                        "speaker": question_host["name"],
                        "text": random.choice(follow_up_questions)
                    })
                    
                    # Generate a detailed response from the original host
                    pressure_options = ['The pressure is mounting as we approach the mid-season.', 'This could be a turning point in the championship battle.', 'The points gap is becoming increasingly significant at this stage.']
                    strategy_options = ['We might see more conservative approaches in similar situations.', 'Teams will likely invest more resources in this area of development.', 'This could trigger a shift in how the regulations are interpreted and applied.']
                    technical_options = ['The gray areas are where we often see the most innovation.', 'Balancing performance and compliance is a constant challenge.', 'The technical directors will be working overtime to find advantages within the rules.']
                    fan_options = ['Social media has been buzzing with theories and opinions.', 'There\'s a clear divide between casual viewers and technical enthusiasts in how they\'ve responded.', 'The passionate debates show just how engaged the community is with these technical aspects.']
                    decision_options = ['focus more on the long-term strategy rather than the immediate gains.', 'consult more closely with the engineers to understand all technical implications.', 'consider the impact on team morale and driver confidence more carefully.']
                    
                    response_templates = [
                        f"That's an excellent question. When we look at the championship implications, we need to consider both the immediate points impact and the psychological effect on the teams and drivers. {random.choice(pressure_options)}",
                        
                        f"Looking at the long-term, I believe this will definitely influence team strategies going forward. {random.choice(strategy_options)}",
                        
                        f"From a technical perspective, the regulations create an interesting framework that teams must navigate. {random.choice(technical_options)}",
                        
                        f"The fan reaction has been particularly interesting to observe. {random.choice(fan_options)}",
                        
                        f"If I were making the decisions, I'd probably {random.choice(decision_options)} It's always a delicate balance between performance and risk."
                    ]
                    
                    dialogue_lines.append({
                        "speaker": host["name"],
                        "text": random.choice(response_templates)
                    })
        
        # Add sound effects if enabled
        if self.config["include_sound_effects"]:
            # Add section-specific sound effects
            if section_name == "key_moments" and len(dialogue_lines) > 2:
                sound_effects.append({
                    "type": "highlight",
                    "description": "Race highlight sound clip",
                    "position": 2  # After the first talking point
                })
            
            if section_name == "race_summary" and len(dialogue_lines) > 1:
                sound_effects.append({
                    "type": "ambient",
                    "description": "Crowd and track ambient noise",
                    "position": 1
                })
        
        # Estimate word count (for timing purposes)
        word_count = sum(len(line["text"].split()) for line in dialogue_lines)
        
        # Create section script
        script_section = {
            "name": section_name,
            "duration": duration,
            "dialogue": dialogue_lines,
            "sound_effects": sound_effects,
            "word_count": word_count
        }
        
        return script_section

    def _talking_point_to_dialogue(self, point: str, host: Dict[str, Any],
                                 script_style: str, humor_level: str) -> str:
        """
        Convert a talking point into natural dialogue for a specific host.
        
        Args:
            point: Talking point content
            host: Host personality definition
            script_style: Style of the script
            humor_level: Level of humor to include
            
        Returns:
            Natural dialogue text
        """
        # In a real implementation, this would use an LLM to generate
        # dialogue that matches the host's personality and style
        
        # Import random at the top of the function to ensure it's available
        import random
        
        host_style = host.get("style", "neutral")
        host_role = host.get("role", "co_host")
        host_expertise = host.get("expertise", "general")
        catchphrases = host.get("catchphrases", [])
        
        # Generate more detailed and expanded dialogue based on the talking point
        # This is a significantly enhanced version that creates much longer dialogue
        
        # Start with a more detailed introduction to the point
        if host_style == "enthusiastic":
            dialogue = f"Wow! {point} This is really fascinating! "
            dialogue += f"You know, when we look deeper into this, we can see that there are several important aspects to consider. "
            dialogue += f"First, the immediate impact on the race/event itself was significant. "
            dialogue += f"But beyond that, there are longer-term implications that fans should be aware of. "
        elif host_style == "analytical":
            dialogue = f"When we analyze {point}, we can see some interesting patterns. "
            dialogue += f"The data shows several key factors at play here. "
            dialogue += f"If we break this down systematically, we can identify the main components that contributed to this situation. "
            dialogue += f"Looking at historical precedents, this follows/breaks from what we've seen in similar scenarios. "
        elif host_style == "neutral":
            dialogue = f"Let's talk about {point}. "
            dialogue += f"This is an important development that deserves our attention. "
            dialogue += f"There are multiple perspectives to consider here, and I think listeners would benefit from a balanced analysis. "
            dialogue += f"When we examine the context surrounding this, several key elements stand out. "
        
        # Add expertise-specific content to make the dialogue more substantive
        if host_expertise == "technical":
            dialogue += f"From a technical standpoint, this involves complex interactions between various systems and components. "
            dialogue += f"The engineering challenges here are significant, and teams have approached them in different ways. "
            dialogue += f"We're seeing innovations in how these technical problems are being solved, with varying degrees of success. "
        elif host_expertise == "general":
            dialogue += f"The broader context here is important for fans to understand. "
            dialogue += f"This connects to several ongoing narratives in the sport that we've been following this season. "
            dialogue += f"The reaction from the community has been mixed, with some interesting perspectives emerging. "
        
        # Add role-specific content
        if host_role == "lead_host":
            dialogue += f"As we've discussed in previous episodes, this type of situation tends to evolve over time. "
            dialogue += f"I'm particularly interested in how this will affect upcoming events and the overall championship picture. "
        elif host_role == "technical_expert":
            dialogue += f"The technical regulations play a key role in how this situation developed. "
            dialogue += f"Teams operating within these constraints have had to make difficult trade-offs. "
        
        # Add examples, analogies, or hypotheticals to further expand the dialogue
        dialogue += f"To put this in perspective, imagine if this had happened at a different point in the season or under different conditions. "
        dialogue += f"We've seen similar situations in the past, such as when teams faced comparable challenges and had to adapt their strategies. "
        
        # Add a personal take or opinion to make the dialogue more engaging
        dialogue += f"Personally, I find this aspect of the sport/situation particularly fascinating because it highlights the human element behind all the technology and competition. "
        
        # Add a catchphrase if available and probability hits
        if catchphrases and len(catchphrases) > 0 and humor_level != "none":
            if random.random() < 0.3:  # 30% chance to add catchphrase
                catchphrase = random.choice(catchphrases)
                dialogue = f"{catchphrase} {dialogue}"
        
        # Add humor if requested
        if humor_level == "moderate" or humor_level == "heavy":
            dialogue += " And hey, isn't that what we all love about this sport? The unpredictability and constant evolution keep us on our toes! "
        
        if humor_level == "heavy":
            dialogue += " I mean, where else would you see such drama every weekend? It's like a technical soap opera with engines instead of evil twins! "
        
        # Add a question or hook for the other host to respond to
        dialogue += f" What do you think about how this might develop going forward? "
        
        return dialogue

    def _generate_handoff(self, current_host: Dict[str, Any], 
                        next_host: Dict[str, Any], point_content: str) -> str:
        """
        Generate a natural handoff between hosts.
        
        Args:
            current_host: Current speaking host
            next_host: Next speaking host
            point_content: Content of the current talking point
            
        Returns:
            Handoff dialogue
        """
        # In a real implementation, this would use an LLM to generate
        # natural handoffs between hosts
        
        # Import random at the top of the function to ensure it's available
        import random
        
        # Enhanced implementation with more substantive handoffs
        next_host_style = next_host.get("style", "neutral")
        next_host_expertise = next_host.get("expertise", "general")
        
        # Create a more detailed and engaging handoff based on the next host's characteristics
        if next_host_style == "enthusiastic":
            handoffs = [
                f"That's a fantastic point! And it reminds me of something else we should discuss. From my perspective, there's also the excitement factor of how this affects the fans and their experience. I've been following the reactions online, and there are some really interesting takes on this that I'd like to share...",
                f"Absolutely! I'm so glad you brought that up. It connects directly with what I was researching earlier about how these developments are changing the landscape of the sport. There are several angles to this that I think our listeners would find fascinating...",
                f"You've hit on something really important there. I'd like to build on that by adding some context about how this compares to historical situations. When we look back at similar moments in the sport, we can see some patterns emerging that might help us understand where things are heading..."
            ]
        elif next_host_style == "analytical":
            handoffs = [
                f"That's an interesting perspective. If I may add some analytical context to what you're saying, the data suggests several underlying factors at play here. When we examine the numbers more closely, we can identify three key trends that help explain this situation...",
                f"I see what you mean, and the technical implications are significant. Building on your point, I've been analyzing how this affects performance metrics across different scenarios. The results show a clear pattern that might surprise our listeners...",
                f"Your assessment raises some important questions. From a data-driven perspective, I'd like to elaborate on how these developments fit into the broader technical evolution we're seeing this season. There are several interconnected factors that deserve a closer look..."
            ]
        else:  # neutral
            handoffs = [
                f"That's right, and I'd add that there are multiple perspectives to consider here. Looking at this from a different angle, we should also consider how this affects the competitive balance and what it means for upcoming events...",
                f"Interesting point! I was also thinking about the wider implications of this. When we consider how this fits into the current season's narrative, several important connections emerge that help us understand the bigger picture...",
                f"I see what you mean. From my perspective, there's also the question of how this will influence strategic decisions going forward. Teams are likely to adapt in several ways that could significantly change the dynamics we've been observing..."
            ]
        
        # Add expertise-specific content
        if next_host_expertise == "technical":
            technical_additions = [
                f" The technical aspects here are particularly noteworthy, especially when we consider the engineering challenges involved.",
                f" From an engineering standpoint, this represents a significant development in how teams are approaching performance optimization.",
                f" The technical regulations play a crucial role in how this situation has developed, creating constraints that teams must navigate carefully."
            ]
            handoffs = [h + random.choice(technical_additions) for h in handoffs]
        
        return random.choice(handoffs)
    
    def _generate_intro_script(self, title: str, description: str,
                             host_personalities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate script for the episode introduction.
        
        Args:
            title: Episode title
            description: Episode description
            host_personalities: List of host personality definitions
            
        Returns:
            Script for the intro section
        """
        # In a real implementation, this would use an LLM to generate
        # a natural introduction based on the episode content
        
        # Placeholder implementation with templates
        dialogue_lines = [
            {
                "speaker": "INTRO",
                "text": "[Theme music plays]"
            }
        ]
        
        # Add host introductions
        primary_host = host_personalities[0]
        dialogue_lines.append({
            "speaker": primary_host["name"],
            "text": f"Welcome to DopCast! I'm {primary_host['name']}, and today we're discussing {title}."
        })
        
        if len(host_personalities) > 1:
            co_hosts = ", ".join([h["name"] for h in host_personalities[1:]])
            dialogue_lines.append({
                "speaker": primary_host["name"],
                "text": f"Joining me as always is {co_hosts}. Great to have you here!"
            })
            
            # Add a response from one co-host
            dialogue_lines.append({
                "speaker": host_personalities[1]["name"],
                "text": f"Great to be here! We've got an exciting episode lined up today."
            })
        
        # Add episode description
        dialogue_lines.append({
            "speaker": primary_host["name"],
            "text": f"In today's episode: {description}"
        })
        
        # Add sound effects
        sound_effects = [
            {
                "type": "intro",
                "description": "Theme music",
                "position": 0
            }
        ]
        
        return {
            "name": "intro",
            "duration": 60,  # Default intro duration
            "dialogue": dialogue_lines,
            "sound_effects": sound_effects,
            "word_count": sum(len(line["text"].split()) for line in dialogue_lines)
        }
    
    def _generate_outro_script(self, host_personalities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate script for the episode conclusion.
        
        Args:
            host_personalities: List of host personality definitions
            
        Returns:
            Script for the outro section
        """
        # In a real implementation, this would use an LLM to generate
        # a natural conclusion based on the episode content
        
        # Placeholder implementation with templates
        primary_host = host_personalities[0]
        
        dialogue_lines = [
            {
                "speaker": primary_host["name"],
                "text": "Well, that brings us to the end of today's episode. Thanks for listening!"
            }
        ]
        
        if len(host_personalities) > 1:
            co_host = host_personalities[1]
            dialogue_lines.append({
                "speaker": co_host["name"],
                "text": "It's been a great discussion. Join us next time for more insights and analysis."
            })
        
        dialogue_lines.append({
            "speaker": primary_host["name"],
            "text": "Don't forget to subscribe and leave us a review. Until next time, goodbye!"
        })
        
        dialogue_lines.append({
            "speaker": "OUTRO",
            "text": "[Outro music plays and fades]"
        })
        
        # Add sound effects
        sound_effects = [
            {
                "type": "outro",
                "description": "Outro music",
                "position": len(dialogue_lines) - 1
            }
        ]
        
        return {
            "name": "outro",
            "duration": 30,  # Default outro duration
            "dialogue": dialogue_lines,
            "sound_effects": sound_effects,
            "word_count": sum(len(line["text"].split()) for line in dialogue_lines)
        }
