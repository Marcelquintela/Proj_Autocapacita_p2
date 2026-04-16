# Projeto Autocapacita P2

Backend em FastAPI com integração de IA generativa usando LangChain e LangGraph.

O projeto implementa um fluxo híbrido em que o LLM interpreta a mensagem do usuário, identifica a intenção e extrai o CEP quando necessário. A partir disso, o grafo segue por ramificações determinísticas para consultar APIs externas e devolver uma resposta estruturada e amigável.

## Objetivo

Demonstrar na prática:

- papel de LangChain na integração com o modelo
- papel de LangGraph na orquestração do fluxo
- diferença entre etapa inteligente e workflow determinístico
- structured output com Pydantic
- integração com APIs externas
- organização em camadas no backend

## Stack

- FastAPI
- LangChain
- LangGraph
- Azure AI Foundry
- Pydantic
- Requests

## Fluxo atual

1. O usuário envia uma mensagem para o endpoint de chat.
2. O nó `classify_intent` usa o LLM para classificar a intenção e extrair o CEP.
3. O grafo decide de forma determinística qual caminho seguir.
4. O nó `execute_tool` consulta a integração externa necessária.
5. O nó `format_response` devolve uma resposta amigável e padronizada.

Fluxo resumido:

```text
START
	↓
classify_intent
	↓
	├── cep      → execute_tool → format_response → END
	├── weather  → execute_tool → format_response → END
	└── unknown  → format_response → END
```

## Estrutura do projeto

```text
app/
	agents/      # Camada de adaptação entre serviços e modelos
	core/        # Configuração e utilitários compartilhados
	graph/       # State, nós e compilação do LangGraph
	llm/         # Cliente LangChain e prompts
	models/      # Schemas Pydantic de entrada, saída e structured output
	routes/      # Endpoints FastAPI
	services/    # Integrações externas e orquestração de aplicação
main.py        # Inicialização da API
```

## Arquitetura por camada

### routes

Recebem a requisição HTTP e delegam para os serviços.

### services

Concentram integração com APIs externas e a ponte entre FastAPI e o grafo.

### graph

Define o estado compartilhado e os nós do fluxo LangGraph.

### llm

Centraliza o cliente do modelo e os prompts usados no fluxo.

### models

Define contratos de entrada e saída da API, além do structured output do classificador.

### agents

Adaptam os dados retornados pelos serviços para os modelos de resposta da aplicação.

## Endpoints

### Health check

```http
GET /
```

Resposta:

```json
{
	"message": "API funcionando!"
}
```

### Consulta de CEP

```http
GET /api/address/{cep}
```

Exemplo:

```http
GET /api/address/01001000
```

### Consulta de clima por CEP

```http
GET /api/weather?cep=01001000
```

### Chat com roteamento inteligente

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

Resposta esperada:

```json
{
	"intent": "weather",
	"message": "Em São Paulo - SP, o clima está com predominantemente limpo durante a noite, temperatura de 20.1°C e vento de 9.2 km/h. (Fonte: Open-Meteo (https://open-meteo.com))",
	"data": {
		"location": {
			"city": "São Paulo",
			"state": "SP"
		},
		"time": "2026-04-15T22:45",
		"interval": 900,
		"temperature": 20.1,
		"windspeed": 9.2,
		"winddirection": 138,
		"is_day": 0,
		"weathercode": 1,
		"source": "Open-Meteo (https://open-meteo.com)"
	}
}
```

## Variáveis de ambiente

O projeto usa um arquivo `.env` na raiz.

Exemplo:

```env
AZURE_OPENAI_BASE_URL=https://seu-recurso.openai.azure.com/openai/v1
AZURE_OPENAI_API_KEY=sua-chave
AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-4.1

AWESOME_API_BASE_URL=https://cep.awesomeapi.com.br/json
AWESOME_API_TOKEN=seu-token
AWESOME_API_KEY_HEADER=seu-token
```

Observação:

- para Azure AI Foundry, o projeto usa a API unificada `/openai/v1`
- o nome do deployment deve ser exatamente o nome configurado no Foundry

## Instalação

Crie e ative um ambiente virtual:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Instale as dependências principais:

```powershell
pip install -e .
```

Instale também as dependências de desenvolvimento:

```powershell
pip install -e ".[dev]"
```

## Execução

Suba a API com Uvicorn:

```powershell
uvicorn main:app --reload
```

Swagger UI:

```text
http://localhost:8000/docs
```

## Teste rápido do modelo

```powershell
python -c "from app.llm.client import get_chat_model; m=get_chat_model(); r=m.invoke('qual a capital do Brasil?'); print(r.content)"
```

## Integrações externas

### AwesomeAPI CEP

Usada para obter:

- endereço
- cidade
- estado
- DDD
- latitude
- longitude

### Open-Meteo

Usada para obter:

- temperatura atual
- velocidade do vento
- direção do vento
- código meteorológico
- período do dia

## O que já está implementado

- cliente LangChain conectado ao Azure AI Foundry
- classificação de intenção com structured output
- extração de CEP via LLM
- roteamento determinístico no LangGraph
- integração com CEP e clima
- resposta estruturada no endpoint de chat
- logs básicos de execução

## Próximos passos possíveis

- mover a formatação final da resposta para um nó com LLM
- padronizar modelos de erro entre integrações
- adicionar testes automatizados para os nós do grafo
- desacoplar formatadores de saída em uma camada própria