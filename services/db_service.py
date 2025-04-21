from typing import List, Dict, Any, Optional
from datetime import datetime
from config.firebase_config import db

# User Preferences
def get_user_preferences(user_id: str) -> Dict[str, Any]:
    """
    Get user preferences from Firestore.
    
    Args:
        user_id (str): The user ID
        
    Returns:
        Dict[str, Any]: User preferences
    """
    doc_ref = db.collection('users').document(user_id).collection('preferences').document('settings')
    doc = doc_ref.get()
    
    if doc.exists:
        return doc.to_dict()
    else:
        # Return default preferences if none exist
        default_prefs = {
            'country': 'United States',
            'riskThreshold': 'medium',
            'notifications': True
        }
        # Save default preferences
        doc_ref.set(default_prefs)
        return default_prefs

def update_user_preferences(user_id: str, preferences: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update user preferences in Firestore.
    
    Args:
        user_id (str): The user ID
        preferences (Dict[str, Any]): The preferences to update
        
    Returns:
        Dict[str, Any]: Updated preferences
    """
    doc_ref = db.collection('users').document(user_id).collection('preferences').document('settings')
    doc_ref.set(preferences)
    return preferences

# User History
def get_user_history(user_id: str) -> List[Dict[str, Any]]:
    """
    Get user history from Firestore.
    
    Args:
        user_id (str): The user ID
        
    Returns:
        List[Dict[str, Any]]: User history
    """
    history_ref = db.collection('users').document(user_id).collection('history')
    docs = history_ref.order_by('analyzedAt', direction='DESCENDING').limit(50).stream()
    
    return [doc.to_dict() for doc in docs]

def add_to_history(user_id: str, history_item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add a history item to Firestore.
    
    Args:
        user_id (str): The user ID
        history_item (Dict[str, Any]): The history item to add
        
    Returns:
        Dict[str, Any]: The added history item
    """
    # Add timestamp if not provided
    if 'analyzedAt' not in history_item:
        history_item['analyzedAt'] = datetime.now().isoformat()
    
    history_ref = db.collection('users').document(user_id).collection('history')
    doc_ref = history_ref.document()
    doc_ref.set(history_item)
    
    return history_item

# Policy Analysis
def save_policy_analysis(user_id: str, url: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Save a policy analysis to Firestore.
    
    Args:
        user_id (str): The user ID
        url (str): The URL of the policy
        analysis (Dict[str, Any]): The analysis data
        
    Returns:
        Dict[str, Any]: The saved analysis
    """
    # Create a document ID based on the URL (sanitized)
    doc_id = url.replace('/', '_').replace(':', '_').replace('.', '_')
    
    analysis_ref = db.collection('policies').document(doc_id)
    analysis_ref.set(analysis)
    
    # Also save a reference in the user's history
    history_item = {
        'url': url,
        'analyzedAt': datetime.now().isoformat(),
        'policyTitle': analysis.get('websiteName', 'Unknown Policy'),
        'riskLevel': analysis.get('overallRisk', 'unknown')
    }
    add_to_history(user_id, history_item)
    
    return analysis

def get_policy_analysis(url: str) -> Optional[Dict[str, Any]]:
    """
    Get a policy analysis from Firestore.
    
    Args:
        url (str): The URL of the policy
        
    Returns:
        Optional[Dict[str, Any]]: The analysis data or None if not found
    """
    # Create a document ID based on the URL (sanitized)
    doc_id = url.replace('/', '_').replace(':', '_').replace('.', '_')
    
    analysis_ref = db.collection('policies').document(doc_id)
    doc = analysis_ref.get()
    
    if doc.exists:
        return doc.to_dict()
    else:
        return None 