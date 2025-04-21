from typing import Dict, Any
from policy_analyzer_agent import analyze_policy_content
from dotenv import load_dotenv


def main() -> None:
    # Load environment variables
    load_dotenv()
    
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
    
    # Analyze the policy
    print("Analyzing privacy policy...")
    analysis: Dict[str, Any] = analyze_policy_content(sample_policy)
    
    # Display results
    print("\nAnalysis Results:")
    print("=" * 50)
    
    # Check if there was an error
    if "error" in analysis:
        print(f"\nError: {analysis['error']}")
        return
    
    # Display content analysis
    print("\nContent Analysis:")
    if "content_analysis" in analysis:
        for key, value in analysis["content_analysis"].items():
            print(f"- {key}: {value}")
    else:
        print("No content analysis available")
    
    # Display fact check
    print("\nFact Check:")
    if "fact_check" in analysis:
        for key, value in analysis["fact_check"].items():
            print(f"- {key}: {value}")
    else:
        print("No fact check available")
    
    # Display legal analysis
    print("\nLegal Analysis:")
    if "legal_analysis" in analysis:
        for key, value in analysis["legal_analysis"].items():
            print(f"- {key}: {value}")
    else:
        print("No legal analysis available")
    
    # Display risk assessment
    print("\nRisk Assessment:")
    if "risk_assessment" in analysis:
        for key, value in analysis["risk_assessment"].items():
            print(f"- {key}: {value}")
    else:
        print("No risk assessment available")
    
    # Display recommendations
    print("\nRecommendations:")
    if "recommendations" in analysis and analysis["recommendations"]:
        for rec in analysis["recommendations"]:
            print(f"- {rec}")
    else:
        print("No recommendations available")


if __name__ == "__main__":
    main() 