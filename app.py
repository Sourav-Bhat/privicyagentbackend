"""
Main FastAPI application for the Privacy Policy Analyzer backend.

Handles API requests for policy analysis, user preferences, history,
and webhook events.
"""
import os
import hmac
import hashlib
from datetime import datetime
from typing import List, Literal, Dict, Any, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends, Header, Request
# TODO: Check if langchain imports are still needed after full agent integration
# from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from pydantic import BaseModel

# Import project modules with updated paths
from utils.prompts import (
    WEBSEARCH_TEMPLATE, FACT_CHECK_TEMPLATE, LEGAL_TEMPLATE
)
from agents.websearch_agent import run_websearch
from config.firebase_config import verify_firebase_token
from services.db_service import (
    get_user_preferences,
    update_user_preferences,
    get_user_history,
    add_to_history,
    # save_policy_analysis, # This seems unused currently
    # get_policy_analysis # Was only used in commented-out caching logic
)
from services.user_service import (
    create_or_update_firebase_user,
    get_firebase_user,
    delete_firebase_user
)

# Load environment variables from .env file
load_dotenv()

# --- FastAPI App Initialization ---
app = FastAPI(
    title="Privacy Policy Analyzer API",
    description=(
        "API for analyzing privacy policies and managing user data."
    ),
    version="0.1.0"
)

# --- Configuration & Setup ---

# Initialize Gemini LLM
# (Consider moving LLM initialization to a dedicated service/config)
gemini_api_key = os.getenv("GEMINI_API_KEY")
if not gemini_api_key:
    print("Warning: GEMINI_API_KEY not set in environment variables")


# --- Langchain Agent/Prompt Setup (Placeholder/Legacy) ---
# TODO: Review and integrate these properly or remove if replaced by agent files.

# Websearch Prompt Template
websearch_prompt = PromptTemplate(
    input_variables=["url"],
    template=WEBSEARCH_TEMPLATE,
)

# Fact Check Prompt Template
fact_check_prompt = PromptTemplate(
    input_variables=["policy_content"],
    template=FACT_CHECK_TEMPLATE,
)

# Legal Analysis Prompt Template
legal_prompt = PromptTemplate(
    input_variables=["policy_content", "location", "demographics"],
    template=LEGAL_TEMPLATE,
)

# Conversation Memory (If using conversational agents)
# memory = ConversationBufferMemory(
#     memory_key="chat_history", return_messages=True
# )


# --- Pydantic Models ---

class PolicySection(BaseModel):
    """Represents a single analyzed section of a privacy policy."""
    title: str
    summary: str
    details: str
    riskLevel: Literal["low", "medium", "high"]


class PolicyAnalysis(BaseModel):
    """Represents the overall analysis result for a privacy policy."""
    url: str
    websiteName: str
    lastUpdated: str
    overallRisk: Literal["low", "medium", "high"]
    overallSummary: str
    userLocation: str
    relevantRegulations: List[str]
    sections: List[PolicySection]


class UserPreferences(BaseModel):
    """Represents user-specific preferences for policy analysis."""
    country: str
    riskThreshold: Literal["low", "medium", "high"]
    notifications: bool


class HistoryItem(BaseModel):
    """Represents an item in the user's policy analysis history."""
    url: str
    analyzedAt: str
    policyTitle: str
    riskLevel: Literal["low", "medium", "high"]


class TextingRiskResponse(BaseModel):
    """Response model for the texting risk analysis endpoint."""
    url: str
    textingRisk: Literal["medium", "high"]
    message: str


class AnalyzeRequest(BaseModel):
    """Request model for the original POST /analyze_privacy_policy endpoint."""
    url: str
    location: str  # e.g., "US-CA" or "UK"
    demographics: Optional[str] = None  # (Optional) e.g., "age:25"


class ClerkWebhookEvent(BaseModel):
    """Request model for incoming Clerk webhook events."""
    type: str
    data: Dict[str, Any]


# --- Authentication ---

async def get_current_user(authorization: str = Header(...)):
    """
    Dependency function to verify Firebase JWT token and return user info.

    Raises HTTPException 401 if the token is invalid or missing.
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials"
        )
    token = authorization.split(" ")[1]
    # Verify the Firebase token
    user = verify_firebase_token(token)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired authentication token"
        )
    return user


# --- Clerk Webhook Handler ---

def verify_clerk_webhook(request_body: bytes, signature: str) -> bool:
    """
    Verify that the webhook request genuinely came from Clerk using HMAC-SHA256.

    Args:
        request_body: The raw request body bytes.
        signature: The signature string provided in the Clerk webhook headers.

    Returns:
        True if the signature is valid, False otherwise.
    """
    webhook_secret = os.getenv("CLERK_SECRET_KEY")
    if not webhook_secret:
        print("Error: CLERK_SECRET_KEY not configured.")
        return False

    # Calculate the expected signature
    expected_signature = hmac.new(
        webhook_secret.encode(),
        request_body,
        hashlib.sha256
    ).hexdigest()

    # Compare the signatures securely
    return hmac.compare_digest(expected_signature, signature)


@app.post("/api/webhooks/clerk")
async def clerk_webhook(
    request: Request,
    svix_id: str = Header(None),
    svix_timestamp: str = Header(None),
    svix_signature: str = Header(None)
):
    """
    Handle Clerk webhooks for user creation, update, and deletion events.

    Synchronizes user data between Clerk and Firebase Authentication/Firestore.
    Requires signature verification using CLERK_SECRET_KEY.
    """
    # Get the raw request body
    body = await request.body()

    # Verify the webhook signature
    # TODO: Add proper svix header verification if using Svix library
    if not svix_signature or not verify_clerk_webhook(body, svix_signature):
        raise HTTPException(
            status_code=401, detail="Invalid webhook signature"
        )

    # Parse the webhook payload
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # Process the webhook event based on its type
    event_type = payload.get("type")
    data = payload.get("data", {})

    if not data or not event_type:
        raise HTTPException(
            status_code=400, detail="Invalid webhook payload structure"
        )

    user_id = data.get("id")
    if not user_id:
        raise HTTPException(
            status_code=400, detail="User ID missing in webhook data"
        )

    if event_type == "user.created" or event_type == "user.updated":
        # Create or update the user in Firebase
        # Extract primary email address safely
        email_info = data.get("email_addresses", [{}])[0]
        email = email_info.get("email_address", "")
        if not email:
            print(f"Warning: Email missing for user {user_id} in {event_type} event.")
            # Decide if email is mandatory or handle accordingly

        user_data = {
            "email": email,
            "name": f"{data.get('first_name', '')} {data.get('last_name', '')}".strip(),
            "image_url": data.get("image_url", ""),
            # Extract custom metadata safely
            "is_admin": data.get("public_metadata", {}).get("is_admin", False),
            "metadata": data.get("public_metadata", {})
        }

        try:
            create_or_update_firebase_user(user_id, user_data)
            print(f"Successfully processed {event_type} for Clerk user: {user_id}")
        except Exception as e:
            print(f"Error processing {event_type} for Clerk user {user_id}: {e}")
            # Consider raising HTTPException or logging more details
            raise HTTPException(
                status_code=500, detail="Failed to sync user with Firebase"
            )

    elif event_type == "user.deleted":
        # Delete the user from Firebase
        print(f"Processing user.deleted event for Clerk user: {user_id}")
        try:
            # Get the corresponding Firebase UID (assuming stored previously)
            # Assumes get_firebase_user retrieves the mapping
            firebase_user_record = get_firebase_user(user_id)

            if firebase_user_record and firebase_user_record.get("firebase_uid"):
                firebase_uid = firebase_user_record["firebase_uid"]
                delete_firebase_user(firebase_uid)
                print(
                    f"Successfully deleted Firebase user: {firebase_uid} "
                    f"(Clerk ID: {user_id})"
                )
            else:
                print(
                    "Warning: Firebase mapping not found for deleted Clerk user: "
                    f"{user_id}"
                )

        except Exception as e:
            print(f"Error deleting Firebase user for Clerk ID {user_id}: {e}")
            # Decide if this should be a blocking error
            raise HTTPException(
                status_code=500, detail="Failed to delete user from Firebase"
            )

    else:
        print(f"Received unhandled Clerk event type: {event_type}")

    return {"status": "ok"}


# --- API Endpoints ---

# --- Policy Analysis ---
@app.get("/api/policies/{url:path}", response_model=PolicyAnalysis)
async def analyze_policy(url: str):
    """
    Analyze a privacy policy given its URL. (Placeholder Implementation)

    TODO: Replace this with actual analysis logic using agents.
          Currently returns dummy data and doesn't save results.
          Needs authentication dependency `user = Depends(get_current_user)`
          if saving per user.
    """
    try:
        print(f"Received request to analyze URL: {url}")
        # Check if we already have this policy analyzed (optional caching)
        # existing_analysis = get_policy_analysis(url)
        # if existing_analysis:
        #     print(f"Returning cached analysis for: {url}")
        #     return PolicyAnalysis(**existing_analysis)

        # 1. Use the Websearch Agent to get the privacy policy content
        # privacy_policy_content = run_websearch(url) # Placeholder

        # 2. Use Facts Checker Agent to verify claims
        # verified_claims = "Verified claims would go here" # Placeholder

        # 3. Use Legal Agent to summarize and provide insights
        # legal_summary = "Legal summary would go here" # Placeholder

        # --- Dummy Analysis Data ---
        website_name = url.split("//")[-1].split("/")[0] if url else "Unknown"
        analysis = PolicyAnalysis(
            url=url,
            websiteName=website_name,
            lastUpdated=datetime.now().strftime("%Y-%m-%d"),
            overallRisk="medium",
            overallSummary=(
                "This privacy policy is fairly standard but has some "
                "concerning elements regarding data sharing with third parties "
                "and unclear data retention policies."
            ),
            userLocation="United States",  # Placeholder - should be dynamic
            relevantRegulations=["GDPR", "CCPA"],  # Placeholder
            sections=[
                PolicySection(
                    title="Data Collection",
                    summary="Collects standard and some sensitive personal info",
                    details=(
                        "Collects name, email, device info, browsing history, "
                        "and potentially location data."
                    ),
                    riskLevel="medium"
                ),
                PolicySection(
                    title="Data Usage",
                    summary="Uses data for service improvement & marketing",
                    details=(
                        "Used to improve service, personalize experience, and "
                        "for targeted marketing via third-party networks."
                    ),
                    riskLevel="medium"
                ),
                PolicySection(
                    title="Data Sharing",
                    summary="Shares data with numerous third parties",
                    details=(
                        "Shared with service providers, advertisers, analytics co. "
                        "Some data may be sold (claimed anonymized)."
                     ),
                    riskLevel="high"
                )
            ]
        )
        # --- End Dummy Data ---

        # Save the analysis to Firestore (Requires user context)
        # Need user = Depends(get_current_user) in function signature
        # user_id = user["uid"] # Assuming 'uid' is the key
        # save_policy_analysis(user_id, url, analysis.dict())
        # print(f"Saved analysis for {url} for user {user_id}")

        return analysis
    except Exception as e:
        print(f"Error in analyze_policy for {url}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred during analysis: {str(e)}"
        )


# --- User Preferences ---

@app.get("/api/user/preferences", response_model=UserPreferences)
async def get_user_preferences_endpoint(user: dict = Depends(get_current_user)):
    """Fetch the current user's saved preferences from Firestore."""
    try:
        user_id = user["uid"]
        prefs_data = get_user_preferences(user_id)
        if not prefs_data:
            # Return default preferences or raise 404
            print(f"No preferences found for user {user_id}, returning defaults.")
            # Example default:
            # default_prefs = UserPreferences(
            #     country="US", riskThreshold="medium", notifications=True
            # )
            # return default_prefs
            raise HTTPException(
                status_code=404, detail="User preferences not found."
            )
        return UserPreferences(**prefs_data)
    except Exception as e:
        print(f"Error getting preferences for user {user.get('uid')}: {e}")
        raise HTTPException(
            status_code=500, detail="Could not retrieve preferences."
        )


@app.post("/api/user/preferences", response_model=dict)
async def update_user_preferences_endpoint(
    preferences: UserPreferences,
    user: dict = Depends(get_current_user)
):
    """Update the current user's preferences in Firestore."""
    try:
        user_id = user["uid"]
        updated_prefs_data = update_user_preferences(
            user_id, preferences.dict()
        )
        return {
            "status": "ok",
            "preferences": updated_prefs_data
        }
    except Exception as e:
        print(f"Error updating preferences for user {user.get('uid')}: {e}")
        raise HTTPException(
            status_code=500, detail="Could not update preferences."
        )


# --- User History ---

@app.get("/api/user/history", response_model=List[HistoryItem])
async def get_user_history_endpoint(user: dict = Depends(get_current_user)):
    """Fetch the current user's policy analysis history from Firestore."""
    try:
        user_id = user["uid"]
        history_data = get_user_history(user_id)
        # Convert Firestore Timestamps to strings if necessary?
        return [HistoryItem(**item) for item in history_data]
    except Exception as e:
        print(f"Error getting history for user {user.get('uid')}: {e}")
        raise HTTPException(
            status_code=500, detail="Could not retrieve history."
        )


@app.post("/api/user/history", response_model=dict)
async def add_to_history_endpoint(
    history_item: HistoryItem,
    user: dict = Depends(get_current_user)
):
    """Add a new analysis result to the current user's history in Firestore."""
    try:
        user_id = user["uid"]
        # Add server-side timestamp if 'analyzedAt' isn't reliable from client
        # history_item.analyzedAt = datetime.now().isoformat()
        add_to_history(user_id, history_item.dict())
        return {"status": "ok"}
    except Exception as e:
        print(f"Error adding history for user {user.get('uid')}: {e}")
        raise HTTPException(
            status_code=500, detail="Could not add to history."
        )


# --- Extension Features ---

@app.get("/api/extension/texting-risk", response_model=TextingRiskResponse)
async def check_texting_risk(url: str, user: dict = Depends(get_current_user)):
    """
    Placeholder endpoint for checking texting/SMS marketing risk for a URL.

    TODO: Implement actual logic, possibly using another agent.
    """
    print(f"Checking texting risk for {url} for user {user.get('uid')}")
    # In a real app, implement the actual logic based on policy analysis
    return TextingRiskResponse(
        url=url,
        textingRisk="medium",  # Placeholder
        message="Texting/SMS marketing appears average. Opt-out is available."
    )


# --- Legacy / Compatibility Endpoints ---

@app.post("/analyze_privacy_policy")
async def analyze_privacy_policy_legacy(request: AnalyzeRequest):
    """
    Original POST endpoint for policy analysis (kept for backward compatibility).

    Uses websearch agent but returns a fixed, detailed dummy analysis structure.
    Does not use the policy analyzer agent.
    """
    print(f"Received legacy request to analyze URL: {request.url}")
    try:
        # Example usage of websearch agent (currently commented out)
        # privacy_policy_content = run_websearch(request.url)
        # if not privacy_policy_content:
        #     raise HTTPException(
        #         status_code=404, detail="Could not fetch policy content."
        #     )

        # Create a detailed *dummy* analysis response matching old structure
        website_name = request.url.split("//")[-1].split("/")[0]
        analysis = {
            "success": True,
            "data": {
                "url": request.url,
                "websiteName": website_name,
                "lastUpdated": datetime.now().strftime("%Y-%m-%d"),
                "overallRisk": "medium",
                "overallSummary": (
                    "Legacy Endpoint: Fairly standard policy with some concerns "
                    "about data sharing and retention."
                ),
                "userLocation": request.location,
                "relevantRegulations": ["GDPR", "CCPA"],  # Placeholder
                "sections": [
                    {
                        "title": "Data Collection",
                        "summary": "Collects standard and sensitive info",
                        "details": ("Name, email, device, browsing history, "
                                    "location."),
                        "riskLevel": "medium"
                    },
                    {
                        "title": "Data Usage",
                        "summary": "Service improvement & marketing",
                        "details": ("Improvement, personalization, "
                                    "targeted ads."),
                        "riskLevel": "medium"
                    },
                    {
                        "title": "Data Sharing",
                        "summary": "Shares with third parties",
                        "details": ("Providers, advertisers, analytics. "
                                    "Data may be sold."),
                        "riskLevel": "high"
                    }
                ]
            }
        }

        return analysis

    except Exception as e:
        print(f"Error in legacy analyze_policy for {request.url}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred: {str(e)}"
        )


@app.get("/analyze/{url:path}")
async def analyze_privacy_policy_get(url: str, location: str = "US"):
    """
    GET endpoint for policy analysis, accessible via browser.

    Uses the websearch agent to fetch content and the policy analyzer agent
    for the actual analysis.
    """
    print(f"Received GET request to analyze URL: {url} for location: {location}")
    try:
        # 1. Use the Websearch Agent to get the privacy policy content
        privacy_policy_content = run_websearch(url)

        if not privacy_policy_content:
            print(f"Failed to retrieve content for URL: {url}")
            raise HTTPException(
                status_code=404,
                detail="Could not find or access the privacy policy for this URL"
            )
        content_len = len(privacy_policy_content)
        print(f"Successfully retrieved content for {url} (Length: {content_len})")

        # 2. Use the Policy Analyzer Agent to analyze the content
        # Import moved inside function? Check if needed globally.
        from agents.policy_analyzer_agent import (
            analyze_policy_content, get_risk_level
        )

        print(f"Starting analysis for URL: {url} with location: {location}")
        analysis_results = analyze_policy_content(
            privacy_policy_content=privacy_policy_content,
            location=location
            # demographics=None # Add if needed
        )
        print(f"Analysis completed for URL: {url}")

        # Check for errors during analysis itself
        if analysis_results.get("error"):
            analysis_error = analysis_results['error']
            print(f"Analysis agent returned error for {url}: {analysis_error}")
            raise HTTPException(
                status_code=500,
                detail=f"Analysis failed: {analysis_error}"
            )

        # 3. Create a structured response based on agent results
        website_name = url.split("//")[-1].split("/")[0]
        content_analysis = analysis_results.get("content_analysis", {})
        fact_check = analysis_results.get("fact_check", {})
        recommendations = analysis_results.get("recommendations", [])

        analysis_response = {
            "success": True,
            "data": {
                "url": url,
                "websiteName": website_name,
                # Or parse from policy
                "lastUpdated": datetime.now().strftime("%Y-%m-%d"),
                "userLocation": location,
                "overallRisk": get_risk_level(analysis_results),  # Use helper
                "sections": [
                    {
                        "title": "Data Collection",
                        "summary": content_analysis.get(
                            "data_collection", "Not found"
                        ),
                        # Example detail field
                        "details": content_analysis.get(
                            "data_collection_details", "Details not found"
                        ),
                        # Example risk field
                        "riskLevel": content_analysis.get(
                            "data_collection_risk", "medium"
                        )
                    },
                    {
                        "title": "Data Usage",
                        "summary": content_analysis.get(
                            "data_usage", "Not found"
                        ),
                        "details": content_analysis.get(
                            "data_usage_details", "Details not found"
                        ),
                        "riskLevel": content_analysis.get(
                            "data_usage_risk", "medium"
                        )
                    },
                    {
                        "title": "User Rights",
                        "summary": content_analysis.get(
                            "user_rights", "Not found"
                        ),
                        "details": content_analysis.get(
                            "user_rights_details", "Details not found"
                        ),
                        "riskLevel": content_analysis.get(
                            "user_rights_risk", "medium"
                        )
                    },
                    {
                        "title": "Compliance",
                        "summary": fact_check.get("compliance", "Not verified"),
                        "details": fact_check.get(
                            "compliance_details", "Details not found"
                        ),
                        "riskLevel": fact_check.get(
                            "compliance_risk", "medium"
                        )
                    }
                    # Add other sections as needed (e.g., Data Sharing, Security)
                ],
                "recommendations": recommendations
            }
        }

        return analysis_response

    except HTTPException as http_exc:
        # Re-raise HTTPExceptions to return proper status codes
        raise http_exc
    except Exception as e:
        import traceback
        print(f"Unexpected error in analyze_policy_get for {url}: {str(e)}")
        print(traceback.format_exc())  # Log full traceback for debugging
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected server error occurred: {str(e)}"
        )


# --- Optional: Add root endpoint for health check ---
@app.get("/")
async def root():
    """Basic health check endpoint."""
    return {"message": "Privacy Policy Analyzer API is running."}

# --- Optional: Run directly with uvicorn for development ---
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8002, reload=True)