"""
Entrypoint do coletor.

Autentica no backend e inicia o loop de monitoramento contínuo,
intercalando tráfego de baseline com cenários probabilísticos
de anomalia (ICMP burst, port scan TCP e DNS burst).
"""
from config import API_BASE_URL, API_PASSWORD, API_USERNAME, MONITORING_INTERVAL
from services.api_client import APIClient
from simulator import EventSimulator


def main() -> None:
    print(f"[INFO] Autenticando no backend em {API_BASE_URL}...")

    api_client = APIClient(API_BASE_URL, API_USERNAME, API_PASSWORD)
    api_client.authenticate()

    print("[INFO] Iniciando simulador...")

    simulator = EventSimulator(api_client)
    simulator.run_realtime_monitoring(interval=MONITORING_INTERVAL)


if __name__ == "__main__":
    main()
