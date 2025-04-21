import os
import requests
from bs4 import BeautifulSoup
from typing import Dict, Any, Optional, List
import re
import urllib.parse

def run_websearch(url: str) -> str:
    """
    Run a web search to find the privacy policy for the given URL.
    Uses multiple strategies to locate the privacy policy.
    
    Args:
        url (str): The URL to search for a privacy policy
        
    Returns:
        str: The content of the privacy policy
    """
    try:
        # Normalize the URL
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Extract the base domain
        parsed_url = urllib.parse.urlparse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        # Strategy 1: Try to find privacy policy in sitemap
        privacy_url = find_privacy_policy_in_sitemap(base_url)
        
        # Strategy 2: If not found in sitemap, try common URL patterns
        if not privacy_url:
            privacy_url = find_privacy_policy_common_patterns(base_url)
        
        # Strategy 3: If still not found, scrape the main page for privacy policy links
        if not privacy_url:
            privacy_url = find_privacy_policy_links(base_url)
        
        # If we found a privacy policy URL, fetch its content
        if privacy_url:
            return fetch_page_content(privacy_url)
        
        # If all strategies fail, return the main page content
        return fetch_page_content(url)
    
    except Exception as e:
        return f"Error searching for privacy policy: {str(e)}"

def find_privacy_policy_in_sitemap(base_url: str) -> Optional[str]:
    """
    Try to find the privacy policy URL in the site's sitemap.
    
    Args:
        base_url (str): The base URL of the website
        
    Returns:
        Optional[str]: The privacy policy URL if found, None otherwise
    """
    try:
        # Try common sitemap locations
        sitemap_urls = [
            f"{base_url}/sitemap.xml",
            f"{base_url}/sitemap_index.xml",
            f"{base_url}/sitemap/sitemap.xml"
        ]
        
        for sitemap_url in sitemap_urls:
            response = requests.get(sitemap_url, timeout=10)
            if response.status_code == 200:
                # Parse the sitemap XML
                soup = BeautifulSoup(response.text, 'xml')
                
                # Look for URLs containing privacy-related terms
                for url_elem in soup.find_all(['loc', 'url']):
                    url_text = url_elem.text.lower()
                    if any(term in url_text for term in ['privacy', 'legal', 'terms']):
                        return url_text
        
        return None
    except:
        return None

def find_privacy_policy_common_patterns(base_url: str) -> Optional[str]:
    """
    Try to find the privacy policy URL using common URL patterns.
    
    Args:
        base_url (str): The base URL of the website
        
    Returns:
        Optional[str]: The privacy policy URL if found, None otherwise
    """
    # Common privacy policy URL patterns
    patterns = [
        f"{base_url}/privacy",
        f"{base_url}/privacy-policy",
        f"{base_url}/privacy_policy",
        f"{base_url}/legal/privacy",
        f"{base_url}/legal/privacy-policy",
        f"{base_url}/terms/privacy",
        f"{base_url}/about/privacy",
        f"{base_url}/about/privacy-policy",
        f"{base_url}/info/privacy",
        f"{base_url}/info/privacy-policy"
    ]
    
    for url in patterns:
        try:
            response = requests.head(url, timeout=5)
            if response.status_code == 200:
                return url
        except:
            continue
    
    return None

def find_privacy_policy_links(base_url: str) -> Optional[str]:
    """
    Scrape the main page for privacy policy links.
    
    Args:
        base_url (str): The base URL of the website
        
    Returns:
        Optional[str]: The privacy policy URL if found, None otherwise
    """
    try:
        # Fetch the main page
        response = requests.get(base_url, timeout=10)
        if response.status_code == 200:
            # Parse the HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for privacy policy links
            privacy_links = []
            
            # Check all links
            for link in soup.find_all('a'):
                href = link.get('href', '')
                text = link.get_text().lower()
                
                # Skip empty links
                if not href:
                    continue
                
                # Handle relative URLs
                if not href.startswith(('http://', 'https://')):
                    if href.startswith('/'):
                        href = base_url + href
                    else:
                        href = base_url + '/' + href
                
                # Check if this is a privacy policy link
                if any(term in text for term in ['privacy', 'legal', 'terms']):
                    privacy_links.append(href)
            
            # If we found privacy policy links, return the first one
            if privacy_links:
                return privacy_links[0]
        
        return None
    except:
        return None

def fetch_page_content(url: str) -> str:
    """
    Fetch and extract the content from a webpage.
    
    Args:
        url (str): The URL to fetch
        
    Returns:
        str: The extracted content
    """
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            # Parse the HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "header", "footer"]):
                script.decompose()
            
            # Get the text content
            text = soup.get_text(separator='\n')
            
            # Clean up the text
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            return text
        
        return f"Could not fetch content from {url}. Status: {response.status_code}"
    except Exception as e:
        return f"Error fetching content: {str(e)}" 