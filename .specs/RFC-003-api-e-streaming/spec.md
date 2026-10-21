# API, Streaming & Integração
**Projeto:** Agente de Suporte à Revendedora (Plataforma Agentes GB)
**Arquivo:** `.specs/RFC-003-api-e-streaming/spec.md`
**Propósito:** Definir os contratos de entrada/saída do FastAPI e detalhar o comportamento do Server-Sent Events (SSE) acoplado ao LangGraph.

## 1. Stack Tecnológica e Endpoints
*   **Framework:** FastAPI.
*   **Servidor ASGI:** Uvicorn.
*   **Endpoint de Chat:** `POST /api/v1/chat/stream`

## 2. Contratos de Dados (Pydantic Schemas)
A validação de entrada deve garantir o isolamento da sessão exigido pelo negócio.

```python
class ChatRequest(BaseModel):
    session_id: str = Field(..., description="Identificador único da revendedora para manter contexto.")
    message: str = Field(..., description="Mensagem ou intenção enviada pela revendedora.")
    cpf: Optional[str] = Field(None, description="Opcional. CPF da revendedora ativa na sessão para uso nas Tools.")
```

## 3. Comportamento do Streaming (SSE)
Para garantir percepção de baixa latência ao usuário final, a resposta da API não deve aguardar a geração completa do texto.

*   **Padrão de Resposta:** `StreamingResponse` do FastAPI com `media_type="text/event-stream"`.
*   **Formato do Chunk:** Cada pedaço de texto extraído do LLM deve ser formatado estritamente no padrão SSE.
    ```text
    data: {"chunk": "Olá"}
    
    data: {"chunk": " Revendedora"}
    
    ```
*   **Integração LangGraph:** O endpoint deve invocar o grafo utilizando o método assíncrono `.astream_events(version="v1")` ou capturando apenas os nós do LLM. É imperativo filtrar os eventos internos de roteamento do LangGraph, devolvendo via fluxo de rede (`yield`) apenas os tokens finais de texto destinados à interface de chat.

## 4. Tratamento de Erros e Timeout
*   **Timeout:** Se o RAG ou as Tools demorarem mais que um limiar aceitável, o gerador deve emitir um chunk de erro padronizado antes de encerrar o stream.
*   **Circuit Breaker (Proteção):** Se a invocação exceder o limite de *tool calls* recursivos no grafo, retornar via `HTTPException`.