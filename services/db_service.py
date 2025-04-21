"""
Firestore Database Service.

Provides functions to interact with Firestore for managing user preferences,
analysis history, and cached policy analyses.
Relies on the Firebase Admin SDK being initialized (see config.firebase_config).
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from config.firebase_config import db

# --- Firestore Collection References ---
# It can be useful to define collection names as constants
USERS_COLLECTION = "users"
PREFERENCES_DOC = "preferences"
HISTORY_COLLECTION = "history"
ANALYSIS_CACHE_COLLECTION = "policyAnalysisCache"


# --- User Preferences --- #


def get_user_preferences(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves user preferences from Firestore.

    Args:
        user_id: The unique identifier for the user.

    Returns:
        A dictionary containing user preferences if found, otherwise None.
    """
    if not user_id:
        print("Error: user_id cannot be empty for get_user_preferences")
        return None
    try:
        # print(f"Attempting to get preferences for user: {user_id}") # Debug
        prefs_ref = db.collection(USERS_COLLECTION).document(user_id)
        prefs_doc = prefs_ref.get()
        # print(f"Firestore doc snapshot exists: {prefs_doc.exists}") # Debug
        if prefs_doc.exists:
            user_data = prefs_doc.to_dict()
            # print(f"User data fetched: {user_data}") # Debug
            # Preferences might be nested under a 'preferences' field
            # or directly in the user doc
            if PREFERENCES_DOC in user_data:
                # print(f"Preferences found under '{PREFERENCES_DOC}' field.")  # Debug
                return user_data[PREFERENCES_DOC]
            elif 'analysisSettings' in user_data:  # Check for legacy field?
                # print(f"Preferences found under legacy 'analysisSettings' field.") # Debug
                return user_data['analysisSettings']
            else:
                # If no specific preferences field, maybe the root doc IS the
                # prefs? This depends on your data structure. Let's assume
                # for now preferences are expected under the PREFERENCES_DOC
                # field.
                print(
                    f"No '{PREFERENCES_DOC}' field found for user {user_id}, "
                    "returning None."
                )
                return None  # Or return user_data if root doc is prefs
        else:
            print(f"No preferences document found for user: {user_id}")
            return None
    except Exception as e:
        print(f"An error occurred retrieving preferences for {user_id}: {e}")
        # Consider more specific error handling (e.g., network errors, 
        # permissions)
        return None


def save_user_preferences(
    user_id: str, preferences: Dict[str, Any]
) -> bool:
    """
    Saves or updates user preferences in Firestore.

    Uses set with merge=True to only update provided fields or create if not
    exists.

    Args:
        user_id: The unique identifier for the user.
        preferences: A dictionary containing the preferences to save.

    Returns:
        True if the operation was successful, False otherwise.
    """
    if not user_id or not preferences:
        print(
            "Error: user_id and preferences cannot be empty for "
            "save_user_preferences"
        )
        return False
    try:
        # We save preferences directly within the user document
        # under a specific key 'preferences'.
        prefs_ref = db.collection(USERS_COLLECTION).document(user_id)
        # Use set with merge=True to update/create the preferences field
        prefs_ref.set({PREFERENCES_DOC: preferences}, merge=True)
        print(f"Preferences successfully saved for user: {user_id}")
        return True
    except Exception as e:
        print(f"An error occurred saving preferences for {user_id}: {e}")
        return False


# --- User History --- #


def get_user_history(
    user_id: str
) -> List[Dict[str, Any]]:
    """
    Retrieves the user's analysis history from Firestore.

    Orders history by timestamp descending (most recent first).

    Args:
        user_id: The unique identifier for the user.

    Returns:
        A list of history items (dictionaries), or an empty list if none
        found or error.
    """
    if not user_id:
        print("Error: user_id cannot be empty for get_user_history")
        return []
    try:
        history_ref = (
            db.collection(USERS_COLLECTION)
            .document(user_id)
            .collection(HISTORY_COLLECTION)
        )
        # Order by timestamp, descending
        history_query = history_ref.order_by(
            "timestamp", direction="DESCENDING"
        )
        history_snapshot = history_query.stream()
        history_list = [doc.to_dict() for doc in history_snapshot]
        # print(f"Retrieved {len(history_list)} history items for {user_id}") # Debug
        return history_list
    except Exception as e:
        print(f"An error occurred retrieving history for {user_id}: {e}")
        return []  # Return empty list on error


def add_to_history(
    user_id: str, history_item: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Adds a new analysis result to the user's history in Firestore.

    Args:
        user_id: The unique identifier for the user.
        history_item: A dictionary representing the analysis result.
                      Should include 'url', 'summary', 'timestamp'.

    Returns:
        The added history item dictionary if successful, otherwise None.
    """
    if not user_id or not history_item:
        print(
            "Error: user_id and history_item cannot be empty for "
            "add_to_history"
        )
        return None

    # Add server-side timestamp if not provided by the client
    if 'timestamp' not in history_item:
        history_item['timestamp'] = datetime.now()  # Use server time

    try:
        history_ref = (
            db.collection(USERS_COLLECTION)
            .document(user_id)
            .collection(HISTORY_COLLECTION)
        )
        # Add a new document with an auto-generated ID
        update_time, new_doc_ref = history_ref.add(history_item)
        print(
            f"History item added for user {user_id} with ID: {new_doc_ref.id} "
            f"at {update_time}"
        )
        # Return the added item (useful if timestamp was added)
        return history_item
    except Exception as e:
        print(f"An error occurred adding history for {user_id}: {e}")
        return None


# --- Cached Policy Analysis --- #


def get_policy_analysis(url: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves a cached policy analysis from Firestore based on the URL.

    Args:
        url: The URL of the privacy policy.

    Returns:
        The cached analysis dictionary if found, otherwise None.
    """
    if not url:
        print("Error: url cannot be empty for get_policy_analysis")
        return None
    try:
        doc_ref = db.collection(ANALYSIS_CACHE_COLLECTION).document(url)
        doc_snapshot = doc_ref.get()
        if doc_snapshot.exists:
            # print(f"Cache hit for URL: {url}") # Debug
            return doc_snapshot.to_dict()
        else:
            # print(f"Cache miss for URL: {url}") # Debug
            return None
    except Exception as e:
        print(f"An error occurred retrieving cached analysis for {url}: {e}")
        return None


def save_policy_analysis(url: str, analysis: Dict[str, Any]) -> bool:
    """
    Saves a policy analysis result to the Firestore cache.

    Args:
        url: The URL of the privacy policy (used as the document ID).
        analysis: The analysis result dictionary to cache.

    Returns:
        True if saving was successful, False otherwise.
    """
    if not url or not analysis:
        print(
            "Error: url and analysis cannot be empty for "
            "save_policy_analysis"
        )
        return False
    try:
        # Use the URL as the document ID for easy lookup
        doc_ref = db.collection(ANALYSIS_CACHE_COLLECTION).document(url)
        doc_ref.set(analysis)
        # print(f"Analysis cached successfully for URL: {url}") # Debug
        return True
    except Exception as e:
        print(f"An error occurred saving analysis for {url}: {e}")
        return False