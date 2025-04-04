"""
Dialogue generator tool for the Script Generation Agent.
Provides enhanced dialogue generation capabilities using Google Gemini LLM.
"""

import logging
import random
from typing import Dict, Any, List, Optional

from agents.common.llm_client import GeminiLLMClient

class DialogueGeneratorTool:
    """
    Enhanced dialogue generator tool for creating natural podcast dialogue using LLM.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the dialogue generator tool.

        Args:
            config: Configuration parameters
        """
        self.logger = logging.getLogger("dopcast.script_generation.dialogue_generator")
        self.config = config or {}

        # Initialize the LLM client
        llm_config = self.config.get("llm_config", {})
        self.llm_client = GeminiLLMClient(llm_config)

        # Set up caching to reduce API calls
        self.cache = {}
        self.use_cache = self.config.get("use_cache", True)

        self.logger.info("Initialized DialogueGeneratorTool with Gemini LLM")

    async def talking_point_to_dialogue(self, point: str, host: Dict[str, Any],
                                script_style: str, humor_level: str) -> str:
        """
        Convert a talking point into natural dialogue for a specific host using LLM.

        Args:
            point: Talking point content
            host: Host personality definition
            script_style: Style of the script
            humor_level: Level of humor to include

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

            # Create system prompt
            system_prompt = f"""
            You are an expert podcast script writer for a motorsport podcast called DopCast.
            You specialize in creating natural, engaging dialogue that sounds like real conversation.
            """

            # Create the main prompt
            prompt = f"""
            Generate natural, engaging dialogue for a host discussing the following talking point:

            TALKING POINT: {point}

            HOST INFORMATION:
            - Name: {host_name}
            - Role: {host_role} (e.g., lead host, technical expert, co-host)
            - Style: {host_style} (e.g., enthusiastic, analytical, neutral)
            - Expertise: {host_expertise} (e.g., technical, general)
            - Catchphrases: {', '.join(catchphrases) if catchphrases else 'None'}

            SCRIPT STYLE: {script_style} (e.g., conversational, formal, educational)
            HUMOR LEVEL: {humor_level} (e.g., none, light, moderate, heavy)

            The dialogue should:
            - Sound natural and conversational, like real speech (not written text)
            - Match the host's style and expertise level
            - Include detailed analysis and insights appropriate to the host's expertise
            - Be engaging and informative for motorsport fans
            - Include one of the host's catchphrases if appropriate (but don't force it)
            - Be between 150-250 words
            - End with a question or statement that allows another host to respond

            Generate ONLY the dialogue text without any additional formatting, explanation, or quotation marks.
            """

            # Generate dialogue using LLM
            self.logger.info(f"Generating dialogue for {host_name} on topic: {point[:30]}...")
            dialogue = await self.llm_client.generate_text(prompt, system_prompt)

            # Clean up the dialogue
            dialogue = dialogue.strip()

            # Cache the result if caching is enabled
            if self.use_cache:
                self.cache[cache_key] = dialogue

            return dialogue

        except Exception as e:
            self.logger.error(f"Error generating dialogue: {str(e)}")

            # Fallback to template-based generation
            self.logger.info("Falling back to template-based dialogue generation")

            # Start with a more detailed introduction to the point
            if host_style == "enthusiastic":
                dialogue = f"Wow! {point} This is really fascinating! "
                dialogue += f"You know, when we look deeper into this, we can see that there are several important aspects to consider. "
            elif host_style == "analytical":
                dialogue = f"When we analyze {point}, we can see some interesting patterns. "
                dialogue += f"The data shows several key factors at play here. "
            else:  # neutral
                dialogue = f"Let's talk about {point}. "
                dialogue += f"This is an important development that deserves our attention. "

            # Add expertise-specific content
            if host_expertise == "technical":
                dialogue += f"From a technical standpoint, this involves complex interactions between various systems and components. "
            else:  # general
                dialogue += f"The broader context here is important for fans to understand. "

            # Add a question for the other host
            dialogue += f"What do you think about how this might develop going forward? "

            return dialogue

    async def generate_handoff(self, current_host: Dict[str, Any],
                       next_host: Dict[str, Any], point_content: str) -> str:
        """
        Generate a natural handoff between hosts using LLM.

        Args:
            current_host: Current speaking host
            next_host: Next speaking host
            point_content: Content of the current talking point

        Returns:
            Handoff dialogue
        """
        # Create a cache key
        cache_key = f"handoff_{hash(point_content)}_{current_host['name']}_{next_host['name']}"

        # Check cache first if enabled
        if self.use_cache and cache_key in self.cache:
            self.logger.info(f"Using cached handoff from {current_host['name']} to {next_host['name']}")
            return self.cache[cache_key]

        try:
            # Extract host information
            current_host_name = current_host.get("name", "Current Host")
            next_host_name = next_host.get("name", "Next Host")
            next_host_style = next_host.get("style", "neutral")
            next_host_expertise = next_host.get("expertise", "general")
            next_host_role = next_host.get("role", "co_host")

            # Create system prompt
            system_prompt = f"""
            You are an expert podcast script writer for a motorsport podcast called DopCast.
            You specialize in creating natural transitions and handoffs between hosts that sound like real conversation.
            """

            # Create the main prompt
            prompt = f"""
            Generate a natural handoff or transition where one host responds to another and then introduces their own perspective.

            TOPIC: {point_content}

            CURRENT HOST: {current_host_name}

            NEXT HOST INFORMATION:
            - Name: {next_host_name}
            - Role: {next_host_role}
            - Style: {next_host_style} (e.g., enthusiastic, analytical, neutral)
            - Expertise: {next_host_expertise} (e.g., technical, general)

            The handoff should:
            - Begin with a brief acknowledgment of what the previous host said
            - Transition smoothly to the next host's own perspective
            - Sound natural and conversational, like real speech
            - Match the next host's style and expertise level
            - Be between 50-100 words
            - Not end with a question (as this is just the beginning of their turn to speak)

            Generate ONLY the handoff dialogue without any additional formatting, explanation, or quotation marks.
            """

            # Generate handoff using LLM
            self.logger.info(f"Generating handoff from {current_host_name} to {next_host_name}")
            handoff = await self.llm_client.generate_text(prompt, system_prompt)

            # Clean up the handoff
            handoff = handoff.strip()

            # Cache the result if caching is enabled
            if self.use_cache:
                self.cache[cache_key] = handoff

            return handoff

        except Exception as e:
            self.logger.error(f"Error generating handoff: {str(e)}")

            # Fallback to template-based generation
            self.logger.info("Falling back to template-based handoff generation")

            # Create a more detailed and engaging handoff based on the next host's characteristics
            if next_host_style == "enthusiastic":
                handoffs = [
                    f"That's a fantastic point! And it reminds me of something else we should discuss. From my perspective, there's also the excitement factor of how this affects the fans and their experience.",
                    f"Absolutely! I'm so glad you brought that up. It connects directly with what I was researching earlier about how these developments are changing the landscape of the sport."
                ]
            elif next_host_style == "analytical":
                handoffs = [
                    f"That's an interesting perspective. If I may add some analytical context to what you're saying, the data suggests several underlying factors at play here.",
                    f"I see what you mean, and the technical implications are significant. Building on your point, I've been analyzing how this affects performance metrics across different scenarios."
                ]
            else:  # neutral
                handoffs = [
                    f"That's right, and I'd add that there are multiple perspectives to consider here. Looking at this from a different angle, we should also consider how this affects the competitive balance.",
                    f"Interesting point! I was also thinking about the wider implications of this. When we consider how this fits into the current season's narrative, several important connections emerge."
                ]

            return random.choice(handoffs)

    async def generate_follow_up_question(self, host: Dict[str, Any], topic: str) -> str:
        """
        Generate a follow-up question for a host using LLM.

        Args:
            host: Host personality definition
            topic: Topic of the current discussion

        Returns:
            Follow-up question
        """
        # Create a cache key
        cache_key = f"question_{hash(topic)}_{host['name']}"

        # Check cache first if enabled
        if self.use_cache and cache_key in self.cache:
            self.logger.info(f"Using cached follow-up question for {host['name']} on topic: {topic[:30]}...")
            return self.cache[cache_key]

        try:
            # Extract host information
            host_name = host.get("name", "Host")
            host_style = host.get("style", "neutral")
            host_expertise = host.get("expertise", "general")

            # Create system prompt
            system_prompt = f"""
            You are an expert podcast script writer for a motorsport podcast called DopCast.
            You specialize in creating natural, engaging questions that sound like real conversation.
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
            - Sound natural and conversational, like real speech
            - Match the host's style and expertise level
            - Be open-ended to encourage detailed responses
            - Be specific enough to guide the conversation in an interesting direction
            - Be between 15-30 words

            Generate ONLY the question without any additional formatting, explanation, or quotation marks.
            """

            # Generate question using LLM
            self.logger.info(f"Generating follow-up question for {host_name} on topic: {topic[:30]}...")
            question = await self.llm_client.generate_text(prompt, system_prompt)

            # Clean up the question
            question = question.strip()

            # Cache the result if caching is enabled
            if self.use_cache:
                self.cache[cache_key] = question

            return question

        except Exception as e:
            self.logger.error(f"Error generating follow-up question: {str(e)}")

            # Fallback to template-based generation
            self.logger.info("Falling back to template-based question generation")

            # Generic follow-up questions
            generic_questions = [
                f"That's fascinating. Could you elaborate on how this specifically affects the championship standings?",
                f"I'm curious about your take on the long-term implications. Do you think this will change how teams approach similar situations in the future?",
                f"That raises an interesting point about the technical regulations. How do you see this influencing development strategies for the rest of the season?"
            ]

            # Style-specific questions
            if host_style == "enthusiastic":
                style_questions = [
                    f"Wow, that's incredible! What do you think was the most exciting aspect of this development?"
                ]
            elif host_style == "analytical":
                style_questions = [
                    f"Looking at the data, what patterns do you see emerging from this situation?"
                ]
            else:  # neutral
                style_questions = [
                    f"What's your perspective on how this might evolve in the coming weeks?"
                ]

            # Combine and select a question
            all_questions = generic_questions + style_questions
            return random.choice(all_questions)

    async def generate_detailed_response(self, host: Dict[str, Any], question: str, topic: str) -> str:
        """
        Generate a detailed response to a follow-up question using LLM.

        Args:
            host: Host personality definition
            question: The question being answered
            topic: The general topic of discussion

        Returns:
            Detailed response
        """
        # Create a cache key
        cache_key = f"response_{hash(question)}_{host['name']}"

        # Check cache first if enabled
        if self.use_cache and cache_key in self.cache:
            self.logger.info(f"Using cached response for {host['name']} to question: {question[:30]}...")
            return self.cache[cache_key]

        try:
            # Extract host information
            host_name = host.get("name", "Host")
            host_style = host.get("style", "neutral")
            host_expertise = host.get("expertise", "general")
            host_role = host.get("role", "co_host")
            catchphrases = host.get("catchphrases", [])

            # Create system prompt
            system_prompt = f"""
            You are an expert podcast script writer for a motorsport podcast called DopCast.
            You specialize in creating natural, engaging responses that sound like real conversation.
            """

            # Create the main prompt
            prompt = f"""
            Generate a natural, engaging response to a question during a podcast discussion.

            TOPIC: {topic}
            QUESTION: {question}

            HOST INFORMATION:
            - Name: {host_name}
            - Role: {host_role} (e.g., lead host, technical expert, co-host)
            - Style: {host_style} (e.g., enthusiastic, analytical, neutral)
            - Expertise: {host_expertise} (e.g., technical, general)
            - Catchphrases: {', '.join(catchphrases) if catchphrases else 'None'}

            The response should:
            - Sound natural and conversational, like real speech
            - Match the host's style and expertise level
            - Include detailed analysis and insights appropriate to the host's expertise
            - Be engaging and informative for motorsport fans
            - Include one of the host's catchphrases if appropriate (but don't force it)
            - Be between 100-200 words
            - Directly address the question asked

            Generate ONLY the response without any additional formatting, explanation, or quotation marks.
            """

            # Generate response using LLM
            self.logger.info(f"Generating response for {host_name} to question: {question[:30]}...")
            response = await self.llm_client.generate_text(prompt, system_prompt)

            # Clean up the response
            response = response.strip()

            # Cache the result if caching is enabled
            if self.use_cache:
                self.cache[cache_key] = response

            return response

        except Exception as e:
            self.logger.error(f"Error generating detailed response: {str(e)}")

            # Fallback to template-based generation
            self.logger.info("Falling back to template-based response generation")

            # Prepare response components
            technical_options = ['The gray areas are where we often see the most innovation.', 'Balancing performance and compliance is a constant challenge.']
            strategy_options = ['We might see more conservative approaches in similar situations.', 'Teams will likely invest more resources in this area of development.']

            # Create a basic response
            if "technical" in question.lower() or host_expertise == "technical":
                response = f"That's an excellent question. From a technical perspective, the regulations create an interesting framework that teams must navigate. {random.choice(technical_options)}"
            else:
                response = f"Looking at the long-term, I believe this will definitely influence team strategies going forward. {random.choice(strategy_options)}"

            # Add style-specific flourishes
            if host_style == "enthusiastic":
                response += f" It's absolutely fascinating to see how these dynamics play out in real-time!"
            elif host_style == "analytical":
                response += f" The data suggests this trend will continue, though we should monitor for any anomalies."

            return response

    async def generate_intro_dialogue(self, title: str, description: str,
                              host_personalities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate dialogue for the episode introduction using LLM.

        Args:
            title: Episode title
            description: Episode description
            host_personalities: List of host personality definitions

        Returns:
            List of dialogue lines
        """
        # Create a cache key
        cache_key = f"intro_{hash(title)}_{hash(description)}"

        # Check cache first if enabled
        if self.use_cache and cache_key in self.cache:
            self.logger.info(f"Using cached intro dialogue for episode: {title}")
            return self.cache[cache_key]

        try:
            # Start with the theme music
            dialogue_lines = [
                {
                    "speaker": "INTRO",
                    "text": "[Theme music plays]"
                }
            ]

            # Extract host information
            primary_host = host_personalities[0]
            primary_host_name = primary_host.get("name", "Host")
            primary_host_style = primary_host.get("style", "neutral")

            # Create system prompt
            system_prompt = f"""
            You are an expert podcast script writer for a motorsport podcast called DopCast.
            You specialize in creating natural, engaging podcast introductions.
            """

            # Create the main prompt
            prompt = f"""
            Generate a natural, engaging introduction for a motorsport podcast episode.

            EPISODE TITLE: {title}
            EPISODE DESCRIPTION: {description}

            PRIMARY HOST: {primary_host_name}
            HOST STYLE: {primary_host_style}

            CO-HOSTS: {', '.join([h.get('name', 'Co-host') for h in host_personalities[1:]]) if len(host_personalities) > 1 else 'None'}

            The introduction should include:
            1. A welcome from the primary host
            2. Introduction of co-hosts (if any)
            3. A brief overview of the episode topic
            4. A hook to engage listeners

            Format the response as a JSON array of dialogue objects with 'speaker' and 'text' fields.
            Do not include the initial theme music line (already added).
            Each line should be natural, conversational speech appropriate for the host's style.

            Example format:
            [
                {{
                    "speaker": "{primary_host_name}",
                    "text": "Welcome to DopCast! I'm {primary_host_name}, and today..."
                }},
                ...
            ]
            """

            # Generate intro dialogue using LLM
            self.logger.info(f"Generating intro dialogue for episode: {title}")
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

            # Cache the result if caching is enabled
            if self.use_cache:
                self.cache[cache_key] = dialogue_lines

            return dialogue_lines

        except Exception as e:
            self.logger.error(f"Error generating intro dialogue: {str(e)}")

            # Fallback to template-based generation
            self.logger.info("Falling back to template-based intro generation")
            dialogue_lines = [
                {
                    "speaker": "INTRO",
                    "text": "[Theme music plays]"
                }
            ]

            self._add_fallback_intro(dialogue_lines, title, description, host_personalities)
            return dialogue_lines

    def _add_fallback_intro(self, dialogue_lines: List[Dict[str, Any]],
                          title: str, description: str,
                          host_personalities: List[Dict[str, Any]]) -> None:
        """
        Add fallback intro dialogue lines when LLM generation fails.

        Args:
            dialogue_lines: List to add dialogue lines to
            title: Episode title
            description: Episode description
            host_personalities: List of host personality definitions
        """
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

    async def generate_outro_dialogue(self, host_personalities: List[Dict[str, Any]],
                               episode_title: str = "") -> List[Dict[str, Any]]:
        """
        Generate dialogue for the episode conclusion using LLM.

        Args:
            host_personalities: List of host personality definitions
            episode_title: Optional title of the episode for context

        Returns:
            List of dialogue lines
        """
        # Create a cache key
        cache_key = f"outro_{hash(episode_title)}_{','.join([h.get('name', '') for h in host_personalities])}"

        # Check cache first if enabled
        if self.use_cache and cache_key in self.cache:
            self.logger.info(f"Using cached outro dialogue for episode: {episode_title}")
            return self.cache[cache_key]

        try:
            # Extract host information
            primary_host = host_personalities[0]
            primary_host_name = primary_host.get("name", "Host")
            primary_host_style = primary_host.get("style", "neutral")

            # Create system prompt
            system_prompt = f"""
            You are an expert podcast script writer for a motorsport podcast called DopCast.
            You specialize in creating natural, engaging podcast conclusions.
            """

            # Create the main prompt
            prompt = f"""
            Generate a natural, engaging conclusion for a motorsport podcast episode.

            EPISODE TITLE: {episode_title}

            PRIMARY HOST: {primary_host_name}
            HOST STYLE: {primary_host_style}

            CO-HOSTS: {', '.join([h.get('name', 'Co-host') for h in host_personalities[1:]]) if len(host_personalities) > 1 else 'None'}

            The conclusion should include:
            1. A wrap-up from the primary host
            2. Brief closing remarks from co-hosts (if any)
            3. A call to action for listeners (subscribe, leave reviews, etc.)
            4. A farewell until the next episode

            Format the response as a JSON array of dialogue objects with 'speaker' and 'text' fields.
            Do not include the final outro music line (will be added separately).
            Each line should be natural, conversational speech appropriate for the host's style.

            Example format:
            [
                {{
                    "speaker": "{primary_host_name}",
                    "text": "Well, that brings us to the end of today's episode..."
                }},
                ...
            ]
            """

            # Generate outro dialogue using LLM
            self.logger.info(f"Generating outro dialogue for episode: {episode_title}")
            outro_json = await self.llm_client.generate_structured_output(
                prompt,
                [{"speaker": "string", "text": "string"}],
                system_prompt
            )

            # Start with an empty list
            dialogue_lines = []

            # Process the response
            if isinstance(outro_json, list) and len(outro_json) > 0:
                # Add the LLM-generated lines to our dialogue
                dialogue_lines.extend(outro_json)
            else:
                # Fallback if the LLM didn't return proper JSON
                self.logger.warning("LLM didn't return proper JSON for outro dialogue, using fallback")
                self._add_fallback_outro(dialogue_lines, host_personalities)

            # Always add the outro music line at the end
            dialogue_lines.append({
                "speaker": "OUTRO",
                "text": "[Outro music plays and fades]"
            })

            # Cache the result if caching is enabled
            if self.use_cache:
                self.cache[cache_key] = dialogue_lines

            return dialogue_lines

        except Exception as e:
            self.logger.error(f"Error generating outro dialogue: {str(e)}")

            # Fallback to template-based generation
            self.logger.info("Falling back to template-based outro generation")
            dialogue_lines = []

            self._add_fallback_outro(dialogue_lines, host_personalities)

            # Add the outro music line
            dialogue_lines.append({
                "speaker": "OUTRO",
                "text": "[Outro music plays and fades]"
            })

            return dialogue_lines

    def _add_fallback_outro(self, dialogue_lines: List[Dict[str, Any]],
                          host_personalities: List[Dict[str, Any]]) -> None:
        """
        Add fallback outro dialogue lines when LLM generation fails.

        Args:
            dialogue_lines: List to add dialogue lines to
            host_personalities: List of host personality definitions
        """
        # Add host conclusions
        primary_host = host_personalities[0]
        dialogue_lines.append({
            "speaker": primary_host["name"],
            "text": "Well, that brings us to the end of today's episode. Thanks for listening!"
        })

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
