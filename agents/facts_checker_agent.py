import os
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import LLMChain
# Import the fact check prompt from prompts.py
from utils.prompts import FACT_CHECK_TEMPLATE

# Initialize Gemini LLM
gemini = ChatGoogleGenerativeAI(model="gemini-pro", google_api_key=os.environ.get("GEMINI_API_KEY"))

# Create the Facts Checker Agent
fact_check_prompt = PromptTemplate(
    input_variables=["policy_content"],
    template=FACT_CHECK_TEMPLATE,
)
fact_check_chain = LLMChain(llm=gemini, prompt=fact_check_prompt)

def run_fact_checker(policy_content):
  """
  Runs the fact checker agent to verify claims in the privacy policy.

  Args:
    policy_content: The content of the privacy policy.

  Returns:
    A summary of the verified claims.
  """
  return fact_check_chain.invoke(policy_content)