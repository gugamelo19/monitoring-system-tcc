from auth import get_access_token
from services.api_client import APIClient
from simulator import EventSimulator


def main():
    print("[INFO] Autenticando no backend...")
    token = get_access_token()
    print("[INFO] Token obtido com sucesso.")

    api_client = APIClient(token)
    simulator = EventSimulator(api_client)

    simulator.send_normal_traffic(total=15)
    simulator.simulate_icmp_burst()
    simulator.simulate_port_scan()
    simulator.simulate_dns_burst()

    print("\n[INFO] Simulação concluída com sucesso.")


if __name__ == "__main__":
    main()
