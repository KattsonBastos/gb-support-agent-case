# ADR-005: LLMOps e Observabilidade de Execução

**Data:** 17/10/2026

**Status:** Aceito

## Contexto
Em sistemas baseados em agentes e Tools, é impossível depurar alucinações apenas com logs tradicionais de texto. É necessário demonstrar tracing das etapas do LangGraph, medindo latência das Tools e consumo de tokens para viabilizar operações escaláveis.

## Decisão
Integraremos o **LangFuse** como ferramenta primária de tracing e observabilidade, através de Callbacks injetados dinamicamente na invocação do LangGraph pelo FastAPI. Os traces serão categorizados por `session_id` e identificador do usuário (ex: CPF).

## Consequências
*   **Positivas:** Permite a visualização em árvore de toda a cadeia de execução (Router -> RAG -> LLM). A atrelação ao `session_id` facilita o suporte técnico ("qual foi o contexto exato que gerou esta resposta para esta revendedora?"). Facilita futuras análises preditivas para o Data Lake.
*   **Negativas:** Adiciona ligeiro overhead de latência de rede para o envio assíncrono dos traces para a nuvem da ferramenta.