import os
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import LLMChain

# Import the legal prompt from prompts.py
from utils.prompts import LEGAL_TEMPLATE

# Initialize Gemini LLM
gemini = ChatGoogleGenerativeAI(model="gemini-pro", google_api_key=os.environ.get("GEMINI_API_KEY"))

# Create the Legal Agent
legal_prompt = PromptTemplate(
    input_variables=["policy_content", "location", "demographics"],
    template=LEGAL_TEMPLATE,
)
legal_chain = LLMChain(llm=gemini, prompt=legal_prompt)

def run_legal_agent(policy_content, location, demographics):
  """
  Runs the legal agent to summarize the policy and provide insights.

  Args:
    policy_content: The content of the privacy policy.
    location: The user's location.
    demographics: The user's demographics.

  Returns:
    A dictionary containing the legal summary, location, and key points.
  """

  # Get the full legal summary from the LLM
  full_summary = legal_chain.invoke({
      "policy_content": policy_content,
      "location": location,
      "demographics": demographics
  })

  # Extract the country name from the location
  country = location.split("-")[0]  # Assumes location is in the format "Country-Region"

  # Generate key points (replace with your actual logic)
  key_points = extract_key_points(full_summary)

  # Generate a concise summary (replace with your actual logic)
  concise_summary = generate_concise_summary(full_summary)

  return {
      "success": True,
      "data": {
          "summary": concise_summary,
          "location": country,
          "keyPoints": key_points
      }
  }

# --- Helper functions to generate concise summary and key points ---

def extract_key_points(summary):
  """
  Extracts key points from the summary.

  Args:
    summary: The legal summary of the privacy policy.

  Returns:
    A list of key points (maximum 5).
  """
  # TODO: Implement your logic to extract key points
  # This is a placeholder, replace with your actual implementation
  key_points = []
  # ... (Your logic to extract key points from the summary)
  return key_points[:5]  # Return at most 5 key points


def generate_concise_summary(summary):
  """
  Generates a concise summary (less than 50 words).

  Args:
    summary: The legal summary of the privacy policy.

  Returns:
    A concise summary of the privacy policy.
  """
  # TODO: Implement your logic to generate a concise summary
  # This is a placeholder, replace with your actual implementation
  words = summary.split()
  return " ".join(words[:50])  # Return the first 50 words