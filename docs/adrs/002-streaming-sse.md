# ADR-002: Padrão de Comunicação de Baixa Latência (Streaming)
**Data:** [Data de Hoje]
**Status:** Aceito

## Contexto
A experiência da revendedora no chat depende de percepção de baixa latência. Esperar que o LLM processe toda a resposta, após consultar o RAG e as Tools, gera bloqueios indesejados e prejudica a UX, tornando essencial o retorno progressivo da resposta[cite: 2].

## Decisão
Implementaremos **Server-Sent Events (SSE)** através da classe `StreamingResponse` do FastAPI[cite: 1, 2]. O orquestrador LangGraph será consumido via `.astream_events()`, filtrando eventos internos de roteamento e repassando exclusivamente os tokens finais de texto no formato `data: {chunk}\n\n`.

## Consequências
*   **Positivas:** O SSE é unidirecional (Servidor -> Cliente), sendo mais leve que WebSockets e perfeitamente adequado para geração de texto de LLMs. Facilita o balanceamento de carga em um API Gateway no cenário de 500 mil usuários[cite: 2].
*   **Negativas:** SSE puro não lida nativamente com desconexões bidirecionais complexas, o que exigirá que o frontend envie a intenção em requisições POST separadas da via de leitura.