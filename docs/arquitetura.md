# Arquitetura do Sistema

O sistema será composto por quatro blocos principais:

1. Coletor de eventos de rede
2. Backend para processamento e API
3. Banco de dados PostgreSQL
4. Frontend para visualização e gerenciamento

## Fluxo

1. O coletor captura ou simula eventos
2. Os eventos são enviados para a API
3. A API persiste os dados
4. O motor de detecção avalia anomalias
5. Alertas são gerados
6. O dashboard exibe os dados
