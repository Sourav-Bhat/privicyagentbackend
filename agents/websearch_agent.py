import os
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import LLMChain

# Import the web search prompt from prompts.py
from utils.prompts import WEBSEARCH_TEMPLATE

# Initialize Gemini LLM
gemini = ChatGoogleGenerativeAI(model="gemini-pro", google_api_key=os.environ.get("GEMINI_API_KEY"))

# Create the Websearch Agent
websearch_prompt = PromptTemplate(
    input_variables=["url"],
    template=WEBSEARCH_TEMPLATE,
)
websearch_chain = LLMChain(llm=gemini, prompt=websearch_prompt)

def run_websearch(url):
  """
  Runs the websearch agent to find the privacy policy for a URL.

  Args:
    url: The URL of the website.

  Returns:
    The content of the privacy policy.
  """
  return websearch_chain.invoke(url)