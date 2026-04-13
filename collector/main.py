from services.api_client import APIClient
from simulator import EventSimulator


def main():
    base_url = "http://127.0.0.1:8000"
    username = "admin"
    password = "admin"

    print("[INFO] Autenticando no backend...")

    api_client = APIClient(base_url, username, password)
    api_client.authenticate()

    print("[INFO] Iniciando simulador...")

    simulator = EventSimulator(api_client)
    simulator.run_realtime_monitoring(interval=5)


if __name__ == "__main__":
    main()
