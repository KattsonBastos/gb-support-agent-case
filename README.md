# Motor Transacional: Agente de Suporte à Revendedora (GB)

<p align="justify">
&ensp;&ensp;&ensp;&ensp;
Este repositório implementa um MVP de um orquestrador de intenções baseado em IA, focado em auxiliar a Revendedora no seu ciclo de vendas através de consultas ao catálogo (RAG) e a sistemas transacionais (Tools).
</p>

## 1. Visão Geral da Solução
<p align="justify">
&ensp;&ensp;&ensp;&ensp;
A solução foi arquitetada utilizando o padrão <strong>ReAct (Reasoning and Acting)</strong>. O núcleo inteligente é construído com <strong>LangGraph</strong>, que atua como o "cérebro" para rotear chamadas. A comunicação com a interface é feita através do <strong>FastAPI</strong>, servindo o conteúdo gerado em tempo real via <strong>Streaming (Server-Sent Events - SSE)</strong>. Para a interface visual de simulação do chat, optou-se por um frontend leve em <strong>Streamlit</strong>.
</p>

## 2. Decisões de Arquitetura e Documentação
<p align="justify">
&ensp;&ensp;&ensp;&ensp;
Para garantir a escalabilidade técnica e a segurança operacional exigidas pelo negócio, a arquitetura foi mapeada e documentada seguindo padrões da indústria.
</p>

*   **Modelo C4:** Os diagramas de Contexto e Container (em Mermaid) estão disponíveis em [docs/c4-model/](docs/c4-model/).
*   **Diagramas de Sequência:** O detalhamento técnico dos casos de uso (Pré-venda, Consulta Transacional e Disparo de Guardrails) pode ser consultado em [docs/c4-model/03-sequencia-casos-uso.md](docs/c4-model/03-sequencia-casos-uso.md).
*   **ADRs (Architecture Decision Records):** As decisões críticas que moldaram este MVP estão detalhadas em [docs/adrs/](docs/adrs/). Destacam-se:
    *   [`ADR-001`](docs/adrs/001-gestao-estado.md): Estratégia de Gestão de Estado e Isolamento de Sessão (Transição de Memória Local para Redis).
    *   [`ADR-002`](docs/adrs/002-streaming-sse.md): Comunicação Assíncrona via Streaming SSE.
    *   [`ADR-003`](docs/adrs/003-guardrails-pii.md): Defesa em Profundidade (Guardrails) para Proteção de PII e Margens de Lucro.

## 3. Instruções para Rodar Localmente
<p align="justify">
&ensp;&ensp;&ensp;&ensp;
O projeto foi integralmente dockerizado para facilitar a execução local. Os bancos de dados (Vector Store e SQLite do State) persistem os dados mapeando volumes locais.
</p>

**Pré-requisitos:** Docker e Docker Compose instalados.

1.  Clone este repositório:

    *   Com SSH:
        ```bash
        git clone git@github.com:KattsonBastos/gb-support-agent-case.git
        cd git@github.com:KattsonBastos/gb-support-agent-case.git
        ```
    *   Com HTTPS:
        ```bash
        git clone https://github.com/KattsonBastos/gb-support-agent-case.git
        cd gb-support-agent-case
        ```

2.  Configure as variáveis de ambiente:
    *   Duplique o arquivo [`.env.example`](.env.example) e renomeie para `.env`.
    *   Insira as suas chaves de API (`OPENAI_API_KEY` ou `GOOGLE_API_KEY`, e credenciais do `LANGFUSE` para observabilidade).
3.  Inicie a infraestrutura:
    ```bash
    docker-compose up -d --build
    ```
4.  Acesse a aplicação:
    *   **Frontend (Chat da Revendedora):** `http://localhost:8501`
    *   **Backend (Swagger/Docs da API):** `http://localhost:8000/docs`
    *   **Langfuse (Obserbabilidade):** `http://localhost:3000`

## 4. Relatório de Vibe Coding (Desenvolvimento Assistido por IA)

<p align="justify">
&ensp;&ensp;&ensp;&ensp;
Abaixo segue um descritivo de como a IA foi utilizada no desenvolvimento deste projeto:
</p>

*   **Ferramentas Utilizadas:** Gemini Chat para a idealização, discussão arquitetural e de produto; Google Antigravity IDE orquestrando o modelo **Gemini 3.8 Flash** para a implementação e estruturação de boilerplate.
*   **Estruturação de Prompts:**
    *   **Vibe coding via prompts com o Gemini:** Discussão e criação das [ADRs](docs/adrs) e diagramas do [Modelo C4](docs/c4-model).
    *   **Framework pessoal de Spec-Driven Development (SDD):** Para a implementação, foi utilizado o SDD com um framework lighweight pessoal (registro em [.specs](.specs)). As [skills de SDD](.agents/skills) foram versionadas apenas para fins de explicação.
    *   **Prompts Vibe Coding:** Registro em [docs/vibe-coding-prompts](docs/vibe-coding-prompts) dos prompts usados no vibe coding via chat para atividades gerais.
*   **O Maior Obstáculo da IA:** Durante a implementação do LangGraph, a IA teve grande dificuldade em correlacionar o gerador assíncrono do grafo (`.astream_events()`) com o formato exigido pelo `StreamingResponse` do FastAPI. O modelo insistia em devolver objetos internos de roteamento do LangChain no meio do stream SSE, quebrando a interface do usuário.
*   **A Correção (Human-in-the-Loop):** Intervi criando um filtro heurístico na função geradora do FastAPI ([`src/api/routes.py`](src/api/routes.py)). Ajustei o loop assíncrono para inspecionar os dicionários gerados pelo evento, garantindo que o `yield` ocorresse estritamente quando a chave `"event"` fosse `on_chat_model_stream`, formatando manualmente o chunk no padrão nativo de Server-Sent Events (`data: {chunk}\n\n`).

## 5. Visão de Evolução (System Design para 500 mil revendedoras)

<p align="justify">
&ensp;&ensp;&ensp;&ensp;
A estratégia de transição do MVP para a escala de 500.000 revendedoras simultâneas migra a arquitetura de um modelo síncrono para uma abordagem <strong>Event-Driven desacoplada</strong>, combinando otimização de custos (FinOps) e integração bidirecional com o Data Lake corporativo (BigQuery).
</p>

*   **Arquitetura Desacoplada (Event-Driven):** O FastAPI Edge gerencia exclusivamente as conexões SSE via Redis Pub/Sub, delegando o processamento pesado do LangGraph para workers assíncronos no Kubernetes via Kafka/PubSub.
*   **Estratégia Híbrida de Dados & BigQuery:** Consultas em tempo real ao ERP (estoque e pedidos) combinadas a leituras de baixa latência em FastDB (alimentado via *Reverse ETL* do BigQuery). Telemetria analítica enviada em batch assíncrono pós-interação via Dataflow.
*   **FinOps & Sub-grafos Especializados:** Substituição do loop ReAct puro por sub-grafos acionados por modelos de decisão na borda, com *Semantic Caching* no Redis e *Output Guardrails* dedicados (mitigando vazamentos de PII e margem).

> O detalhamento completo da arquitetura TO-BE, esteira de AI Data Engineering (RAG), matriz de evolução (AS-IS vs TO-BE) e diagramas Mermaid estão disponíveis em:  
> 📄 **[docs/system-design-500k.md](docs/system-design-500k.md)**