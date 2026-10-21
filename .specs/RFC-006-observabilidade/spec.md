# Observabilidade e LLMOps
**Projeto:** Agente de Suporte à Revendedora (Plataforma Agentes GB)
**Ficheiro:** `.specs/RFC-006-observabilidade/spec.md`
**Propósito:** Definir os padrões de telemetria e rastreamento das etapas do LangGraph, consumo de tokens e latência, utilizando uma instância local do LangFuse.

## 1. Stack e Infraestrutura
*   **Plataforma de Tracing:** LangFuse (Self-hosted via Docker).
*   **Base de Dados:** PostgreSQL (exclusiva para persistência dos traces do LangFuse).
*   **Integração Python:** Biblioteca `langfuse`.

## 2. Padrões de Implementação no FastAPI
A observabilidade não deve estar acoplada dentro dos nós do LangGraph, mas sim injetada no momento da execução.
*   **Handler Dinâmico:** Para cada requisição no endpoint `POST /api/v1/chat/stream`, instanciar o `LangfuseCallbackHandler`.
*   **Isolamento de Contexto:** É obrigatório passar o `session_id` e o `user_id` (utilizando o CPF da revendedora **pseudonimizado** via HMAC-SHA256, nunca em texto claro) para o construtor do callback. Isto garante a auditoria de acessos e facilita a depuração caso ocorra disparo das travas de segurança (Guardrails), sem expor PII na plataforma de telemetria.
*   **Injeção no Grafo:** O handler deve ser passado no argumento `callbacks` da configuração de execução (`config`) durante a invocação do `astream_events`.

## 3. Variáveis de Ambiente Necessárias
A aplicação FastAPI deve ler as seguintes variáveis para se conectar ao container do LangFuse na mesma rede Docker:
*   `LANGFUSE_PUBLIC_KEY`
*   `LANGFUSE_SECRET_KEY`
*   `LANGFUSE_HOST="http://langfuse:3000"`