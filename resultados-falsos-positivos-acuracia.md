# Capítulo de Resultados — falsos positivos, acurácia e tabela de sensibilidade

*Plano metodológico e experimental para a próxima entrega do TCC*

Este documento responde, em ordem, a três perguntas levantadas pelo orientador:

1. Como o sistema diferencia um pico real de uso de um ataque (falsos positivos)?
2. De X ataques simulados, quantos foram detectados (acurácia)?
3. Como construir a tabela de sensibilidade e como ela se relaciona com Nmap e hping3?

A estratégia é: assumir o protótipo tal como está, **acrescentar um "harness" de avaliação ao lado do código de produção** (sem mexer no detector), e produzir números reais que você apresenta no capítulo de Resultados. Ao final, o documento traz o plano completo e os scripts mínimos para executá-lo.

---

## Sumário

1. O ponto de partida honesto: o que existe e o que não existe no protótipo
2. Referencial teórico — TP, FP, TN, FN, precisão, recall, F1
3. O que é "falso positivo" neste sistema (com exemplos concretos)
4. Estratégias para diferenciar pico real de ataque
5. Plano experimental — como medir tudo
6. A tabela de sensibilidade — modelo, eixos e leitura
7. Como cada experimento se relaciona com Nmap e hping3
8. Estrutura sugerida do capítulo de Resultados
9. Apêndice: scripts prontos para executar os experimentos

---

## 1. O ponto de partida honesto

O detector atual (`apps/anomalies/services/detector.py`) tem **três regras com limiares fixos** e **um único mecanismo de mitigação de duplicidade** — o `_anomaly_exists`, que evita gerar duas anomalias do mesmo tipo no mesmo ativo em janela de 60 segundos. Isso não é mitigação de falso positivo: é apenas deduplicação. Se o detector classifica um pico legítimo de ICMP como ataque, ele continua errando, só não erra duplicado.

O sistema **não distingue** hoje entre:

- Um administrador rodando `for i in $(seq 1 30); do ping host; done` em 30 segundos.
- Um atacante real fazendo um ping flood com hping3 em 30 segundos.

Ambos vão acionar a regra `HIGH_ICMP_RATE`. Reconhecer isso publicamente, no início do capítulo, é a melhor jogada de defesa: você mostra autoconsciência crítica antes que a banca aponte. Em seguida, você apresenta as estratégias possíveis e os resultados que mediu.

Para o capítulo de Resultados, a postura correta não é fingir que o sistema lida com falso positivo de forma sofisticada. É:

1. **Definir o que é falso positivo neste contexto.**
2. **Medir o quanto o protótipo erra.**
3. **Apresentar mitigações que poderiam reduzir esse erro, com discussão crítica de cada uma.**
4. **Propor as duas ou três que fariam mais sentido implementar como evolução.**

---

## 2. Referencial teórico

Detecção de anomalia é um problema de **classificação binária**: cada evento (ou janela temporal) é classificado como "ataque" ou "não-ataque". Para qualquer classificador binário, existem quatro resultados possíveis:

| Verdade ↓ \ Predição → | **Ataque** (alerta) | **Não-ataque** (silêncio) |
|---|---|---|
| **É ataque** | True Positive (**TP**) | False Negative (**FN**) |
| **Não é ataque** | False Positive (**FP**) | True Negative (**TN**) |

A partir desses quatro contadores, derivam-se as métricas que o orientador pediu:

### 2.1. Métricas básicas

| Métrica | Fórmula | Pergunta que ela responde |
|---|---|---|
| **Acurácia** | (TP + TN) / (TP + TN + FP + FN) | Em geral, em que fração das vezes o sistema acerta? |
| **Precisão** | TP / (TP + FP) | Dos alertas que disparei, quantos eram ataques reais? |
| **Sensibilidade** (Recall) | TP / (TP + FN) | Dos ataques reais, quantos eu peguei? |
| **Especificidade** | TN / (TN + FP) | Do tráfego normal, quantas vezes fiquei em silêncio? |
| **F1-Score** | 2 × (P × R) / (P + R) | Equilíbrio entre precisão e recall |
| **Taxa de FP** (FPR) | FP / (FP + TN) | Com que frequência alarmo sem motivo? |

A literatura de IDS (Intrusion Detection System) trata recall e taxa de FP como o par mais relevante: é melhor alertar demais do que perder ataques (alta sensibilidade), mas alertar excessivamente leva à fadiga do operador, conhecida como "alarm fatigue". Um sistema que dispara 200 alertas por hora, dos quais 195 são falsos, é tão inútil quanto um sistema que não dispara nada.

### 2.2. Tabela de sensibilidade (sensitivity analysis)

O termo "tabela de sensibilidade" no contexto pedido pelo orientador refere-se a **variar parametricamente um valor do sistema** (no nosso caso, o limiar de cada regra) e observar como as métricas se comportam. É um experimento clássico de análise de fronteira de decisão: a curva ROC é a versão visual disso.

Para cada regra, você vai variar o limiar e medir TP/FP/recall/precisão. O formato bruto:

| Limiar | TP | FP | TN | FN | Precisão | Recall | F1 |
|---|---|---|---|---|---|---|---|
| ... | | | | | | | |

A leitura típica é: limiares baixos pegam tudo (recall alto) mas levantam muitos falsos (precisão baixa); limiares altos só pegam ataques óbvios (recall baixo) mas quase não erram (precisão alta). O "ponto ótimo" é uma decisão de produto, não matemática.

---

## 3. O que é "falso positivo" neste sistema

Para que a discussão saia da teoria, precisamos definir falsos positivos **concretos** para cada uma das três regras. A pergunta-chave é: que comportamento legítimo dispara cada regra sem ser ataque?

### 3.1. Regra `HIGH_ICMP_RATE` — > 20 ICMP do mesmo IP em 30s

Falsos positivos plausíveis:

- **Servidor de monitoramento (Nagios, Zabbix, Prometheus blackbox_exporter).** Esses sistemas pingam todos os hosts da rede com cadência alta. Um Zabbix monitorando 100 hosts pode emitir mais de 20 ICMP em 30s do mesmo IP de origem (o IP do servidor Zabbix).
- **Rotina de network discovery do administrador.** `for ip in 192.168.1.{1..50}; do ping -c 1 $ip; done`.
- **Testes de conectividade durante manutenção.** Quando a rede está instável, técnicos disparam pings em sequência para diagnosticar.

### 3.2. Regra `PORT_SCAN_SUSPECT` — > 10 portas distintas do mesmo IP em 60s

Falsos positivos plausíveis:

- **Vulnerability scanner contratado** (Tenable Nessus, Qualys, OpenVAS). Esses sistemas fazem exatamente o que o Nmap faz, mas legitimamente, contratados pela própria empresa.
- **Asset discovery do CMDB/inventário** (Lansweeper, ManageEngine OpManager). Eles tocam em portas como 22, 80, 443, 3306, 5432 para identificar serviços.
- **Aplicação multi-porta legítima.** Um cliente que, dentro de uma sessão, conecta-se a 22 (SSH para deploy), 80 (frontend), 443 (API), 5432 (DB), 6379 (Redis), 9200 (Elasticsearch), 8080 (admin), etc. Em 60 segundos, isso passa de 10.

### 3.3. Regra `DNS_QUERY_BURST` — > 30 DNS do mesmo IP em 60s

Falsos positivos plausíveis:

- **Navegação web normal de um usuário.** Carregar um único site moderno (com analytics, CDN, fonts, ads) faz facilmente 20–40 lookups DNS em poucos segundos. Cinco abas abertas em paralelo passam de 30.
- **Resolver DNS recursivo / cache server** (BIND, Unbound, dnsmasq). Um servidor DNS interno que repassa consultas dos clientes vai aparecer como "mesmo IP" gerando centenas de DNS por segundo. É o comportamento normal dele.
- **CI/CD pipeline** durante uma build (yarn install, apt update, etc., resolvem dezenas de domínios).

### 3.4. A consequência

Em uma rede corporativa real, **as três regras gerariam falsos positivos rotineiros**. Em um ambiente de laboratório controlado (que é onde o protótipo vive), só geram quando o coletor sintetiza os cenários de ataque. Essa é a primeira frase que vai num parágrafo de discussão crítica do capítulo: **o sistema, hoje, tem 0% de falsos positivos no laboratório, mas isso é artefato do ambiente, não mérito do detector**.

---

## 4. Estratégias para diferenciar pico real de ataque

Aqui você apresenta o "menu de mitigações" — sete estratégias possíveis, ordenadas da mais simples à mais sofisticada. Para a defesa, escolha duas ou três para implementar como prova de conceito e cite as outras como evoluções futuras.

### 4.1. Allowlist de IPs confiáveis

A mais simples. Mantenha uma tabela `TrustedSource` no banco com IPs e/ou ranges CIDR que ficam imunes às regras (ou recebem limiares mais altos). Servidores de monitoramento, IPs internos de TI, CIDR do corporate VPN ficam aqui.

```python
@staticmethod
def _is_trusted_source(source_ip: str) -> bool:
    return TrustedSource.objects.filter(
        ip_or_cidr__contains=source_ip
    ).exists()

# antes de processar uma regra:
if AnomalyDetectorService._is_trusted_source(event.source_ip):
    return
```

**Vantagem:** trivial de implementar, elimina FP causados por scanner contratado e monitoring stack.
**Desvantagem:** exige curadoria manual e não detecta um atacante que comprometeu o IP confiável.

### 4.2. Baseline por janela longa (média histórica)

Para cada `source_ip`, calcular a taxa média de eventos por minuto nas últimas 24 horas. Só dispara alerta se a taxa atual está N desvios-padrão acima da média histórica.

```python
def _is_above_baseline(source_ip, protocol, current_rate):
    historical = NetworkEvent.objects.filter(
        source_ip=source_ip,
        protocol=protocol,
        event_timestamp__gte=now - timedelta(hours=24),
    ).count() / (24 * 60)  # por minuto
    threshold = historical + 3 * stdev_estimate
    return current_rate > threshold
```

**Vantagem:** reduz drasticamente FP de monitoramento contínuo (Zabbix vai ter sempre o mesmo padrão e nunca passar do baseline).
**Desvantagem:** requer histórico — primeiras 24h são frias. E um atacante "lento e baixo" (low-and-slow) que evolui o padrão gradualmente engana o baseline.

### 4.3. Score por correlação multi-sinal

Em vez de regras independentes, pondere múltiplos indicadores. Um ataque "verdadeiro" tem alta probabilidade de gerar **simultaneamente** dois ou mais sinais. Exemplo:

- Port scan + IP nunca visto antes (`first seen < 5 min`) → alta confiança.
- Port scan + IP visto pela primeira vez há 6 meses → média confiança.
- Port scan + IP em allowlist → baixa confiança ou ignorar.

A anomalia já tem um campo `score` (0–100) inutilizado hoje além de receber um valor fixo. Ele pode passar a ser computado como soma ponderada de fatores.

### 4.4. Janela de tempo adaptativa

Em horário comercial (9h–18h em dias úteis) usar limiares mais permissivos; fora disso, mais restritivos. Um port scan às 3h da manhã é muito mais suspeito que o mesmo scan às 14h, quando o time de DevOps roda inventários.

### 4.5. Categorização do `source_ip` (interno vs externo)

IPs em RFC 1918 (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`) são internos: aplicar limiares mais altos. IPs externos são potenciais atacantes: aplicar limiares mais baixos. Uma única regra não cabe nos dois mundos.

### 4.6. Feedback loop com `FALSE_POSITIVE` do operador

O sistema já tem o status `FALSE_POSITIVE` no `AlertViewSet`. Hoje ele é só visual — não realimenta nada. A evolução natural é: quando um operador marca um alerta como FP, registrar o `(source_ip, anomaly_type)` numa tabela de "perdoados" por N dias. Próximas anomalias do mesmo par ficam suprimidas ou rebaixadas a severidade `LOW`.

```python
class FalsePositiveFeedback(models.Model):
    source_ip = models.GenericIPAddressField()
    anomaly_type = models.CharField(max_length=100)
    suppress_until = models.DateTimeField()
```

**Esta é a mitigação que mais agrega ao TCC** porque ela transforma o sistema em adaptativo sem ML. É um caminho elegante que vale ressaltar na defesa.

### 4.7. Evolução para detecção estatística / ML (somente menção)

Substituir limiares fixos por:

- **Z-score** sobre janela móvel (parâmetros: μ e σ aprendidos por IP).
- **EWMA** (Exponentially Weighted Moving Average) — versão de média móvel que dá mais peso ao recente.
- **Isolation Forest** — algoritmo de ML não-supervisionado para detecção de outliers em features multi-dimensionais.
- **Autoencoder** sobre sequências de eventos — para padrões temporais.

Não implemente isso para a próxima entrega. Cite como horizonte.

---

## 5. Plano experimental

Aqui está a parte concreta: o que rodar, como rodar, o que medir.

### 5.1. Definição da unidade experimental

Cada **execução** é definida por três parâmetros:

- **Ambiente**: protótipo zerado, banco vazio, ativos cadastrados (digamos 5 ativos).
- **Geração de tráfego**: um script que produz N "rounds" alternando ataque e tráfego normal/ruidoso.
- **Configuração da regra**: limiares atuais ou variantes (para a tabela de sensibilidade).

### 5.2. Cenários a executar

Construa **seis cenários**, três de ataque e três de "ruído legítimo":

| Cenário | Tipo | Conteúdo | Verdade |
|---|---|---|---|
| A1 | Ataque | Port scan (13 portas, hping3-style ICMP burst de 25, DNS burst de 35) | Alarme esperado |
| A2 | Ataque | ICMP burst de 30 pacotes em 25s | Alarme esperado |
| A3 | Ataque | DNS burst de 50 consultas em 50s | Alarme esperado |
| N1 | Ruído | "Zabbix" — 50 ICMPs em 60s do mesmo source_ip simulando monitoramento | NÃO deve alarmar (é FP se alarmar) |
| N2 | Ruído | "Vulnerability scanner contratado" — 12 portas distintas em 60s do mesmo IP, mas IP em allowlist (se mitigação 4.1 estiver implementada) | NÃO deve alarmar |
| N3 | Ruído | "Navegação web" — 40 DNS em 30s do mesmo IP de cliente | NÃO deve alarmar (é FP se alarmar) |

> **Estratégia:** sem mitigações implementadas, N1, N2 e N3 vão **todos** disparar alerta — esses são os falsos positivos do protótipo cru. Isso é o seu **baseline**. Depois você implementa mitigações (escolha duas: por exemplo, allowlist + feedback loop) e re-roda. A queda de FPs entre os dois experimentos é o que você reporta como resultado da pesquisa.

### 5.3. Repetição e medição

Rode cada cenário **30 vezes** (com sementes aleatórias diferentes para os IPs e timing) para ter significância estatística. Para cada execução, conte:

- Anomalias geradas, separadas por `anomaly_type`.
- Para cada anomalia, classifique TP ou FP comparando com a verdade do cenário.

Some por cenário e calcule precisão, recall e F1.

### 5.4. Configuração mínima

Você pode controlar tudo isso com **dois scripts auxiliares**:

1. `benchmark/run_scenarios.py` — gera os 6 cenários × 30 execuções, chamando a API de eventos.
2. `benchmark/measure.py` — depois das execuções, lê o banco e tabula TP/FP/FN/TN, gera a matriz de confusão e calcula métricas. Pode exportar tudo para CSV ou Markdown.

Os scripts vão no Apêndice deste documento.

---

## 6. A tabela de sensibilidade

Esta é a entrega visível para o orientador. Para cada uma das três regras, você varia o limiar e mede como TP, FP e métricas se comportam.

### 6.1. Modelo da tabela — regra `HIGH_ICMP_RATE`

A regra atual usa "mais de 20 eventos em 30s". Vamos varrer de 5 a 40:

| Limiar | TP (em 30 ataques) | FP (em 30 cenários N1) | Recall | Precisão | F1 |
|---|---|---|---|---|---|
| > 5 | 30 | 30 | 1.00 | 0.50 | 0.67 |
| > 10 | 30 | 30 | 1.00 | 0.50 | 0.67 |
| > 15 | 30 | 30 | 1.00 | 0.50 | 0.67 |
| > 20 (atual) | 30 | 30 | 1.00 | 0.50 | 0.67 |
| > 25 | 28 | 25 | 0.93 | 0.53 | 0.68 |
| > 30 | 20 | 0 | 0.67 | 1.00 | 0.80 |
| > 35 | 5 | 0 | 0.17 | 1.00 | 0.29 |
| > 40 | 0 | 0 | 0.00 | indef. | indef. |

Os números acima são **ilustrativos** — você vai produzir os reais. A leitura é exemplo: o limiar atual (20) tem recall perfeito mas precisão 0.50 porque o cenário "Zabbix monitorando" produz 50 ICMP/min, sempre acima de 20. Subir para > 30 zera FP mas perde 1/3 dos ataques. **Entre 25 e 30 está a fronteira**.

### 6.2. Modelo da tabela — regra `PORT_SCAN_SUSPECT`

| Limiar (portas distintas em 60s) | TP | FP | Recall | Precisão | F1 |
|---|---|---|---|---|---|
| > 5 | 30 | 30 | 1.00 | 0.50 | 0.67 |
| > 10 (atual) | 30 | 30 | 1.00 | 0.50 | 0.67 |
| > 12 | 30 | 0 | 1.00 | 1.00 | 1.00 |
| > 13 | 0 | 0 | 0.00 | indef. | indef. |
| > 15 | 0 | 0 | 0.00 | indef. | indef. |

Repare no detalhe que liga **diretamente ao Nmap**: o cenário do simulador toca em **13 portas exatas**. Se o limiar passar de 13, o Nmap cumpriu seu papel mas a regra perde o recall — porque o detector exige ESTRITAMENTE MAIS de 13 portas distintas. O cenário N2 usa 12 portas distintas (escolhido propositalmente), então a fronteira está entre 12 e 13. Esse exemplo é didático para a banca — você mostra que o limiar não é arbitrário, é função do que o atacante real faria.

### 6.3. Modelo da tabela — regra `DNS_QUERY_BURST`

| Limiar (consultas em 60s) | TP | FP | Recall | Precisão | F1 |
|---|---|---|---|---|---|
| > 20 | 30 | 30 | 1.00 | 0.50 | 0.67 |
| > 30 (atual) | 30 | 30 | 1.00 | 0.50 | 0.67 |
| > 40 | 30 | 0 | 1.00 | 1.00 | 1.00 |
| > 50 | 0 | 0 | 0.00 | indef. | indef. |

### 6.4. Como apresentar no capítulo

Para cada uma das três tabelas, acompanhe de:

- Um **gráfico de duas linhas** (recall e precisão como função do limiar) — uma curva clássica de fronteira de decisão.
- Um **parágrafo de discussão** apontando a fronteira ótima e justificando o limiar atual ou um limiar recomendado.
- Uma **observação sobre o efeito de mitigações** — após adicionar allowlist, o cenário N2 sai da contagem de FP, e a precisão para o limiar > 10 sobe de 0.50 para 1.00 sem ajuste.

---

## 7. Como cada experimento se relaciona com Nmap e hping3

Esta é a articulação que o orientador esperará.

### 7.1. Nmap e a regra `PORT_SCAN_SUSPECT`

O Nmap, no protótipo, varre **13 portas** exatas. Os números importantes que aparecem na tabela de sensibilidade vêm direto desse fato:

- Limiar > 13 → o Nmap não consegue mais ser detectado (recall 0). Isso é a **fronteira superior**.
- O limiar precisa ser > N onde N é o **número de portas que um asset discovery legítimo costuma testar**. Cenário N2 (12 portas) define a fronteira inferior do FP.
- Conclusão: o **único limiar válido é exatamente entre 12 e 13**. Em outras palavras, o limiar atual de 10 é detectável demais (gera FP do scanner contratado) e poderia subir para 12.

Mais sutil: você pode argumentar que **se o atacante souber o limiar**, ele varre só as 13 portas mais comuns. Para cobrir isso, o sistema deveria correlacionar com **first-seen** do `source_ip`. Atacante = IP novo + 13 portas. Scanner contratado = IP conhecido + 13 portas. **Aqui o Nmap como ferramenta de simulação ajuda a torcer o limite até onde ele faz sentido.**

### 7.2. hping3 e a regra `HIGH_ICMP_RATE`

O hping3 no protótipo dispara **25 pacotes em ~2,5s** com `--fast`. A regra atual exige > 20 em 30s — folgada. Os números relevantes:

- Limiar > 25 → o cenário sintético do hping3 começa a falhar (porque o coletor envia exatamente 25 eventos, com `time.sleep(0.05)`).
- Limiar > 20 → captura o burst mas captura também o Zabbix.
- Limiar > 50 → não captura nem o burst nem o Zabbix.
- O **uso de `--fast` em vez de `--flood`** fixa a taxa máxima do simulador em 10 pps, o que põe um teto duro na curva.

Argumento para a defesa: **o limiar atual está calibrado para o hping3 com `--fast`, não para um atacante real**. Um atacante real usaria `--flood` (centenas de pps) e mesmo um limiar muito mais alto detectaria. O protótipo é conservador propositalmente — em ambientes reais, o limiar deveria ser dinâmico (baseline + 3σ).

### 7.3. A regra `DNS_QUERY_BURST` (sem ferramenta externa)

Como a regra de DNS não tem ferramenta externa equivalente, a fronteira é puramente sintética. Vale apresentá-la como **caso de controle** — limiar movido por escolha de design, sem ancoragem em comportamento real de ferramenta. É honesto admitir isso.

### 7.4. Conclusão da articulação

A escolha de Nmap e hping3 como ferramentas de carga não é decorativa: **elas amarram os limiares das regras a comportamentos concretos do mundo real** (port scan clássico de 13 portas; ping flood com taxa controlada). Isso permite que o capítulo de Resultados não seja "limiares arbitrários funcionando contra dados arbitrários", mas sim "limiares ancorados em ferramentas conhecidas, validados contra cenários conhecidos". A banca entende essa amarração e tende a valorizar.

---

## 8. Estrutura sugerida do capítulo de Resultados

Proposta de seções e o que cada uma contém:

### 8.1. Metodologia experimental

- Definição de TP/FP/TN/FN no contexto deste sistema.
- Métricas escolhidas: recall, precisão, F1.
- Configuração do laboratório: 5 ativos cadastrados, banco PostgreSQL local, coletor rodando em loop, frontend conectado.
- Descrição dos seis cenários (A1–A3, N1–N3).
- Repetições (30) e justificativa amostral.

### 8.2. Resultados quantitativos

- Tabela 1: matriz de confusão consolidada para os limiares atuais.
- Tabela 2: tabela de sensibilidade da regra `HIGH_ICMP_RATE`.
- Tabela 3: tabela de sensibilidade da regra `PORT_SCAN_SUSPECT`.
- Tabela 4: tabela de sensibilidade da regra `DNS_QUERY_BURST`.
- Gráficos correspondentes (recall × limiar, precisão × limiar).

### 8.3. Análise de falsos positivos

- Os três cenários N1–N3 e por que cada um gera falso positivo.
- Discussão de quanto isso seria pior em rede real.
- Comparação com literatura (ex.: estudos de Snort, Suricata reportam ordens de FP semelhantes).

### 8.4. Mitigações implementadas e seu efeito

- Mitigação 1 (sugestão: allowlist) implementada. Mede-se a queda de FP.
- Mitigação 2 (sugestão: feedback loop com `FALSE_POSITIVE`) implementada. Mede-se a queda de FP em segunda execução.
- Tabela comparativa "antes × depois".

### 8.5. Limitações

- Ambiente controlado, não rede real.
- Apenas três tipos de ataque cobertos.
- Sem evasão (atacante "consciente" do detector).
- Volume baixo.

### 8.6. Discussão crítica

- O quanto o sistema é defensável como prova de conceito.
- Caminho para um produto: ML, fila assíncrona, escala, etc.

---

## 9. Apêndice — scripts prontos

Para facilitar a execução do plano experimental, os três scripts abaixo são suficientes. Crie a pasta `benchmark/` na raiz do projeto e coloque-os lá.

### 9.1. `benchmark/scenarios.py` — gera os seis cenários

```python
import random
import time
from datetime import datetime, timedelta

# importe o seu APIClient
import sys
sys.path.append("../collector")
from services.api_client import APIClient
from services.event_factory import EventFactory


def run_attack_port_scan(api, asset, attacker_ip, scenario_id):
    """Cenário A1: 13 portas distintas em ~1 segundo."""
    ports = [21, 22, 23, 25, 53, 80, 110, 135, 139, 143, 443, 445, 3306]
    for port in ports:
        payload = EventFactory.tcp_event(
            asset_id=asset["id"],
            source_ip=attacker_ip,
            destination_ip=asset["ip_address"],
            destination_port=port,
        )
        payload["raw_summary"] = f"benchmark={scenario_id} truth=ATTACK"
        api.send_event(payload)
        time.sleep(0.05)


def run_attack_icmp_burst(api, asset, attacker_ip, scenario_id, count=30):
    """Cenário A2: burst ICMP."""
    for _ in range(count):
        payload = EventFactory.icmp_event(
            asset_id=asset["id"],
            source_ip=attacker_ip,
            destination_ip=asset["ip_address"],
        )
        payload["raw_summary"] = f"benchmark={scenario_id} truth=ATTACK"
        api.send_event(payload)
        time.sleep(0.02)


def run_attack_dns_burst(api, asset, attacker_ip, scenario_id, count=50):
    """Cenário A3: burst DNS."""
    for _ in range(count):
        payload = EventFactory.dns_event(
            asset_id=asset["id"],
            source_ip=attacker_ip,
            destination_ip=asset["ip_address"],
        )
        payload["raw_summary"] = f"benchmark={scenario_id} truth=ATTACK"
        api.send_event(payload)
        time.sleep(0.02)


def run_noise_zabbix(api, assets, monitor_ip, scenario_id, count=50):
    """Cenário N1: monitoramento legítimo, mesmo source_ip pingando muitos hosts."""
    for _ in range(count):
        target = random.choice(assets)
        payload = EventFactory.icmp_event(
            asset_id=target["id"],
            source_ip=monitor_ip,
            destination_ip=target["ip_address"],
        )
        payload["raw_summary"] = f"benchmark={scenario_id} truth=NORMAL"
        api.send_event(payload)
        time.sleep(0.05)


def run_noise_inventory(api, asset, scanner_ip, scenario_id):
    """Cenário N2: scanner contratado, 12 portas distintas (logo abaixo do limiar atual)."""
    ports = [21, 22, 80, 443, 3306, 5432, 6379, 8080, 8443, 9200, 27017, 5672]
    for port in ports:
        payload = EventFactory.tcp_event(
            asset_id=asset["id"],
            source_ip=scanner_ip,
            destination_ip=asset["ip_address"],
            destination_port=port,
        )
        payload["raw_summary"] = f"benchmark={scenario_id} truth=NORMAL"
        api.send_event(payload)
        time.sleep(0.05)


def run_noise_browsing(api, asset, client_ip, scenario_id, count=40):
    """Cenário N3: navegação web normal, muitas resoluções DNS."""
    for _ in range(count):
        payload = EventFactory.dns_event(
            asset_id=asset["id"],
            source_ip=client_ip,
            destination_ip=asset["ip_address"],
        )
        payload["raw_summary"] = f"benchmark={scenario_id} truth=NORMAL"
        api.send_event(payload)
        time.sleep(0.05)


def main():
    api = APIClient("http://127.0.0.1:8000", "admin", "admin")
    api.authenticate()

    assets = api.get_assets()
    monitored = [a for a in assets if a["is_monitored"]]
    if not monitored:
        print("Cadastre ao menos um ativo monitorado antes de rodar.")
        return

    REPETITIONS = 30
    scenarios = [
        ("A1_PORT_SCAN", lambda i: run_attack_port_scan(
            api, random.choice(monitored), EventFactory.suspicious_source_ip(), f"A1_{i}")),
        ("A2_ICMP_BURST", lambda i: run_attack_icmp_burst(
            api, random.choice(monitored), EventFactory.suspicious_source_ip(), f"A2_{i}")),
        ("A3_DNS_BURST",  lambda i: run_attack_dns_burst(
            api, random.choice(monitored), EventFactory.suspicious_source_ip(), f"A3_{i}")),
        ("N1_ZABBIX",     lambda i: run_noise_zabbix(
            api, monitored, "10.0.0.50", f"N1_{i}")),  # IP fixo do "monitor"
        ("N2_INVENTORY",  lambda i: run_noise_inventory(
            api, random.choice(monitored), "10.0.0.60", f"N2_{i}")),
        ("N3_BROWSING",   lambda i: run_noise_browsing(
            api, random.choice(monitored), f"10.0.0.{100+i}", f"N3_{i}")),
    ]

    for name, fn in scenarios:
        print(f"\n=== Rodando {name} ({REPETITIONS} repetições) ===")
        for i in range(REPETITIONS):
            print(f"  [{name}] iteração {i+1}/{REPETITIONS}")
            fn(i)
            time.sleep(70)  # garante separação entre iterações além da janela de detecção

if __name__ == "__main__":
    main()
```

> **Observação sobre o `time.sleep(70)`** entre iterações: as regras agregam por janelas de 30–60s; precisamos garantir que a iteração anterior já saiu da janela antes de começar a próxima, senão eventos de iterações distintas se misturam. Em um benchmark sério, esse sleep é essencial.

### 9.2. `benchmark/measure.py` — calcula as métricas

```python
"""
Roda APÓS scenarios.py. Lê as anomalias geradas no banco
e cruza com a "verdade" gravada em raw_summary do evento original.
"""
import os
import sys
import django

# bootstrap Django
sys.path.append("../backend")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.events.models import NetworkEvent
from apps.anomalies.models import Anomaly


def parse_truth(raw_summary):
    if "truth=ATTACK" in raw_summary:
        return "ATTACK"
    if "truth=NORMAL" in raw_summary:
        return "NORMAL"
    return None


def parse_scenario(raw_summary):
    parts = raw_summary.split()
    for p in parts:
        if p.startswith("benchmark="):
            return p.split("=", 1)[1]
    return None


def measure():
    # Para cada cenário, conta TP e FP
    counters = {}

    for anomaly in Anomaly.objects.select_related("event"):
        truth = parse_truth(anomaly.event.raw_summary or "")
        scenario = parse_scenario(anomaly.event.raw_summary or "")
        if scenario is None:
            continue

        prefix = scenario.split("_")[0] + "_" + scenario.split("_")[1]
        bucket = counters.setdefault(prefix, {"TP": 0, "FP": 0})

        if truth == "ATTACK":
            bucket["TP"] += 1
        elif truth == "NORMAL":
            bucket["FP"] += 1

    print(f"{'Cenário':<20} {'TP':>5} {'FP':>5}")
    print("-" * 32)
    for name, c in sorted(counters.items()):
        print(f"{name:<20} {c['TP']:>5} {c['FP']:>5}")


if __name__ == "__main__":
    measure()
```

### 9.3. `benchmark/sensitivity.py` — gera a tabela de sensibilidade

A ideia aqui é diferente: **rodar o detector offline contra um conjunto fixo de eventos**, variando o limiar a cada passada, sem precisar regerar tráfego.

```python
"""
Carrega os eventos coletados em scenarios.py e simula a aplicação das regras
com diferentes limiares, sem persistir no banco. Útil para varrer rapidamente.
"""
import os, sys, django, csv
from datetime import timedelta
sys.path.append("../backend")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.events.models import NetworkEvent


def truth_from_summary(s):
    if "truth=ATTACK" in s: return "ATTACK"
    if "truth=NORMAL" in s: return "NORMAL"
    return None


def simulate_icmp_rule(threshold_count, window_seconds=30):
    """
    Para cada evento ICMP, conta os ICMPs do mesmo source_ip nos últimos
    window_seconds. Se passar do limiar, é "alerta". Compara com truth.
    """
    events = list(NetworkEvent.objects.filter(protocol="ICMP")
                  .order_by("event_timestamp"))
    tp = fp = fn = tn = 0
    flagged_ips_recent = {}  # source_ip -> last alert timestamp (deduplicação)

    for ev in events:
        truth = truth_from_summary(ev.raw_summary or "")
        if truth is None:
            continue

        window_start = ev.event_timestamp - timedelta(seconds=window_seconds)
        count = sum(1 for e in events
                    if e.source_ip == ev.source_ip
                    and e.protocol == "ICMP"
                    and window_start <= e.event_timestamp <= ev.event_timestamp)

        is_alert = count > threshold_count

        # deduplicação simulada de 60s
        last = flagged_ips_recent.get(ev.source_ip)
        if is_alert and last and (ev.event_timestamp - last).total_seconds() < 60:
            is_alert = False
        if is_alert:
            flagged_ips_recent[ev.source_ip] = ev.event_timestamp

        if truth == "ATTACK" and is_alert: tp += 1
        elif truth == "ATTACK" and not is_alert: fn += 1
        elif truth == "NORMAL" and is_alert: fp += 1
        elif truth == "NORMAL" and not is_alert: tn += 1

    precision = tp / (tp + fp) if (tp + fp) else float("nan")
    recall = tp / (tp + fn) if (tp + fn) else float("nan")
    f1 = (2 * precision * recall / (precision + recall)
          if precision and recall and precision + recall > 0
          else float("nan"))
    return {"threshold": threshold_count, "TP": tp, "FP": fp, "TN": tn, "FN": fn,
            "precision": precision, "recall": recall, "f1": f1}


def main():
    rows = [simulate_icmp_rule(t) for t in (5, 10, 15, 20, 25, 30, 35, 40)]
    with open("sensitivity_icmp.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)
    print("OK: sensitivity_icmp.csv")
    # Replicar para PORT_SCAN e DNS_BURST com a mesma lógica adaptada


if __name__ == "__main__":
    main()
```

> Esse script é um esqueleto. Para `PORT_SCAN_SUSPECT`, em vez de contar eventos, contar `len(set(destination_port))` na janela. Para `DNS_QUERY_BURST`, contar eventos como em ICMP mas com janela de 60s.

---

## Resumo executivo

Para a próxima entrega, faça nesta ordem:

1. **Aceite que o protótipo, hoje, não diferencia pico real de ataque.** Reconheça isso explicitamente no capítulo.
2. **Defina os seis cenários** (A1, A2, A3, N1, N2, N3) — três ataques e três pseudo-ataques legítimos.
3. **Implemente `benchmark/scenarios.py` e `measure.py`** — eles produzem os números do capítulo.
4. **Construa três tabelas de sensibilidade** (uma por regra), variando o limiar.
5. **Implemente uma ou duas mitigações** (sugestão: allowlist + feedback loop com `FALSE_POSITIVE`) e mostre a queda de FP.
6. **Escreva o capítulo** seguindo a estrutura da seção 8.
7. **Articule explicitamente com Nmap (13 portas) e hping3 (25 ICMP @10 pps)** mostrando como esses parâmetros amarram os limiares — é a articulação que o orientador vai querer ver.

A maior virada de chave aqui é entender que **o detector hoje é uma fronteira de decisão fixa, e o capítulo de Resultados é uma análise da qualidade dessa fronteira**. Você não precisa que o sistema seja perfeito — precisa medir honestamente o que ele faz e propor o que melhoraria. Isso é pesquisa.
