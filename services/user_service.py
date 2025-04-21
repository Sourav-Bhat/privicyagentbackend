"""
Firebase User Management Service.

Handles interactions with Firebase Authentication and Firestore for user data,
synchronizing with Clerk user events.
Relies on the Firebase Admin SDK being initialized (see config.firebase_config).
"""

# import firebase_admin # Not needed if only using auth and firestore submodules
from firebase_admin import auth, firestore
from typing import Dict, Any, Optional

# Assuming db and USERS_COLLECTION are defined in db_service or firebase_config
# If they are in db_service, import from there.
# If firebase_config only initializes, import db from there.
# For now, assuming db is directly available after initialization.
# Best practice would be to explicitly import db from config.firebase_config
# and USERS_COLLECTION from services.db_service if defined there.
from config.firebase_config import db  # Explicit import is better

# Define USERS_COLLECTION if not imported (consistency needed)
USERS_COLLECTION = 'users'

def create_or_update_firebase_user(
    clerk_user_id: str, user_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Creates or updates a user record in Firestore based on Clerk user data.

    If a Firestore document with the clerk_user_id exists, it updates it.
    Otherwise, it attempts to create a corresponding Firebase Auth user
    (if email is provided) and then creates the Firestore document,
    storing the Firebase Auth UID.

    Args:
        clerk_user_id: The user ID from Clerk (used as Firestore doc ID).
        user_data: A dictionary containing user attributes from Clerk
                   (e.g., email, name, image_url, metadata).

    Returns:
        The user data dictionary (potentially updated with firebase_uid)
        stored in Firestore.

    Raises:
        ValueError: If clerk_user_id is empty.
        Exception: Propagates exceptions from Firestore/Firebase Auth operations.
    """
    if not clerk_user_id:
        raise ValueError("clerk_user_id cannot be empty.")

    user_ref = db.collection(USERS_COLLECTION).document(clerk_user_id)

    try:
        user_doc = user_ref.get()

        if user_doc.exists:
            # --- Update Existing User ---
            print(f"Updating existing Firestore user: {clerk_user_id}")
            update_data = user_data.copy()  # Avoid modifying original dict
            # Optionally add/update a timestamp
            update_data['updatedAt'] = firestore.SERVER_TIMESTAMP
            user_ref.update(update_data)
            # Return the updated data from Firestore
            updated_doc = user_ref.get()  # Re-fetch to get server timestamp etc.
            return updated_doc.to_dict() if updated_doc.exists else user_data
        else:
            # --- Create New User ---
            print(f"Creating new Firestore user for Clerk ID: {clerk_user_id}")
            new_user_data = user_data.copy()
            firebase_uid = None

            # Attempt to create Firebase Auth user only if email exists
            if new_user_data.get('email'):
                try:
                    firebase_user = auth.create_user(
                        email=new_user_data['email'],
                        display_name=new_user_data.get('name'),
                        photo_url=new_user_data.get('image_url'),
                        disabled=False
                    )
                    firebase_uid = firebase_user.uid
                    new_user_data['firebase_uid'] = firebase_uid
                    print(f"Created Firebase Auth user with UID: {firebase_uid}")
                except auth.EmailAlreadyExistsError:
                    email = new_user_data['email']
                    print(f"Auth user with email {email} already exists.")
                    # Try to find existing user by email to link
                    try:
                        existing_auth_user = auth.get_user_by_email(email)
                        firebase_uid = existing_auth_user.uid
                        new_user_data['firebase_uid'] = firebase_uid
                        print(f"Found existing Auth user UID by email: {firebase_uid}")
                    except auth.UserNotFoundError:
                        print(f"Could not find Auth user by email {email}. Proceeding.")
                        # Proceed without firebase_uid or handle error
                except Exception as auth_error:
                    # Log auth creation error but continue to create Firestore doc
                    clerk_id = clerk_user_id # Alias for f-string clarity
                    print(f"Warning: Failed to create Auth user for {clerk_id}: {auth_error}")
            else:
                print(f"Skipping Auth creation for {clerk_user_id} (no email).")

            # Create the user document in Firestore
            new_user_data['createdAt'] = firestore.SERVER_TIMESTAMP
            user_ref.set(new_user_data)
            print(f"Created Firestore user document for {clerk_user_id}")
            return new_user_data  # Return data used for creation

    except Exception as e:
        print(f"Error during create_or_update for {clerk_user_id}: {e}")
        # Re-raise the exception to be handled by the caller (e.g., webhook handler)
        raise

def get_firebase_user(clerk_user_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves a user document from Firestore using the Clerk user ID.

    Args:
        clerk_user_id: The Clerk user ID (which is the Firestore document ID).

    Returns:
        The user data dictionary if the document exists, otherwise None.
    """
    if not clerk_user_id:
        print("Warning: get_firebase_user called with empty clerk_user_id.")
        return None

    try:
        user_ref = db.collection(USERS_COLLECTION).document(clerk_user_id)
        user_doc = user_ref.get()

        if user_doc.exists:
            return user_doc.to_dict()
        else:
            print(f"Firestore user document not found for Clerk ID: {clerk_user_id}")
            return None
    except Exception as e:
        clerk_id = clerk_user_id # Alias for f-string
        print(f"Error getting Firestore user for Clerk ID {clerk_id}: {e}")
        return None


def get_firebase_user_by_id(firebase_user_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a user document from Firestore by their Firebase Authentication UID.

    This requires querying the collection as the document ID is the Clerk ID.

    Args:
        firebase_user_id: The Firebase Authentication user ID.

    Returns:
        The user data dictionary if found, otherwise None.
    """
    if not firebase_user_id:
        print("Warning: get_firebase_user_by_id called with empty firebase_user_id.")
        return None

    try:
        users_ref = db.collection(USERS_COLLECTION)
        # Query Firestore for the document containing the matching firebase_uid
        query = users_ref.where('firebase_uid', '==', firebase_user_id).limit(1)
        docs = query.stream()  # Use stream() for potentially large collections

        user_doc = next(docs, None)  # Get the first matching document, if any

        if user_doc:
            return user_doc.to_dict()
        else:
            print(f"Firestore user not found for Firebase UID: {firebase_user_id}")
            return None
    except Exception as e:
        fb_uid = firebase_user_id # Alias for f-string
        print(f"Error querying Firestore user by Firebase UID {fb_uid}: {e}")
        return None


def delete_firebase_user(firebase_uid: str) -> bool:
    """
    Deletes a user from both Firebase Authentication and Firestore.

    Finds the Firestore document based on the firebase_uid before deleting.

    Args:
        firebase_uid: The Firebase Authentication user ID to delete.

    Returns:
        True if deletion from both services was successful or if the user
        didn't exist initially, False if an error occurred during deletion.
    """
    if not firebase_uid:
        print("Warning: delete_firebase_user called with empty firebase_uid.")
        return False

    firestore_deleted = False
    auth_deleted = False
    fb_uid = firebase_uid # Alias for f-strings

    try:
        # --- Delete Firestore Document ---
        users_ref = db.collection(USERS_COLLECTION)
        query = users_ref.where('firebase_uid', '==', fb_uid).limit(1)
        docs = query.stream()

        doc_to_delete = next(docs, None)
        if doc_to_delete:
            doc_id = doc_to_delete.id
            doc_to_delete.reference.delete()
            print(f"Deleted Firestore document: {doc_id}")
            firestore_deleted = True
        else:
            print(f"No Firestore doc for Firebase UID: {fb_uid}. Assuming deleted.")
            firestore_deleted = True  # Treat as success if not found

    except Exception as e:
        print(f"Error deleting Firestore data for Firebase UID {fb_uid}: {e}")
        # Continue to attempt Auth deletion

    try:
        # --- Delete Firebase Auth User ---
        print(f"Attempting to delete Firebase Auth user: {fb_uid}")
        auth.delete_user(fb_uid)
        print(f"Successfully deleted Firebase Auth user: {fb_uid}")
        auth_deleted = True
    except auth.UserNotFoundError:
        print(f"Firebase Auth user {fb_uid} not found. Assuming deleted.")
        auth_deleted = True  # Treat as success if not found
    except Exception as e:
        print(f"Error deleting Firebase Auth user {fb_uid}: {str(e)}")

    # Return True only if both deletions were successful (or user didn't exist)
    return firestore_deleted and auth_deleted 