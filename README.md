## Sistema Inteligente de Monitoramento de Infraestrutura de TI

Projeto desenvolvido como Trabalho de Conclusão de Curso (TCC) com o objetivo de monitorar ativos de rede, coletar eventos, detectar anomalias de protocolo e gerar alertas para identificação de possíveis ameaças.

---

## Visão Geral

O sistema realiza:

- Monitoramento contínuo de ativos de TI
- Coleta de eventos de rede (TCP, ICMP, DNS)
- Detecção de comportamentos anômalos
- Geração e gerenciamento de alertas
- Visualização em dashboard interativo

---

## Arquitetura do Sistema

```bash
[ Coletor / Simulador ]
           ↓
[ API Backend - Django ]
           ↓
[ Banco de Dados - PostgreSQL ]
           ↓
[ Dashboard - Next.js ]
```

## Tecnologias Utilizadas

BACKEND

- Python 
- Django
- Django REST Framework 
- Postgres

FRONTEND
- Next.js
- React
- Typescript
- Tailwind CSS

OUTROS 
- JWT (Autenticação)
- Git e GitHub
- Simulador de eventos de rede

## Funcionalidades

DASHBOARD
- Visão geral dos ativos
- Indicadores de status (online/offline)
- Gráficos de protocolos e severidade

ALERTAS
- Listagem de alertas
- Classificação por severidade
- Atualização de status:
- OPEN
- IN_PROGRESS
- RESOLVED
- FALSE_POSITIVE
- Filtros por status e severidade

EVENTOS DE REDE
- Visualização detalhada de eventos
- Protocolos suportados:
- TCP
- ICMP
- DNS
- Filtros por protocolo

ATIVOS
- Inventário de ativos monitorados
- Status operacional
- Tipo e localização
- Filtro por status e tipo

## Estrutura do projeto

backend/
  ├── apps/
  │   ├── accounts/
  │   ├── assets/
  │   ├── events/
  │   ├── alerts/
  │   └── dashboard/
  └── manage.py

frontend/
  ├── src/
  │   ├── app/
  │   ├── components/
  │   ├── lib/
  │   └── types/

collector/
  └── simulador de eventos

## Como executar o projeto

## BACKEND
- Acessar pasta
cd backend

- Criar ambiente virtual 
python -m venv venv

- Ativar ambiente 
venv\Scripts\activate  - Windows
source venv/bin/activate - Linux/Mac

- Instalar Dependências
pip install -r requirements.txt

- Rodar migrações
python manage.py migrate

- Criar superusuário
python manage.py createsuperuser

- Rodar servidor
python manage.py runserver


## FRONTEND
- Acessar pasta
cd frontend

- Rodar servidor
npm run dev


## COLLECTOR
- Acessar pasta
cd collector 

- Instalar dependências
npm install

- Rodar servidor 
python main.py



## Objetivo do Projeto

Este projeto tem como objetivo demonstrar a viabilidade de um sistema inteligente capaz de:
	•	Monitorar infraestrutura de TI em tempo real
	•	Identificar padrões anômalos de tráfego
	•	Auxiliar na detecção de ameaças
	•	Fornecer suporte à tomada de decisão operacional


## Prints do Sistema

### Dashboard
![Dashboard] (docs/dashboard.png)

### Alertas
![Alertas] (docs/alerts.png)

### Eventos
![Eventos] (docs/events.png)

### Ativos
![Ativos] (docs/assets.png)
