# Benchmark — avaliação de acurácia e sensibilidade

Este diretório contém o harness experimental usado no capítulo de
Resultados do TCC. Ele permite gerar cenários controlados, medir
TP/FP/TN/FN e produzir as tabelas de sensibilidade dos limiares.

## Visão geral

Três scripts independentes:

| Script | Função |
|---|---|
| `scenarios.py` | Gera 6 cenários (A1-A3 de ataque, N1-N3 de ruído legítimo) com repetições configuráveis. Marca cada evento com `truth=ATTACK\|NORMAL` no `raw_summary`. |
| `measure.py` | Lê o banco e calcula matriz de confusão por cenário (TP, FP, TN, FN, precisão, recall, F1). Exporta `metrics_summary.csv`. |
| `sensitivity.py` | Reaplica as três regras do detector offline, variando o limiar, e calcula métricas para cada valor. Exporta `sensitivity_icmp.csv`, `sensitivity_port_scan.csv` e `sensitivity_dns.csv`. |

## Cenários

| ID | Tipo | Descrição |
|---|---|---|
| A1 | Ataque | Port scan TCP em 13 portas (21, 22, 23, 25, 53, 80, 110, 135, 139, 143, 443, 445, 3306). |
| A2 | Ataque | ICMP burst de 30 pacotes em curto intervalo. |
| A3 | Ataque | DNS burst de 50 consultas em curto intervalo. |
| N1 | Ruído | Servidor de monitoramento (Zabbix) pingando vários hosts — mesmo `source_ip` emite >20 ICMPs. |
| N2 | Ruído | Scanner de inventário tocando em 12 portas distintas (logo abaixo do limiar padrão). |
| N3 | Ruído | Navegação web normal — 40 resoluções DNS em curto intervalo. |

## Pré-requisitos

1. Backend Django rodando em `http://127.0.0.1:8000`.
2. Pelo menos um ativo cadastrado com `is_monitored=True`.
3. Coletor **parado** (evita ruído no experimento).
4. Banco preferencialmente limpo. Se preciso, rode:
   ```bash
   cd backend
   python manage.py flush --no-input
   ```
   e recrie o superusuário e o ativo.

## Fluxo de execução completo

```bash
# 1) Gera os eventos dos 6 cenários (30 repetições cada).
cd benchmark
python scenarios.py --repetitions 30

# 2) Tabula a matriz de confusão e métricas por cenário.
python measure.py

# 3) Produz as tabelas de sensibilidade para as três regras.
python sensitivity.py
```

## Argumentos úteis

```bash
# Roda com menos repetições para iterar rapidamente.
python scenarios.py --repetitions 5 --gap 30

# Aponta para um backend remoto.
python scenarios.py --base-url http://10.0.0.10:8000 --username admin --password secret
```

## Como interpretar os CSV gerados

### `metrics_summary.csv`

Uma linha por cenário, com TP/FP/TN/FN e métricas. Quando a precisão
de N1/N2/N3 cai abaixo de 1.0, significa que aquele ruído legítimo
está disparando falso positivo — exatamente o que se deseja
visualizar.

### `sensitivity_*.csv`

Uma linha por valor de limiar, com TP/FP/TN/FN e precisão/recall/F1.
A leitura típica:

* Limiares **muito baixos**: recall alto, precisão baixa (alarmes
  excessivos).
* Limiares **muito altos**: recall baixo, precisão alta (perde
  ataques reais).
* A **fronteira ótima** em F1 é o ponto recomendado para o
  limiar — ou para fundamentar argumentação sobre o valor atual.

## Variando os limiares do detector em produção

Para mover os limiares sem mexer no código, edite `backend/.env`
acrescentando variáveis. Exemplo:

```env
ICMP_RATE_COUNT=25
ICMP_RATE_WINDOW_SECONDS=30
PORT_SCAN_DISTINCT_PORTS=12
PORT_SCAN_WINDOW_SECONDS=60
DNS_BURST_COUNT=40
DNS_BURST_WINDOW_SECONDS=60
DEDUPLICATION_WINDOW_SECONDS=60
FALSE_POSITIVE_SUPPRESS_HOURS=24
```

Reinicie o backend após a mudança.

## Testando o efeito das mitigações de falso positivo

Para mostrar o "antes e depois" no capítulo de Resultados:

1. Rode `scenarios.py` em banco limpo. Anote N1/N2/N3 gerando FPs.
2. No Django Admin, cadastre os IPs `10.0.0.50` (Zabbix), `10.0.0.60`
   (scanner) e a faixa `10.0.0.100`–`10.0.0.200` em
   **Anomalies → Trusted sources**.
3. Limpe o banco e rode `scenarios.py` novamente.
4. Compare as tabelas — N1, N2 e N3 não devem mais gerar FPs.

Para demonstrar o feedback loop:

1. Rode `scenarios.py` e marque manualmente, no frontend, alertas
   gerados por N1 como **FALSE_POSITIVE**.
2. Cada marcação cria um `FalsePositiveFeedback` válido por 24h.
3. Rode `scenarios.py` novamente — N1 não deve mais gerar FPs.
