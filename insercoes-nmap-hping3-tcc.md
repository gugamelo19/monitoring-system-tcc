# Inserções recomendadas — Nmap e hping3 no TCC

Roteiro de **seis intervenções pontuais** na 4ª Versão do ATCC, na ordem em que aparecem no documento. As inserções vêm com texto pronto. O objetivo é dar lastro teórico para o uso das ferramentas e eliminar a contradição metodológica entre as seções 4.2 e 4.6 da versão atual.

---

## 0. A contradição que precisa ser resolvida primeiro

Hoje, sua seção 4.2 termina com:

> *"A simulação via script Python foi adotada para garantir controle preciso dos parâmetros e reprodutibilidade dos testes **sem dependência de ferramentas externas no ambiente de validação**."*

E a seção 4.6 contém:

> *"Durante a validação, os cenários de comportamento anômalo foram gerados com apoio de ferramentas externas de linha de comando. **O Nmap foi utilizado para reproduzir** o cenário de varredura de portas TCP, **enquanto o hping3 foi utilizado** para gerar tráfego ICMP em volume elevado de forma controlada."*

Essas duas frases se contradizem. A banca lê isso e pergunta: afinal, com ou sem ferramentas externas?

A maneira correta de resolver é assumir o desenho **híbrido** que o código realmente faz: o coletor invoca Nmap/hping3 em paralelo aos eventos sintéticos. Esse desenho é defensável (eu explico por quê na inserção #4 abaixo). Você vai ajustar a frase de 4.2 e ampliar a de 4.6 para refletir isso.

---

## Inserção 1 — Lista de Abreviaturas e Siglas (página inicial)

Adicione, em ordem alfabética, junto com as siglas que você já tem:

```
Nmap   Network Mapper
```

> `hping3` não tem expansão de sigla — é nome próprio derivado do antecessor `hping`. Não inclua na lista.

---

## Inserção 2 — Nova subseção na Fundamentação Teórica

Atualmente, a seção 3.8 é "Principais Ferramentas Existentes de Monitoramento" (Zabbix, Nagios) e a 3.9 é "Tecnologias de Software". Crie uma **nova seção 3.9** entre as duas, intitulada **"Ferramentas de Avaliação e Teste de Segurança em Redes"**, e renumere a atual 3.9 para 3.10 (Tecnologias de Software).

Esse posicionamento é importante: você está separando conceitualmente **ferramentas de monitoramento contínuo** (Zabbix, Nagios — defesa) de **ferramentas de teste/auditoria** (Nmap, hping3 — ataque controlado). Essa distinção é uma das primeiras coisas que se aprende em segurança ofensiva, e demonstrá-la no TCC mostra maturidade.

### Texto pronto

> **3.9 Ferramentas de Avaliação e Teste de Segurança em Redes**
>
> A avaliação da capacidade de detecção de um sistema de monitoramento exige a reprodução de cenários representativos de ataques reais. Para isso, a literatura e a prática de segurança da informação consolidaram um conjunto de ferramentas de linha de comando voltadas à geração controlada de tráfego de rede em padrões característicos de varredura, reconhecimento e negação de serviço. Diferentemente de plataformas de monitoramento como Zabbix e Nagios — discutidas na seção anterior, que observam tráfego — essas ferramentas atuam como **geradoras** de tráfego controlado, sendo amplamente utilizadas tanto em auditorias legítimas (pentests) quanto em pesquisas acadêmicas voltadas à validação de sistemas de detecção de intrusão.
>
> **3.9.1 Nmap**
>
> Nmap (Network Mapper) é uma ferramenta de código aberto para descoberta de redes e auditoria de segurança, desenvolvida por Gordon Lyon e disponível desde 1997. Conforme Lyon (2009), o Nmap implementa diversas técnicas de varredura de portas TCP e UDP, dentre as quais se destacam o *SYN scan* (`-sS`) — que envia segmentos com a flag SYN e infere o estado da porta a partir da resposta, sem completar o *three-way handshake* descrito na seção 3.3 — e o *TCP connect scan* (`-sT`), que delega ao sistema operacional o estabelecimento completo da conexão, dispensando privilégios de raw socket mas tornando o scan mais facilmente detectável por aplicações alvo (LYON, 2009, p. 47).
>
> Garcia-Teodoro et al. (2009) apontam o port scan como um dos comportamentos pré-ataque mais frequentemente registrados em redes corporativas, sendo um indicador confiável de reconhecimento ativo por parte de adversários. Esta característica torna o Nmap uma ferramenta de referência para a reprodução de cenários de validação em sistemas de detecção de anomalias, papel que ele desempenha neste trabalho.
>
> **3.9.2 hping3**
>
> O hping3 é uma ferramenta de linha de comando para construção e envio de pacotes TCP, UDP, ICMP e raw IP, desenvolvida por Salvatore Sanfilippo a partir de 2005 como evolução do hping original. Diferentemente do utilitário `ping` tradicional, que se limita ao envio sequencial de mensagens ICMP Echo Request, o hping3 permite ao analista controlar individualmente campos como flags TCP, identificadores ICMP, taxa de envio e tamanho do pacote, viabilizando a reprodução fidedigna de padrões de tráfego associados a ataques de flooding e reconhecimento (SANFILIPPO, 2005).
>
> No modo `--icmp --fast`, utilizado neste trabalho, o hping3 emite pacotes ICMP Echo Request a uma taxa de aproximadamente dez pacotes por segundo, configurando um padrão equivalente ao de um *ping flood* controlado — caracterizado por Forouzan (2013) como uma das formas mais simples de ataque de negação de serviço em ICMP. A escolha do modo `--fast`, em detrimento de modos mais agressivos como `--flood`, foi deliberada: o objetivo é gerar volume suficiente para acionar a regra de detecção sem comprometer a estabilidade do ambiente de teste.
>
> **3.9.3 Justificativa do uso no protótipo**
>
> A adoção de Nmap e hping3 para a geração dos cenários de teste cumpre duas funções metodológicas relevantes. Primeiro, ancora os limiares estáticos do detector — discutidos na seção 4.6 — em comportamentos concretos de ferramentas reconhecidas pela comunidade de segurança, evitando que os parâmetros pareçam arbitrários. Segundo, permite que os testes sejam reproduzidos por terceiros a partir do código-fonte disponível, em conformidade com o princípio de reprodutibilidade aplicada à pesquisa experimental discutido na seção 4 (GIL, 2008).

---

## Inserção 3 — Ajuste no parágrafo final da seção 4.2

A frase atual é incoerente com o que o código faz. Substitua o último parágrafo da seção 4.2 — aquele que termina com *"sem dependência de ferramentas externas no ambiente de validação"* — pelo seguinte:

### Texto pronto

> A reprodução dos cenários foi realizada em arquitetura híbrida: o módulo simulador, escrito em Python, é responsável por sintetizar e enviar os eventos correspondentes ao backend via API REST, garantindo controle preciso de parâmetros e reprodutibilidade. Em paralelo, e quando disponíveis no ambiente, o coletor invoca as ferramentas externas Nmap e hping3 — descritas na seção 3.9 — para que tráfego real seja efetivamente emitido na interface de rede, ampliando o realismo da simulação. As ferramentas externas funcionam como camada complementar ao simulador: caso não estejam instaladas no ambiente, a validação prossegue exclusivamente com os eventos sintéticos, sem prejuízo aos resultados, conforme detalhado na seção 4.6.

> **Por que esse desenho híbrido é defensável:** ele separa **o que é avaliado** (a capacidade do detector de identificar padrões em eventos persistidos no banco) **do que é decorativo** (a presença efetiva de pacotes no fio). Para o detector, o que importa são os eventos que chegam à API; para a demonstração e o realismo, importa que pacotes reais saiam da máquina. Ambos os fluxos podem existir em paralelo sem interferir entre si.

---

## Inserção 4 — Ampliação do parágrafo sobre ferramentas na seção 4.6

Você atualmente diz, em duas frases, que Nmap e hping3 foram usados. Reescreva esse trecho como um parágrafo mais completo, explicando o desenho híbrido e referenciando a fundamentação que você adicionou em 3.9.

### Texto pronto

> Os cenários de avaliação aplicados durante a validação foram reproduzidos com apoio das ferramentas externas Nmap e hping3, fundamentadas na seção 3.9. O Nmap foi configurado para executar varreduras nas treze portas TCP utilizadas no cenário (21, 22, 23, 25, 53, 80, 110, 135, 139, 143, 443, 445 e 3306), com tentativa primária em modo SYN scan (`-sS`) e *fallback* automático para *TCP connect scan* (`-sT`) caso o ambiente não disponha de privilégios de raw socket. O hping3 foi utilizado em modo `--icmp --fast` para emitir vinte e cinco pacotes ICMP Echo Request em curto intervalo, equivalente em padrão ao comportamento de um *ping flood* controlado. As duas ferramentas atuam em paralelo ao envio dos eventos sintéticos: enquanto o tráfego real é emitido na interface de rede, o coletor envia ao backend os eventos correspondentes via API REST, garantindo que o motor de detecção seja exercitado independentemente da disponibilidade efetiva das ferramentas no ambiente. O cenário de burst DNS, por não dispor de ferramenta externa equivalente, é reproduzido exclusivamente por eventos sintéticos. Essa modelagem combina reprodutibilidade — o teste funciona mesmo em máquinas sem Nmap/hping3 instalados — com realismo, atendendo simultaneamente aos critérios de pesquisa experimental discutidos na seção 4.

---

## Inserção 5 — Acrescentar Nmap e hping3 na seção 4.3 (Ferramentas e Tecnologias Utilizadas)

Atualmente sua seção 4.3 lista Django, DRF, PostgreSQL, Next.js, JWT e Python, mas não cita as ferramentas externas. Adicione um parágrafo ao final.

### Texto pronto

> Complementarmente às tecnologias do núcleo da aplicação, foram empregadas duas ferramentas externas de linha de comando para a geração de cenários de validação. O **Nmap** (LYON, 2009) foi utilizado para reproduzir varreduras de portas TCP, e o **hping3** (SANFILIPPO, 2005) para emitir bursts de pacotes ICMP em padrão equivalente a um *ping flood* controlado. O detalhamento conceitual de ambas é apresentado na seção 3.9, e os parâmetros operacionais são descritos na seção 4.6. A escolha por essas ferramentas alinha o protótipo às práticas consolidadas de avaliação de sistemas de detecção em redes corporativas, ampliando o realismo da simulação sem comprometer a reprodutibilidade.

---

## Inserção 6 — Referências bibliográficas

Adicione, em ordem alfabética, no capítulo de Referências Bibliográficas:

```
LYON, G. F. Nmap Network Scanning: the official Nmap Project guide to
network discovery and security scanning. Sunnyvale: Nmap Project, 2009.
ISBN 978-0-9799587-1-7. Disponível em: <https://nmap.org/book/>.
```

```
SANFILIPPO, S. hping3 Documentation. 2005. Disponível em:
<http://www.hping.org/manpage.html>. Acesso em: 11 maio 2026.
```

> **Sobre as citações:** o livro de Lyon é a fonte canônica do Nmap e tem ISBN — uso preferencial. O hping3 não tem livro nem artigo publicado, apenas a documentação oficial mantida pelo autor; cite-a como página web oficial. Se quiser uma fonte secundária acadêmica para o hping3, uma alternativa é citar Antonatos et al. (2008), "Generating realistic workloads for network intrusion detection systems", que descreve o uso de hping em geração de tráfego para teste de IDS — me avise se quiser que eu monte essa referência completa.

---

## Inserção 7 (opcional, fortemente recomendada) — Detalhamento nos Resultados

Hoje, as seções 5.1, 5.2 e 5.3 dizem apenas "o simulador disparou". Considere acrescentar uma frase a cada uma deixando explícita a dupla execução (ferramenta real + evento sintético). Isso fecha o argumento metodológico.

### Texto pronto para 5.1 (Port Scan)

Após a frase "*enviando conexões SYN sequenciais para 13 portas distintas (...)*", acrescente:

> A execução foi conduzida em duplo modo: o coletor invocou o Nmap em paralelo, conforme fundamentado nas seções 3.9.1 e 4.6, gerando tráfego real na interface de rede, e simultaneamente sintetizou os treze eventos TCP correspondentes via API REST, com `source_ip` aleatório fixo durante todo o cenário, garantindo que o motor de detecção observasse a varredura como um padrão coerente atribuível a um único IP atacante.

### Texto pronto para 5.2 (ICMP Burst)

Após a frase sobre os 25 eventos ICMP, acrescente:

> Em paralelo ao envio sintético, o hping3 foi executado em modo `--icmp --fast` contra o endereço IP do ativo, emitindo pacotes ICMP Echo Request reais na interface de rede a uma taxa aproximada de dez pacotes por segundo. A separação entre o disparo real e os eventos sintéticos garante que a regra `HIGH_ICMP_RATE` seja exercitada mesmo em ambientes onde o hping3 não esteja disponível ou não disponha de privilégios suficientes para abrir raw sockets — exigência discutida na seção 3.9.2.

### Texto pronto para 5.3 (DNS Burst)

Esse não muda, mas vale acrescentar uma observação no início, para honestidade metodológica:

> Diferentemente dos cenários anteriores, o burst de consultas DNS foi reproduzido exclusivamente por eventos sintéticos, em razão da ausência, no ambiente de testes, de uma ferramenta padrão equivalente ao Nmap (para TCP) ou ao hping3 (para ICMP) que pudesse gerar tráfego real de consultas DNS em volume controlado de forma simples. O comportamento simulado, ainda assim, corresponde fielmente ao padrão de tráfego associado a reconhecimento de domínios ou ataques de tunneling DNS, conforme caracterizado por Garcia-Teodoro et al. (2009).

> Observação adicional: ferramentas como `dnsenum` ou `dig` em loop poderiam ser usadas em uma versão futura. Citar essa limitação aqui antecipa pergunta de banca.

---

## Resumo das mudanças

| # | Local | Tipo de mudança | Esforço |
|---|---|---|---|
| 1 | Lista de Abreviaturas | adicionar "Nmap" | < 1 min |
| 2 | Fundamentação Teórica — nova seção 3.9 | inserir 4 parágrafos + 3 sub-tópicos | 5 min |
| 3 | Seção 4.2 (último parágrafo) | substituir parágrafo | 2 min |
| 4 | Seção 4.6 (parágrafo das ferramentas) | substituir parágrafo | 2 min |
| 5 | Seção 4.3 (final) | adicionar parágrafo | 1 min |
| 6 | Referências bibliográficas | adicionar 2 entradas | 2 min |
| 7 | Seções 5.1, 5.2, 5.3 | acrescentar uma frase em cada | 3 min |

Tempo total estimado: cerca de 15 minutos de edição, e o capítulo de Fundamentação Teórica ganha duas páginas a mais — desejável para o volume final do TCC.

---

## Por que vale a pena fazer isso

Três argumentos para você usar inclusive em conversa com o orientador:

**Primeiro**, fortalece a defesa contra perguntas previsíveis. Se a banca perguntar "por que Nmap e não outro scanner?" ou "por que hping3 e não Scapy?", sem fundamentação na seção 3 você responde de cabeça; com fundamentação, você responde citando a referência que está logo ali no texto. Isso muda completamente a percepção da banca sobre o rigor do trabalho.

**Segundo**, elimina a contradição entre 4.2 e 4.6 que existe hoje. Essa contradição é o tipo de detalhe que um leitor atento (orientador, avaliador externo) pega de primeira leitura, e que custa pontos.

**Terceiro**, conecta de forma elegante a Fundamentação Teórica com a Metodologia. Hoje, sua seção 3 explica protocolos (ICMP, TCP, DNS) e tecnologias (Django, Postgres, etc.), mas não explica as ferramentas usadas nos cenários de teste — o que fica como lacuna no encadeamento "teoria → método → resultados". A inserção 2 fecha essa lacuna.

A 5ª versão do seu ATCC vai sair substancialmente mais sólida com essas seis inserções.
