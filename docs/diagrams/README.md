# Galeria de Diagramas de Arquitetura

Este diretório contém as imagens pré-renderizadas de todos os diagramas Mermaid presentes na documentação técnica do projeto. 

> 💡 **Objetivo:** Caso a visualização nativa de diagramas Mermaid do GitHub falhe ou apresente instabilidades em seu navegador, você pode visualizar e baixar diretamente as versões estáticas em imagem aqui indexadas.

---

## 📐 Índice de Diagramas

### 1. Modelo C4 e Arquitetura de Software
| Diagrama | Arquivo de Imagem | Documento de Origem | Descrição |
| :--- | :--- | :--- | :--- |
| **C4 Nível 1: Contexto** | [`c4-contexto.png`](c4-contexto.png) | [01-contexto.md](../c4-model/01-contexto.md) | Limites do sistema, atores (revendedora), integrações com catálogo e pedidos. |
| **C4 Nível 2: Containers** | [`c4-container.png`](c4-container.png) | [02-container.md](../c4-model/02-container.md) | Decomposição técnica (FastAPI, LangGraph, Redis, ChromaDB, Streamlit). |

---

### 2. Diagramas de Sequência (Casos de Uso Core)
| Caso de Uso | Arquivo de Imagem | Documento de Origem | Descrição |
| :--- | :--- | :--- | :--- |
| **Consulta ao Catálogo (Pré-Venda)** | [`sequencia-consulta-catalogo.png`](sequencia-consulta-catalogo.png) | [03-sequencia-casos-uso.md](../c4-model/03-sequencia-casos-uso.md) | Roteamento agêntico para a Tool de RAG com busca vetorial no catálogo em PDF. |
| **Consulta Transacional (Pós-Venda)** | [`sequencia-consulta-transacional.png`](sequencia-consulta-transacional.png) | [03-sequencia-casos-uso.md](../c4-model/03-sequencia-casos-uso.md) | Injeção estrita de CPF de sessão na Tool de Pedidos (Zero Vazamento de PII). |
| **Disparo de Guardrail (Compliance)** | [`sequencia-guardrail-pii.png`](sequencia-guardrail-pii.png) | [03-sequencia-casos-uso.md](../c4-model/03-sequencia-casos-uso.md) | Interrupção imediata em tentativas de extrair margem ou dados confidenciais. |

---

### 3. System Design para 500k Conexões Simultâneas
| Diagrama | Arquivo de Imagem | Documento de Origem | Descrição |
| :--- | :--- | :--- | :--- |
| **Cloud Architecture (TO-BE)** | [`system-design-cloud-architecture.png`](system-design-cloud-architecture.png) | [system-design-500k.md](../system-design-500k.md) | Topologia Event-Driven na GCP com Envoy/NGINX, Redis Pub/Sub, Kafka e BigQuery. |
| **Esteira de AI Data Engineering (RAG)** | [`system-design-esteira-rag.png`](system-design-esteira-rag.png) | [system-design-500k.md](../system-design-500k.md) | Pipeline de ingestão batch de PDFs e recuperação híbrida em tempo real com re-ranking. |
| **Orquestração por Sub-grafos** | [`system-design-orquestracao-subgrafos.png`](system-design-orquestracao-subgrafos.png) | [system-design-500k.md](../system-design-500k.md) | Roteamento determinístico por modelos de decisão na borda (FinOps & Menor Latência). |

---

### 4. Metodologia de Desenvolvimento
| Diagrama | Arquivo de Imagem | Documento de Origem | Descrição |
| :--- | :--- | :--- | :--- |
| **Fluxo SDD e Vibe Coding** | [`vibe-coding-fluxo-desenvolvimento.png`](vibe-coding-fluxo-desenvolvimento.png) | [relatorio_vibe_coding.md](../relatorio_vibe_coding.md) | Interação entre Constituição, ADRs, RFCs, Spec-Driven Development e Vibe Coding. |
