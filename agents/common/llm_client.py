"""
Google Gemini LLM client for DopCast.
Provides a unified interface for interacting with Google's Gemini models.
"""

import os
import logging
import re
from typing import Dict, Any, List, Optional
import json
import asyncio

# Import Google Gemini SDK
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, SystemMessage

class GeminiLLMClient:
    """
    Client for interacting with Google's Gemini models.
    Provides methods for generating text, chat completions, and structured outputs.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Gemini LLM client.

        Args:
            config: Configuration parameters including:
                - api_key: Google API key (defaults to GOOGLE_API_KEY env var)
                - model_name: Model to use (defaults to gemini-2.0-flash)
                - temperature: Temperature for generation (defaults to 0.7)
                - max_tokens: Maximum tokens to generate (defaults to 1024)
        """
        self.logger = logging.getLogger("dopcast.llm_client")
        self.config = config or {}

        # Get API key from config or environment
        self.api_key = self.config.get("api_key", os.environ.get("GOOGLE_API_KEY", ""))
        if not self.api_key:
            self.logger.warning("No Google API key provided. Set GOOGLE_API_KEY environment variable or pass in config.")

        # Set model parameters
        self.model_name = self.config.get("model_name", "gemini-2.0-flash")
        self.temperature = self.config.get("temperature", 0.7)
        self.max_tokens = self.config.get("max_tokens", 1024)

        # Initialize the LLM
        self.llm = ChatGoogleGenerativeAI(
            model=self.model_name,
            temperature=self.temperature,
            max_output_tokens=self.max_tokens,
            google_api_key=self.api_key,
            convert_system_message_to_human=True
        )

        self.logger.info(f"Initialized Gemini LLM client with model: {self.model_name}")

    async def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Generate text based on a prompt.

        Args:
            prompt: The prompt to generate text from
            system_prompt: Optional system prompt for context

        Returns:
            Generated text
        """
        messages = []

        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))

        messages.append(HumanMessage(content=prompt))

        try:
            response = await asyncio.to_thread(self.llm.invoke, messages)
            return response.content
        except Exception as e:
            self.logger.error(f"Error generating text: {str(e)}")
            return f"Error generating text: {str(e)}"

    async def generate_structured_output(self,
                                      prompt: str,
                                      output_schema: Dict[str, Any] | List[Dict[str, Any]],
                                      system_prompt: Optional[str] = None) -> Any:
        """
        Generate structured output based on a prompt and schema.

        Args:
            prompt: The prompt to generate from
            output_schema: JSON schema for the expected output (dict or list)
            system_prompt: Optional system prompt for context

        Returns:
            Structured output matching the schema (dict, list, or other JSON-compatible type)
        """
        # Determine if we're expecting an array or object
        is_array = isinstance(output_schema, list)
        example_json = json.dumps(output_schema, indent=2)

        # Create a prompt that includes the schema and clear instructions
        schema_prompt = f"""
        {prompt}

        Please provide your response in the following JSON format:
        ```json
        {example_json}
        ```

        IMPORTANT INSTRUCTIONS:
        1. Your response MUST be valid JSON that matches this schema exactly
        2. Do NOT include any explanations, notes, or text outside the JSON
        3. The JSON should be a{' list' if is_array else 'n object'} as shown in the example
        4. Ensure all field names and types match the schema
        5. Return ONLY the JSON with no additional text
        """

        messages = []

        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))

        messages.append(HumanMessage(content=schema_prompt))

        try:
            response = await asyncio.to_thread(self.llm.invoke, messages)
            content = response.content

            # Extract JSON from the response
            json_content = self._extract_json(content)

            if json_content:
                try:
                    parsed_json = json.loads(json_content)
                    return parsed_json
                except json.JSONDecodeError as e:
                    self.logger.warning(f"JSON parsing error: {str(e)}")
                    # Try to fix common JSON issues
                    fixed_json = self._attempt_json_repair(json_content)
                    if fixed_json:
                        return fixed_json

            # If we couldn't extract or parse JSON, log the response and try direct parsing
            self.logger.warning(f"Failed to extract valid JSON from response: {content}")
            try:
                # Try to parse the entire response as JSON
                return json.loads(content)
            except json.JSONDecodeError:
                # Last resort: try to extract any JSON-like structure
                self.logger.error("Failed to parse response as JSON")
                fallback_result = self._extract_any_json_structure(content, is_array)
                if fallback_result is not None:
                    return fallback_result
                return {"error": "Failed to generate structured output"} if not is_array else []
        except Exception as e:
            self.logger.error(f"Error generating structured output: {str(e)}")
            return {"error": f"Error generating structured output: {str(e)}"} if not is_array else []

    def _extract_json(self, text: str) -> Optional[str]:
        """
        Extract JSON from text that might contain markdown code blocks.

        Args:
            text: Text that might contain JSON

        Returns:
            Extracted JSON string or None if not found
        """
        # Try to extract JSON from markdown code blocks
        if "```json" in text and "```" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            if start > 7 and end > start:
                return text[start:end].strip()

        # Try to extract JSON from any code blocks
        if "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            if start > 3 and end > start:
                return text[start:end].strip()

        # Check if the entire text is JSON (object)
        if text.strip().startswith("{") and text.strip().endswith("}"):
            return text.strip()

        # Check if the entire text is JSON (array)
        if text.strip().startswith("[") and text.strip().endswith("]"):
            return text.strip()

        return None

    def _attempt_json_repair(self, text: str) -> Optional[Any]:
        """
        Attempt to repair common JSON formatting issues.

        Args:
            text: Text that might be malformed JSON

        Returns:
            Parsed JSON object/array or None if repair failed
        """
        try:
            # Try to parse as is first
            return json.loads(text)
        except json.JSONDecodeError:
            # Common repair attempts
            repairs = [
                # Try removing trailing commas in objects
                lambda t: re.sub(r',\s*}', '}', t),
                # Try removing trailing commas in arrays
                lambda t: re.sub(r',\s*]', ']', t),
                # Try fixing unquoted property names
                lambda t: re.sub(r'([{,]\s*)([a-zA-Z0-9_]+)\s*:', r'\1"\2":', t),
                # Try fixing single quotes used instead of double quotes
                lambda t: t.replace("'", '"'),
                # Try fixing JavaScript-style comments
                lambda t: re.sub(r'//.*?\n', '\n', t),
                # Try fixing multi-line comments
                lambda t: re.sub(r'/\*.*?\*/', '', t, flags=re.DOTALL),
            ]

            # Try each repair strategy
            for repair in repairs:
                try:
                    repaired = repair(text)
                    result = json.loads(repaired)
                    self.logger.info("Successfully repaired JSON")
                    return result
                except (json.JSONDecodeError, Exception):
                    continue

            return None

    def _extract_any_json_structure(self, text: str, expect_array: bool = False) -> Optional[Any]:
        """
        Extract any JSON-like structure from text as a last resort.

        Args:
            text: Text that might contain JSON-like structures
            expect_array: Whether we expect an array result

        Returns:
            Extracted JSON structure or None
        """
        # For arrays, look for anything that looks like an array
        if expect_array:
            array_match = re.search(r'\[\s*{.*?}\s*(,\s*{.*?}\s*)*\]', text, re.DOTALL)
            if array_match:
                try:
                    return json.loads(array_match.group(0))
                except json.JSONDecodeError:
                    pass

            # If we can't find a valid array, try to extract individual objects and build an array
            objects = re.findall(r'{\s*".*?"\s*:.*?}', text, re.DOTALL)
            if objects:
                result = []
                for obj in objects:
                    try:
                        parsed = json.loads(obj)
                        result.append(parsed)
                    except json.JSONDecodeError:
                        continue
                if result:
                    return result
        else:
            # For objects, look for anything that looks like an object
            object_match = re.search(r'{\s*".*?"\s*:.*?}', text, re.DOTALL)
            if object_match:
                try:
                    return json.loads(object_match.group(0))
                except json.JSONDecodeError:
                    pass

        return None
