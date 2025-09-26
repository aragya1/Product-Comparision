# core/llm.py
"""
Gemini LLM client setup for AutoGen agents.
"""
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from dotenv import load_dotenv
import os
from autogen_core.models import UserMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient
import asyncio
from autogen_core.models import ModelInfo
from pydantic import BaseModel


# Load environment variables from a .env file


# Configure the Gemini API client
# --------------------------------------------------------------------
# Helper: get Gemini client
# --------------------------------------------------------------------
def get_gemini_client(model_name: str = "gemini-2.5-flash", response_format:BaseModel = None):
    """
    Returns a Gemini GenerativeModel instance.
    """
    load_dotenv()
# Get the API key from environment variables
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("Missing GOOGLE_API_KEY environment variable for Gemini access.")
    
    try:
        model_client = OpenAIChatCompletionClient(
        model="gemini-2.5-flash",
        model_info=ModelInfo(vision=True, function_calling=True, json_output=True, family="unknown", structured_output=True),
        api_key = api_key,
        response_format = response_format,
        )
        
        return model_client
    except Exception as e:
        raise RuntimeError(f"Failed to initialize Gemini model: {e}")

async def main():
    """
    Main asynchronous function to interact with the Gemini model.
    """
    try:
        # Get the Gemini model instance
        model_client = get_gemini_client()

        # Send a prompt and get the response
        prompt = "Who are you?"
        print(f"Sending prompt: '{prompt}' to Gemini...")
        
        # Use aiohttp or another async library if needed for a more robust solution.
        # This simple example uses a synchronous call wrapped in an executor.
        response = await model_client.create([UserMessage(content=prompt, source="user")])
        
        # Print the response content
        if response:
            print("Response from Gemini:")
            print(response)
        else:
            print("No text content in the response.")

    except Exception as e:
        print(f"An error occurred: {e}")

# Run the main asynchronous function
if __name__ == "__main__":
    asyncio.run(main())