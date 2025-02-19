# utils.py
import ast
import random
import requests
from typing import Dict, Optional

# Constants
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/57.0",
    # Add more user agents as needed
]

def get_random_user_agent() -> Dict[str, str]:
    """
    Returns a random user agent from the predefined list.

    :return: A dictionary with a random user agent string.
    """
    return {'User-Agent': random.choice(USER_AGENTS)}

def complete_href(href: str) -> str:
    """
    Completes a relative URL to a full URL.

    :param href: The relative URL.
    :return: The complete URL.
    """
    base_url = 'https://www.marketscreener.com'
    return f'{base_url}{href}'

def fetch_url_content(url: str, headers: Optional[Dict[str, str]] = None) -> Optional[str]:
    """
    Fetches the content of a URL.

    :param url: The URL to fetch.
    :param headers: Optional headers to include in the request.
    :return: The content of the URL if successful, None otherwise.
    :raises: requests.exceptions.RequestException if the request fails.
    """
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        # Log the exception or handle it as needed
        print(f"Error fetching {url}: {e}")
        return None
    
def str_to_dict_expansion(dict_repr: any) -> dict:
    dict_repr = str(dict_repr)
    if dict_repr.strip() == '{}':
        return {}
    else:
        try:
            return ast.literal_eval(dict_repr.strip())
        except Exception as e:
            print(e)
            return {}