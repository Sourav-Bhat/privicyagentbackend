import requests
import json
from datetime import datetime

# Base URL - change this to your server URL
BASE_URL = "http://localhost:8002"

# Add your Firebase token here
AUTH_TOKEN = "your_firebase_token_here"
HEADERS = {
    "Authorization": f"Bearer {AUTH_TOKEN}"
}

def test_policy_analysis():
    print("\nTesting Policy Analysis API...")
    url = "https://www.google.com/privacy-policy"
    try:
        response = requests.get(
            f"{BASE_URL}/api/policies/{url}",
            headers=HEADERS
        )
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {str(e)}")

def test_user_preferences():
    print("\nTesting User Preferences API...")
    # Test data
    preferences = {
        "country": "US",
        "riskThreshold": "medium",
        "notifications": True
    }
    try:
        # Get preferences
        response = requests.get(
            f"{BASE_URL}/api/user/preferences",
            headers=HEADERS
        )
        print("GET Preferences:")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        # Update preferences
        response = requests.post(
            f"{BASE_URL}/api/user/preferences",
            headers=HEADERS,
            json=preferences
        )
        print("\nPOST Preferences:")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {str(e)}")

def test_user_history():
    print("\nTesting User History API...")
    # Test data
    history_item = {
        "url": "https://example.com/privacy",
        "analyzedAt": datetime.now().isoformat(),
        "policyTitle": "Example Privacy Policy",
        "riskLevel": "medium"
    }
    try:
        # Get history
        response = requests.get(
            f"{BASE_URL}/api/user/history",
            headers=HEADERS
        )
        print("GET History:")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        # Add to history
        response = requests.post(
            f"{BASE_URL}/api/user/history",
            headers=HEADERS,
            json=history_item
        )
        print("\nPOST History:")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {str(e)}")

def test_texting_risk():
    print("\nTesting Texting Risk API...")
    url = "https://example.com"
    try:
        response = requests.get(
            f"{BASE_URL}/api/extension/texting-risk",
            headers=HEADERS,
            params={"url": url}
        )
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {str(e)}")

def test_analyze_privacy_policy():
    print("\nTesting Analyze Privacy Policy API...")
    data = {
        "url": "https://www.google.com/privacy-policy",
        "location": "US-CA",
        "demographics": "age:25"
    }
    try:
        response = requests.post(
            f"{BASE_URL}/analyze_privacy_policy",
            json=data
        )
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    print("Starting API Tests...")
    
    # Run all tests
    test_policy_analysis()
    test_user_preferences()
    test_user_history()
    test_texting_risk()
    test_analyze_privacy_policy()
    
    print("\nAPI Tests Completed!") 