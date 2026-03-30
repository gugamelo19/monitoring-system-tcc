import requests

from config import API_BASE_URL, API_USERNAME, API_PASSWORD


def get_access_token() -> str:
    url = f"{API_BASE_URL}/api/auth/login/"
    payload = {
        "username": API_USERNAME,
        "password": API_PASSWORD,
    }

    response = requests.post(url, json=payload, timeout=10)
    response.raise_for_status()

    data = response.json()
    return data["access"]
