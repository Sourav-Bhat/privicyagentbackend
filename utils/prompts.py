#prompts.py

WEBSEARCH_TEMPLATE = """
Find the privacy policy for this website: {url} and extract its text content.

Here's how to find a privacy policy:
1. Look for a link to the privacy policy in the website's footer.
2. Check the website's menu or navigation bar.
3. Search the website for "privacy policy".
4. If you can't find it on the website, try searching Google for "[website name] privacy policy".

Can you help me find the privacy policy for {url}?
"""

FACT_CHECK_TEMPLATE = """
Here is the content of a privacy policy:
{policy_content}

Can you verify the following claims from the policy?
* Data collection practices
* Data usage practices
* Data sharing practices
* Data security measures
* User rights and control

Please provide a summary of your findings, highlighting any discrepancies or inconsistencies.
"""

LEGAL_TEMPLATE = """
Here is the content of a privacy policy:
{policy_content}

The user is located in {location} and their demographics are: {demographics}

Can you summarize the privacy policy in plain language, highlighting the key points relevant to the user's location and demographics?

Also, mention any potential risks or concerns based on the user's context.
"""