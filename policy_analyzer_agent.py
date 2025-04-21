from typing import Dict, Any, List, Optional
import google.generativeai as genai
from dotenv import load_dotenv
import os
import json

# Load environment variables
load_dotenv()

# Configure the Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Initialize the model
model = genai.GenerativeModel('models/gemini-1.5-pro')

def safe_parse_response(response: str) -> Dict[str, Any]:
    """Safely parse the model's response into a dictionary."""
    try:
        # Clean up the response string
        response = response.strip()
        
        # Remove markdown code block markers
        response = response.replace("```json", "").replace("```", "").strip()
        
        # If the response is already a valid JSON, parse it directly
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            print(f"Debug - Failed to parse cleaned response: {response}")
        
        # Try to find a JSON-like structure in the response
        start = response.find('{')
        end = response.rfind('}') + 1
        
        if start >= 0 and end > start:
            json_str = response[start:end]
            try:
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                print(f"Debug - Failed to parse JSON: {e}")
                print(f"Debug - JSON string: {json_str}")
                return {"error": f"Failed to parse JSON: {str(e)}"}
        
        # Try to find a JSON array if no object is found
        start = response.find('[')
        end = response.rfind(']') + 1
        
        if start >= 0 and end > start:
            json_str = response[start:end]
            try:
                return {"result": json.loads(json_str)}
            except json.JSONDecodeError as e:
                print(f"Debug - Failed to parse JSON array: {e}")
                print(f"Debug - JSON string: {json_str}")
                return {"error": f"Failed to parse JSON array: {str(e)}"}
        
        print(f"Debug - No JSON structure found in response: {response}")
        return {"error": "No JSON structure found in response"}
    except Exception as e:
        print(f"Debug - Unexpected error: {str(e)}")
        print(f"Debug - Response: {response}")
        return {"error": f"Failed to parse response: {str(e)}"}

def analyze_policy_content(
    privacy_policy_content: str,
    location: str = "United States",
    demographics: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Analyze privacy policy content using multiple specialized agents.
    
    Args:
        privacy_policy_content (str): The content of the privacy policy
        location (str): User's location for legal context
        demographics (Optional[Dict[str, Any]]): User's demographic information
        
    Returns:
        Dict[str, Any]: Structured analysis results
    """
    try:
        # 1. Content Analysis Agent
        content_analysis = analyze_content(
            privacy_policy_content
        )
        
        # 2. Fact Checker Agent
        fact_check = verify_claims(
            privacy_policy_content
        )
        
        # 3. Legal Analysis Agent
        legal_analysis = analyze_legal_implications(
            privacy_policy_content,
            location,
            demographics
        )
        
        # 4. Risk Assessment
        risk_assessment = assess_risks(
            content_analysis,
            fact_check,
            legal_analysis
        )
        
        # Combine all analyses
        return {
            "content_analysis": content_analysis,
            "fact_check": fact_check,
            "legal_analysis": legal_analysis,
            "risk_assessment": risk_assessment,
            "recommendations": generate_recommendations(
                content_analysis,
                fact_check,
                legal_analysis,
                risk_assessment
            )
        }
    except Exception as e:
        return {
            "error": f"Error analyzing policy: {str(e)}",
            "content_analysis": {},
            "fact_check": {},
            "legal_analysis": {},
            "risk_assessment": {},
            "recommendations": []
        }

def analyze_content(content: str) -> Dict[str, Any]:
    """
    Analyze the content structure and key sections of the privacy policy.
    """
    prompt = """You are a JSON-only response API. Your response must be a valid JSON object with no additional text, comments, or explanations.

Analyze this privacy policy and return a JSON object with the following structure:
{
    "data_collection": "string describing data collection practices",
    "data_usage": "string describing how data is used",
    "data_sharing": "string describing third-party sharing practices",
    "user_rights": "string describing user rights and controls",
    "data_retention": "string describing retention and deletion policies",
    "security": "string describing security measures",
    "childrens_privacy": "string describing children's privacy practices",
    "international_transfers": "string describing international data transfers"
}

Privacy Policy:
""" + content + """

Remember: Return ONLY the JSON object with no additional text."""
    
    response = model.generate_content(prompt)
    return safe_parse_response(response.text)

def verify_claims(content: str) -> Dict[str, Any]:
    """
    Verify specific claims made in the privacy policy against known standards.
    """
    prompt = """You are a JSON-only response API. Your response must be a valid JSON object with no additional text, comments, or explanations.

Verify the following privacy policy claims and return a JSON object with this structure:
{
    "compliance": "string verifying compliance claims (GDPR, CCPA, etc.)",
    "protection": "string verifying data protection measures",
    "sharing": "string verifying third-party sharing practices",
    "rights": "string verifying user rights implementation",
    "retention": "string verifying data retention policies"
}

Privacy Policy:
""" + content + """

Remember: Return ONLY the JSON object with no additional text."""
    
    response = model.generate_content(prompt)
    return safe_parse_response(response.text)

def analyze_legal_implications(
    content: str,
    location: str,
    demographics: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Analyze legal implications based on user's location and demographics.
    """
    demographics_context = ""
    if demographics:
        demographics_context = (
            f"with the following characteristics: {demographics}"
        )
    
    prompt = f"""You are a JSON-only response API. Your response must be a valid JSON object with no additional text, comments, or explanations.

Analyze the legal implications of this privacy policy and return a JSON object with this structure:
{{
    "applicable_laws": "string listing applicable laws and regulations",
    "compliance_status": "string describing current compliance status",
    "legal_risks": "string describing potential legal risks",
    "user_rights": "string describing user rights under local law",
    "enforcement": "string describing available enforcement mechanisms"
}}

Location: {location}
Demographics: {demographics_context}

Privacy Policy:
{content}

Remember: Return ONLY the JSON object with no additional text."""
    
    response = model.generate_content(prompt)
    return safe_parse_response(response.text)

def assess_risks(
    content_analysis: Dict[str, Any],
    fact_check: Dict[str, Any],
    legal_analysis: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Assess overall risks based on all analyses.
    """
    prompt = f"""You are a JSON-only response API. Your response must be a valid JSON object with no additional text, comments, or explanations.

Assess the overall risks based on these analyses and return a JSON object with this structure:
{{
    "risk_level": "string indicating overall risk level (high/medium/low)",
    "risk_factors": "string listing identified risk factors",
    "impact": "string describing impact assessment details",
    "mitigation": "string suggesting mitigation measures"
}}

Content Analysis:
{content_analysis}

Fact Check Results:
{fact_check}

Legal Analysis:
{legal_analysis}

Remember: Return ONLY the JSON object with no additional text."""
    
    response = model.generate_content(prompt)
    return safe_parse_response(response.text)

def generate_recommendations(
    content_analysis: Dict[str, Any],
    fact_check: Dict[str, Any],
    legal_analysis: Dict[str, Any],
    risk_assessment: Dict[str, Any]
) -> List[str]:
    """
    Generate specific recommendations based on all analyses.
    """
    prompt = f"""You are a JSON-only response API. Your response must be a valid JSON array with no additional text, comments, or explanations.

Generate specific recommendations based on these analyses and return a JSON array of strings:

Content Analysis:
{content_analysis}

Fact Check Results:
{fact_check}

Legal Analysis:
{legal_analysis}

Risk Assessment:
{risk_assessment}

Remember: Return ONLY a JSON array of recommendation strings with no additional text."""
    
    response = model.generate_content(prompt)
    
    try:
        response_text = response.text
        # Remove markdown code block markers
        response_text = response_text.replace("```json", "").replace("```", "").strip()
        
        # Try to find a JSON array in the response
        start = response_text.find('[')
        end = response_text.rfind(']') + 1
        if start >= 0 and end > start:
            json_str = response_text[start:end]
            return json.loads(json_str)
        return ["Failed to find recommendations in response"]
    except Exception:
        return ["Failed to parse recommendations"]

def get_risk_level(analysis: Dict[str, Any]) -> str:
    """
    Determine the overall risk level based on the analysis.
    
    Args:
        analysis (Dict[str, Any]): The analysis results
        
    Returns:
        str: Risk level ("low", "medium", or "high")
    """
    # Count the number of high, medium, and low risk levels
    risk_counts = {"high": 0, "medium": 0, "low": 0}
    
    sections = ["data_collection", "data_usage", "user_rights", "compliance"]
    for section in sections:
        if section in analysis and "risk_level" in analysis[section]:
            risk_level = analysis[section]["risk_level"].lower()
            if risk_level in risk_counts:
                risk_counts[risk_level] += 1
    
    # Determine overall risk level
    if risk_counts["high"] >= 2:
        return "high"
    elif risk_counts["high"] == 1 or risk_counts["medium"] >= 2:
        return "medium"
    else:
        return "low" 