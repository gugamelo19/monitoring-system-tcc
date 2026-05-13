# Coletor, Nmap e hping3 — guia técnico de estudo

*Material complementar para a defesa do TCC*

Este documento aprofunda o módulo `collector/` do protótipo, com ênfase em entender **o que cada ferramenta externa faz**, **como ela faz** (no nível de protocolo de rede) e **por que** ela foi escolhida para reproduzir cada cenário de anomalia. Ao final, você deve conseguir explicar para a banca o caminho completo de um pacote — desde o disparo no terminal até a anomalia aparecer no dashboard.

---

## Sumário

1. Arquitetura do coletor
2. Anatomia de um evento sintético
3. NetworkToolRunner: a ponte com o sistema operacional
4. Nmap a fundo
5. hping3 a fundo
6. Por que o coletor envia eventos "sintéticos" mesmo executando as ferramentas reais
7. O encontro entre o coletor e o detector
8. Glossário de defesa

---

## 1. Arquitetura do coletor

O coletor é uma aplicação Python independente, um processo que vive em loop e fala apenas HTTP com o backend. Ele não compartilha memória, banco ou configuração com o Django — está acoplado ao backend exclusivamente pelo contrato de API REST. Esse desacoplamento é uma das principais virtudes arquiteturais do projeto e é o que permite, no futuro, trocar o coletor por um sniffer real (Scapy, libpcap) sem mexer em uma única linha do backend.

### 1.1. Hierarquia de arquivos

```
collector/
├── main.py                # entrypoint: autentica e chama run_realtime_monitoring
├── simulator.py           # EventSimulator: orquestra cenários de tráfego
├── auth.py                # função utilitária get_access_token()
├── config.py              # leitura do .env via decouple
└── services/
    ├── api_client.py      # APIClient: wrapper sobre requests.Session
    ├── event_factory.py   # EventFactory: builders de payloads ICMP/TCP/DNS
    └── network_tools.py   # NetworkToolRunner: subprocess para Nmap e hping3
```

### 1.2. Sequência de inicialização

Quando você executa `python collector/main.py`, acontece o seguinte, em ordem:

1. `main()` instancia `APIClient(base_url, username, password)`.
2. `api_client.authenticate()` faz `POST http://127.0.0.1:8000/api/auth/login/` com `{"username": "admin", "password": "admin"}`. O backend devolve `{"access": "<jwt>", "refresh": "<jwt>"}`.
3. O `access` token é guardado dentro do `requests.Session` como header default `Authorization: Bearer <jwt>`. Toda chamada futura usa essa sessão e, portanto, vai autenticada sem código adicional.
4. `EventSimulator` é instanciado, recebendo o `api_client` e criando internamente um `NetworkToolRunner`.
5. `simulator.run_realtime_monitoring(interval=5)` entra em loop infinito.

### 1.3. O loop principal

O coração do coletor é uma máquina de estados de uma única linha lógica:

```python
while True:
    self.monitor_assets_once()              # baseline: 1 ICMP por ativo monitorado

    if random.random() < 0.3:               # 30% de chance
        self.simulate_icmp_burst(total=25)

    if random.random() < 0.2:               # 20% de chance
        self.simulate_port_scan()

    if random.random() < 0.2:               # 20% de chance
        self.simulate_dns_burst(total=35)

    time.sleep(interval)                    # 5s
```

Esse desenho probabilístico garante que, em poucos minutos, todos os três cenários de anomalia tenham acontecido pelo menos uma vez — sem ninguém precisar acionar comandos manualmente. Essa "vivacidade aleatória" é o que torna a demonstração ao vivo eficiente diante da banca.

> **Detalhe importante para defesa:** os três `if` são independentes. Em um único ciclo, é possível ocorrer simultaneamente um burst ICMP, um port scan e um burst DNS. Isso é proposital: o detector precisa lidar com fontes de anomalia concorrentes.

### 1.4. `monitor_assets_once`: o tráfego de baseline

Antes de qualquer cenário de ataque, o coletor envia **um evento ICMP por ativo monitorado**. Isso popula o sistema com tráfego "normal" — um operador real veria um pulso de baseline contínuo, contra o qual os ataques se destacam. É o que permite que o gráfico de protocolos no dashboard tenha sempre uma fração de ICMP nativo, em vez de aparecer só durante ataques.

---

## 2. Anatomia de um evento sintético

Antes de mergulhar em Nmap e hping3, é fundamental entender o que o coletor **manda** para o backend. Um evento é um JSON simples, e o que diferencia um evento "normal" de um "atacante" é apenas o conteúdo dos campos.

### 2.1. Os três tipos de payload

O `EventFactory` tem três builders, um por protocolo. Os campos relevantes mudam de acordo com o protocolo:

| Campo | ICMP | TCP | DNS |
|---|---|---|---|
| `protocol` | "ICMP" | "TCP" | "DNS" |
| `source_port` | null | aleatório 1024–65535 | aleatório 1024–65535 |
| `destination_port` | null | parâmetro (ex: 22) | 53 |
| `tcp_flags` | "" | "SYN" | "" |
| `dns_query` | "" | "" | aleatório (google.com, etc.) |
| `icmp_type` | 8 (echo request) | null | null |
| `icmp_code` | 0 | null | null |
| `packet_size` | 64–128 | 64–1500 | 64–512 |
| `raw_summary` | "ICMP echo request detected" | "TCP connection attempt to port X" | "DNS query request detected" |
| `collector_name` | "simulator" / "hping3" | "simulator" / "nmap" | "simulator" |

### 2.2. O IP atacante: `suspicious_source_ip()`

Para que um cenário de port scan ou flood seja **detectável**, todos os eventos do mesmo ataque precisam ter o **mesmo `source_ip`**. Isso é crítico, porque as três regras do detector agrupam por `source_ip`. Repare no fluxo dentro de `simulate_port_scan`:

```python
attacker_ip = EventFactory.suspicious_source_ip()  # gera UMA vez
for index, port in enumerate(ports, start=1):
    payload = EventFactory.tcp_event(
        ...
        source_ip=attacker_ip,        # mesmo IP em todos os 13 eventos
        destination_port=port,
    )
```

A mesma lógica vale para `simulate_icmp_burst` e `simulate_dns_burst`. Já o `monitor_assets_once` (tráfego normal) **não passa `source_ip`**, então cada evento ganha um IP aleatório diferente — e portanto não dispara a deduplicação por IP do detector. É justamente por isso que o tráfego de baseline gera estatística de protocolos, mas não gera anomalia.

### 2.3. Geração do IP atacante

```python
@staticmethod
def suspicious_source_ip() -> str:
    return ".".join(str(part) for part in [
        random.randint(11, 223),  # primeiro octeto (evita 0–10 e 224–255)
        random.randint(0, 255),
        random.randint(0, 255),
        random.randint(1, 254),   # último octeto evita .0 e .255 (broadcast)
    ])
```

A faixa `11–223` no primeiro octeto evita IPs reservados como `0.0.0.0/8` (rede), `10.0.0.0/8` (RFC 1918 — embora coletor pudesse usar), `127.0.0.0/8` (loopback) e a faixa multicast/experimental `224.0.0.0/4` em diante. É um truque elegante para gerar IPs que "parecem" de internet pública, dando realismo visual no dashboard.

---

## 3. NetworkToolRunner: a ponte com o sistema operacional

O arquivo `services/network_tools.py` encapsula toda a interação com o shell. É deliberadamente pequeno, mas resolve três problemas de produção que dão ótimos pontos de defesa.

### 3.1. Detecção de ferramenta ausente

```python
@staticmethod
def _require_tool(tool_name: str) -> str:
    executable = shutil.which(tool_name)
    if executable is None:
        raise ExternalToolUnavailable(f"{tool_name} nao encontrado no PATH.")
    return executable
```

`shutil.which` faz exatamente o mesmo que o comando `which` do bash: percorre o `$PATH` procurando o binário. Se não encontrar, retorna `None`. O `_require_tool` traduz isso numa exceção customizada, que é capturada lá em cima no `simulator.py`:

```python
try:
    result = self.network_tools.run_nmap_port_scan(...)
except (ExternalToolUnavailable, TimeoutError) as error:
    print(f"[WARN] {error}")
```

Resultado prático: se o avaliador rodar a demo numa máquina sem Nmap instalado, o coletor **não trava** — apenas pula a execução real e segue enviando os eventos sintéticos. Isso é importante de mencionar: a robustez não é por acidente, é por design.

### 3.2. Timeout obrigatório

```python
def _run(self, command: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=self.timeout,   # 30 segundos por padrão
        check=False,
    )
```

`subprocess.run` com `timeout=30` garante que um Nmap travado (rede congestionada, host inalcançável) não congele o coletor para sempre. Se passar de 30s, levanta `subprocess.TimeoutExpired`, capturado e re-lançado como `TimeoutError`. O `check=False` impede que o subprocess levante exceção ao retornar código diferente de zero — porque `nmap` pode retornar não-zero em casos perfeitamente normais (host filtrado, sem privilégios). Em vez disso, o código de retorno é inspecionado manualmente.

### 3.3. Captura de stdout e stderr

`capture_output=True` + `text=True` faz com que `result.stdout` e `result.stderr` sejam strings (não bytes). Isso permite imprimir mensagens de erro do Nmap no terminal do coletor, dando feedback útil para depuração:

```python
if result.returncode != 0:
    if result.stderr:
        print(result.stderr.strip())
```

---

## 4. Nmap a fundo

### 4.1. O que é Nmap

**Nmap** (Network Mapper) é a ferramenta de descoberta de redes mais usada do mundo, criada por Gordon Lyon ("Fyodor") em 1997. Sua função primária é responder a perguntas como:

- Quais hosts estão ativos nessa faixa de IPs?
- Que portas TCP/UDP estão abertas em um host?
- Que serviços estão escutando nessas portas?
- Que sistema operacional o host está executando?

No protótipo, usamos apenas a função mais básica e a mais "barulhenta": **port scan**, ou varredura de portas.

### 4.2. O que é uma porta e por que isso importa

Em redes IP, uma "porta" é um número de 16 bits (0–65535) que identifica um **endpoint** dentro de um host. O par `(IP, porta)` identifica univocamente um serviço escutando. Por convenção da IANA, portas baixas (0–1023) são reservadas para serviços bem-conhecidos:

| Porta | Serviço |
|---|---|
| 21 | FTP |
| 22 | SSH |
| 23 | Telnet |
| 25 | SMTP |
| 53 | DNS |
| 80 | HTTP |
| 110 | POP3 |
| 135 | RPC (Windows) |
| 139 | NetBIOS |
| 143 | IMAP |
| 443 | HTTPS |
| 445 | SMB (Windows) |
| 3306 | MySQL |

**Estas são exatamente as 13 portas** que o `simulate_port_scan` testa. A escolha não é aleatória — são portas que um atacante real verificaria primeiro num reconhecimento, porque correspondem a serviços comumente expostos com falhas conhecidas (FTP/Telnet são velhos, SMB do Windows é histórico de exploits, MySQL exposto é desastre, etc.).

### 4.3. A "varredura": o que significa "escanear" uma porta

Escanear uma porta TCP significa **enviar um pacote** ao destino e **observar a resposta** (ou ausência dela). As três respostas possíveis em TCP são:

| Resposta do alvo | Estado da porta |
|---|---|
| `SYN/ACK` | **Aberta** — há um serviço escutando |
| `RST` (reset) | **Fechada** — não há serviço, mas o host respondeu |
| Sem resposta | **Filtrada** — provavelmente um firewall descartou o pacote |

A diferença entre os tipos de scan está em **como** esse pacote é enviado e em **quanto** do handshake TCP é completado.

### 4.4. SYN scan (`-sS`) — "stealth scan"

O TCP normal estabelece conexão pelo three-way handshake:

```
Cliente -> Servidor :  SYN
Cliente <- Servidor :  SYN/ACK
Cliente -> Servidor :  ACK            (conexão estabelecida)
```

O **SYN scan** envia o primeiro `SYN` mas **não responde com ACK**. Em vez disso, ao receber `SYN/ACK` (porta aberta), envia `RST` para abortar. Isso significa que **a conexão nunca se completa**, o que historicamente fazia com que muitos sistemas operacionais e logs de aplicação **não registrassem** o scan — daí o nome "stealth" (furtivo).

Características do `-sS`:
- **Mais rápido** (não precisa completar handshake).
- **Menos detectável** por logs de aplicação (apesar de IDS modernos detectarem facilmente).
- **Exige privilégio de raw socket** — ou seja, `root` no Linux, Administrator no Windows, ou capability `CAP_NET_RAW` em containers. Sem privilégio, o Nmap não consegue construir o pacote SYN bruto.

### 4.5. Connect scan (`-sT`) — "TCP connect"

O **Connect scan** delega tudo ao sistema operacional: chama a syscall `connect()` exatamente como um cliente comum. Se a conexão completa, a porta está aberta; se recebe `ECONNREFUSED`, fechada; se dá timeout, filtrada.

Características do `-sT`:
- **Não exige privilégio**, porque não constrói pacote bruto.
- **Mais lento** (handshake completo + close) e **mais detectável** (a aplicação alvo enxerga uma conexão).
- É o **fallback automático** que o protótipo usa quando `-sS` falha.

### 4.6. Por que o fallback `-sS` → `-sT`

```python
result = self._run(command)
if result.returncode != 0 and scan_type == "-sS":
    fallback_command = command.copy()
    fallback_command[1] = "-sT"
    result = self._run(fallback_command)
return result
```

Esse padrão garante que a demo funcione **com ou sem privilégios**. Em uma estação de aluno rodando Windows comum ou Linux sem `sudo`, o `-sS` falha porque não consegue abrir raw socket; o coletor detecta o erro (returncode != 0), reescreve o argumento para `-sT` e tenta de novo. Para a banca, o resultado é o mesmo — 13 portas testadas, eventos enviados, regra disparada.

> **Pergunta provável da banca:** "Por que você não exige sempre `-sT`, já que ele funciona para todos?" — Resposta: porque `-sS` é o método clássico de varredura furtiva e é o que um atacante real usaria em primeira tentativa. Manter `-sS` como tentativa primária reflete uma simulação mais fiel ao mundo real, com `-sT` como degradação graciosa apenas em ambientes restritos.

### 4.7. Outras flags do comando

```python
command = [
    nmap,
    scan_type,           # -sS ou -sT
    "-Pn",               # pula host discovery
    "--max-retries", "1",
    "-p", port_argument, # lista de portas separada por vírgula
    target_ip,
]
```

| Flag | Significado |
|---|---|
| `-Pn` | "Treat all hosts as online". Pula a fase de descoberta (ping). Sem `-Pn`, o Nmap primeiro tenta um ICMP echo + TCP ACK na porta 80; se não obtém resposta, marca o host como down e nem tenta scan de porta. Com `-Pn`, ele segue direto para o port scan. Isso é importante porque firewalls frequentemente bloqueiam ICMP, e sem `-Pn` o Nmap acharia que o alvo está offline. |
| `--max-retries 1` | Reduz o número de retries por porta. Padrão é 10. Para o protótipo, é uma otimização: queremos rapidez, não completude. |
| `-p` | Especifica as portas. Aceita ranges (`-p 1-1000`), listas (`-p 22,80,443`) ou ambos. |

### 4.8. O que acontece no fio quando `simulate_port_scan` roda

Para cada uma das 13 portas, o Nmap (em `-sS`) emite um pacote TCP com flag SYN. O conteúdo aproximado de cada pacote:

```
+----------------+----------------+-----------------+----------------+
| Source IP      | Dest IP        | Source port     | Dest port      |
| 192.168.0.??   | 192.168.0.10   | 51234 (random)  | 22 (target)    |
+----------------+----------------+-----------------+----------------+
| Flags: SYN | Window: 1024 | TCP Options: MSS, SACK, ...           |
+----------------------------------------------------------------------+
```

Note que o `source_ip` real do Nmap é o IP da máquina que está rodando o coletor — **não** o `attacker_ip` aleatório que o coletor manda no payload sintético. Esse é o ponto crítico para entender no item 6 deste documento.

---

## 5. hping3 a fundo

### 5.1. O que é hping3

**hping3** é uma ferramenta de linha de comando para construir e enviar pacotes TCP, UDP, ICMP e RAW IP customizados. Diferentemente do `ping` tradicional (que só envia ICMP echo request), o hping3 permite controlar campos arbitrários do cabeçalho IP/TCP/ICMP — porta de origem, flags TCP, payload, intervalo entre pacotes, IP de origem spoofado, etc.

No protótipo, o hping3 é usado para uma única função: **gerar um burst de ICMP echo request rápido** contra um alvo, simulando um *ping flood*. Isso aciona a regra `HIGH_ICMP_RATE` do detector.

### 5.2. ICMP em três minutos

**ICMP** (Internet Control Message Protocol) é o protocolo "auxiliar" da pilha TCP/IP, definido na RFC 792. Ele é usado para mensagens de controle e diagnóstico, **não para transferência de dados de aplicação**. As mensagens ICMP têm um campo `Type` (8 bits) e um campo `Code` (8 bits) que juntos identificam a operação.

| Type | Code | Significado |
|---|---|---|
| 0 | 0 | Echo Reply (resposta de ping) |
| 3 | 0 | Destination Unreachable (rede inalcançável) |
| 3 | 3 | Destination Unreachable (porta inalcançável) |
| 8 | 0 | **Echo Request (ping)** |
| 11 | 0 | Time Exceeded (TTL chegou a zero — o que `traceroute` explora) |

O `EventFactory.icmp_event` sempre cria payloads com `icmp_type=8, icmp_code=0`, ou seja, **echo request** — exatamente o que o `ping` ou o hping3 disparariam.

### 5.3. O comando do hping3 no protótipo

```python
command = [
    hping3,
    "--icmp",      # protocolo: ICMP em vez de TCP/UDP padrão
    "--fast",      # 10 pacotes por segundo
    "-c", str(count),  # quantidade total de pacotes (no caso, 25)
    target_ip,
]
```

| Flag | Significado |
|---|---|
| `--icmp` | Diz ao hping3 para enviar ICMP echo request. Sem essa flag, o padrão é TCP. |
| `--fast` | Modo rápido: 10 pacotes por segundo (intervalo de 100ms). Sem `--fast`, o padrão é 1 pacote por segundo. |
| `-c <n>` | Conta total de pacotes a enviar. Após enviar `n`, o hping3 termina. |

> **Existem modos ainda mais agressivos** (`--faster`, `--flood`) — `--flood` envia o mais rápido que a interface aguenta, sem esperar resposta. O coletor escolheu `--fast` porque é suficiente para acionar a regra (mais de 20 ICMP em 30s) sem saturar a interface. Saturar a interface da máquina de demonstração no momento da defesa seria uma péssima ideia.

### 5.4. O que é um "ping flood" e por que ele é uma anomalia

Em uso normal, o `ping` é mandado de forma cadenciada (1 pacote por segundo) e em pequena quantidade (4 pacotes no Windows, indefinido no Linux por default). Um `ping flood` é qualquer rajada que envie centenas ou milhares de echo requests em poucos segundos. As três principais razões para um atacante fazer isso:

1. **Reconhecimento agressivo** — verificar se um host está vivo, ignorando rate limits.
2. **Saturação de banda/CPU** — em ICMP echo request, o kernel do alvo precisa responder com echo reply, e cada resposta consome CPU e banda. Em larga escala isso vira um *DoS* (Denial of Service). O ataque clássico "Smurf" é uma variação amplificada disso.
3. **Cobertura para outro ataque** — gerar ruído ICMP enquanto outro vetor age, para confundir analistas.

A regra `HIGH_ICMP_RATE` do detector responde exatamente a esse padrão: **mais de 20 echo requests do mesmo `source_ip` em 30 segundos**.

### 5.5. O que sai pela rede quando o hping3 roda

O hping3 emite, por padrão, pacotes ICMP com payload pequeno (`packet_size` padrão de 0–28 bytes além do cabeçalho). Aproximadamente:

```
+----------------+----------------+--------------------------------+
| Source IP      | Dest IP        |  ICMP Type=8 Code=0 (Echo Req) |
| host-coletor   | target-asset   |  Identifier, Sequence Number   |
+----------------+----------------+--------------------------------+
```

25 desses pacotes saem em ~2,5 segundos (devido ao `--fast`). O kernel do alvo, ao receber, responde com `Type=0 Code=0` (echo reply) — a menos que o firewall/iptables esteja configurado para descartar ICMP, o que é comum em ambientes endurecidos.

### 5.6. Privilégios do hping3

Assim como `-sS` do Nmap, hping3 também precisa de **raw socket**, ou seja, root no Linux. No Windows ele não funciona nativamente — daí a recomendação no README do projeto de usar Linux/WSL. Se o hping3 estiver ausente ou sem privilégio, o coletor captura a exceção e segue gerando os 25 eventos sintéticos no backend, garantindo que a regra dispare de qualquer forma.

---

## 6. Por que o coletor envia eventos "sintéticos" mesmo executando as ferramentas reais

Este é o ponto mais sutil e mais importante do coletor — e o que a banca tem mais chance de questionar. Repare na ordem dos comandos dentro de `simulate_port_scan`:

```python
# 1. EXECUTA O NMAP DE VERDADE
result = self.network_tools.run_nmap_port_scan(target_ip, ports)

# 2. INDEPENDENTEMENTE DO RESULTADO, SINTETIZA OS EVENTOS
for index, port in enumerate(ports, start=1):
    payload = EventFactory.tcp_event(
        asset_id=asset["id"],
        source_ip=attacker_ip,
        destination_ip=asset["ip_address"],
        destination_port=port,
    )
    payload["collector_name"] = "nmap"
    payload["raw_summary"] = f"Nmap TCP scan attempt to port {port}"
    response = self.api_client.send_event(payload)
```

### 6.1. A pergunta natural

> "Se o Nmap está sondando a rede de verdade, por que o coletor envia outros 13 eventos para a API ao invés de capturar os pacotes reais que o Nmap gerou?"

A resposta tem três camadas, e dominá-la é o que separa uma defesa sólida de uma defesa fraca.

### 6.2. Camada 1 — O coletor não é um sniffer

O protótipo não usa libpcap/Scapy. Ele não está escutando a interface de rede para capturar pacotes que passam por ela. Para fazer isso, seria necessário:

- abrir um socket em modo promíscuo (raw socket, requer root);
- decodificar cabeçalhos Ethernet/IP/TCP/ICMP em Python;
- montar um buffer com timestamps;
- correlacionar pacotes em flows;
- gerar eventos a partir dos flows.

Tudo isso é trabalho de uma biblioteca como Scapy, e seria escopo equivalente ao próprio TCC. Por isso a decisão arquitetural foi: **a tarefa do coletor é gerar eventos compatíveis com o que um sniffer geraria, e a API do backend é o "contrato" que ambos os mundos respeitam**.

### 6.3. Camada 2 — A execução real serve a três propósitos

Mesmo sendo "decorativa" do ponto de vista da detecção, a chamada real do Nmap/hping3 serve a três propósitos não-triviais:

1. **Realismo demonstrável.** Durante a defesa, você pode rodar `tcpdump -i any 'icmp or port 22'` em outro terminal e mostrar à banca que pacotes reais estão saindo. Isso prova que o sistema dialoga com ferramentas usadas na indústria.
2. **Verificação de ambiente.** A tentativa de execução real funciona como uma sanity check do PATH, das permissões e da conectividade com o alvo. Se algo está errado, o aviso chega imediatamente.
3. **Possível evolução futura.** Em uma versão posterior, o coletor poderia parsear a saída do Nmap (`result.stdout`) e gerar eventos a partir das portas efetivamente abertas — convergindo para um modo "sniffer light".

### 6.4. Camada 3 — O detector é independente do que aconteceu na rede

A regra `PORT_SCAN_SUSPECT` não pergunta "houve um Nmap real?". Ela pergunta "vieram 13 POSTs em `/api/events/` com mesmo `source_ip`, protocol=TCP e portas distintas dentro de 60 segundos?". Essa é a beleza arquitetural: o detector vive no mundo do banco de dados, não no mundo dos pacotes. Qualquer fonte que escreva eventos coerentes — coletor sintético, Scapy real, importação de PCAP, log do firewall — ativa o detector da mesma forma.

### 6.5. Dois fluxos paralelos

Para fixar, lembre-se de que **dois fluxos** acontecem em paralelo durante um cenário:

```
       ┌────────────────────────────────────┐
       │ FLUXO REAL (rede)                  │
       │ Nmap envia pacotes SYN ao alvo     │
       │ -> tráfego visível em tcpdump      │
       │ -> kernel do alvo responde         │
       │ (este fluxo NÃO chega ao backend)  │
       └────────────────────────────────────┘

       ┌────────────────────────────────────┐
       │ FLUXO SINTÉTICO (HTTP)             │
       │ Coletor monta 13 JSON              │
       │ -> POST /api/events/               │
       │ -> backend persiste e analisa      │
       │ -> detector dispara                │
       │ (este fluxo é o que importa para o │
       │  sistema)                          │
       └────────────────────────────────────┘
```

Quem entende essa separação consegue responder a qualquer pergunta da banca sobre o coletor.

---

## 7. O encontro entre o coletor e o detector

Para amarrar coletor e backend, vale revisar como cada cenário encontra a regra correspondente.

### 7.1. ICMP burst → HIGH_ICMP_RATE

```
hping3 --icmp --fast -c 25            (real, no fio)
+ 25 POST /api/events/ com protocol=ICMP, mesmo source_ip
=> regra: > 20 ICMP do mesmo IP em 30s
=> Anomaly(MEDIUM, score=70) + Alert("Alta taxa de ICMP detectada")
```

O coletor manda 25 pacotes em pouco mais de 2 segundos via hping3, e simultaneamente sintetiza 25 eventos com `time.sleep(0.05)` entre eles. Os 25 sintéticos chegam ao backend em ~1,25 segundos. Quando o 21º chega, a regra dispara. Os outros 4 não geram nova anomalia por causa da deduplicação de 60s.

### 7.2. Port scan → PORT_SCAN_SUSPECT

```
nmap -sS (ou -sT) -p 21,22,...,3306 alvo     (real, no fio)
+ 13 POST /api/events/ com protocol=TCP, mesmo source_ip, ports distintas
=> regra: > 10 portas distintas do mesmo IP em 60s
=> Anomaly(HIGH, score=85) + Alert("Suspeita de port scan")
```

A regra é especialmente engenhosa: ela **não conta eventos**, conta **valores distintos** do campo `destination_port`. Um atacante que tentasse 1000 vezes a mesma porta não dispararia esta regra (mas dispararia outra mais específica, se existisse). É exatamente o padrão de Nmap: muitas portas, poucas tentativas por porta.

### 7.3. DNS burst → DNS_QUERY_BURST

```
(sem ferramenta externa)
35 POST /api/events/ com protocol=DNS, mesmo source_ip
=> regra: > 30 DNS do mesmo IP em 60s
=> Anomaly(MEDIUM, score=75) + Alert("Burst de consultas DNS")
```

Não há ferramenta externa para o cenário DNS — apenas eventos sintéticos. Conceitualmente representaria um bot tentando exfiltrar dados via tunneling DNS, ou simplesmente um malware fazendo lookup massivo. É o cenário "puramente sintético" do protótipo, e isso é defensável — DNS tunneling real exigiria infraestrutura (servidor DNS de exfiltração) que extrapola escopo de TCC.

---

## 8. Glossário de defesa

Termos para você usar com fluência durante a apresentação.

**Three-way handshake** — Sequência SYN/SYN-ACK/ACK que estabelece uma conexão TCP. Um SYN scan interrompe esse handshake antes do último ACK.

**Raw socket** — Tipo de socket que permite ao programa construir cabeçalhos IP/TCP manualmente, em vez de delegar ao kernel. Exige privilégio elevado e é a base de Nmap `-sS`, hping3, Scapy e tcpdump.

**Furtividade (stealth)** — Característica de um scan que evita logs de aplicação. SYN scan é stealth porque a conexão nunca completa; Connect scan não é, porque a aplicação alvo "vê" a conexão.

**RFC 1918** — Define faixas privadas: `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`. IPs nessas faixas não são roteados pela internet pública.

**ICMP echo request / reply** — Tipos 8 e 0 do protocolo ICMP. São os pacotes do `ping`.

**Janela deslizante (sliding window)** — Padrão de detecção que avalia eventos dentro de um intervalo de tempo recente que "desliza" com o tempo. Todas as três regras do detector usam janela deslizante.

**Deduplicação** — Mecanismo do `_anomaly_exists` que evita criar múltiplas anomalias do mesmo tipo no mesmo ativo dentro de 60s.

**False positive** — Alerta gerado por evento legítimo que se parece com ataque. O sistema permite marcar manualmente alertas como `FALSE_POSITIVE`, dando insumo para futura calibração.

**Stateless** — Característica do backend: cada request HTTP é independente; o servidor não guarda contexto entre chamadas. JWT é a peça que viabiliza o stateless porque o cliente carrega seu próprio "ticket".

---

## Caminho sugerido de estudo

1. Leia este documento de cabo a rabo uma vez para ter o mapa.
2. Abra `collector/services/network_tools.py` lado a lado e refaça mentalmente o ciclo `_require_tool` → `_run` → `subprocess.run`.
3. Em outro terminal, rode `nmap --help` e identifique cada flag que o protótipo usa.
4. Teste numa VM ou WSL: `nmap -sT -Pn -p 22,80,443 google.com` — observe a saída em texto.
5. Se hping3 estiver disponível (Linux/WSL), rode `sudo hping3 --icmp --fast -c 5 8.8.8.8` (cuidado com alvos que não sejam seus). Observe o tráfego em paralelo com `sudo tcpdump -i any 'icmp'`.
6. Refaça a leitura da seção 6 deste documento — é a que mais costuma render perguntas em banca.
7. Treine em voz alta o caminho completo de um port scan, do `random.random() < 0.2` até o `Alert.objects.create(...)` no Django.

Boa defesa.
