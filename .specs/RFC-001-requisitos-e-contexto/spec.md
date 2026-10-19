# Product Requirements Document (PRD) & Master Spec
**Projeto:** Agente de Suporte à Revendedora (Plataforma Agentes GB)
**Propósito deste Documento:** Servir como fonte de verdade arquitetural e spec principal para o desenvolvimento assistido por IA (Spec-Driven Development / Vibe Coding).

## 1. Visão Geral e Escopo
O objetivo é construir o MVP de um motor transacional baseado em IA para apoiar a Revendedora Boticário durante o ciclo de vendas. O agente atua como um **Orquestrador de Intenções**, recebendo a entrada do usuário e decidindo autonomamente entre duas vias de ação:
1. Consultar a base de conhecimento (RAG) para dúvidas de catálogo e promoções.
2. Acionar ferramentas de backend (Tools) para consultas transacionais (status de pedido, estoque).

## 2. Atores e Fronteiras do Sistema
*   **Ator Principal:** Revendedora Boticário (interagindo via simulador de chat/WhatsApp).
*   **Core System:** Agente Orquestrador (FastAPI + LangGraph).
*   **Base de Conhecimento (RAG):** Catálogo em PDF/Markdown do Ciclo 15 (Mock).
*   **Sistemas Externos (Mock APIs):** Banco de dados analítico/transacional de Pedidos e Estoque.

## 3. Requisitos Funcionais (Core MVP)
*   **RF01 - Roteamento Semântico:** O LangGraph deve possuir um nó de decisão (Conditional Edge) capaz de classificar se a pergunta do usuário requer o acionamento de uma Tool ou uma busca no Vector Store.
*   **RF02 - Consulta de Catálogo (RAG):** Implementar um pipeline de Retrieval-Augmented Generation simples para responder a dúvidas sobre produtos e promoções ativas do ciclo.
*   **RF03 - Execução de Tools Transacionais:** O agente deve ser capaz de invocar funções de forma estruturada. Obrigatório: `buscar_status_pedido`.
*   **RF04 - Gestão de Estado:** A aplicação deve manter a memória e contexto da conversa estritamente isolados por revendedora, utilizando `session_id` ou `thread_id`.

## 4. Restrições e Guardrails de Segurança (Invioláveis)
As regras abaixo devem ser garantidas via system prompt rigoroso e/ou camadas de validação (Guardrails) no fluxo do LangGraph:
*   **SEC01 - Proteção de PII:** É estritamente proibido que o agente solicite, manipule em logs abertos ou vaze Dados Pessoais (PII) que não pertençam ao escopo transacional da revendedora ativa.
*   **SEC02 - Sigilo Comercial:** O agente não pode, sob nenhuma hipótese, calcular, estimar ou fornecer informações referentes a margens de lucro de outras revendedoras.

## 5. Contratos de Implementação (Spec para Vibe Coding)

### 5.1. Interface da API (FastAPI)
*   **Endpoint Principal:** `POST /api/v1/chat/stream`
*   **Payload Esperado (Input):**
    ```json
    {
      "session_id": "uuid-da-revendedora",
      "message": "string"
    }
    ```
*   **Resposta (Output):** O endpoint deve retornar um fluxo de dados em formato **Streaming (SSE - Server-Sent Events)** contendo os chunks gerados pelo LLM para garantir percepção de baixa latência.

### 5.2. Assinatura da Tool de Pedido
*   **Nome:** `buscar_status_pedido`
*   **Descrição para o LLM:** "Utilize esta ferramenta APENAS quando a revendedora quiser saber onde está o seu pedido, se já foi faturado ou detalhes de entrega."
*   **Parâmetros (Pydantic Schema):**
    *   `cpf` (string): CPF da revendedora para validação de acesso.
    *   `id_pedido` (string): Código alfanumérico do pedido.
*   **Retorno Mockado:** Objeto JSON contendo `status_entrega`, `data_previsao`, `transportadora`.

## 6. Requisitos Não Funcionais (Perspectiva MVP vs. TO-BE 500k)
| Domínio | Abordagem MVP (Local) | Abordagem TO-BE (Escala 500k Revendedoras) |
| :--- | :--- | :--- |
| **Persistência de Estado** | SQLite / Memória RAM nativa do LangGraph. | Redis distribuído com TTL (Sliding Window Memory). |
| **Banco Vetorial (RAG)** | ChromaDB local ou FAISS local. | Vector Database Gerenciado (Pinecone / Vertex AI Search). |
| **Monitoramento / Tracing** | LangFuse local ou Phoenix. | Integração nativa com DataDog APM + LangFuse Cloud. |
| **Data & Analytics** | Logs no console / arquivos locais. | Ingestão assíncrona do resumo das sessões no BigQuery via Pub/Sub. |
