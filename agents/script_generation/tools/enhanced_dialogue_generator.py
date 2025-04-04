"""
Enhanced Dialogue Generator tool for the Script Generation Agent.
Provides improved dialogue generation with research data integration.
"""

import logging
import os
import random
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import asyncio

class EnhancedDialogueGeneratorTool:
    """
    Enhanced tool for generating natural dialogue with research data integration.
    """

    def __init__(self, content_dir: str = None, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the enhanced dialogue generator tool.

        Args:
            content_dir: Directory to store dialogue data
            config: Configuration parameters
        """
        self.logger = logging.getLogger("dopcast.script_generation.enhanced_dialogue_generator")
        self.content_dir = content_dir or os.path.join("output", "script_generation")
        self.config = config or {}

        # Set default configuration
        self.use_cache = self.config.get("use_cache", True)
        self.cache = {}

        # Set up LLM client
        self.llm_client = self.config.get("llm_client", None)
        if not self.llm_client:
            try:
                from agents.common.llm_client import LLMClient
                self.llm_client = LLMClient()
            except ImportError as e:
                self.logger.warning(f"Could not import LLMClient: {str(e)}")
                self.llm_client = None

        # Ensure directories exist
        os.makedirs(self.content_dir, exist_ok=True)

        self.logger.info("Enhanced Dialogue Generator Tool initialized")

    async def talking_point_to_dialogue(self, point: str, host: Dict[str, Any],
                                script_style: str, humor_level: str,
                                research_data: Dict[str, Any]) -> str:
        """
        Convert a talking point into natural dialogue for a specific host using LLM.
        Incorporates research data for more specific and accurate dialogue.

        Args:
            point: Talking point content
            host: Host personality definition
            script_style: Style of the script
            humor_level: Level of humor to include
            research_data: Research data to incorporate

        Returns:
            Natural dialogue text
        """
        # Create a cache key
        cache_key = f"dialogue_{hash(point)}_{host['name']}_{script_style}_{humor_level}"

        # Check cache first if enabled
        if self.use_cache and cache_key in self.cache:
            self.logger.info(f"Using cached dialogue for {host['name']} on topic: {point[:30]}...")
            return self.cache[cache_key]

        try:
            # Extract host information
            host_name = host.get("name", "Host")
            host_style = host.get("style", "neutral")
            host_role = host.get("role", "co_host")
            host_expertise = host.get("expertise", "general")
            catchphrases = host.get("catchphrases", [])

            # Extract key research information
            sport = research_data.get("sport", "unknown")
            event_type = research_data.get("event_type", "unknown")
            event_id = research_data.get("event_id", "")

            # Extract key findings from research data
            key_findings = self._extract_key_findings(research_data)

            # Create system prompt
            system_prompt = f"""
            You are an expert podcast script writer for a motorsport podcast called DopCast.
            You specialize in creating natural, engaging dialogue that sounds like real conversation.

            The current episode is about {sport.upper()} {event_type} {event_id}.

            Use the following research information to make the dialogue specific, accurate, and informative:
            {key_findings}
            """

            # Create the main prompt
            prompt = f"""
            Generate natural, engaging dialogue for a host discussing the following talking point:

            TALKING POINT: {point}

            HOST INFORMATION:
            - Name: {host_name}
            - Style: {host_style} (e.g., enthusiastic, analytical, neutral)
            - Role: {host_role} (e.g., main_host, co_host, expert)
            - Expertise: {host_expertise} (e.g., technical, general, historical)
            - Catchphrases: {', '.join(catchphrases) if catchphrases else 'None'}

            SCRIPT STYLE: {script_style} (e.g., conversational, formal, educational)
            HUMOR LEVEL: {humor_level} (e.g., minimal, moderate, high)

            The dialogue should:
            - Sound natural and conversational, like real speech (not written text)
            - Match the host's style and expertise level
            - Include detailed analysis and insights appropriate to the host's expertise
            - Be engaging and informative for motorsport fans
            - Include specific details from the research data about {sport.upper()} {event_type} {event_id}
            - Include one of the host's catchphrases if appropriate (but don't force it)
            - Be between 150-250 words
            - End with a question or statement that allows another host to respond

            Generate ONLY the dialogue text without any additional formatting, explanation, or quotation marks.
            """

            # Generate dialogue using LLM
            self.logger.info(f"Generating dialogue for {host_name} on topic: {point[:30]}...")
            if self.llm_client:
                dialogue = await self.llm_client.generate_text(prompt, system_prompt)
            else:
                self.logger.warning("No LLM client available, using fallback dialogue")
                dialogue = self._get_fallback_dialogue(point, host)

            # Cache the result if caching is enabled
            if self.use_cache:
                self.cache[cache_key] = dialogue

            return dialogue

        except Exception as e:
            self.logger.error(f"Error generating dialogue: {str(e)}")
            return self._get_fallback_dialogue(point, host)

    async def generate_follow_up_question(self, topic: str, host: Dict[str, Any],
                                   research_data: Dict[str, Any]) -> str:
        """
        Generate a follow-up question for a host to ask.
        Incorporates research data for more specific and accurate questions.

        Args:
            topic: Topic of the discussion
            host: Host personality definition
            research_data: Research data to incorporate

        Returns:
            Follow-up question text
        """
        # Create a cache key
        cache_key = f"question_{hash(topic)}_{host['name']}"

        # Check cache first if enabled
        if self.use_cache and cache_key in self.cache:
            self.logger.info(f"Using cached question for {host['name']} on topic: {topic[:30]}...")
            return self.cache[cache_key]

        try:
            # Extract host information
            host_name = host.get("name", "Host")
            host_style = host.get("style", "neutral")
            host_expertise = host.get("expertise", "general")

            # Extract key research information
            sport = research_data.get("sport", "unknown")
            event_type = research_data.get("event_type", "unknown")
            event_id = research_data.get("event_id", "")

            # Extract key findings from research data
            key_findings = self._extract_key_findings(research_data)

            # Create system prompt
            system_prompt = f"""
            You are an expert podcast script writer for a motorsport podcast called DopCast.
            You specialize in creating natural, engaging questions that sound like real conversation.

            The current episode is about {sport.upper()} {event_type} {event_id}.

            Use the following research information to make the question specific, accurate, and thought-provoking:
            {key_findings}
            """

            # Create the main prompt
            prompt = f"""
            Generate a natural, engaging follow-up question for a host to ask during a podcast discussion.

            TOPIC: {topic}

            HOST INFORMATION:
            - Name: {host_name}
            - Style: {host_style} (e.g., enthusiastic, analytical, neutral)
            - Expertise: {host_expertise} (e.g., technical, general)

            The question should:
            - Sound natural and conversational
            - Match the host's style and expertise level
            - Be specific to {sport.upper()} {event_type} {event_id}
            - Reference specific details from the research data
            - Be thought-provoking and open-ended
            - Be 1-2 sentences long

            Generate ONLY the question text without any additional formatting, explanation, or quotation marks.
            """

            # Generate question using LLM
            self.logger.info(f"Generating follow-up question for {host_name} on topic: {topic[:30]}...")
            if self.llm_client:
                question = await self.llm_client.generate_text(prompt, system_prompt)
            else:
                self.logger.warning("No LLM client available, using fallback question")
                question = self._get_fallback_question(topic, host)

            # Cache the result if caching is enabled
            if self.use_cache:
                self.cache[cache_key] = question

            return question

        except Exception as e:
            self.logger.error(f"Error generating follow-up question: {str(e)}")
            return self._get_fallback_question(topic, host)

    async def generate_detailed_response(self, host: Dict[str, Any], question: str,
                                  topic: str, research_data: Dict[str, Any]) -> str:
        """
        Generate a detailed response to a follow-up question.
        Incorporates research data for more specific and accurate responses.

        Args:
            host: Host personality definition
            question: Question to respond to
            topic: Topic of the discussion
            research_data: Research data to incorporate

        Returns:
            Detailed response text
        """
        # Create a cache key
        cache_key = f"response_{hash(question)}_{host['name']}"

        # Check cache first if enabled
        if self.use_cache and cache_key in self.cache:
            self.logger.info(f"Using cached response for {host['name']} on question: {question[:30]}...")
            return self.cache[cache_key]

        try:
            # Extract host information
            host_name = host.get("name", "Host")
            host_style = host.get("style", "neutral")
            host_expertise = host.get("expertise", "general")
            host_role = host.get("role", "co_host")
            catchphrases = host.get("catchphrases", [])

            # Extract key research information
            sport = research_data.get("sport", "unknown")
            event_type = research_data.get("event_type", "unknown")
            event_id = research_data.get("event_id", "")

            # Extract key findings from research data
            key_findings = self._extract_key_findings(research_data)

            # Create system prompt
            system_prompt = f"""
            You are an expert podcast script writer for a motorsport podcast called DopCast.
            You specialize in creating natural, engaging responses that sound like real conversation.

            The current episode is about {sport.upper()} {event_type} {event_id}.

            Use the following research information to make the response specific, accurate, and informative:
            {key_findings}
            """

            # Create the main prompt
            prompt = f"""
            Generate a natural, engaging response to a question during a podcast discussion.

            TOPIC: {topic}
            QUESTION: {question}

            HOST INFORMATION:
            - Name: {host_name}
            - Style: {host_style} (e.g., enthusiastic, analytical, neutral)
            - Role: {host_role} (e.g., main_host, co_host, expert)
            - Expertise: {host_expertise} (e.g., technical, general, historical)
            - Catchphrases: {', '.join(catchphrases) if catchphrases else 'None'}

            The response should:
            - Sound natural and conversational
            - Match the host's style and expertise level
            - Be specific to {sport.upper()} {event_type} {event_id}
            - Include detailed analysis and insights appropriate to the host's expertise
            - Reference specific details from the research data
            - Include one of the host's catchphrases if appropriate (but don't force it)
            - Be between 150-250 words

            Generate ONLY the response text without any additional formatting, explanation, or quotation marks.
            """

            # Generate response using LLM
            self.logger.info(f"Generating detailed response for {host_name} on question: {question[:30]}...")
            if self.llm_client:
                response = await self.llm_client.generate_text(prompt, system_prompt)
            else:
                self.logger.warning("No LLM client available, using fallback response")
                response = self._get_fallback_response(question, host, topic)

            # Cache the result if caching is enabled
            if self.use_cache:
                self.cache[cache_key] = response

            return response

        except Exception as e:
            self.logger.error(f"Error generating detailed response: {str(e)}")
            return self._get_fallback_response(question, host, topic)

    async def generate_intro_dialogue(self, title: str, description: str,
                              host_personalities: List[Dict[str, Any]],
                              research_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Generate dialogue for the episode introduction.
        Incorporates research data for more specific and accurate introductions.

        Args:
            title: Episode title
            description: Episode description
            host_personalities: List of host personality definitions
            research_data: Research data to incorporate

        Returns:
            List of dialogue lines with speaker and text
        """
        # Create a cache key
        cache_key = f"intro_{hash(title)}_{len(host_personalities)}"

        # Check cache first if enabled
        if self.use_cache and cache_key in self.cache:
            self.logger.info(f"Using cached intro dialogue for episode: {title[:30]}...")
            return self.cache[cache_key]

        try:
            # Extract host information
            primary_host = host_personalities[0]
            primary_host_name = primary_host.get("name", "Host")
            primary_host_style = primary_host.get("style", "neutral")

            # Extract key research information
            sport = research_data.get("sport", "unknown")
            event_type = research_data.get("event_type", "unknown")
            event_id = research_data.get("event_id", "")

            # Extract key findings from research data
            key_findings = self._extract_key_findings(research_data)

            # Create system prompt
            system_prompt = f"""
            You are an expert podcast script writer for a motorsport podcast called DopCast.
            You specialize in creating natural, engaging podcast introductions.

            The current episode is about {sport.upper()} {event_type} {event_id}.

            Use the following research information to make the introduction specific, accurate, and engaging:
            {key_findings}
            """

            # Create the main prompt
            prompt = f"""
            Generate a natural, engaging introduction for a motorsport podcast episode.

            EPISODE TITLE: {title}
            EPISODE DESCRIPTION: {description}

            PRIMARY HOST: {primary_host_name}
            HOST STYLE: {primary_host_style}

            CO-HOSTS: {', '.join([h.get('name', 'Co-host') for h in host_personalities[1:]]) if len(host_personalities) > 1 else 'None'}

            The introduction should:
            - Begin with a warm welcome from the primary host
            - Introduce the episode topic clearly
            - Be specific about {sport.upper()} {event_type} {event_id}
            - Reference specific details from the research data
            - Introduce all co-hosts by name
            - Briefly outline what will be discussed in the episode
            - Sound natural and conversational
            - Be engaging and set the tone for the episode
            - Be approximately 3-5 dialogue exchanges

            Format the output as a list of JSON objects, each with "speaker" and "text" fields.
            """

            # Generate intro dialogue using LLM
            self.logger.info(f"Generating intro dialogue for episode: {title}")
            dialogue_lines = []
            if self.llm_client:
                intro_json = await self.llm_client.generate_structured_output(
                    prompt,
                    [{"speaker": "string", "text": "string"}],
                    system_prompt
                )

                # Process the response
                if isinstance(intro_json, list) and len(intro_json) > 0:
                    # Add the LLM-generated lines to our dialogue
                    dialogue_lines.extend(intro_json)
                else:
                    # Fallback if the LLM didn't return proper JSON
                    self.logger.warning("LLM didn't return proper JSON for intro dialogue, using fallback")
                    self._add_fallback_intro(dialogue_lines, title, description, host_personalities)
            else:
                self.logger.warning("No LLM client available, using fallback intro")
                self._add_fallback_intro(dialogue_lines, title, description, host_personalities)



            # Cache the result if caching is enabled
            if self.use_cache:
                self.cache[cache_key] = dialogue_lines

            return dialogue_lines

        except Exception as e:
            self.logger.error(f"Error generating intro dialogue: {str(e)}")
            dialogue_lines = []
            self._add_fallback_intro(dialogue_lines, title, description, host_personalities)
            return dialogue_lines

    async def generate_outro_dialogue(self, host_personalities: List[Dict[str, Any]],
                              title: str, research_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Generate dialogue for the episode outro.
        Incorporates research data for more specific and accurate outros.

        Args:
            host_personalities: List of host personality definitions
            title: Episode title
            research_data: Research data to incorporate

        Returns:
            List of dialogue lines with speaker and text
        """
        # Create a cache key
        cache_key = f"outro_{hash(title)}_{len(host_personalities)}"

        # Check cache first if enabled
        if self.use_cache and cache_key in self.cache:
            self.logger.info(f"Using cached outro dialogue for episode: {title[:30]}...")
            return self.cache[cache_key]

        try:
            # Extract host information
            primary_host = host_personalities[0]
            primary_host_name = primary_host.get("name", "Host")
            primary_host_style = primary_host.get("style", "neutral")

            # Extract key research information
            sport = research_data.get("sport", "unknown")
            event_type = research_data.get("event_type", "unknown")
            event_id = research_data.get("event_id", "")

            # Extract key findings from research data
            key_findings = self._extract_key_findings(research_data)

            # Create system prompt
            system_prompt = f"""
            You are an expert podcast script writer for a motorsport podcast called DopCast.
            You specialize in creating natural, engaging podcast conclusions.

            The current episode is about {sport.upper()} {event_type} {event_id}.

            Use the following research information to make the conclusion specific, accurate, and forward-looking:
            {key_findings}
            """

            # Create the main prompt
            prompt = f"""
            Generate a natural, engaging conclusion for a motorsport podcast episode.

            EPISODE TITLE: {title}
            PRIMARY HOST: {primary_host_name}
            HOST STYLE: {primary_host_style}
            CO-HOSTS: {', '.join([h.get('name', 'Co-host') for h in host_personalities[1:]]) if len(host_personalities) > 1 else 'None'}

            The conclusion should:
            - Summarize the key points discussed in the episode
            - Be specific about {sport.upper()} {event_type} {event_id}
            - Reference specific details from the research data
            - Include a teaser for the next episode or upcoming events
            - Thank the listeners for tuning in
            - Include a sign-off from each host
            - Sound natural and conversational
            - Be approximately 3-4 dialogue exchanges

            Format the output as a list of JSON objects, each with "speaker" and "text" fields.
            """

            # Generate outro dialogue using LLM
            self.logger.info(f"Generating outro dialogue for episode: {title}")
            dialogue_lines = []
            if self.llm_client:
                outro_json = await self.llm_client.generate_structured_output(
                    prompt,
                    [{"speaker": "string", "text": "string"}],
                    system_prompt
                )

                # Process the response
                if isinstance(outro_json, list) and len(outro_json) > 0:
                    # Add the LLM-generated lines to our dialogue
                    dialogue_lines.extend(outro_json)
                else:
                    # Fallback if the LLM didn't return proper JSON
                    self.logger.warning("LLM didn't return proper JSON for outro dialogue, using fallback")
                    self._add_fallback_outro(dialogue_lines, host_personalities, title)
            else:
                self.logger.warning("No LLM client available, using fallback outro")
                self._add_fallback_outro(dialogue_lines, host_personalities, title)



            # Cache the result if caching is enabled
            if self.use_cache:
                self.cache[cache_key] = dialogue_lines

            return dialogue_lines

        except Exception as e:
            self.logger.error(f"Error generating outro dialogue: {str(e)}")
            dialogue_lines = []
            self._add_fallback_outro(dialogue_lines, host_personalities, title)
            return dialogue_lines

    def _extract_key_findings(self, research_data: Dict[str, Any]) -> str:
        """
        Extract key findings from research data.

        Args:
            research_data: Research data

        Returns:
            String with key findings
        """
        findings = []

        # Extract basic information
        sport = research_data.get("sport", "unknown")
        event_type = research_data.get("event_type", "unknown")
        event_id = research_data.get("event_id", "")

        findings.append(f"Sport: {sport.upper()}")
        findings.append(f"Event Type: {event_type}")
        if event_id:
            findings.append(f"Event ID: {event_id}")

        # Extract key findings from comprehensive summary if available
        if "comprehensive_summary" in research_data:
            summary = research_data["comprehensive_summary"]
            if "key_findings" in summary:
                findings.append("Key Findings:")
                key_findings = summary["key_findings"]

                # Add web search findings
                if "findings" in key_findings and "web_search" in key_findings["findings"]:
                    web_findings = key_findings["findings"]["web_search"]
                    findings.append("From Web Search:")
                    for i, finding in enumerate(web_findings[:3]):
                        findings.append(f"- {finding.get('title', '')}: {finding.get('summary', '')}")

                # Add YouTube findings
                if "findings" in key_findings and "youtube" in key_findings["findings"]:
                    youtube_findings = key_findings["findings"]["youtube"]
                    findings.append("From YouTube:")
                    for i, finding in enumerate(youtube_findings[:2]):
                        findings.append(f"- {finding.get('title', '')}: {finding.get('excerpt', '')[:100]}...")

                # Add web article findings
                if "findings" in key_findings and "web_articles" in key_findings["findings"]:
                    article_findings = key_findings["findings"]["web_articles"]
                    findings.append("From Web Articles:")
                    for i, finding in enumerate(article_findings[:2]):
                        findings.append(f"- {finding.get('title', '')}: {finding.get('excerpt', '')[:100]}...")

        # Extract key entities if available
        if "key_entities" in research_data:
            entities = research_data["key_entities"]
            findings.append("Key Entities:")

            # Add drivers
            if "drivers" in entities and entities["drivers"]:
                findings.append(f"Drivers: {', '.join(entities['drivers'][:5])}")

            # Add teams
            if "teams" in entities and entities["teams"]:
                findings.append(f"Teams: {', '.join(entities['teams'][:5])}")

            # Add tracks
            if "tracks" in entities and entities["tracks"]:
                findings.append(f"Tracks: {', '.join(entities['tracks'][:3])}")

        # Join all findings
        return "\n".join(findings)

    def _get_fallback_dialogue(self, point: str, host: Dict[str, Any]) -> str:
        """
        Get fallback dialogue for a talking point.

        Args:
            point: Talking point content
            host: Host personality definition

        Returns:
            Fallback dialogue text
        """
        host_name = host.get("name", "Host")
        host_style = host.get("style", "neutral")

        # Create a basic response based on the host's style
        if host_style == "enthusiastic":
            return f"I'm really excited to talk about {point}! This is such an important aspect of the race weekend and it really shows how the teams are adapting to the challenges. What's particularly fascinating is how this impacts the overall championship standings. I'd love to hear what you think about this!"

        elif host_style == "analytical":
            return f"Looking at {point} from a data perspective, we can see several interesting patterns emerging. The statistics show a clear trend in how teams are approaching this aspect of racing. When we analyze the historical context, it becomes even more significant. What's your take on how this will develop in the coming races?"

        else:  # neutral or default
            return f"Let's talk about {point}. This is an important element of the race weekend that deserves our attention. There are multiple factors at play here, and it's interesting to see how teams and drivers are responding. I'm curious to hear your thoughts on this."

    def _get_fallback_question(self, topic: str, host: Dict[str, Any]) -> str:
        """
        Get fallback question for a topic.

        Args:
            topic: Topic of the discussion
            host: Host personality definition

        Returns:
            Fallback question text
        """
        host_expertise = host.get("expertise", "general")

        # Create a basic question based on the host's expertise
        if host_expertise == "technical":
            return f"From a technical perspective, how do you think the aerodynamic changes have affected performance on this track?"

        elif host_expertise == "historical":
            return f"How does this compare to similar situations we've seen in previous seasons?"

        else:  # general or default
            return f"What do you think were the key factors that influenced the outcome this weekend?"

    def _get_fallback_response(self, question: str, host: Dict[str, Any], topic: str) -> str:
        """
        Get fallback response for a question.

        Args:
            question: Question to respond to
            host: Host personality definition
            topic: Topic of the discussion

        Returns:
            Fallback response text
        """
        host_expertise = host.get("expertise", "general")

        # Create a basic response based on the host's expertise
        if host_expertise == "technical":
            technical_options = [
                "The teams have had to make significant compromises between downforce and straight-line speed.",
                "The suspension setup is critical here, especially with the bumpy surface in certain sections.",
                "Tire management has been the deciding factor, with degradation higher than expected."
            ]
            return f"That's an excellent question. From a technical perspective, the regulations create an interesting framework that teams must navigate. {random.choice(technical_options)} This has really separated the top teams from the midfield in terms of performance."

        elif host_expertise == "historical":
            historical_options = [
                "We've seen similar situations in the past, particularly in the 2012 season.",
                "This reminds me of the classic battles we saw in the early 2000s.",
                "Historically, this track has always produced unexpected results."
            ]
            return f"If we look at the historical context, {random.choice(historical_options)} The patterns tend to repeat themselves in motorsport, though the technology is constantly evolving. It's fascinating to see how teams adapt to these challenges over time."

        else:  # general or default
            strategy_options = [
                "The strategy calls made during the race were absolutely crucial.",
                "Team orders played a significant role in how things unfolded.",
                "The weather conditions added an extra layer of complexity to decision-making."
            ]
            return f"Looking at the big picture, I believe this will definitely influence team strategies going forward. {random.choice(strategy_options)} It's these moments that often define a championship campaign."

    def _add_fallback_intro(self, dialogue_lines: List[Dict[str, str]],
                          title: str, description: str,
                          host_personalities: List[Dict[str, Any]]) -> None:
        """
        Add fallback intro dialogue lines.

        Args:
            dialogue_lines: List to add dialogue lines to
            title: Episode title
            description: Episode description
            host_personalities: List of host personality definitions
        """
        # Get the primary host
        primary_host = host_personalities[0]
        primary_host_name = primary_host.get("name", "Host")

        # Add welcome line
        dialogue_lines.append({
            "speaker": primary_host_name,
            "text": f"Welcome to DopCast, your premier motorsport podcast! I'm {primary_host_name}, and today we're diving into {title}. {description}"
        })

        # Add co-host introductions
        for i, host in enumerate(host_personalities[1:]):
            host_name = host.get("name", f"Co-host {i+1}")
            dialogue_lines.append({
                "speaker": host_name,
                "text": f"Great to be here! I'm {host_name}, and I'm excited to break down all the action with you today."
            })

        # Add episode overview
        dialogue_lines.append({
            "speaker": primary_host_name,
            "text": f"In today's episode, we'll be analyzing the key moments, discussing the standout performances, and looking at the championship implications. Let's get started!"
        })

    def _add_fallback_outro(self, dialogue_lines: List[Dict[str, str]],
                          host_personalities: List[Dict[str, Any]],
                          title: str) -> None:
        """
        Add fallback outro dialogue lines.

        Args:
            dialogue_lines: List to add dialogue lines to
            host_personalities: List of host personality definitions
            title: Episode title
        """
        # Get the primary host
        primary_host = host_personalities[0]
        primary_host_name = primary_host.get("name", "Host")

        # Add summary line
        dialogue_lines.append({
            "speaker": primary_host_name,
            "text": f"That wraps up our discussion on {title}. We've covered the key moments, analyzed the performances, and looked at what this means for the championship."
        })

        # Add co-host sign-offs
        for i, host in enumerate(host_personalities[1:]):
            host_name = host.get("name", f"Co-host {i+1}")
            dialogue_lines.append({
                "speaker": host_name,
                "text": f"It's been a great discussion. Thanks to everyone for listening, and we'll see you next time for more motorsport analysis!"
            })

        # Add final sign-off
        dialogue_lines.append({
            "speaker": primary_host_name,
            "text": "Thanks for tuning in to DopCast. Don't forget to subscribe, leave a review, and join us for our next episode. Until then, this is the DopCast team signing off!"
        })
