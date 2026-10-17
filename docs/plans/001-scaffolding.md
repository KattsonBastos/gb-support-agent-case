# Plano de Execução Arquitetural: MVP Agente de Suporte à Revendedora GB

**Projeto:** Plataforma Agentes GB — Agente de Suporte à Revendedora  
**Papel:** Arquiteto de Software  
**Documentos de Referência:** 
- [01-requisitos-e-contexto.md](file:///home/kattson/Documents/case-gb-spec-2/gb-support-agent-case/docs/specs/01-requisitos-e-contexto.md)
- [03-api-e-streaming.md](file:///home/kattson/Documents/case-gb-spec-2/gb-support-agent-case/docs/specs/03-api-e-streaming.md)
- [guardrails.md](file:///home/kattson/Documents/case-gb-spec-2/gb-support-agent-case/.agents/rules/guardrails.md)

---

## 1. Visão Arquitetural do MVP

O sistema é desenhado como um **Motor Transacional Cognitivo** desacoplado em camadas claras de responsabilidade:

1. **Camada de Entrada / API (FastAPI):**
   - Recepção de requisições autenticadas/identificadas via `POST /api/v1/chat/stream`.
   - Validação estrita de contratos de dados com Pydantic v2 (isolamento por `session_id` e validação algorítmica de `cpf`).
   - Resposta reativa e assíncrona via **Server-Sent Events (SSE)** (`text/event-stream`) para baixa latência percebida.

2. **Camada de Raciocínio / Orquestração (LangGraph):**
   - Padrão **ReAct com Agentic RAG**.
   - Nó central orquestrador avalia intenção e aciona Tools ou responde diretamente.
   - Isolamento estrito de memória e contexto por sessão (`session_id` / `thread_id`) com Checkpointer nativo.

3. **Camada de Guardrails & Segurança (Defesa em Profundidade):**
   - **Regra 1 - Zero Vazamento de PII:** Amarração mandatória do CPF da sessão nas Tools de pedidos. Nenhum CPF consulta pedidos de outro CPF.
   - **Regra 2 - Sigilo Comercial:** Bloqueio cognitivo no System Prompt e validação de saída impedindo cálculos ou palpites sobre margens de lucro de outras revendedoras.
   - **Regra 3 - Resposta SSE Nativa:** Todos os fluxos de chat retornam chunks padronizados `data: {"chunk": "..."}\n\n`.

4. **Camada de Dados & Ferramentas (RAG e Mock APIs):**
   - RAG local com ChromaDB e embeddings `all-MiniLM-L6-v2` para catálogo do Ciclo 15.
   - Tool `buscar_status_pedido` com banco em memória simulando ERP/Logística do GB.

---

## 2. Estrutura de Pastas Proposta

```text
gb-support-agent-case/
├── .agents/
│   └── rules/
│       └── guardrails.md           # Guardrails globais invioláveis
├── docs/                           # Especificações, ADRs e C4 Models
│   ├── specs/
│   ├── adrs/
│   └── c4-model/
├── data/
│   └── catalogo_ciclo_15.md       # Catálogo sintético do Ciclo 15 (Boticário & Eudora)
├── frontend/                       # Interface de simulação do chat
│   └── app.py
├── src/
│   ├── __init__.py
│   ├── main.py                     # App FastAPI, CORS, lifespans e inclusão de routers
│   ├── api/                        # Camada de Apresentação e Transporte HTTP
│   │   ├── __init__.py
│   │   ├── routes.py               # Endpoint POST /api/v1/chat/stream (SSE)
│   │   └── schemas.py              # Schemas Pydantic com validação de CPF e session_id
│   ├── agent/                      # Motor Cognitivo LangGraph
│   │   ├── __init__.py
│   │   ├── state.py                # AgentState (TypedDict com histórico, CPF e contexto)
│   │   ├── graph.py                # Montagem e compilação do StateGraph + Checkpointer
│   │   ├── nodes.py                # Nós de orquestração, RAG e API
│   │   ├── edges.py                # Arestas condicionais (should_continue)
│   │   └── prompts.py              # System prompts com diretivas de PII e Sigilo Comercial
│   ├── core/                       # Configurações Globais e Segurança
│   │   ├── __init__.py
│   │   ├── config.py               # Settings (Pydantic Settings / .env)
│   │   └── guardrails.py           # Funções determinísticas de validação de CPF e PII
│   ├── rag/                        # Pipeline de RAG
│   │   ├── __init__.py
│   │   ├── ingestion.py            # Script/loader do catalogo_ciclo_15.md
│   │   └── retriever.py            # Vector Store local (ChromaDB) e embeddings
│   └── tools/                      # Ferramentas Transacionais
│       ├── __init__.py
│       ├── order_status.py         # buscar_status_pedido(cpf, id_pedido)
│       ├── catalog.py              # consultar_catalogo(query)
│       └── mock_db.py              # Base simulada de pedidos com validação de titularidade
├── tests/                          # Suíte de Testes Automatizados
│   ├── test_api.py                 # Testes de rota SSE e validações de input
│   ├── test_guardrails.py          # Testes de PII e proteção de CPF
│   └── test_agent.py               # Testes do grafo LangGraph
├── pyproject.toml                  # Dependências gerenciadas via uv/pip
└── README.md
```

---

## 3. Especificação dos Componentes Imediatos (Fase 1)

### 3.1. `src/api/schemas.py`
Contratos Pydantic v2 com validações rigorosas de segurança:

- **`ChatRequest`:**
  - `session_id: str`: Campo obrigatório. Não pode ser vazio ou conter apenas espaços em branco. Mínimo de 3 caracteres (suporta UUIDs e slugs de sessão).
  - `message: str`: Campo obrigatório. Mensagem da revendedora (`min_length=1`, `max_length=2000`). Sanitizada contra caracteres de controle abusivos.
  - `cpf: Optional[str]`: Opcional no payload geral, mas quando presente:
    - Normalização automática (remove `.`, `-` e espaços).
    - Validação de 11 dígitos numéricos.
    - Rejeição de sequências óbvias repetidas (`111.111.111-11`, etc.).
    - Validação matemática dos dois dígitos verificadores (DV1 e DV2) segundo a regra da Receita Federal.
- **`ChatChunkResponse`:**
  - `chunk: str`: Fragmento de texto gerado para streaming.
- **`ErrorResponse`:**
  - `detail: str`: Mensagem padronizada de erro.
  - `code: str`: Código interno de erro (ex: `INVALID_CPF`, `GUARDRAIL_VIOLATION`).

### 3.2. `src/api/routes.py`
Implementação do endpoint assíncrono de streaming:

- **Endpoint:** `POST /api/v1/chat/stream`
- **Headers:** `media_type="text/event-stream"`, `Cache-Control: "no-cache"`, `X-Accel-Buffering: "no"`
- **Mecanismo Mock Inicial:**
  - Gerador assíncrono `mock_event_streamer(request: ChatRequest)`:
    - Realiza yield de chunks SSE no padrão `data: {"chunk": "..."}\n\n`.
    - Emite a frase *"Teste de streaming SSE"* palavra por palavra com intervalo de 0.5s entre cada emissão.
    - Finaliza com evento limpo de encerramento (`data: {"chunk": "", "done": true}\n\n`).
  - Tratamento de exceções e desconexão prematura do cliente sem vazamento de recursos.

---

## 4. Roteiro de Implementação Pós-Aprovação

1. **Etapa 1 (Imediata):**
   - Criação dos arquivos `src/api/schemas.py` e `src/api/routes.py`.
   - Criação de `src/main.py` com o app FastAPI integrado e CORS configurado.
   - Criação de `__init__.py` nos diretórios para estabelecer os módulos Python.
   - Validação da rota executando teste de requisição HTTP e parsing do SSE.

2. **Etapa 2 (Tools & RAG):**
   - Criação de `data/catalogo_ciclo_15.md` e `src/tools/order_status.py` com `mock_db.py`.
   - Configuração do retriever com ChromaDB em `src/rag/retriever.py`.

3. **Etapa 3 (Motor LangGraph):**
   - Definição de `AgentState`, nós ReAct, arestas condicionais e injeção do System Prompt com Guardrails.

4. **Etapa 4 (Conexão do Streaming Real):**
   - Conexão do endpoint `POST /api/v1/chat/stream` com `graph.astream_events()`, filtrando nós internos e transmitindo apenas tokens gerados pelo LLM.
