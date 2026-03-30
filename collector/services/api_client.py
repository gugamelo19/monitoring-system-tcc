import requests

from config import API_BASE_URL


class APIClient:
    def __init__(self, token: str):
        self.base_url = API_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    def send_event(self, payload: dict) -> dict:
        url = f"{self.base_url}/api/events/"
        response = requests.post(
            url, json=payload, headers=self.headers, timeout=10)
        response.raise_for_status()
        return response.json()
