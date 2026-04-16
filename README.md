# Projeto Autocapacita P2 - Versão 2

Backend em FastAPI com LangChain + LangGraph, evoluído para uma arquitetura multiagente real.

Nesta V2, o fluxo deixou de ser um classificador simples e passou para uma orquestração com papéis cognitivos distintos:

- agente planejador
- agente especialista de domínio
- executor determinístico de tool
- agente crítico/revisor
- formatador de resposta final

## Objetivo da V2

Demonstrar um fluxo híbrido robusto onde:

- o LLM decide e planeja
- agentes especializados preparam execução
- ferramentas externas continuam fora do LLM
- um agente crítico avalia consistência do resultado
- a resposta final usa contexto de execução e revisão

## Stack

- FastAPI
- LangChain
- LangGraph
- Azure AI Foundry (Chat Model)
- Pydantic
- Requests
- Pytest

## Arquitetura Multiagente

Fluxo principal:

```text
START
    -> planner_node
    -> route_after_planner
            -> cep_specialist_node
            -> weather_specialist_node
            -> format_response (unknown)
    -> route_after_specialist
            -> execute_tool
            -> format_response (dados insuficientes)
    -> critic_node (sempre apos execute_tool)
    -> format_response
    -> END
```

Observações do fluxo real:

- após execute_tool, o critic_node é sempre executado, inclusive em erros técnicos
- no fluxo weather, se clima falhar e CEP estiver disponível, há fallback para resposta de endereço
- agent_path e agent_timings são preenchidos para observabilidade

### Papéis dos nós

1. planner_node

- classifica intencao: cep, weather, unknown
- define target_agent
- define needs_tool e tool_name
- extrai CEP quando aplicável
- escreve plano no estado

1. especialistas (cep_specialist_node, weather_specialist_node)

- validam parâmetros de domínio
- preparam tool_input
- escrevem specialist_notes

1. execute_tool

- executor puro e determinístico
- lê tool_name + tool_input
- executa API/função externa
- não toma decisão de orquestração

1. critic_node

- analisa tool_result/error
- escreve critic_notes de coerência

1. format_response

- monta mensagem final com intent, resultado, critic_notes e erros
- trata fallback de clima para endereço quando necessário

## Melhorias da V2

- estado compartilhado expandido para multiagente
- roteamento condicional rico após planner e specialist
- observabilidade por request_id, agent_path e agent_timings
- cache em memória de CEP com TTL
- fallback inteligente no fluxo weather (retorna endereço quando clima falha)
- testes unitários e de integração para o grafo

## Estrutura do projeto

```text
app/
    agents/      # Adaptadores entre serviços e modelos
    core/        # Configuração e utilitários
    graph/       # State, nós e montagem do LangGraph
    llm/         # Cliente de LLM e prompts
    models/      # Schemas Pydantic
    routes/      # Endpoints FastAPI
    services/    # Integrações externas e serviço do agente
main.py        # App FastAPI
tests/         # Testes unitários e integração
```

## Endpoints

### Health check

```http
GET /
```

### Consulta de CEP

```http
GET /api/address/{cep}
```

### Consulta de clima por CEP

```http
GET /api/weather?cep=01001000
```

### Chat multiagente

```http
POST /api/agent/chat
Content-Type: application/json
```

Body:

```json
{
    "message": "Como está o clima no CEP 01001000?"
}
```

Exemplo de resposta:

```json
{
    "success": true,
    "intent": "weather",
    "message": "Em Sao Paulo - SP, o clima esta com ...",
    "data": {
        "location": {
            "city": "Sao Paulo",
            "state": "SP"
        },
        "temperature": 20.1,
        "windspeed": 9.2,
        "weathercode": 1,
        "source": "Open-Meteo (https://open-meteo.com)"
    },
    "agent_path": [
        "planner",
        "weather_specialist",
        "tool_executor",
        "critic",
        "formatter"
    ]
}
```

## Variáveis de ambiente

Crie um arquivo .env na raiz:

```env
AZURE_OPENAI_BASE_URL=https://seu-recurso.openai.azure.com/openai/v1
AZURE_OPENAI_API_KEY=sua-chave
AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-4.1

AWESOME_API_BASE_URL=https://cep.awesomeapi.com.br/json
AWESOME_API_TOKEN=seu-token
AWESOME_API_KEY_HEADER=seu-token
```

Notas:

- o endpoint de Azure usa /openai/v1
- o nome do deployment precisa bater com o configurado no Foundry

## Instalação

Windows PowerShell:

```powershell
py -m venv .venv
(Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned) ; (& .venv\Scripts\Activate.ps1)
python -m pip install -e .
python -m pip install -e ".[dev]"
```

## Execução da API

```powershell
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Documentação interativa:

- <http://127.0.0.1:8000/docs>
- <http://127.0.0.1:8000/redoc>

## Testes

Rodar testes principais da V2:

```powershell
python -m pytest tests/test_nodes.py tests/test_graph_integration.py -q
```

Rodar suíte completa do projeto:

```powershell
python -m pytest -q
```

## Integrações externas

1. AwesomeAPI CEP

- endereço, cidade, estado, DDD, latitude e longitude

1. Open-Meteo

- clima atual (temperatura, vento, código meteorológico, período)

## Status da versão

As 12 tarefas planejadas para a evolução multiagente foram implementadas nesta V2.
