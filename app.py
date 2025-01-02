from fastapi import FastAPI, HTTPException
from langchain.agents import AgentExecutor, ZeroShotAgent
from langchain.memory import ConversationBufferMemory
from langchain import LLMChain, PromptTemplate
from pydantic import BaseModel
import os

# Import the Gemini LLM
from google.generativeai import Gemini

# Import prompts from a separate file
from prompts import WEBSEARCH_TEMPLATE, FACT_CHECK_TEMPLATE, LEGAL_TEMPLATE

# Import the websearch agent
from websearch_agent import run_websearch

app = FastAPI()

# Initialize Gemini LLM
gemini = Gemini(api_key=os.getenv("GEMINI_API_KEY"), model="gemini-pro")

# --- Create the Websearch Agent ---
websearch_prompt = PromptTemplate(
    input_variables=["url"],
    template=WEBSEARCH_TEMPLATE,
)

# Use RunnableSequence instead of LLMChain (as per the warning)
websearch_chain = websearch_prompt | gemini  

# --- Create the Facts Checker Agent ---
fact_check_prompt = PromptTemplate(
    input_variables=["policy_content"],
    template=FACT_CHECK_TEMPLATE,
)
fact_check_chain = LLMChain(llm=gemini, prompt=fact_check_prompt)

# --- Create the Legal Agent ---
legal_prompt = PromptTemplate(
    input_variables=["policy_content", "location", "demographics"],
    template=LEGAL_TEMPLATE,
)
legal_chain = LLMChain(llm=gemini, prompt=legal_prompt)

# --- Agent Executor ---

# Use the recommended memory type (as per the warning)
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)  

# Initialize the agent with the websearch chain
agent_chain = ZeroShotAgent(llm_chain=websearch_chain, tools=[], verbose=True)

# Initialize the agent executor
agent_executor = AgentExecutor.from_agent_and_tools(
    agent=agent_chain,
    tools=[],
    memory=memory,
    verbose=True
)

# --- Pydantic model for request body ---
class AnalyzeRequest(BaseModel):
    url: str
    location: str  # e.g., "US-CA" or "UK"
    demographics: str = None  # (Optional) e.g., "age:25"

# --- API Endpoint ---
@app.post("/analyze_privacy_policy")
async def analyze_privacy_policy(request: AnalyzeRequest):
    try:
        # 1. Use the Websearch Agent to get the privacy policy content
        privacy_policy_content = agent_executor.run(
            f"What is the privacy policy for {request.url}?"
        )

        # 2. Use Facts Checker Agent to verify claims
        verified_claims = fact_check_chain.run(privacy_policy_content)

        # 3. Use Legal Agent to summarize and provide insights
        legal_summary = legal_chain.run({
            "policy_content": privacy_policy_content,
            "location": request.location,
            "demographics": request.demographics
        })

        return {
            "success": True,
            "data": {
                "summary": legal_summary,
                # "thompsonCompliance": thompson_compliance,  # Implement your logic here
                "location": request.location,
                # "keyPoints": key_points  # Implement your logic here
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"An error occurred: {str(e)}")