import os
from dotenv import load_dotenv
import google.generativeai as genai
import json

# Load environment variables
load_dotenv()

# Configure the Gemini API
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

# Initialize the model
model = genai.GenerativeModel('models/gemini-1.5-pro')

def clean_response(text: str) -> str:
    """Clean the response text by removing markdown code block markers."""
    # Remove ```json and ``` markers
    text = text.replace("```json", "").replace("```", "")
    return text.strip()

def test_policy_analysis():
    # Sample privacy policy text
    sample_policy = """
    Privacy Policy for Example Company
    
    Last Updated: January 1, 2024
    
    1. Information We Collect
    We collect information that you provide directly to us, including:
    - Name and contact information
    - Payment information
    - Usage data and preferences
    
    2. How We Use Your Information
    We use the information we collect to:
    - Provide and maintain our services
    - Process your transactions
    - Send you marketing communications
    - Improve our services
    
    3. Information Sharing
    We may share your information with:
    - Service providers
    - Business partners
    - Legal authorities when required
    
    4. Data Security
    We implement appropriate security measures to protect your personal 
    information.
    
    5. Your Rights
    You have the right to:
    - Access your personal data
    - Request corrections
    - Delete your account
    - Opt-out of marketing communications
    
    6. Contact Us
    If you have any questions, please contact us at privacy@example.com
    """
    
    # Create the prompt
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
""" + sample_policy + """

Remember: Return ONLY the JSON object with no additional text."""

    # Get response from Gemini
    response = model.generate_content(prompt)
    print("\nRaw response from Gemini API:")
    print("=" * 50)
    print(response.text)
    
    try:
        # Clean and parse the response
        cleaned_text = clean_response(response.text)
        result = json.loads(cleaned_text)
        
        print("\nParsed JSON result:", result)
        print("=" * 50)
        for key, value in result.items():
            print(f"\n{key}:")
            print(value)
    except json.JSONDecodeError as e:
        print(f"\nError parsing JSON: {e}")
        print("Raw text that failed to parse:")
        print(cleaned_text)

if __name__ == "__main__":
    test_policy_analysis() 