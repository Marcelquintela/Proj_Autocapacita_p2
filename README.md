# Papel de cada parte

- routes/agent_router.py

Recebe requisição HTTP e delega.

- services/agent_service.py

Faz a ponte entre FastAPI e LangGraph.

- graph/state.py

Define o estado compartilhado do fluxo.

- graph/nodes.py

Contém os nós:

interpretar pedido;
decidir tool;
chamar integração;
formatar saída.

- llm/client.py

Cria o modelo via LangChain.

- llm/tools.py

Expõe funções determinísticas como tools.

- services/external_api_service.py

Faz chamadas externas reais com requests ou httpx.