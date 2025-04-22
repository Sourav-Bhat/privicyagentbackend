"""
Firebase Admin SDK Configuration and Initialization.

This module handles the initialization of the Firebase Admin SDK
using service account credentials and provides access to Firestore
and Authentication services.

SECURITY WARNING: Do NOT commit service account keys directly into
source code. Use environment variables (GOOGLE_APPLICATION_CREDENTIALS)
or a secure path referenced in .gitignore.
"""

import os
import firebase_admin
from firebase_admin import firestore, auth
from fastapi import HTTPException

# --- Firebase Admin SDK Initialization ---

# OPTION 1: Using Environment Variable (Recommended)
# Set the GOOGLE_APPLICATION_CREDENTIALS environment variable to the
# path of your downloaded service account key JSON file.
# If set, initialize_app() can be called without arguments.
# Example (do not run this here, set it in your environment):
# export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/serviceAccountKey.json"
# We will attempt this by default. If the env var isn't set, 
# initialize_app() will raise an error.

# OPTION 2: Using explicit file path (Ensure file is in .gitignore)
# from firebase_admin import credentials # Import only if using Option 2
# SERVICE_ACCOUNT_KEY_PATH = os.path.join(
#    os.path.dirname(__file__), 'serviceAccountKey.json'
# )
# if not os.path.exists(SERVICE_ACCOUNT_KEY_PATH):
#     raise FileNotFoundError(
#         f"Service account key not found at {SERVICE_ACCOUNT_KEY_PATH}. "
#         "Download it from Firebase Console and place it in the config "
#         "directory."
#     )
# cred = credentials.Certificate(SERVICE_ACCOUNT_KEY_PATH)

# OPTION 3: Loading from dictionary (DEPRECATED - INSECURE - REMOVED)
# print("SECURITY WARNING: Loading Firebase credentials directly from code. "
#       "This is insecure!")
# cred_dict = {
#     "type": os.getenv("FIREBASE_TYPE", "service_account"),
#     ... rest of the dict definition ...
# }
# ... checks for cred_dict ...
# cred = credentials.Certificate(cred_dict) # Removed initialization using dict

# Initialize the app only if it hasn't been initialized yet.
# This prevents errors if this module is imported multiple times.
# When GOOGLE_APPLICATION_CREDENTIALS is set, initialize_app() uses it 
# automatically. Otherwise, it will raise an error if no credentials can 
# be found.
if not firebase_admin._apps:
    try:
        # Initialize without explicit credentials - relies on 
        # GOOGLE_APPLICATION_CREDENTIALS
        firebase_admin.initialize_app()
        print("Firebase Admin SDK initialized successfully "
              "(using GOOGLE_APPLICATION_CREDENTIALS).")
    except Exception as e:
        print(f"FATAL: Failed to initialize Firebase Admin SDK: {e}")
        print("Ensure the GOOGLE_APPLICATION_CREDENTIALS environment variable "
              "is set correctly.")
        # Depending on the app structure, might want to exit or raise
        # raise RuntimeError(f"Failed to initialize Firebase: {e}") from e

# --- Firestore Client ---
# Provides access to the Firestore database.
db = firestore.client()

# --- Firebase Authentication Helper ---

def verify_firebase_token(token: str) -> dict:
    """
    Verifies a Firebase ID token provided by a client.

    Uses the Firebase Admin SDK's verify_id_token function.

    Args:
        token: The Firebase ID token string to verify.

    Returns:
        A dictionary containing the decoded token claims upon successful
        verification.

    Raises:
        HTTPException(401): If the token is invalid, expired, revoked,
                           or if any other verification error occurs.
    """
    if not token:
        raise HTTPException(status_code=401, detail="Missing authentication token.")

    try:
        # Verify the ID token while checking if the token is revoked.
        decoded_token = auth.verify_id_token(token, check_revoked=True)
        # TODO: Potentially add checks for specific claims if needed
        # e.g., check issuer, audience
        return decoded_token
    except auth.RevokedIdTokenError:
        print("Authentication failed: Token has been revoked.")
        raise HTTPException(status_code=401, detail="Token revoked.")
    except auth.UserDisabledError:
        print("Authentication failed: User account is disabled.")
        raise HTTPException(status_code=401, detail="User disabled.")
    except auth.InvalidIdTokenError as e:
        # This catches various issues like expiration, malformed token, etc.
        print(f"Authentication failed: Invalid ID token: {str(e)}")
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
    except Exception as e:
        # Catch any other unexpected errors during verification
        print(f"Unexpected error during token verification: {str(e)}")
        raise HTTPException(
            status_code=500,  # Internal server error might be more appropriate
            detail=f"Internal error during authentication: {str(e)}"
        ) 