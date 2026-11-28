import requests

def get_json(url: str, timeout: float = 5.0) -> dict:
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Failed to fetch JSON from {url}: {e}") from e

    try:
        return response.json()
    except ValueError:
        raise ValueError(f"Response body from {url} is not a valid JSON object")
