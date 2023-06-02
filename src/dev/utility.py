import urllib.parse
import random
import string

def generate_random_string(length):
    possible = string.ascii_letters + string.digits
    return ''.join(random.choice(possible) for _ in range(length))

def extract_code_from_url(url):
    parsed_url = urllib.parse.urlparse(url)
    query_params = urllib.parse.parse_qs(parsed_url.query)
    return query_params.get("code", [None])[0], query_params.get("state", [None])[0]