"""
Web Search Agent using Langchain and Google Gemini.

This agent is responsible for fetching the content of a privacy policy
given a URL. It uses a predefined prompt template and the Gemini LLM.
"""

import os
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import LLMChain
from dotenv import load_dotenv

# Import the web search prompt template
from utils.prompts import WEBSEARCH_TEMPLATE

# Load environment variables (ensure GEMINI_API_KEY is set)
load_dotenv()

# --- Initialization ---

# Initialize Gemini LLM
# TODO: Add error handling for missing API key or model initialization failure
# TODO: Consider making the model name configurable
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("Warning: GEMINI_API_KEY not set for websearch_agent.")
    # Handle error appropriately, e.g., raise ValueError or use a default

gemini_llm = ChatGoogleGenerativeAI(
    model="gemini-pro",
    google_api_key=GEMINI_API_KEY,
    # Add other configurations like temperature if needed
)

# Create the Langchain Chain for Websearch
websearch_prompt = PromptTemplate(
    input_variables=["url"],  # The key expected by the prompt template
    template=WEBSEARCH_TEMPLATE,  # The template string itself
)

# LLMChain combines the prompt template and the language model
websearch_chain = LLMChain(llm=gemini_llm, prompt=websearch_prompt)

# --- Agent Execution Function ---

def run_websearch(url: str) -> str:
    """
    Executes the websearch agent chain to find the privacy policy for a URL.

    Args:
        url: The URL of the website whose privacy policy needs to be fetched.

    Returns:
        The content of the privacy policy as returned by the LLM chain.
        This might be the policy text or an indication that it couldn't be found.
        Returns an empty string or raises an exception on error.
    """
    if not url:
        print("Error: No URL provided for web search.")
        return ""

    print(f"Running websearch agent for URL: {url}")
    try:
        # Invoke the chain with the URL as input
        # The input key must match `input_variables` in the PromptTemplate
        result = websearch_chain.invoke({"url": url})

        # Extract the actual text result from the chain's output dictionary
        # The output key depends on the LLMChain implementation, often 'text'
        policy_content = result.get("text", "")

        if not policy_content:
            print(f"Warning: Websearch agent did not return content for {url}.")
            # Consider returning a more specific message or None

        content_len = len(policy_content)
        print(f"Websearch agent finished for {url}. Content length: {content_len}")
        return policy_content

    except Exception as e:
        print(f"Error during websearch agent execution for {url}: {str(e)}")
        # Depending on requirements, either return an error indicator or re-raise
        # return f"Error fetching policy: {str(e)}"
        # raise  # Or re-raise the exception for the caller to handle
        return ""  # Return empty string on error for now