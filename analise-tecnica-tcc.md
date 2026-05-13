# Análise Técnica do Protótipo

**Sistema Inteligente de Monitoramento de Infraestrutura de TI**
*Material de apoio para a defesa do TCC*

---

## 1. Visão geral do projeto

O protótipo é um sistema inteligente de monitoramento de infraestrutura de TI, organizado em três blocos independentes que se comunicam por uma API REST: um **coletor** (que simula e dispara eventos de rede), um **backend Django** responsável por persistir dados, detectar anomalias e expor a API, e um **frontend Next.js** que apresenta dashboard, ativos, eventos e alertas para o usuário operador. O objetivo central do projeto é demonstrar, em escala de protótipo acadêmico, a viabilidade de um pipeline completo de telemetria de rede, indo da captura/simulação de eventos até a geração e gestão de alertas, com foco especial em três cenários de comportamento anômalo: alta taxa de ICMP, suspeita de port scan TCP e burst de consultas DNS.

A divisão em três módulos, conectados apenas por HTTP, é uma das principais decisões arquiteturais do trabalho. Ela materializa o conceito de arquitetura em camadas e, ao mesmo tempo, permite que cada parte evolua de forma isolada. O coletor poderia ser substituído amanhã por um sniffer real baseado em libpcap sem impactar o backend; o frontend poderia ser substituído por um aplicativo móvel; e o backend pode escalar horizontalmente porque cada requisição vinda do coletor é tratada de forma independente, sem estado de sessão entre chamadas.

### 1.1. Tecnologias utilizadas

| Camada | Stack |
|---|---|
| Backend | Python, Django, Django REST Framework, SimpleJWT, django-cors-headers, python-decouple |
| Banco de dados | PostgreSQL (engine `django.db.backends.postgresql`) |
| Frontend | Next.js (App Router), React, TypeScript, Tailwind CSS, Recharts |
| Coletor | Python puro com `requests`, integrando-se a Nmap (port scan) e hping3 (flooding ICMP) |
| Autenticação | JWT (Bearer token) emitido pelo SimpleJWT, com refresh token |

---

## 2. Arquitetura e fluxo de dados

O fluxo principal do sistema pode ser descrito em sete etapas. Primeiro, o coletor autentica-se no backend via JWT (`POST /api/auth/login/`) e armazena o access token em memória. Depois, ele consulta `/api/assets/` para obter a lista de ativos cadastrados e filtra apenas aqueles com `is_monitored = True`. Em loop contínuo (intervalo de 5 segundos no `main.py`), o coletor envia eventos de rede para o backend via `POST /api/events/`. Cada evento traz protocolo, IP de origem, IP de destino, portas, timestamp e metadados específicos do protocolo. No backend, o `NetworkEventViewSet` persiste o evento e, no método `perform_create`, dispara o `AnomalyDetectorService`, que avalia o evento contra três regras estatísticas baseadas em janela de tempo. Quando uma regra é violada, o serviço cria simultaneamente um `Anomaly` e um `Alert`. Por fim, o frontend, em polling de 5 segundos, consulta os endpoints do dashboard, alerta e eventos, e renderiza as informações em tabelas, cartões e gráficos.

### 2.1. Diagrama lógico de comunicação

```
+-----------------+        HTTP/JSON        +-------------------+
|   COLLECTOR     |  ---------------------> |   BACKEND DJANGO  |
| (simulator.py)  |   POST /api/events/     |   /api/events/    |
| Nmap, hping3    |   GET  /api/assets/     |   /api/alerts/    |
+-----------------+                         |   /api/dashboard/ |
                                            +---------+---------+
                                                      |
                                                      | ORM
                                                      v
                                            +-------------------+
                                            |    PostgreSQL     |
                                            +-------------------+
                                                      ^
                                                      |
                                            +---------+---------+
                                            |    FRONTEND       |
                                            |  Next.js + React  |
                                            |   polling 5s      |
                                            +-------------------+
```

### 2.2. Estrutura de pastas

```
monitoring-system-tcc/
├── backend/
│   ├── config/                 # settings, urls, wsgi/asgi
│   ├── apps/
│   │   ├── accounts/           # placeholder para usuários (vazio)
│   │   ├── assets/             # CRUD de ativos monitorados
│   │   ├── events/             # ingestão e listagem de eventos
│   │   ├── anomalies/          # modelo de anomalia + motor de detecção
│   │   ├── alerts/             # alertas gerados a partir das anomalias
│   │   └── dashboard/          # endpoints agregados para o front
│   └── manage.py
├── collector/
│   ├── main.py                 # entrypoint
│   ├── simulator.py            # cenários de eventos
│   ├── auth.py                 # autenticação JWT
│   ├── config.py               # leitura de variáveis .env
│   └── services/
│       ├── api_client.py       # wrapper de requests
│       ├── event_factory.py    # builders de payloads ICMP/TCP/DNS
│       └── network_tools.py    # execução de Nmap e hping3
├── frontend/
│   └── src/
│       ├── app/                # Next.js App Router (páginas)
│       │   ├── login/
│       │   └── dashboard/
│       │       ├── assets/
│       │       ├── events/
│       │       └── alerts/
│       ├── components/dashboard/  # cards, charts, tables
│       ├── lib/                # api.ts e auth-storage.ts
│       └── types/              # tipos TS para assets/dashboard
└── docs/                       # arquitetura, requisitos, backlog
```

---

## 3. Backend Django em profundidade

### 3.1. Configuração geral (`config/settings.py`)

O projeto Django está organizado dentro do pacote `config`. As variáveis sensíveis (`SECRET_KEY`, credenciais de banco e `DEBUG`) são lidas via `python-decouple` a partir de `backend/.env`, o que evita expor segredos no repositório. O banco configurado é PostgreSQL apontando para `localhost` na porta 5432, com nome `monitoring-system-tcc-db`. O timezone está fixado em `America/Bahia` e a língua em `pt-br`, o que é coerente com o público da defesa.

Estão registrados três grupos de apps: os apps padrão do Django (admin, auth, sessions, etc.); três bibliotecas externas (`corsheaders`, `rest_framework` e `rest_framework_simplejwt`); e os seis apps internos do projeto (`accounts`, `assets`, `events`, `anomalies`, `alerts` e `dashboard`). O CORS está configurado de forma permissiva (`CORS_ALLOW_ALL_ORIGINS = True`), o que é aceitável em ambiente de protótipo, mas é um ponto que vale citar como dívida técnica para a defesa.

O Django REST Framework está configurado para usar autenticação por JWT em todas as rotas (`DEFAULT_AUTHENTICATION_CLASSES`) e para exigir `IsAuthenticated` por padrão (`DEFAULT_PERMISSION_CLASSES`). Os tokens têm 60 minutos de vida (access) e 1 dia (refresh).

### 3.2. Roteamento (`config/urls.py`)

O `urls.py` raiz expõe seis grupos de endpoints: o painel administrativo do Django, dois endpoints de autenticação e cinco namespaces da API.

| Rota | Função |
|---|---|
| `POST /api/auth/login/` | Recebe usuário e senha; devolve access e refresh tokens (`TokenObtainPairView`) |
| `POST /api/auth/refresh/` | Renova o access token a partir do refresh |
| `/api/assets/` | CRUD completo de ativos (`ModelViewSet`) |
| `/api/events/` | Listagem e criação de eventos. POST aciona o detector de anomalias |
| `/api/anomalies/` | Listagem somente-leitura das anomalias (`ReadOnlyModelViewSet`) |
| `/api/alerts/` | Listagem e atualização de status (apenas GET e PATCH liberados) |
| `/api/dashboard/...` | Sete endpoints agregados (summary, protocols, severity, recent-events, recent-alerts, assets-status, anomaly-types) |

### 3.3. Modelo de dados

O modelo de dados é compacto e gira em torno de quatro entidades principais — **Asset**, **NetworkEvent**, **Anomaly** e **Alert** — todas com chave estrangeira encadeada de forma a refletir o fluxo do pipeline.

#### Asset (`apps/assets/models.py`)

Representa um ativo monitorado da rede (servidor, roteador, switch, firewall, workstation ou outro). Usa **UUID** como chave primária, o que é uma boa prática para protótipos voltados a defesa porque evita que IDs sequenciais vazem informação sobre o tamanho do inventário. O campo `ip_address` é `unique`, o que garante que não exista mais de um ativo cadastrado com o mesmo IP. O campo `status` pode assumir quatro estados (`ONLINE`, `OFFLINE`, `UNSTABLE`, `UNKNOWN`), e o booleano `is_monitored` controla se o coletor enviará eventos para aquele ativo.

#### NetworkEvent (`apps/events/models.py`)

Modelagem genérica para eventos de rede TCP, ICMP e DNS. Em vez de criar três tabelas distintas, o autor optou por uma única tabela com colunas opcionais específicas de cada protocolo (`tcp_flags`, `dns_query`, `icmp_type`, `icmp_code`, `source_port`, `destination_port`, `packet_size`). Isso é uma decisão pragmática: simplifica queries de agregação no dashboard (basta um `GROUP BY protocol`) e evita JOINs caros, ao custo de algumas colunas vazias por linha. O campo `asset` é uma FK para `Asset`, com `on_delete=CASCADE` — o que significa que excluir um ativo apaga todo o seu histórico de eventos.

#### Anomaly (`apps/anomalies/models.py`)

Cada anomalia detectada referencia o `NetworkEvent` disparador e o `Asset` envolvido. Tem severidade categórica (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`), um `score` numérico (0–100, decimal), o `anomaly_type` (string, por exemplo `HIGH_ICMP_RATE`), o `detection_rule` (string descrevendo a regra que disparou) e um `status` do ciclo de vida (`NEW`, `UNDER_ANALYSIS`, `CONFIRMED`, `DISMISSED`). O campo `detected_at` é gravado como `timezone.now()` pelo serviço.

#### Alert (`apps/alerts/models.py`)

Alerta é o artefato visível ao operador. Tem relação **OneToOne** com `Anomaly` (ou seja, cada anomalia gera no máximo um alerta). Conta com `title`, `message`, `severity` (espelhada da anomalia), `status` (`OPEN`, `IN_PROGRESS`, `RESOLVED`, `FALSE_POSITIVE`), `assigned_to` (FK opcional para `User` do Django) e timestamps de criação, atualização e resolução. O `resolved_at` é preenchido automaticamente pela view quando o status muda para `RESOLVED`.

### 3.4. Endpoints e ViewSets

O backend usa o padrão DRF `ModelViewSet` com `DefaultRouter`, o que automaticamente expõe as rotas list, retrieve, create, update e destroy a partir de uma única classe. **AlertViewSet** restringe os métodos HTTP a GET e PATCH (por `http_method_names`), garantindo que ninguém apague ou crie alertas pela API — alertas só nascem de uma anomalia detectada. **AnomalyViewSet** é `ReadOnlyModelViewSet`, ou seja, não permite escrita pela API: anomalias só são criadas internamente pelo detector.

Vale a pena destacar dois pontos sutis que costumam render boas perguntas em banca. Primeiro, o uso de `select_related` em `Anomaly`, `Alert` e `NetworkEvent` reduz o problema de N+1 queries — ao invés de uma consulta por relacionamento, o ORM faz JOIN antecipado. Segundo, o método `perform_create` em `NetworkEventViewSet` hospeda a integração com o motor de detecção, garantindo que o evento já esteja salvo quando o detector é executado.

### 3.5. O motor de detecção de anomalias

O coração analítico do projeto é o `AnomalyDetectorService` em `apps/anomalies/services/detector.py`. Ele é uma classe estática com um único ponto de entrada público — `analyze_event(event)` — que faz roteamento por protocolo: se for ICMP, chama `_check_high_icmp_rate`; se for TCP, chama `_check_port_scan`; se for DNS, chama `_check_dns_burst`.

Cada regra opera com **janela de tempo deslizante** baseada no `event_timestamp` do evento recém-recebido. Antes de criar uma anomalia, o serviço verifica em `_anomaly_exists` se já existe outra anomalia do mesmo tipo, no mesmo ativo, dentro dos últimos 60 segundos. Esse mecanismo de **deduplicação** é crítico: sem ele, um único port scan geraria dezenas de anomalias e dezenas de alertas idênticos, poluindo o painel.

#### Regra 1 — `HIGH_ICMP_RATE`

Conta quantos eventos ICMP partiram do mesmo `source_ip` nos últimos **30 segundos** a partir do `event_timestamp`. Se forem **mais de 20** eventos, dispara uma anomalia de severidade `MEDIUM` com score 70 e regra interna `icmp_rate_over_20_in_30s`. Esse padrão é compatível com um ping flood controlado (por isso o coletor utiliza `hping3` com 25 pacotes para reproduzi-lo).

#### Regra 2 — `PORT_SCAN_SUSPECT`

Conta o número de **portas de destino distintas** alcançadas pelo mesmo `source_ip` nos últimos **60 segundos**. Usa `values_list("destination_port", flat=True).distinct()` para extrair o conjunto de portas únicas. Se passar de **10 portas distintas**, dispara uma anomalia de severidade `HIGH` com score 85 e regra `distinct_tcp_ports_over_10_in_1m`. É exatamente o comportamento do Nmap sondando 13 portas (21, 22, 23, 25, 53, 80, 110, 135, 139, 143, 443, 445, 3306) no cenário do simulador.

#### Regra 3 — `DNS_QUERY_BURST`

Conta o total de eventos DNS partindo do mesmo `source_ip` nos últimos **60 segundos**. Se passar de **30 consultas**, dispara anomalia `MEDIUM` com score 75. O cenário simulado envia 35 consultas para garantir o disparo.

Em todos os três casos, o método `_create_anomaly_and_alert` cria a anomalia e, em seguida, cria o alerta correspondente, com título e mensagem em português. Esse acoplamento direto entre anomalia e alerta é uma escolha de simplicidade — em produção, faria sentido separar em uma fila de mensagens (Celery/Redis) para desacoplar latência da ingestão da latência da geração de alerta.

### 3.6. Endpoints do dashboard

O app dashboard concentra **sete `APIView`** que servem dados pré-agregados ao frontend, evitando que o front faça processamento estatístico no navegador.

- `/api/dashboard/summary/` devolve totais de ativos por status, total de eventos, total de anomalias e contagem de alertas por status.
- `/api/dashboard/protocols/` retorna a contagem de eventos agrupada por protocolo (input do gráfico de barras).
- `/api/dashboard/severity/` retorna a contagem de alertas agrupada por severidade (input do gráfico de pizza).
- `/api/dashboard/recent-events/?limit=N` e `/api/dashboard/recent-alerts/?limit=N` retornam as últimas N entradas.
- `/api/dashboard/assets-status/` devolve o mesmo bloco de ativos do summary, separado para uso em outras telas.
- `/api/dashboard/anomaly-types/` devolve a contagem por tipo de anomalia detectada (`HIGH_ICMP_RATE`, `PORT_SCAN_SUSPECT`, `DNS_QUERY_BURST`).

Todas as agregações são feitas com a expressão `Count("id")` do ORM e usam `values(...).annotate(...).order_by(...)`. Isso é importante para a defesa: o agrupamento e a contagem são executados no banco PostgreSQL, **não em Python**, garantindo desempenho mesmo com volumes grandes de eventos.

---

## 4. Coletor / Simulador de eventos

O coletor é uma aplicação Python independente que vive em `/collector`. Sua função no protótipo é dupla: simular tráfego normal para popular o sistema com dados de baseline e simular ataques controlados para acionar as três regras do detector. Em uma evolução futura, ele poderia ser substituído por um sniffer real baseado em Scapy ou tcpdump, mas o contrato com o backend permaneceria o mesmo: enviar eventos via `POST /api/events/`.

### 4.1. Componentes

| Arquivo | Responsabilidade |
|---|---|
| `main.py` | Entrypoint. Faz autenticação no backend e dispara o loop `run_realtime_monitoring(interval=5)`. |
| `simulator.py` | Classe `EventSimulator` com os cenários: tráfego normal, ICMP burst, port scan, DNS burst e monitoramento contínuo. |
| `services/api_client.py` | Wrapper sobre `requests.Session`. Anexa o header `Authorization: Bearer <jwt>` em todas as chamadas após `authenticate()`. |
| `services/event_factory.py` | Constrói payloads sintéticos para os três protocolos. Gera IPs de origem aleatórios via `suspicious_source_ip()`. |
| `services/network_tools.py` | Executa Nmap (com fallback de `-sS` para `-sT`) e hping3 via `subprocess`, com timeout e tratamento de ferramenta ausente. |
| `auth.py` / `config.py` | Leem variáveis de ambiente do `.env` e fazem o login JWT inicial. |

### 4.2. Cenários implementados

O método `run_realtime_monitoring` é um loop infinito que, a cada 5 segundos, executa `monitor_assets_once` (envia um evento ICMP por ativo monitorado) e, com probabilidades pré-definidas, dispara cenários adicionais: **30% de chance** de simular um burst de 25 pacotes ICMP, **20% de chance** de port scan e **20% de chance** de burst de 35 consultas DNS. Os três cenários sempre escolhem aleatoriamente um ativo monitorado e um IP de atacante (via `suspicious_source_ip`), que retorna um IP aleatório fora da faixa reservada para garantir que o `source_ip` seja sempre o mesmo dentro do mesmo ataque, mas diferente entre ataques distintos.

Esse desenho probabilístico é elegante para uma defesa: a banca consegue ver, em poucos minutos, todos os tipos de alertas surgindo organicamente no dashboard, sem que o avaliador precise acionar comandos manualmente. É o que torna o protótipo "vivo" durante a apresentação.

### 4.3. Integração com Nmap e hping3

O `NetworkToolRunner` executa as ferramentas externas via `subprocess.run` com captura de stdout/stderr e timeout de 30 segundos. Para o **Nmap**, usa por padrão o scan SYN (`-sS`), que é mais furtivo, mas exige privilégios de raw socket. Se o retorno for diferente de zero (típico em ambientes sem privilégio root), faz **fallback automático** para `-sT` (TCP connect scan), garantindo que o cenário funcione mesmo em uma estação sem permissões elevadas. Esse detalhe é importante de mencionar na defesa, porque mostra preocupação com a portabilidade da demonstração.

O **hping3** é executado em modo `--icmp --fast` com `-c <count>`, gerando pacotes ICMP echo request reais contra o IP-alvo. Se a ferramenta não estiver instalada no PATH, a exceção `ExternalToolUnavailable` é capturada e o sistema apenas loga um aviso, sem interromper a simulação — os eventos sintéticos continuam sendo enviados ao backend para acionar a regra. Essa separação é deliberada: o disparo da ferramenta de rede é "realismo opcional", enquanto o registro dos eventos no backend é o que garante que o detector seja exercitado.

### 4.4. Estrutura dos payloads

Cada evento enviado ao backend tem o seguinte formato JSON (exemplo de um evento TCP gerado pelo cenário de port scan):

```json
{
  "asset": "<uuid-do-ativo>",
  "protocol": "TCP",
  "source_ip": "172.45.10.99",
  "destination_ip": "192.168.0.10",
  "source_port": 51234,
  "destination_port": 22,
  "packet_size": 512,
  "tcp_flags": "SYN",
  "dns_query": "",
  "icmp_type": null,
  "icmp_code": null,
  "event_timestamp": "2026-05-07T14:32:01.123",
  "raw_summary": "Nmap TCP scan attempt to port 22",
  "collector_name": "nmap"
}
```

---

## 5. Frontend Next.js

O frontend foi construído sobre o **App Router** do Next.js (pasta `src/app`), com TypeScript e Tailwind CSS. Todas as páginas são marcadas como `"use client"` e fazem fetch direto do backend via funções utilitárias em `src/lib/api.ts`. Não há server components fazendo SSR de dados de negócio — a opção foi simplicidade: o cliente busca via `fetch`, salva o JWT no `localStorage` e renderiza.

### 5.1. Mapa de rotas

| Rota | Função |
|---|---|
| `/` | Redirect server-side para `/login` (`next/navigation` redirect) |
| `/login` | Formulário de login que chama `POST /api/auth/login/` e salva os tokens no localStorage |
| `/dashboard` | Página principal: cards de resumo, status dos ativos, gráficos de protocolos e severidade, tabelas de eventos e alertas recentes. Polling em 5s |
| `/dashboard/events` | Lista todos os eventos coletados, com filtro por protocolo (ICMP/TCP/DNS) e polling de 5s |
| `/dashboard/alerts` | Lista todos os alertas, com filtros por status e severidade. Permite mudar o status (Em análise / Resolver / Falso positivo) via PATCH |
| `/dashboard/assets` | Lista os ativos cadastrados, com filtro por status e tipo. Tem link para edição |
| `/dashboard/assets/new` | Formulário para cadastrar novo ativo (nome, IP, hostname, MAC, tipo, localização, SO, status, monitorado) |
| `/dashboard/assets/[id]/edit` | Formulário para editar um ativo existente |

### 5.2. Camada de API e autenticação

A função `apiFetch<T>(path, options)` em `src/lib/api.ts` é o ponto único de saída HTTP do front. Ela monta os headers (sempre `Content-Type: application/json`), anexa `Authorization: Bearer <token>` quando o caller fornece a opção `token`, e chama `window.fetch` com `cache: "no-store"` para garantir que o Next.js nunca retorne dados em cache. Em caso de resposta não-OK, lança `Error` com o corpo da resposta como mensagem.

A persistência do JWT é feita em `src/lib/auth-storage.ts` via `localStorage` com as chaves `infraguard_access_token` e `infraguard_refresh_token`. Cada chamada protegida do front lê o access token via `getAccessToken()` e o passa explicitamente para `apiFetch`. Quando um fetch falha (por expiração de token ou erro qualquer), o handler limpa os tokens e redireciona para `/login`. É um padrão simples mas funcional para um protótipo.

### 5.3. Polling em tempo real

As três páginas operacionais (dashboard, events e alerts) usam o mesmo padrão: `useEffect` dispara um `setInterval(fetchData, 5000)` e o cleanup do efeito faz `clearInterval`. Isso simula "tempo real" sem precisar de WebSocket. É uma decisão pragmática perfeita para escopo de TCC, mas vale citar como ponto de evolução: para escala produtiva, o ideal seria server-sent events ou WebSocket via Django Channels, evitando que o cliente puxe dados desnecessariamente quando nada mudou.

### 5.4. Componentes visuais

A pasta `src/components/dashboard` concentra **seis componentes reutilizáveis**: `SummaryCards` (oito cartões de KPI com cores diferentes para online, offline, instável, alertas etc.), `AssetStatusOverview` (visão consolidada do status dos ativos), `ProtocolsChart` (gráfico de barras com Recharts agrupando eventos por protocolo), `SeverityChart` (gráfico de pizza com Recharts agrupando alertas por severidade), `RecentEventsTable` e `RecentAlertsTable`. Os gráficos usam `recharts` (`BarChart` e `PieChart` com `ResponsiveContainer`), o que garante responsividade automática.

A paleta visual é **dark mode** consistente: fundo `bg-slate-950`, painéis `bg-slate-900` com borda `slate-800`, e badges semânticos (verde para online, vermelho para offline e crítico, amarelo para instável e médio, laranja para alto, ciano para ICMP, violeta para TCP, esmeralda para DNS). Essa coerência cromática facilita a leitura rápida da tela em ambiente operacional.

---

## 6. Fluxo end-to-end de uma anomalia

Para a defesa, o melhor caminho é narrar o ciclo completo de uma anomalia desde a sua origem até a tela do operador. Tomando o cenário de **port scan** como exemplo:

**1.** Em um ciclo do loop do coletor, o `random.random()` resulta em < 0.2 e `simulate_port_scan` é invocado. O método escolhe aleatoriamente um ativo monitorado, gera um IP atacante via `suspicious_source_ip` e tenta executar Nmap contra as 13 portas selecionadas (21, 22, 23, 25, 53, 80, 110, 135, 139, 143, 443, 445, 3306).

**2.** Independentemente do sucesso do Nmap real, o coletor sintetiza 13 `NetworkEvent` payloads — um por porta — todos com o mesmo `source_ip` atacante e o asset escolhido como destino. Cada payload é enviado por `POST /api/events/` com o header `Authorization: Bearer <jwt>`.

**3.** No backend, `NetworkEventViewSet.perform_create` persiste o evento e chama `AnomalyDetectorService.analyze_event(event)`. Como `protocol == "TCP"`, a regra `_check_port_scan` é executada para cada novo evento.

**4.** Em algum momento entre o 11º e o 13º evento, a contagem de portas distintas dentro da janela de 60 segundos passa de 10. O serviço chama `_create_anomaly_and_alert` que primeiro verifica em `_anomaly_exists` se já não existe outra anomalia `PORT_SCAN_SUSPECT` no mesmo asset nos últimos 60 segundos. Se não houver, cria um `Anomaly` (severity=HIGH, score=85) e em seguida um `Alert` ligado a ela (status=OPEN, severity=HIGH).

**5.** No frontend, o próximo ciclo de polling (em até 5 segundos) traz o novo alerta nos endpoints `/api/dashboard/summary/` (que mostra alertas abertos +1), `/api/dashboard/severity/` (gráfico de pizza atualiza a fatia HIGH) e `/api/dashboard/recent-alerts/` (a tabela de últimos alertas exibe o novo registro no topo). O componente `lastUpdated` reflete o horário do último fetch.

**6.** O operador acessa `/dashboard/alerts`, vê o alerta com severidade HIGH e escolhe "Em análise". O frontend dispara `updateAlertStatus(alertId, "IN_PROGRESS", token)`, que faz `PATCH /api/alerts/<id>/`. `AlertViewSet.perform_update` grava o novo status. Quando o operador clica em "Resolver", o mesmo fluxo é seguido com `status=RESOLVED`, e o backend automaticamente preenche `resolved_at = timezone.now()` em `update_fields`.

---

## 7. Decisões técnicas e justificativas

Esta seção destrincha as principais escolhas de design e oferece a justificativa pronta para responder à banca.

### Por que Django + DRF e não FastAPI/Flask?

Django entrega Admin pronto, ORM consolidado, migrations declarativas, sistema de autenticação e DRF maduro. Para um sistema com modelagem relacional e CRUD pesado (assets, eventos, anomalias, alertas), Django reduz substancialmente o boilerplate em relação a Flask. FastAPI seria atraente por performance e tipagem nativa, mas exigiria escrever manualmente camadas que Django entrega de fábrica (admin, autenticação, migrations).

### Por que PostgreSQL e não SQLite?

Mesmo em escala de protótipo, PostgreSQL oferece índices melhores para consultas com janelas temporais (`event_timestamp__gte`, `__lte`) e tipos nativos como `GenericIPAddressField` com validação. Em produção, a evolução natural seria adicionar índices compostos em `(source_ip, protocol, event_timestamp)` para acelerar as três regras do detector.

### Por que Next.js e não SPA pura (CRA, Vite)?

Next.js permite que páginas como `/` sejam server-rendered (no caso, fazem apenas redirect, mas em outras telas a estratégia poderia evoluir). Além disso, traz roteamento por arquivos (App Router), bundling otimizado, suporte nativo a TypeScript e fácil deploy em Vercel — atributos atraentes para um TCC.

### Por que JWT e não sessões?

JWT permite que o coletor (uma aplicação que não vive em navegador) autentique-se da mesma forma que o frontend. Em sessões cookie-based seria necessário compartilhar cookies de sessão e CSRF. Com JWT, o coletor faz login uma vez no startup e reaproveita o access token nas chamadas seguintes.

### Por que detecção baseada em regras e não machine learning?

Para o escopo do TCC, regras explícitas são auditáveis, defensáveis e independem de dataset histórico — algo que ML supervisionado exigiria. As três regras (limite de ICMP, contagem de portas distintas, limite de DNS) refletem padrões clássicos descritos na literatura de IDS (Intrusion Detection Systems). Um próximo passo natural, citável na defesa, é evoluir para detecção baseada em estatísticas (z-score, EWMA) ou em ML (isolation forest, autoencoder), mantendo a arquitetura atual.

### Por que polling de 5 segundos e não WebSocket?

Polling é trivial de implementar, fácil de depurar e tolerante a falhas (uma chamada perdida não derruba a sessão). Para um protótipo acadêmico, é suficiente. Em produção com centenas de operadores, faria sentido migrar para Django Channels com WebSocket ou Server-Sent Events para reduzir tráfego.

### Por que separar Anomaly e Alert?

Conceitualmente, anomalia é uma observação do detector e alerta é um item de fila operacional. Manter as duas entidades separadas permite que, no futuro, várias anomalias sejam consolidadas em um único alerta (por exemplo, agrupando port scans repetidos ao longo de uma hora). Hoje a relação é OneToOne, mas o modelo já está preparado para mudar.

---

## 8. Possíveis perguntas da banca e respostas sugeridas

### "O sistema funciona em tempo real?"

Funciona em **tempo próximo do real**. O coletor envia eventos a cada 5 segundos por loop, o detector é síncrono dentro da requisição POST (latência típica de poucas dezenas de ms) e o frontend faz polling a cada 5 segundos. O atraso máximo entre um ataque ocorrer e ele aparecer no painel é, portanto, de aproximadamente 5 segundos. Não usei WebSocket porque o overhead de implementação não se justificava no escopo do TCC.

### "Como você evita falsos positivos?"

Existem dois mecanismos. Primeiro, as três regras usam **limiares conservadores** (mais de 20 ICMP em 30s, mais de 10 portas distintas em 1 minuto, mais de 30 DNS em 1 minuto), que filtram ruído de tráfego normal. Segundo, há **deduplicação**: antes de criar uma anomalia, o detector verifica em `_anomaly_exists` se já existe outra do mesmo tipo no mesmo ativo nos últimos 60 segundos, evitando floods de alertas idênticos. O usuário também pode marcar manualmente um alerta como `FALSE_POSITIVE`, o que poderia alimentar futura calibração das regras.

### "Por que o detector roda dentro da requisição POST?"

Por simplicidade. Como a regra mais cara executa três queries indexáveis em PostgreSQL, a latência adicional é baixa e aceitável para o volume do protótipo. Em produção, a evolução natural seria publicar o evento em uma fila (Celery, Kafka) e processar a detecção de forma assíncrona, desacoplando a latência da ingestão da latência da análise.

### "O que acontece se o coletor cair?"

O backend continua funcionando normalmente — ele é stateless em relação ao coletor. Quando o coletor reinicia, ele faz `authenticate()` novamente, busca os ativos monitorados e retoma o loop. Não há estado do lado do coletor que precise ser persistido.

### "E se houver vários coletores?"

A API é horizontalmente compatível: cada evento traz `collector_name`, então é possível identificar a origem. A modelagem permite que múltiplos coletores enviem eventos simultaneamente, e as três regras de detecção continuam funcionando porque agregam por `source_ip`, não por coletor. Pequenas correções de race condition seriam necessárias se dois coletores enviassem eventos quase simultâneos do mesmo IP, mas o impacto é apenas duplicação de detecção (mitigada pela deduplicação).

### "Como você protege a API?"

Todas as rotas exigem autenticação JWT por padrão (`DEFAULT_PERMISSION_CLASSES = IsAuthenticated`). Os tokens têm validade limitada (60 minutos para access, 1 dia para refresh). O CORS está liberado em modo permissivo para fins de demonstração — em produção, restringir-se-ia ao domínio do frontend. Não há HTTPS configurado na aplicação porque o protótipo roda em localhost; em produção isso seria delegado a um reverse proxy (Nginx, Caddy).

### "Como o sistema lida com volume?"

As consultas mais críticas (as três regras de detecção) são todas filtradas por `source_ip`, `protocol` e janela de `event_timestamp`. Em um cenário de alto volume, o ganho de performance virá de **índices compostos** em `(source_ip, protocol, event_timestamp)`. Para o escopo do TCC, com volume da ordem de centenas de eventos por minuto, o PostgreSQL responde em poucos milissegundos. Para escala maior, a evolução é mover detecção para janela em memória (Redis, stream processing).

### "Por que UUID em vez de auto-incremento?"

UUID elimina o vazamento de informação por enumeração (um adversário não consegue advinhar IDs sequenciais), facilita merges futuros entre bancos distintos sem colisão de chaves e é mais seguro para expor em URLs públicas. O custo é um pouco mais de espaço em disco e índices um pouco maiores, o que é irrelevante na escala do projeto.

### "Qual a maior limitação atual do protótipo?"

O coletor **não captura tráfego real** — ele simula. Para virar um produto, o próximo passo é usar uma biblioteca como Scapy ou pypcap para escutar a interface de rede e gerar eventos a partir de pacotes reais. A arquitetura está pronta para isso porque o contrato com o backend é apenas o JSON de `NetworkEvent`. Outra limitação é que o motor de detecção tem regras estáticas hard-coded — uma evolução natural é externalizá-las para uma tabela `DetectionRule` editável via API.

### "Como você avaliou a qualidade do sistema?"

A validação foi feita por **cenários determinísticos**: cada uma das três regras tem um cenário simulador correspondente (`simulate_icmp_burst`, `simulate_port_scan`, `simulate_dns_burst`) com volume calibrado para garantir o disparo (25 ICMP em pouco tempo, 13 portas TCP distintas, 35 consultas DNS). Isso permite reproduzir os três tipos de alerta de forma confiável durante a demonstração.

---

## 9. Pontos de atenção e melhorias futuras

Esta seção aponta lacunas reais identificadas no código. Conhecê-las protege contra perguntas inesperadas — é melhor mencionar a limitação você mesmo ("sei que isso é uma simplificação porque...") do que ser pego de surpresa.

- **App `accounts` está praticamente vazio** (models, views e urls sem implementação). O sistema usa o `User` padrão do Django via `createsuperuser`. Não há cadastro de usuários pela API nem perfis de acesso (todo usuário autenticado tem permissão total).
- **CORS_ALLOW_ALL_ORIGINS = True** é apropriado para desenvolvimento, mas precisa ser restringido em produção a `CORS_ALLOWED_ORIGINS = ['https://meu-frontend']`.
- **Credenciais hard-coded em `collector/main.py`** (`admin/admin`) em vez de virem do `.env` via `config.py`. Há aqui uma inconsistência: `auth.py` usa `decouple`, mas `main.py` não.
- **Não há testes automatizados** implementados (os arquivos `tests.py` em todos os apps estão vazios). Em uma versão evolutiva, seria valioso adicionar `pytest` cobrindo as três regras do detector com cenários sintéticos.
- **`AlertViewSet` usa `http_method_names`** para limitar verbos, mas seria mais claro escrever uma classe permission custom (por exemplo, `IsOperatorOrReadOnly`) que reflita explicitamente a regra de negócio.
- **`event_factory.py` usa `datetime.utcnow()`** que retorna `datetime` naive. Em `USE_TZ=True` do Django, isso pode levar a comparações de timezone ambíguas. O padrão recomendado é `datetime.now(timezone.utc)`.
- **Dashboard usa cinco fetches em `Promise.all`** sem `AbortController`. Se o usuário sair da página rapidamente os fetches podem disparar `setState` em componentes desmontados.
- **Sem rate limiting nas APIs**. Um coletor mal comportado poderia inundar o backend. Em produção, usar `django-ratelimit` ou um middleware no Nginx.
- **Resolvedor automático de status** faz dois `UPDATE` no banco (um do serializer, outro com `update_fields=["resolved_at"]`). Poderia ser feito em uma única query.
- **Endpoints `/api/events/` e `/api/alerts/` não paginam**. Em volumes altos isso degrada o frontend. Bastaria configurar `DEFAULT_PAGINATION_CLASS` no DRF.

---

## 10. Roteiro sugerido para a demonstração ao vivo

Sugestão de sequência para apresentar o sistema durante a defesa, encadeando narrativa e evidências visuais.

**Passo 1 — Contexto.** Mostre o diagrama de arquitetura (slide ou impresso) e narre os três blocos: coletor, backend e frontend.

**Passo 2 — Suba o backend.** `python manage.py runserver`. Mostre o `/admin` do Django para evidenciar as quatro tabelas principais (`Asset`, `NetworkEvent`, `Anomaly`, `Alert`) já com dados de seed, se existir.

**Passo 3 — Suba o frontend.** `npm run dev` em `/frontend`. Faça login com `admin/admin` e mostre a tela de dashboard com cards e gráficos zerados ou com dados anteriores.

**Passo 4 — Suba o coletor.** `python collector/main.py`. Mantenha o terminal visível para a banca ver as mensagens `[INFO]`, `[PORT SCAN]`, `[ICMP BURST]` aparecendo em tempo real.

**Passo 5 — Volte para o dashboard.** Em poucos segundos, os cards de eventos vão começar a crescer, o gráfico de protocolos passa a desenhar barras e o gráfico de severidade ganha fatias. Aponte para o `lastUpdated` atualizando.

**Passo 6 — Vá para Alertas.** Mostre os alertas chegando, filtre por severidade `HIGH`, mude o status do primeiro para "Em análise" e depois "Resolver". Aponte que o `resolved_at` é gravado automaticamente.

**Passo 7 — Vá para Eventos.** Filtre por TCP. Mostre como aparecem várias entradas com o mesmo `source_ip` atacante e portas destino diferentes — exatamente o padrão que disparou o alerta de port scan.

**Passo 8 — Cadastre um novo ativo.** Em `/dashboard/assets/new`, adicione algo como "Servidor Banco de Dados", IP `192.168.0.50`, tipo SERVER, monitorado=true. Volte ao terminal do coletor — em poucos segundos ele vai começar a enviar eventos para o novo ativo.

**Passo 9 — Encerre.** Volte ao dashboard, mostre os números finais e narre o ciclo completo de uma anomalia (a história do capítulo 6 deste documento).

---

## 11. Resumo executivo (cartão de defesa)

Concentre estes pontos para usar como "cola mental" durante a apresentação:

- **Três blocos independentes** (coletor, backend, frontend) integrados por uma única **API REST autenticada com JWT**.
- **Backend Django** com seis apps modulares; modelo de dados com quatro entidades principais (`Asset`, `NetworkEvent`, `Anomaly`, `Alert`) e relação encadeada.
- **Detector de anomalias síncrono** baseado em três regras estatísticas com janela de tempo (`HIGH_ICMP_RATE`, `PORT_SCAN_SUSPECT`, `DNS_QUERY_BURST`), com **deduplicação por janela de 60 segundos**.
- **Coletor Python** que simula tráfego normal e três cenários de ataque com **Nmap (port scan)**, **hping3 (ICMP flood)** e payloads sintéticos para DNS.
- **Frontend Next.js** com App Router, Tailwind e Recharts; **polling de 5 segundos** para tempo próximo ao real; oito cartões de KPI, dois gráficos e duas tabelas no dashboard principal.
- **Decisões deliberadas de simplicidade**: detecção dentro da request, polling em vez de WebSocket, regras hard-coded em vez de ML — todas justificáveis pelo escopo acadêmico e com caminho claro de evolução.
- **Pontos de evolução conhecidos**: captura real de pacotes, externalização das regras, autenticação por papéis, fila assíncrona para detecção, paginação, testes automatizados.
