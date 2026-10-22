# ADR 001: Padrão de Orquestração - Multi-Agent (ReAct) vs. Semantic Routing com Subgrafos

## 1. Título e Contexto
**Data:** 22 de Outubro de 2026
**Status:** Aceito
**Domínio:** Orquestração de IA / AI Engineering

Para escalar a plataforma Agentes GB a 500.000 revendedoras simultâneas, precisamos definir o padrão central de orquestração do LLM. O MVP utilizava um agente autônomo baseado no padrão ReAct (Reasoning and Acting), onde um único LLM "pensava" de forma iterativa sobre qual ferramenta chamar. Em escala massiva, loops autônomos geram alto consumo de tokens (FinOps), latência imprevisível (múltiplas idas e vindas de rede) e risco de alucinações ao acessar APIs transacionais críticas (ERP/OMS). O desafio é garantir a precisão nas respostas de catálogo (RAG) e a exatidão nas ferramentas de pedidos, com o menor *Time-to-First-Token* (TTFT) e custo financeiro possíveis.

## 2. Opções Consideradas

### Opção A: Multi-Agent System (Padrão ReAct / Swarm)
Múltiplos agentes LLM autônomos conversando entre si. Um agente "Supervisor" recebe a dúvida da revendedora e delega para um "Agente de Catálogo" ou "Agente de Pedidos".
* **Prós:** Altamente flexível; lida bem com prompts vagos ou multi-intenções em uma única mensagem.
* **Contras:** Custo proibitivo (muitos tokens de *system prompts* repetidos em cada nó); latência alta devido à comunicação LLM-to-LLM; difícil prever o fluxo exato de execução (não-determinístico).

### Opção B: Semantic Routing + Subgrafos Determinísticos (LangGraph)
Uso de um classificador ultraleve na borda (Router - ex: modelo SLM, Laya/Jev ou embeddings rápidos) para classificar a intenção da revendedora. Baseado na classificação, o LangGraph direciona o fluxo para um subgrafo determinístico específico (RAG, ERP ou Banco Analítico), chamando o LLM "pesado" (Orquestrador) apenas em casos ambíguos ou para sintetizar a resposta final.
* **Prós:** Controle estrito de custos (FinOps); latência muito menor (evita o loop de raciocínio de grandes LLMs); garante fluxos transacionais consistentes para consulta de estoque/pedidos; facilita a observabilidade por intenção.
* **Contras:** Maior esforço inicial de engenharia de software para mapear e tipar os subgrafos; menor flexibilidade se a revendedora fizer uma pergunta que mistura pedidos e catálogo na mesma frase (requer lógica adicional no nó de roteamento).

### Opção C: LLM Monolítico com Mega-Prompt
Um único LLM gigante que recebe todas as ferramentas e todo o contexto no *System Prompt* e decide tudo em uma única chamada.
* **Prós:** Simplicidade arquitetural e facilidade de implementação.
* **Contras:** Estouro rápido do *Token Budget*; degradação de performance do modelo (Lost in the Middle); impossível escalar financeiramente para 500k usuários.

## 3. Matriz de Trade-off

| Critério | Opção A (Multi-Agent/ReAct) | Opção B (Subgrafos Roteados) | Opção C (Monolítico) |
| :--- | :--- | :--- | :--- |
| **Custo de Inferência (FinOps)** | Alto (Múltiplos loops) | **Baixo** (Uso de SLMs na borda) | Altíssimo (Prompt gigante) |
| **Latência (TTFT)** | Alta (> 5s) | **Baixa** (< 2s p95) | Média |
| **Determinismo (Confiança API)** | Baixo | **Alto** | Médio |
| **Overhead Operacional / LLMOps** | Alto (Difícil debugar falhas) | **Médio** (Tracing claro por grafo) | Baixo |
| **Proteção contra Alucinações** | Baixa | **Alta** (Fluxo controlado) | Baixa |

## 4. Decisão e Justificativa ("Killer Justification")

**Decisão:** Escolhemos a **Opção B (Semantic Routing + Subgrafos Determinísticos)**.

**Killer Justification:**
A decisão de abandonar o padrão puramente autônomo (ReAct) em favor de subgrafos roteados é guiada essencialmente por **FinOps e Escala**. Em um cenário de 500.000 conexões de revendedoras, a maioria das dúvidas possui intenções claras e mapeáveis (ex: "Qual o status do pedido X?" ou "O perfume Y está na promoção?"). 

Usar um LLM de ponta (como GPT-4o ou Gemini 1.5 Pro) para decidir repetidamente a mesma coisa gera um desperdício massivo de tokens. Ao introduzirmos um *Decision Model* na entrada (Router), nós aplicamos o padrão de **Model Cascading**: resolvemos 80% dos casos de forma determinística e barata, acionando as APIs diretamente via subgrafos do LangGraph, e reservamos o poder cognitivo e o custo das chamadas complexas apenas para cenários de fallback/ambiguidade ou para a síntese amigável (Nó de Síntese). Isso nos garante o TTFT esperado (< 2s) e protege os sistemas legados do Grupo Boticário (ERP/OMS) de chamadas alucinadas em loop.