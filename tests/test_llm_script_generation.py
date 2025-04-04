"""
Test script for LLM-based script generation.
This demonstrates how to use an LLM to generate natural dialogue for podcast scripts.
"""

import os
import sys
import json
import logging
from datetime import datetime
import asyncio

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import LangChain components
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory

async def test_llm_script_generation():
    """Test LLM-based script generation."""
    logger.info("Testing LLM-based script generation")
    
    # Check if OpenAI API key is set
    if not os.environ.get("OPENAI_API_KEY"):
        logger.error("OPENAI_API_KEY environment variable not set")
        logger.info("Please set your OpenAI API key with: export OPENAI_API_KEY='your-api-key'")
        return
    
    # Initialize the LLM
    llm = ChatOpenAI(temperature=0.7)
    
    # Create a talking point
    talking_point = "The controversial penalty given to Max Verstappen in the final laps of the Monaco Grand Prix"
    
    # Create host personalities
    host_personalities = [
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
    ]
    
    # Create a prompt template for dialogue generation
    dialogue_template = """
    You are an expert podcast script writer for a motorsport podcast called DopCast.
    
    Generate natural, engaging dialogue for a host discussing the following talking point:
    {talking_point}
    
    Host information:
    - Name: {host_name}
    - Role: {host_role}
    - Style: {host_style}
    - Expertise: {host_expertise}
    - Catchphrases: {host_catchphrases}
    
    The dialogue should:
    - Sound natural and conversational
    - Match the host's style and expertise
    - Include detailed analysis and insights
    - Be engaging and informative
    - Occasionally use one of the host's catchphrases if appropriate
    - Be between 150-200 words
    - End with a question or statement that allows another host to respond
    
    Generate ONLY the dialogue text without any additional formatting or explanation.
    """
    
    dialogue_prompt = PromptTemplate(
        input_variables=["talking_point", "host_name", "host_role", "host_style", "host_expertise", "host_catchphrases"],
        template=dialogue_template
    )
    
    # Create a chain for dialogue generation
    dialogue_chain = LLMChain(llm=llm, prompt=dialogue_prompt)
    
    # Generate dialogue for the first host
    host1 = host_personalities[0]
    logger.info(f"Generating dialogue for {host1['name']}")
    
    host1_dialogue = await dialogue_chain.arun(
        talking_point=talking_point,
        host_name=host1["name"],
        host_role=host1["role"],
        host_style=host1["style"],
        host_expertise=host1["expertise"],
        host_catchphrases=", ".join(host1["catchphrases"])
    )
    
    logger.info(f"{host1['name']}'s dialogue: {host1_dialogue}")
    
    # Create a prompt template for response generation
    response_template = """
    You are an expert podcast script writer for a motorsport podcast called DopCast.
    
    Generate a natural, engaging response to the following dialogue from another host:
    
    {previous_dialogue}
    
    The response should be from this host:
    - Name: {host_name}
    - Role: {host_role}
    - Style: {host_style}
    - Expertise: {host_expertise}
    - Catchphrases: {host_catchphrases}
    
    The response should:
    - Directly address points made in the previous dialogue
    - Sound natural and conversational
    - Match the host's style and expertise
    - Include detailed analysis and insights
    - Be engaging and informative
    - Occasionally use one of the host's catchphrases if appropriate
    - Be between 150-200 words
    
    Generate ONLY the dialogue text without any additional formatting or explanation.
    """
    
    response_prompt = PromptTemplate(
        input_variables=["previous_dialogue", "host_name", "host_role", "host_style", "host_expertise", "host_catchphrases"],
        template=response_template
    )
    
    # Create a chain for response generation
    response_chain = LLMChain(llm=llm, prompt=response_prompt)
    
    # Generate response from the second host
    host2 = host_personalities[1]
    logger.info(f"Generating response from {host2['name']}")
    
    host2_dialogue = await response_chain.arun(
        previous_dialogue=host1_dialogue,
        host_name=host2["name"],
        host_role=host2["role"],
        host_style=host2["style"],
        host_expertise=host2["expertise"],
        host_catchphrases=", ".join(host2["catchphrases"])
    )
    
    logger.info(f"{host2['name']}'s response: {host2_dialogue}")
    
    # Create a complete dialogue exchange
    dialogue_exchange = [
        {
            "speaker": host1["name"],
            "text": host1_dialogue.strip()
        },
        {
            "speaker": host2["name"],
            "text": host2_dialogue.strip()
        }
    ]
    
    # Save the result to a file for inspection
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"llm_dialogue_test_{timestamp}.json"
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(dialogue_exchange, f, indent=2)
    
    logger.info(f"Test result saved to {output_file}")
    
    return dialogue_exchange

if __name__ == "__main__":
    # Run the test
    asyncio.run(test_llm_script_generation())
