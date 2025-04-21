import os
import hmac
import hashlib
from datetime import datetime
from typing import List, Literal, Dict, Any, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends, Header, Request
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from pydantic import BaseModel

# Import prompts from a separate file
from prompts import WEBSEARCH_TEMPLATE, FACT_CHECK_TEMPLATE, LEGAL_TEMPLATE
from websearch_agent import run_websearch
from config.firebase_config import verify_firebase_token
from services.db_service import (
    get_user_preferences, 
    update_user_preferences, 
    get_user_history, 
    add_to_history,
    save_policy_analysis,
    get_policy_analysis
)
from services.user_service import (
    create_or_update_firebase_user,
    get_firebase_user,
    delete_firebase_user
)

# Load environment variables
load_dotenv()

app = FastAPI()

# Initialize Gemini LLM
gemini_api_key = os.getenv("GEMINI_API_KEY")
if not gemini_api_key:
    print("Warning: GEMINI_API_KEY not set in environment variables")

# --- Create the Websearch Agent ---
websearch_prompt = PromptTemplate(
    input_variables=["url"],
    template=WEBSEARCH_TEMPLATE,
)

# --- Create the Facts Checker Agent ---
fact_check_prompt = PromptTemplate(
    input_variables=["policy_content"],
    template=FACT_CHECK_TEMPLATE,
)

# --- Create the Legal Agent ---
legal_prompt = PromptTemplate(
    input_variables=["policy_content", "location", "demographics"],
    template=LEGAL_TEMPLATE,
)

# --- Agent Executor ---
# Use the recommended memory type
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

# --- Pydantic Models ---
class PolicySection(BaseModel):
    title: str
    summary: str
    details: str
    riskLevel: Literal["low", "medium", "high"]

class PolicyAnalysis(BaseModel):
    url: str
    websiteName: str
    lastUpdated: str
    overallRisk: Literal["low", "medium", "high"]
    overallSummary: str
    userLocation: str
    relevantRegulations: List[str]
    sections: List[PolicySection]

class UserPreferences(BaseModel):
    country: str
    riskThreshold: Literal["low", "medium", "high"]
    notifications: bool

class HistoryItem(BaseModel):
    url: str
    analyzedAt: str
    policyTitle: str
    riskLevel: Literal["low", "medium", "high"]

class TextingRiskResponse(BaseModel):
    url: str
    textingRisk: Literal["medium", "high"]
    message: str

class AnalyzeRequest(BaseModel):
    url: str
    location: str  # e.g., "US-CA" or "UK"
    demographics: Optional[str] = None  # (Optional) e.g., "age:25"

class ClerkWebhookEvent(BaseModel):
    type: str
    data: Dict[str, Any]

# --- Authentication ---
async def get_current_user(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401, 
            detail="Invalid authentication credentials"
        )
    token = authorization.split(" ")[1]
    # Verify the Firebase token
    user = verify_firebase_token(token)
    return user

# --- Clerk Webhook Handler ---
def verify_clerk_webhook(request_body: bytes, signature: str) -> bool:
    """
    Verify that the webhook request came from Clerk.
    
    Args:
        request_body (bytes): The raw request body
        signature (str): The signature from the Clerk webhook
        
    Returns:
        bool: True if the signature is valid, False otherwise
    """
    webhook_secret = os.getenv("CLERK_SECRET_KEY")
    if not webhook_secret:
        return False
    
    # Calculate the expected signature
    expected_signature = hmac.new(
        webhook_secret.encode(),
        request_body,
        hashlib.sha256
    ).hexdigest()
    
    # Compare the signatures
    return hmac.compare_digest(expected_signature, signature)

@app.post("/api/webhooks/clerk")
async def clerk_webhook(request: Request, svix_id: str = Header(None), svix_timestamp: str = Header(None), svix_signature: str = Header(None)):
    """
    Handle Clerk webhooks for user synchronization.
    
    This endpoint receives webhook events from Clerk and synchronizes user data with Firebase.
    """
    # Get the raw request body
    body = await request.body()
    
    # Verify the webhook signature
    if not verify_clerk_webhook(body, svix_signature):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")
    
    # Parse the webhook payload
    payload = await request.json()
    
    # Process the webhook event
    event_type = payload.get("type")
    data = payload.get("data", {})
    
    if event_type == "user.created" or event_type == "user.updated":
        # Create or update the user in Firebase
        user_id = data.get("id")
        user_data = {
            "email": data.get("email_addresses", [{}])[0].get("email_address", ""),
            "name": f"{data.get('first_name', '')} {data.get('last_name', '')}".strip(),
            "image_url": data.get("image_url", ""),
            "is_admin": data.get("public_metadata", {}).get("is_admin", False),
            "metadata": data.get("public_metadata", {})
        }
        
        create_or_update_firebase_user(user_id, user_data)
        
    elif event_type == "user.deleted":
        # Delete the user from Firebase
        user_id = data.get("id")
        firebase_user = get_firebase_user(user_id)
        
        if firebase_user and "firebase_uid" in firebase_user:
            delete_firebase_user(firebase_user["firebase_uid"])
    
    return {"status": "ok"}

# --- API Endpoints ---

# Policy Analysis
@app.get("/api/policies/{url}", response_model=PolicyAnalysis)
async def analyze_policy(url: str):
    try:
        # Check if we already have this policy analyzed
        existing_analysis = get_policy_analysis(url)
        if existing_analysis:
            return PolicyAnalysis(**existing_analysis)
        
        # 1. Use the Websearch Agent to get the privacy policy content
        privacy_policy_content = run_websearch(url)

        # 2. Use Facts Checker Agent to verify claims
        # In a real implementation, this would use the fact_check_chain
        verified_claims = "Verified claims would go here"

        # 3. Use Legal Agent to summarize and provide insights
        # In a real implementation, this would use the legal_chain
        legal_summary = "Legal summary would go here"
        
        # Create the analysis object
        analysis = PolicyAnalysis(
            url=url,
            websiteName="Example Website",
            lastUpdated=datetime.now().strftime("%Y-%m-%d"),
            overallRisk="medium",
            overallSummary="This privacy policy is fairly standard but has some concerning elements regarding data sharing with third parties and unclear data retention policies.",
            userLocation="United States",
            relevantRegulations=["GDPR", "CCPA"],
            sections=[
                PolicySection(
                    title="Data Collection",
                    summary="Collects standard and some sensitive personal information",
                    details="This website collects standard information such as your name, email, and device information. It also collects more sensitive data including browsing history and potentially location data when using certain features.",
                    riskLevel="medium"
                ),
                PolicySection(
                    title="Data Usage",
                    summary="Uses data for service improvement and personalized marketing",
                    details="Your data is used to improve the service and personalize your experience. It is also used for targeted marketing both on this platform and through third-party advertising networks.",
                    riskLevel="medium"
                ),
                PolicySection(
                    title="Data Sharing",
                    summary="Shares data with numerous third parties",
                    details="Your information is shared with service providers, advertisers, and analytics companies. Some data may be sold to data brokers, though they claim this is anonymized.",
                    riskLevel="high"
                )
            ]
        )
        
        # Save the analysis to Firestore
        # save_policy_analysis(user["uid"], url, analysis.dict())  # Commented out as we don't have user
        
        return analysis
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"An error occurred: {str(e)}"
        )

# User Preferences
@app.get("/api/user/preferences", response_model=UserPreferences)
async def get_user_preferences_endpoint(user = Depends(get_current_user)):
    # Get preferences from Firestore
    prefs = get_user_preferences(user["uid"])
    return UserPreferences(**prefs)

@app.post("/api/user/preferences", response_model=dict)
async def update_user_preferences_endpoint(
    preferences: UserPreferences, 
    user = Depends(get_current_user)
):
    # Update preferences in Firestore
    updated_prefs = update_user_preferences(user["uid"], preferences.dict())
    return {
        "status": "ok",
        "preferences": updated_prefs
    }

# User History
@app.get("/api/user/history", response_model=List[HistoryItem])
async def get_user_history_endpoint(user = Depends(get_current_user)):
    # Get history from Firestore
    history = get_user_history(user["uid"])
    return [HistoryItem(**item) for item in history]

@app.post("/api/user/history", response_model=dict)
async def add_to_history_endpoint(
    history_item: HistoryItem, 
    user = Depends(get_current_user)
):
    # Add to history in Firestore
    add_to_history(user["uid"], history_item.dict())
    return {"status": "ok"}

# Extension Features
@app.get("/api/extension/texting-risk", response_model=TextingRiskResponse)
async def check_texting_risk(url: str, user = Depends(get_current_user)):
    # In a real app, implement the actual logic
    return TextingRiskResponse(
        url=url,
        textingRisk="medium",
        message="Texting/SMS marketing appears average. Opt-out is available, but read carefully."
    )

# Original endpoint (keeping for backward compatibility)
@app.post("/analyze_privacy_policy")
async def analyze_privacy_policy(request: AnalyzeRequest):
    try:
        # 1. Use the Websearch Agent to get the privacy policy content
        privacy_policy_content = run_websearch(request.url)

        # Create a detailed analysis response
        analysis = {
            "success": True,
            "data": {
                "url": request.url,
                "websiteName": "Example Website",  # This would be extracted from the URL in production
                "lastUpdated": datetime.now().strftime("%Y-%m-%d"),
                "overallRisk": "medium",
                "overallSummary": "This privacy policy is fairly standard but has some concerning elements regarding data sharing with third parties and unclear data retention policies.",
                "userLocation": request.location,
                "relevantRegulations": ["GDPR", "CCPA"],
                "sections": [
                    {
                        "title": "Data Collection",
                        "summary": "Collects standard and some sensitive personal information",
                        "details": "This website collects standard information such as your name, email, and device information. It also collects more sensitive data including browsing history and potentially location data when using certain features.",
                        "riskLevel": "medium"
                    },
                    {
                        "title": "Data Usage",
                        "summary": "Uses data for service improvement and personalized marketing",
                        "details": "Your data is used to improve the service and personalize your experience. It is also used for targeted marketing both on this platform and through third-party advertising networks.",
                        "riskLevel": "medium"
                    },
                    {
                        "title": "Data Sharing",
                        "summary": "Shares data with numerous third parties",
                        "details": "Your information is shared with service providers, advertisers, and analytics companies. Some data may be sold to data brokers, though they claim this is anonymized.",
                        "riskLevel": "high"
                    }
                ]
            }
        }

        return analysis

    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"An error occurred: {str(e)}"
        )

# Add a GET endpoint for browser access
@app.get("/analyze/{url:path}")
async def analyze_privacy_policy_get(url: str, location: str = "US"):
    try:
        # 1. Use the Websearch Agent to get the privacy policy content
        privacy_policy_content = run_websearch(url)
        
        if not privacy_policy_content:
            raise HTTPException(
                status_code=404,
                detail="Could not find or access the privacy policy for this URL"
            )

        # 2. Use the Policy Analyzer Agent to analyze the content
        from policy_analyzer_agent import analyze_policy_content, get_risk_level
        
        analysis_results = analyze_policy_content(
            privacy_policy_content=privacy_policy_content,
            location=location
        )
        
        # 3. Create a structured response
        analysis = {
            "success": True,
            "data": {
                "url": url,
                "websiteName": url.split("//")[-1].split("/")[0],  # Extract domain name
                "lastUpdated": datetime.now().strftime("%Y-%m-%d"),
                "userLocation": location,
                "overallRisk": get_risk_level(analysis_results),
                "sections": [
                    {
                        "title": "Data Collection",
                        "summary": analysis_results.get("content_analysis", {}).get("data_collection", "No summary available"),
                        "details": analysis_results.get("content_analysis", {}).get("data_collection", "No details available"),
                        "riskLevel": analysis_results.get("content_analysis", {}).get("data_collection_risk", "medium")
                    },
                    {
                        "title": "Data Usage",
                        "summary": analysis_results.get("content_analysis", {}).get("data_usage", "No summary available"),
                        "details": analysis_results.get("content_analysis", {}).get("data_usage", "No details available"),
                        "riskLevel": analysis_results.get("content_analysis", {}).get("data_usage_risk", "medium")
                    },
                    {
                        "title": "User Rights",
                        "summary": analysis_results.get("content_analysis", {}).get("user_rights", "No summary available"),
                        "details": analysis_results.get("content_analysis", {}).get("user_rights", "No details available"),
                        "riskLevel": analysis_results.get("content_analysis", {}).get("user_rights_risk", "medium")
                    },
                    {
                        "title": "Compliance",
                        "summary": analysis_results.get("fact_check", {}).get("compliance", "No summary available"),
                        "details": analysis_results.get("fact_check", {}).get("compliance", "No details available"),
                        "riskLevel": analysis_results.get("fact_check", {}).get("compliance_risk", "medium")
                    }
                ],
                "recommendations": analysis_results.get("recommendations", [])
            }
        }

        return analysis

    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"An error occurred: {str(e)}"
        )