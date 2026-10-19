# Constituição do Projeto
**Repositório:** gb-support-agent-case — Plataforma Agentes GB (Agente de Suporte à Revendedora)
**Última Atualização:** 2026-10-19

> Este documento é a fonte de verdade para decisões técnicas transversais. Todo `plan.md`, `tasks.md` e implementação deve obedecê-lo. Em caso de conflito, a ordem de precedência é: **Guardrails (Seção 2) > Constituição > RFC (`spec.md`/`plan.md`)**.

## 1. Stack Tecnológica e Bibliotecas Principais
- **Linguagem:** Python 3.11 (imagem base `python:3.11-slim`).
- **API:** FastAPI + Uvicorn (ASGI). Rotas assíncronas (`async def`).
- **Contratos e Configuração:** Pydantic v2 (`BaseModel`, `field_validator`, `ConfigDict`) e `pydantic-settings` (`Settings` lido de `.env`).
- **Orquestração Cognitiva:** LangGraph (`StateGraph`, checkpointer) + `langchain-core` (mensagens, `@tool`, `BaseChatModel`).
- **LLM:** Google Gemini via `langchain-google-genai` (modelo padrão `gemini-2.5-flash`). Sem chave de API, usar obrigatoriamente o `MockGeminiLLM`.
- **RAG:** ChromaDB persistente local + embeddings `all-MiniLM-L6-v2` (sentence-transformers) + `langchain-text-splitters`.
- **Frontend de Simulação:** Streamlit + `requests` (pasta `frontend/`, dependências isoladas em `frontend/requirements.txt`).
- **Observabilidade:** LangFuse self-hosted, SDK `langfuse>=2.50,<3.0` (major alinhada à imagem `langfuse/langfuse:2`).
- **Infraestrutura:** Docker + `docker-compose` na rede `agentes-network`.
- **Dependências:** declaradas em `requirements.txt` com versão mínima; fixar teto de major (`<X.0`) quando houver quebra conhecida de API.
- Novas bibliotecas só podem ser adicionadas se justificadas no `plan.md` da RFC correspondente.

## 2. Guardrails Invioláveis (Segurança e Conformidade)
Espelham `.agents/rules/guardrails.md` e se aplicam a todo código gerado:
1. **Zero Vazamento de PII:** nenhum CPF pode acessar pedidos de outro CPF. O CPF da sessão (`state["cpf"]`) **sempre sobrescreve** o CPF gerado pelo LLM antes de invocar Tools transacionais, e a Tool deve validar a titularidade de forma determinística. Respostas de acesso negado não podem conter nenhum dado do pedido ou da titular.
2. **Sigilo Comercial:** o agente não pode calcular, estimar ou fornecer margens de lucro, ganhos ou faturamento de outras revendedoras. A proibição deve constar no System Prompt e ser coberta por teste.
3. **SSE Nativo:** toda rota de chat responde com `StreamingResponse` (`text/event-stream`), chunks no formato `data: {"chunk": "..."}\n\n` e headers `Cache-Control: no-cache` e `X-Accel-Buffering: no`.
- **Isolamento de sessão:** memória do grafo sempre indexada por `configurable.thread_id = session_id`.
- **Logs:** nunca registrar CPF, conteúdo de pedidos ou chaves de API em logs abertos. Em exceções cujo texto possa conter argumentos de Tools, logar apenas o tipo do erro e o `session_id`; traceback completo somente com `DEBUG=true`.
- **Telemetria:** o CPF enviado a sistemas de observabilidade (ex.: `user_id` do LangFuse) deve ser pseudonimizado via `src.core.security.pseudonimizar_cpf` (HMAC-SHA256 com `PII_HASH_SALT`).
- **Segredos:** apenas via variáveis de ambiente / `.env` (nunca versionado); manter `.env.example` atualizado.

## 3. Regras Arquiteturais
- **Camadas e responsabilidades (`src/`):**
  - `api/` — transporte HTTP: schemas Pydantic, rotas e formatação SSE. Sem lógica de negócio.
  - `agent/` — motor LangGraph: `state.py` (`AgentState`), `graph.py` (nós, arestas, compilação), `prompts.py`, `mock_llm.py`.
  - `tools/` — Tools transacionais e mocks de sistemas externos.
  - `rag/` — ingestão, vector store e Tool de catálogo.
  - `core/` — configuração (`config.py`) e utilidades transversais.
- **Direção de dependências:** `api → agent → (tools, rag) → core`. Camadas inferiores nunca importam camadas superiores.
- **Tools:** expostas via `@tool` com `args_schema` Pydantic e docstring que serve de descrição ao LLM. A lógica fica em uma função `_<nome>_core()` pura e testável; o decorator é apenas um adaptador.
- **Nós do grafo:** funções `async` que recebem o `AgentState` e retornam **apenas o delta** do estado (`Dict[str, Any]`). Campos acumulativos usam `Annotated[..., operator.add]`.
- **Circuit Breaker:** todo loop de Tools deve respeitar `settings.CIRCUIT_BREAKER_LIMIT`.
- **Observabilidade desacoplada:** callbacks (LangFuse) são injetados no `config` da execução, nunca dentro dos nós. A falha da observabilidade não pode interromper o atendimento (degradar para `None` + `logger.warning`).
- **Estado global:** proibido estado mutável em nível de módulo, exceto singletons de recursos caros (grafo compilado, coleção ChromaDB) com inicialização preguiçosa encapsulada em funções `get_*()`.
- **Configuração:** valores ajustáveis vêm de `src.core.config.settings`; não usar números mágicos nem caminhos absolutos fixos.

## 4. Tratamento de Erros
- **Entrada:** validações no schema Pydantic → FastAPI retorna `422` automaticamente. `ChatRequest` usa `extra="forbid"`.
- **Durante o streaming:** após o envio dos headers não é possível alterar o status HTTP; erros devem ser logados (respeitando a regra de logs da Seção 2) e emitidos como chunk SSE genérico com `code` (ex.: `STREAM_ERROR`) antes de encerrar o stream. O texto da exceção nunca é repassado ao cliente.
- **Tools:** erros de negócio (CPF inválido, pedido inexistente, acesso negado) retornam JSON estruturado com `status` e `codigo` (ex.: `ACESSO_NEGADO`, `CPF_INVALIDO`, `nao_encontrado`) para que o LLM explique a recusa sem quebrar o grafo.
- **Nunca** silenciar exceções com `except: pass`, exceto em rotinas de best-effort explicitamente documentadas (ex.: flush de telemetria).
- Mensagens de erro voltadas ao usuário em português, sem stack traces nem dados sensíveis.

## 5. Mandatos de Testes
- **Framework:** `pytest` + `pytest-asyncio` (testes `async` com `@pytest.mark.asyncio`); rotas com `fastapi.testclient.TestClient`.
- **Sem rede:** a suíte deve rodar sem chaves de API e sem LangFuse, usando `MockGeminiLLM`. Chamadas HTTP do frontend são testadas com `unittest.mock.patch`.
- **Cobertura obrigatória:**
  - Validações de schema (casos válidos e inválidos).
  - Cada Tool (sucesso e todos os códigos de erro).
  - Roteamento do grafo e Circuit Breaker.
  - **Cada guardrail da Seção 2** com pelo menos um teste ponta a ponta (acesso cruzado de CPF, pergunta de margem de lucro, formato SSE).
- Organização: um arquivo por domínio em `tests/` (`test_api.py`, `test_agent.py`, `test_tools_and_rag.py`, `test_frontend.py`, `test_security.py`); classes `Test<Assunto>` agrupando casos relacionados.
- Novos testes devem preferir `@pytest.mark.parametrize` para múltiplas entradas/saídas do mesmo comportamento. Testes legados podem ser migrados de forma oportunista, quando o arquivo for alterado.
- Dados de teste usam os CPFs válidos do mock (`52998224725` Juliana, `14183884784` Camila).
- Toda tarefa só é marcada `[x]` em `tasks.md` com `pytest` verde.

## 6. Estilo de Código e Convenções
- **Idioma:** código (identificadores técnicos) pode seguir termos do domínio em português (`buscar_status_pedido`, `tentativas_tool`); docstrings, comentários, mensagens ao usuário e documentação em **português**.
- **Type hints** obrigatórios em assinaturas públicas; preferir `Optional[...]`, `List`, `Dict` coerentes com o restante do código.
- **Docstrings** em todos os módulos, classes e funções públicas.
- **Early returns:** evitar aninhamento profundo; validar e retornar cedo.
- **Logging:** usar `logging.getLogger(__name__)`; proibido `print()` em `src/`.
- **Async:** não bloquear o event loop em rotas e nós; I/O bloqueante prolongado deve ser isolado.
- **JSON:** serializar com `ensure_ascii=False` para preservar acentuação.
- **Markdown/moeda:** chunks e textos renderizados devem escapar `$` (valores `R$`) para não serem interpretados como LaTeX.
- **Nomenclatura:** `snake_case` para funções/variáveis, `PascalCase` para classes, `UPPER_SNAKE_CASE` para constantes; funções internas prefixadas com `_`.

## 7. Documentação e Fluxo SDD
- Cada funcionalidade vive em `.specs/RFC-XXX-<nome>/` com `spec.md`, `plan.md` e (opcionalmente) `tasks.md`.
- Decisões arquiteturais relevantes geram ou atualizam um ADR em `docs/adrs/`.
- Desvios da spec durante a implementação devem ser registrados no `plan.md` da RFC (seção de decisões ou "Fora de Escopo").
