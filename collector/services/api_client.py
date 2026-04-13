import requests


class APIClient:
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.token = None

    def authenticate(self) -> None:
        response = self.session.post(
            f"{self.base_url}/api/auth/login/",
            json={
                "username": self.username,
                "password": self.password,
            },
        )
        response.raise_for_status()
        data = response.json()
        self.token = data["access"]
        self.session.headers.update(
            {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
            }
        )

    def send_event(self, payload: dict) -> dict:
        response = self.session.post(
            f"{self.base_url}/api/events/",
            json=payload,
        )
        response.raise_for_status()
        return response.json()

    def get_assets(self) -> list[dict]:
        response = self.session.get(f"{self.base_url}/api/assets/")
        response.raise_for_status()
        return response.json()
