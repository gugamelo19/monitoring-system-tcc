"""
Configuração do coletor.

As variáveis abaixo são lidas do arquivo .env localizado na pasta
do coletor (collector/.env). Caso o arquivo não exista, valores
padrão são utilizados para que o coletor funcione em ambiente
local de desenvolvimento sem configuração adicional.
"""
from decouple import config

API_BASE_URL = config("API_BASE_URL", default="http://127.0.0.1:8000")
API_USERNAME = config("API_USERNAME", default="admin")
API_PASSWORD = config("API_PASSWORD", default="admin")

# Intervalo (em segundos) entre os ciclos de monitoramento em tempo real.
MONITORING_INTERVAL = config("MONITORING_INTERVAL", default=5, cast=int)
