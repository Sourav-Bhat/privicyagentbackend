"""
Agent responsible for analyzing privacy policy content using Google Gemini.

This module coordinates multiple analysis steps (content, fact-checking,
legal implications, risk assessment) and generates recommendations.
"""
from typing import Dict, Any, List, Optional
import google.generativeai as genai
from dotenv import load_dotenv
import os
import json

# Load environment variables (ensure .env file has GEMINI_API_KEY)
load_dotenv()

# Configure the Gemini API Key
# Consider moving API key configuration to a central config module
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    # Handle missing API key gracefully (e.g., raise error, log warning)
    print("Warning: GEMINI_API_KEY not found in environment variables.")
    # raise ValueError("GEMINI_API_KEY environment variable not set.")
genai.configure(api_key=API_KEY)

# Initialize the Generative Model
# Consider making the model name configurable
# TODO: Add error handling for model initialization failure
model = genai.GenerativeModel('models/gemini-1.5-pro')

def safe_parse_response(response: str) -> Dict[str, Any]:
    """
    Safely parses a string potentially containing a JSON object or array.

    Handles responses wrapped in markdown code blocks (```json ... ```).
    Attempts to find and parse JSON objects ({...}) or arrays ([...]).

    Args:
        response: The raw string response from the generative model.

    Returns:
        A dictionary containing the parsed JSON data, or an error message
        if parsing fails or no JSON is found.
        For JSON arrays, returns {"result": [...]}.
    """
    try:
        # Clean up the response string
        response = response.strip()

        # Remove markdown code block markers if present
        if response.startswith("```json"):
            response = response[len("```json"):].strip()
        if response.startswith("```"):
            response = response[len("```"):].strip()
        if response.endswith("```"):
            response = response[:-len("```")].strip()

        # Try parsing directly first
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Expected if response contains extra text or is not pure JSON
            print("Debug - Initial JSON parse failed, trying extraction.")

        # Try to extract a JSON object {...}
        start_obj = response.find('{')
        end_obj = response.rfind('}')
        if start_obj != -1 and end_obj != -1 and end_obj > start_obj:
            json_str = response[start_obj:end_obj + 1]
            try:
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                print(f"Debug - Failed to parse extracted JSON object: {e}")
                print(f"Debug - Extracted object string: {json_str}")
                # Continue to try array extraction

        # Try to extract a JSON array [...] if no object found or parsed
        start_arr = response.find('[')
        end_arr = response.rfind(']')
        if start_arr != -1 and end_arr != -1 and end_arr > start_arr:
            json_str = response[start_arr:end_arr + 1]
            try:
                # Return array within a standard dictionary structure
                return {"result": json.loads(json_str)}
            except json.JSONDecodeError as e:
                print(f"Debug - Failed to parse extracted JSON array: {e}")
                print(f"Debug - Extracted array string: {json_str}")
                # If array parsing also fails, return error

        # If neither object nor array parsing worked
        print(f"Debug - No valid JSON structure found in response: {response}")
        return {"error": "No valid JSON structure found in the response."}

    except Exception as e:
        # Catch any unexpected errors during processing
        print(f"Debug - Unexpected error in safe_parse_response: {str(e)}")
        print(f"Debug - Original response: {response}")
        return {"error": f"Failed to parse response due to unexpected error: {str(e)}"}


def analyze_policy_content(
    privacy_policy_content: str,
    location: str = "United States",
    demographics: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Analyzes privacy policy content using multiple specialized LLM calls.

    This function orchestrates calls to agents for content analysis,
    fact-checking, legal implications, risk assessment, and generates
    recommendations based on the combined results.

    Args:
        privacy_policy_content: The full text of the privacy policy.
        location: The user's geographical location (e.g., "UK", "US-CA")
                  to provide context for legal analysis.
        demographics: Optional dictionary containing user demographic
                      information (e.g., {"age": 25}) for tailored analysis.

    Returns:
        A dictionary containing the structured analysis results from each
        agent, including content_analysis, fact_check, legal_analysis,
        risk_assessment, and recommendations. Includes an "error" key
        if the overall analysis fails.
    """
    results = {}
    try:
        # 1. Content Analysis Agent
        print("Starting content analysis...")
        results["content_analysis"] = analyze_content(privacy_policy_content)
        print("Content analysis finished.")

        # 2. Fact Checker Agent
        print("Starting fact check...")
        results["fact_check"] = verify_claims(privacy_policy_content)
        print("Fact check finished.")

        # 3. Legal Analysis Agent
        print("Starting legal analysis...")
        results["legal_analysis"] = analyze_legal_implications(
            privacy_policy_content,
            location,
            demographics
        )
        print("Legal analysis finished.")

        # 4. Risk Assessment Agent
        print("Starting risk assessment...")
        results["risk_assessment"] = assess_risks(
            results.get("content_analysis", {}),  # Pass results safely
            results.get("fact_check", {}),
            results.get("legal_analysis", {})
        )
        print("Risk assessment finished.")

        # 5. Recommendation Generation
        print("Generating recommendations...")
        results["recommendations"] = generate_recommendations(
            results.get("content_analysis", {}),
            results.get("fact_check", {}),
            results.get("legal_analysis", {}),
            results.get("risk_assessment", {})
        )
        print("Recommendations generated.")

        # Return combined results
        return results

    except Exception as e:
        # Catch errors during the orchestration process
        print(f"Error during policy analysis orchestration: {str(e)}")
        # Return partial results along with the error
        results["error"] = f"Error analyzing policy: {str(e)}"
        # Ensure default empty structures for keys not yet populated
        results.setdefault("content_analysis", {})
        results.setdefault("fact_check", {})
        results.setdefault("legal_analysis", {})
        results.setdefault("risk_assessment", {})
        results.setdefault("recommendations", [])
        return results


def analyze_content(content: str) -> Dict[str, Any]:
    """
    Analyzes the content structure and key sections of the privacy policy.

    Uses the Gemini model to extract information about data collection, usage,
    sharing, user rights, retention, security, children's privacy, and
    international transfers based on the provided policy text.

    Args:
        content: The privacy policy text.

    Returns:
        A dictionary parsed from the model's JSON response, containing the
        extracted content details or an error message.
    """
    # Note: Ensure the prompt clearly specifies the desired JSON structure.
    prompt = ("""You are a JSON-only response API. Your response must be a "
              "valid JSON object with no additional text, comments, or explanations.\n\n"
              "Analyze this privacy policy and return a JSON object with the "
              "following structure:\n"
              "{\n"
              "    \"data_collection\": \"string describing data collection practices\",\n"
              "    \"data_usage\": \"string describing how data is used\",\n"
              "    \"data_sharing\": \"string describing third-party sharing practices\",\n"
              "    \"user_rights\": \"string describing user rights and controls\",\n"
              "    \"data_retention\": \"string describing retention and deletion policies\",\n"
              "    \"security\": \"string describing security measures\",\n"
              "    \"childrens_privacy\": \"string describing children's privacy practices\",\n"
              "    \"international_transfers\": \"string describing international data transfers\"\n"
              "}\n\n"
              "Privacy Policy:\n""" + content + """\n\n"
              "Remember: Return ONLY the JSON object with no additional text.""")

    try:
        response = model.generate_content(prompt)
        # TODO: Add checks for response safety/appropriateness if needed
        return safe_parse_response(response.text)
    except Exception as e:
        print(f"Error calling Gemini for content analysis: {str(e)}")
        return {"error": f"Content analysis failed: {str(e)}"}


def verify_claims(content: str) -> Dict[str, Any]:
    """
    Verifies specific claims made in the privacy policy against known standards.

    Uses the Gemini model to check claims related to compliance (GDPR, CCPA),
    data protection, sharing practices, user rights implementation, and
    retention policies.

    Args:
        content: The privacy policy text.

    Returns:
        A dictionary parsed from the model's JSON response, containing the
        verification results or an error message.
    """
    prompt = ("""You are a JSON-only response API. Your response must be a valid "
              "JSON object with no additional text, comments, or explanations.\n\n"
              "Verify the following privacy policy claims and return a JSON "
              "object with this structure:\n"
              "{\n"
              "    \"compliance\": \"string verifying compliance claims (GDPR, CCPA, etc.)\",\n"
              "    \"protection\": \"string verifying data protection measures\",\n"
              "    \"sharing\": \"string verifying third-party sharing practices\",\n"
              "    \"rights\": \"string verifying user rights implementation\",\n"
              "    \"retention\": \"string verifying data retention policies\"\n"
              "}\n\n"
              "Privacy Policy:\n""" + content + """\n\n"
              "Remember: Return ONLY the JSON object with no additional text.""")

    try:
        response = model.generate_content(prompt)
        return safe_parse_response(response.text)
    except Exception as e:
        print(f"Error calling Gemini for fact checking: {str(e)}")
        return {"error": f"Fact checking failed: {str(e)}"}


def analyze_legal_implications(
    content: str,
    location: str,
    demographics: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Analyzes legal implications based on user's location and demographics.

    Uses the Gemini model to identify applicable laws, assess compliance status,
    highlight legal risks, describe user rights under local law, and mention
    enforcement mechanisms, considering the provided location and demographics.

    Args:
        content: The privacy policy text.
        location: The user's geographical location (e.g., "UK", "US-CA").
        demographics: Optional user demographic information.

    Returns:
        A dictionary parsed from the model's JSON response, containing the
        legal analysis or an error message.
    """
    demographics_context = ""
    if demographics:
        # Format demographics safely for inclusion in the prompt
        try:
            demo_str = ", ".join(f"{k}: {v}" for k, v in demographics.items())
            demographics_context = f"with the following characteristics: {demo_str}"
        except Exception as e:
            print(f"Warning: Could not format demographics: {e}")
            demographics_context = "(demographics provided but could not be formatted)"

    prompt = (f"""You are a JSON-only response API. Your response must be a "
              f"valid JSON object with no additional text, comments, or explanations.\n\n"
              f"Analyze the legal implications of this privacy policy and return a "
              f"JSON object with this structure:\n"
              f"{{ "
              f"    \"applicable_laws\": \"string listing applicable laws/regulations\", "
              f"    \"compliance_status\": \"string describing current compliance status\", "
              f"    \"legal_risks\": \"string describing potential legal risks\", "
              f"    \"user_rights\": \"string describing user rights under local law\", "
              f"    \"enforcement\": \"string describing available enforcement mechanisms\" "
              f"}}\n\n"
              f"Location: {location}\n"
              f"Demographics: {demographics_context}\n\n"
              f"Privacy Policy:\n{content}\n\n"
              f"Remember: Return ONLY the JSON object with no additional text.""")

    try:
        response = model.generate_content(prompt)
        return safe_parse_response(response.text)
    except Exception as e:
        print(f"Error calling Gemini for legal analysis: {str(e)}")
        return {"error": f"Legal analysis failed: {str(e)}"}


def assess_risks(
    content_analysis: Dict[str, Any],
    fact_check: Dict[str, Any],
    legal_analysis: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Assesses overall privacy risks based on previous analysis stages.

    Uses the Gemini model to determine an overall risk level (high/medium/low),
    identify risk factors, describe potential impact, and suggest mitigation
    measures, based on the provided content, fact-check, and legal analyses.

    Args:
        content_analysis: The dictionary result from analyze_content.
        fact_check: The dictionary result from verify_claims.
        legal_analysis: The dictionary result from analyze_legal_implications.

    Returns:
        A dictionary parsed from the model's JSON response, containing the
        risk assessment or an error message.
    """
    # Safely convert analysis dicts to string representations for the prompt
    content_str = json.dumps(content_analysis, indent=2)
    fact_str = json.dumps(fact_check, indent=2)
    legal_str = json.dumps(legal_analysis, indent=2)

    prompt = (f"""You are a JSON-only response API. Your response must be a "
              f"valid JSON object with no additional text, comments, or explanations.\n\n"
              f"Assess the overall risks based on these analyses and return a JSON "
              f"object with this structure:\n"
              f"{{ "
              f"    \"risk_level\": \"string indicating overall risk level (high/medium/low)\", "
              f"    \"risk_factors\": \"string listing identified risk factors\", "
              f"    \"impact\": \"string describing impact assessment details\", "
              f"    \"mitigation\": \"string suggesting mitigation measures\" "
              f"}}\n\n"
              f"Content Analysis:\n{content_str}\n\n"
              f"Fact Check Results:\n{fact_str}\n\n"
              f"Legal Analysis:\n{legal_str}\n\n"
              f"Remember: Return ONLY the JSON object with no additional text.""")

    try:
        response = model.generate_content(prompt)
        return safe_parse_response(response.text)
    except Exception as e:
        print(f"Error calling Gemini for risk assessment: {str(e)}")
        return {"error": f"Risk assessment failed: {str(e)}"}


def generate_recommendations(
    content_analysis: Dict[str, Any],
    fact_check: Dict[str, Any],
    legal_analysis: Dict[str, Any],
    risk_assessment: Dict[str, Any]
) -> List[str]:
    """
    Generates specific, actionable recommendations based on all analysis stages.

    Uses the Gemini model to create a list of recommendations addressing issues
    found in the content analysis, fact-checking, legal implications, and
    risk assessment.

    Args:
        content_analysis: Result from analyze_content.
        fact_check: Result from verify_claims.
        legal_analysis: Result from analyze_legal_implications.
        risk_assessment: Result from assess_risks.

    Returns:
        A list of strings, where each string is a recommendation. Returns a
        list containing an error message if parsing or generation fails.
    """
    content_str = json.dumps(content_analysis, indent=2)
    fact_str = json.dumps(fact_check, indent=2)
    legal_str = json.dumps(legal_analysis, indent=2)
    risk_str = json.dumps(risk_assessment, indent=2)

    prompt = (f"""You are a JSON-only response API. Your response must be a "
              f"valid JSON array of strings with no additional text, comments, "
              f"or explanations.\n\n"
              f"Generate specific recommendations based on these analyses and return "
              f"a JSON array of strings:\n\n"
              f"Content Analysis:\n{content_str}\n\n"
              f"Fact Check Results:\n{fact_str}\n\n"
              f"Legal Analysis:\n{legal_str}\n\n"
              f"Risk Assessment:\n{risk_str}\n\n"
              f"Remember: Return ONLY a JSON array of recommendation strings "
              f"with no additional text.""")

    try:
        response = model.generate_content(prompt)
        parsed_response = safe_parse_response(response.text)

        # Expecting format {'result': [...]}
        if isinstance(parsed_response, dict) and "result" in parsed_response:
            if isinstance(parsed_response["result"], list):
                # Ensure all items in the list are strings
                return [str(item) for item in parsed_response["result"]]
            else:
                print("Warning: Recommendations result is not a list.")
                return ["Failed to parse recommendations: result is not a list."]
        # Handle case where model might return a list directly (less likely with prompt)
        elif isinstance(parsed_response, list):
             print("Warning: Model returned a list directly for recommendations.")
             return [str(item) for item in parsed_response]
        elif parsed_response.get("error"):
             print(f"Error in recommendation response: {parsed_response['error']}")
             return [f"Failed to generate recommendations: {parsed_response['error']}"]
        else:
            print("Warning: Unexpected format for recommendations response.")
            return ["Failed to parse recommendations: Unexpected format."]

    except Exception as e:
        print(f"Error calling Gemini for recommendations: {str(e)}")
        return [f"Recommendation generation failed: {str(e)}"]


def get_risk_level(analysis: Dict[str, Any]) -> str:
    """
    Determines an overall risk level based on the combined analysis results.

    This is a simplified heuristic. It primarily looks at the risk_level
    field within the 'risk_assessment' part of the analysis dictionary.
    If that's missing, it falls back to a default or simple check.

    Args:
        analysis: The complete analysis results dictionary potentially containing
                  content_analysis, fact_check, legal_analysis, risk_assessment.

    Returns:
        A risk level string: "low", "medium", or "high". Defaults to "medium".
    """
    # Prioritize the risk level directly from the risk assessment agent
    risk_assessment = analysis.get("risk_assessment", {})
    explicit_risk = risk_assessment.get("risk_level", "").lower()

    if explicit_risk in ["high", "medium", "low"]:
        return explicit_risk

    print("Warning: Risk level not explicitly found in risk_assessment. Using fallback logic.")

    # --- Fallback Logic (Optional - if risk_assessment doesn't provide level) ---
    # Example: Count high/medium risks in other sections (less reliable)
    # risk_counts = {"high": 0, "medium": 0, "low": 0}
    # sections_to_check = [
    #     analysis.get("content_analysis", {}),
    #     analysis.get("fact_check", {}),
    #     analysis.get("legal_analysis", {})
    # ]
    # for section_data in sections_to_check:
    #     # Need to know the exact keys where risk might be stored, e.g., 'compliance_risk'
    #     # This part is highly dependent on the structure returned by other agents
    #     pass # Implement detailed fallback logic if needed

    # Default fallback if no clear risk level is found
    return "medium" 