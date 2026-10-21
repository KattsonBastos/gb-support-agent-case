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
*   **Galeria de Imagens dos Diagramas:** Imagens renderizadas de todos os diagramas da arquitetura para visualização direta caso o Mermaid não renderize no GitHub: [docs/diagrams/](docs/diagrams/).
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
    *   **Langfuse (Observabilidade):** `http://localhost:3000`

## 4. Relatório de Vibe Coding (Desenvolvimento Assistido por IA)

<p align="justify">
&ensp;&ensp;&ensp;&ensp;
O projeto foi desenvolvido sob a abordagem de <strong>Spec-Driven Development (SDD) assistido por IA</strong>, combinando o ambiente agentic do <strong>Google Antigravity IDE</strong> (orquestrando o modelo <strong>Gemini 3.8 Flash</strong> para implementação/scaffolding e o <strong>Claude Opus 5.5</strong> para revisão final do código e documentação) e o <strong>Gemini Chat (Modelo Pro)</strong> para discussões conceituais, decisões arquiteturais ([ADRs](docs/adrs)) e diagramação do [Modelo C4](docs/c4-model). A disciplina do SDD e a intervenção ativa <em>Human-in-the-Loop</em> — especialmente no tratamento de fluxos assíncronos de streaming SSE no LangGraph e na aplicação estrita de guardrails de PII — garantiram alta velocidade de entrega (~75% de ganho de produtividade) com robustez corporativa.
</p>

> O relatório técnico completo, detalhando as ferramentas, engenharia de prompts, desafios enfrentados, intervenções humanas e lições aprendidas, está disponível em:  
> 📄 **[docs/relatorio_vibe_coding.md](docs/relatorio_vibe_coding.md)**

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