import os
import firebase_admin
from firebase_admin import auth, firestore
from typing import Dict, Any, Optional
from datetime import datetime

# Initialize Firebase Admin SDK if not already initialized
if not firebase_admin._apps:
    firebase_admin.initialize_app()

# Get Firestore client
db = firestore.client()

def create_or_update_firebase_user(clerk_user_id: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create or update a Firebase user based on Clerk user data.
    
    Args:
        clerk_user_id (str): The Clerk user ID
        user_data (Dict[str, Any]): The user data from Clerk
        
    Returns:
        Dict[str, Any]: The created/updated user data
    """
    # Check if the user already exists in Firestore
    user_ref = db.collection('users').document(clerk_user_id)
    user_doc = user_ref.get()
    
    if user_doc.exists:
        # Update the existing user
        user_ref.update(user_data)
        return user_doc.to_dict()
    else:
        # Create a new Firebase Auth user
        try:
            firebase_user = auth.create_user(
                email=user_data.get('email', ''),
                display_name=user_data.get('name', ''),
                photo_url=user_data.get('image_url', ''),
                disabled=False
            )
            
            # Add the Firebase UID to the user data
            user_data['firebase_uid'] = firebase_user.uid
            
            # Create the user document in Firestore
            user_ref.set(user_data)
            
            return user_data
        except Exception as e:
            print(f"Error creating Firebase user: {str(e)}")
            # If Firebase Auth creation fails, still create the Firestore document
            user_ref.set(user_data)
            return user_data

def get_firebase_user(clerk_user_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a Firebase user by Clerk user ID.
    
    Args:
        clerk_user_id (str): The Clerk user ID
        
    Returns:
        Optional[Dict[str, Any]]: The user data if found, None otherwise
    """
    user_ref = db.collection('users').document(clerk_user_id)
    user_doc = user_ref.get()
    
    if user_doc.exists:
        return user_doc.to_dict()
    return None

def get_firebase_user_by_id(firebase_user_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a user from Firebase by their Firebase UID.
    
    Args:
        firebase_user_id (str): The Firebase user ID
        
    Returns:
        Optional[Dict[str, Any]]: The user data or None if not found
    """
    doc_ref = db.collection('users').document(firebase_user_id)
    doc = doc_ref.get()
    
    if doc.exists:
        return doc.to_dict()
    
    return None

def delete_firebase_user(firebase_uid: str) -> bool:
    """
    Delete a Firebase user.
    
    Args:
        firebase_uid (str): The Firebase user ID
        
    Returns:
        bool: True if the user was deleted, False otherwise
    """
    try:
        # Delete the user from Firebase Auth
        auth.delete_user(firebase_uid)
        
        # Find and delete the user document in Firestore
        users_ref = db.collection('users')
        query = users_ref.where('firebase_uid', '==', firebase_uid).limit(1)
        docs = query.get()
        
        for doc in docs:
            doc.reference.delete()
        
        return True
    except Exception as e:
        print(f"Error deleting Firebase user: {str(e)}")
        return False 