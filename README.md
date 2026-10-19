# Motor Transacional: Agente de Suporte à Revendedora (GB)

Este repositório contém a entrega do Case Técnico para a posição de **Pessoa Engenheira de IA - Especialista II** na Plataforma Agentes GB. O projeto implementa um MVP de um orquestrador de intenções baseado em IA, focado em auxiliar a Revendedora no seu ciclo de vendas através de consultas ao catálogo (RAG) e a sistemas transacionais (Tools).

## 1. Visão Geral da Solução
A solução foi arquitetada utilizando o padrão **ReAct (Reasoning and Acting)**. O núcleo inteligente é construído com **LangGraph**, que atua como o "cérebro" para rotear chamadas. A comunicação com a interface é feita através do **FastAPI**, servindo o conteúdo gerado em tempo real via **Streaming (Server-Sent Events - SSE)**. Para a interface visual de simulação do chat, optou-se por um frontend leve em **Streamlit**.

## 2. Decisões de Arquitetura e Documentação
Para garantir a escalabilidade técnica e a segurança operacional exigidas pelo negócio, a arquitetura foi mapeada e documentada seguindo padrões da indústria.

*   **Modelo C4:** Os diagramas de Contexto e Container (em Mermaid) estão disponíveis em `docs/c4-model/`.
*   **Diagramas de Sequência:** O detalhamento técnico dos casos de uso (Pré-venda, Consulta Transacional e Disparo de Guardrails) pode ser consultado no repositório.
*   **ADRs (Architecture Decision Records):** As decisões críticas que moldaram este MVP estão detalhadas em `docs/adrs/`. Destacam-se:
    *   `ADR-001`: Estratégia de Gestão de Estado e Isolamento de Sessão (Transição de Memória Local para Redis).
    *   `ADR-002`: Comunicação Assíncrona via Streaming SSE.
    *   `ADR-003`: Defesa em Profundidade (Guardrails) para Proteção de PII e Margens de Lucro.

## 3. Instruções para Rodar Localmente
O projeto foi integralmente dockerizado para emular um ambiente de microsserviços. Os bancos de dados (Vector Store e SQLite do State) persistem os dados mapeando volumes locais.

**Pré-requisitos:** Docker e Docker Compose instalados.

1.  Clone este repositório:
    ```bash
    git clone [INSERIR_URL_DO_REPO]
    cd [INSERIR_NOME_DO_REPO]
    ```
2.  Configure as variáveis de ambiente:
    *   Duplique o arquivo `.env.example` e renomeie para `.env`.
    *   Insira as suas chaves de API (`OPENAI_API_KEY` ou `GOOGLE_API_KEY`, e credenciais do `LANGFUSE` para observabilidade).
3.  Inicie a infraestrutura:
    ```bash
    docker-compose up -d --build
    ```
4.  Acesse a aplicação:
    *   **Frontend (Chat da Revendedora):** `http://localhost:8501`
    *   **Backend (Swagger/Docs da API):** `http://localhost:8000/docs`

## 4. Relatório de Vibe Coding (Desenvolvimento Assistido por IA)

Conforme exigido pelo escopo do desafio, a esteira de desenvolvimento foi fortemente assistida por IA. Adotei uma metodologia de **Contract-First Vibe Coding**, garantindo que as fronteiras arquiteturais guiassem a geração de código.

*   **Ferramentas Utilizadas:** Google Antigravity IDE (Agent-first IDE) orquestrando o modelo **Gemini 3.5 Flash** para tarefas paralelas e estruturação de boilerplate.
*   **Estruturação dos Prompts Iniciais:** Não utilizei prompts de "tentativa e erro". A etapa 0 do projeto foi a criação de Especificações Rigorosas em Markdown (`.specs/RFC-*/spec.md`). Estes arquivos serviram como instrução de sistema (Contexto Mestre) para as *Tasks* no Antigravity, delegando paralelamente a criação dos modelos Pydantic da API e os conectores (Tools mockadas).
*   **O Maior Obstáculo da IA:** Durante a implementação do LangGraph, a IA teve grande dificuldade em correlacionar o gerador assíncrono do grafo (`.astream_events()`) com o formato exigido pelo `StreamingResponse` do FastAPI. O modelo insistia em devolver objetos internos de roteamento do LangChain no meio do stream SSE, quebrando a interface do usuário.
*   **A Correção (Human-in-the-Loop):** Como Especialista, intervi criando um filtro heurístico na função geradora do FastAPI (`routes.py`). Ajustei o loop assíncrono para inspecionar os dicionários gerados pelo evento, garantindo que o `yield` ocorresse estritamente quando a chave `"event"` fosse `on_chat_model_stream`, formatando manualmente o chunk no padrão nativo de Server-Sent Events (`data: {chunk}\n\n`).

## 5. Visão de Evolução (System Design para 500 mil revendedoras)
Para escalar este MVP para 500 mil acessos simultâneos e integrar ao BigLake/BigQuery corporativo:
*   **Desacoplamento:** O FastAPI passará a atuar estritamente como um API Gateway (gestão de conexões longas de SSE), delegando as execuções do LangGraph via fila (ex: Apache Kafka/PubSub) para workers assíncronos.
*   **Estado:** O checkpointer em memória será substituído por um cluster **Redis**, permitindo latência de milissegundos no resgate das threads. Implementaremos "Sliding Window Summarization" para baratear custos de contexto no LLM longo.
*   **Data Lake:** Um CronJob consumirá eventos sumarizados do LangFuse e dados consolidados das interações e enviará os *logs* analíticos diretamente para o BigQuery, municiando a equipe de negócio sem penalizar a API transacional principal.