import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Configure the Gemini API
api_key = os.getenv("GEMINI_API_KEY")
print(f"API Key: {api_key[:10]}...")
genai.configure(api_key=api_key)

# List available models
print("\nAvailable Models:")
for m in genai.list_models():
    print(f"- {m.name}")

# Test with different model versions
models_to_try = [
    'models/gemini-1.5-pro',
    'models/gemini-1.5-pro-latest',
    'models/chat-bison-001'
]

for model_name in models_to_try:
    print(f"\nTrying model: {model_name}")
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content("What is 2+2?")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {str(e)}") 