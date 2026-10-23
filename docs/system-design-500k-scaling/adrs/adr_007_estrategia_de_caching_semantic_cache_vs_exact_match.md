# ADR 007: Estratégia de Caching - Semantic Cache vs. Exact-Match Caching

## 1. Título e Contexto

- **Data:** 22 de Outubro de 2026
- **Status:** Aceito
- **Domínio:** FinOps / AI Engineering

Durante eventos de pico ou lançamentos de campanhas (ex: início do Ciclo 15, Black Friday), a Plataforma Agentes GB recebe um volume massivo de perguntas repetitivas das revendedoras (ex: dúvidas sobre datas de fechamento do ciclo, promoções âncora, ou regras de pontuação). 

Na arquitetura TO-BE desenhada para 500.000 conexões, rotear cada uma dessas interações até o *LangGraph Worker* para gerar inferência no LLM resulta em custos desnecessários (FinOps) e uso ineficiente da infraestrutura de GPUs. Precisamos de uma camada de interceptação na borda que identifique perguntas repetidas e devolva a resposta instantaneamente, mas o *caching* tradicional de software não funciona bem com linguagem natural.

## 2. Opções Consideradas

### Opção A: Caching Tradicional (Exact Match no Redis)

Uso de chaves de cache baseadas na string exata da pergunta do usuário. Se a string for 100% idêntica, devolve a resposta cacheada.

* **Prós:** Latência ultrabaixa (O(1) no Redis); zero custo computacional extra; implementação trivial.
* **Contras:** Taxa de acerto (*Hit Rate*) quase nula em interfaces conversacionais. "Tem promo de malbec?" e "O malbec está na promo?" gerariam chaves diferentes, forçando o processamento no LLM em ambos os casos.

### Opção B: Semantic Caching (Busca Vetorial no Redis Cluster)

Uso de um modelo de embedding ultraleve e rápido na borda (Edge/API Gateway) para converter a pergunta da revendedora em um vetor. Esse vetor é comparado via busca de similaridade (KNN/HNSW) contra as perguntas recentemente respondidas no Redis Vector. Se a similaridade for superior a um *threshold* (ex: 95%), a resposta em cache é devolvida.

* **Prós:** Altíssimo *Hit Rate*, absorvendo variações linguísticas, erros de digitação e regionalismos comuns no WhatsApp; reduz o custo marginal de picos sazonais a praticamente zero (100% de offload do LangGraph para perguntas frequentes).
* **Contras:** Introduz uma pequena latência inicial (algumas dezenas de milissegundos) para gerar o embedding na borda; exige gerenciar um *threshold* de confiança rigoroso para evitar que perguntas levemente diferentes (ex: "Status do pedido 123" vs "Status do pedido 124") gerem falsos positivos.

## 3. Matriz de Trade-off

| Critério | Opção A (Exact Match) | Opção B (Semantic Caching) |
| ----- | ----- | ----- |
| **Taxa de Acerto (Cache Hit Rate)** | < 5% (Muito baixa) | **> 60%** (Alta eficácia) |
| **Custo de Inferência Poupado (FinOps)** | Mínimo | **Massivo** |
| **Risco de Falso Positivo (Alucinação de Cache)** | Nulo | Requer *thresholds* rigorosos e particionamento |
| **Latência na Borda (Edge)** | < 1ms | ~20-40ms (Embedding + Vector Search) |
| **Complexidade Arquitetural** | Baixa | **Média** (Redis Vector + SLM Embedding) |

## 4. Decisão e Justificativa ("Killer Justification")

**Decisão:** Escolhemos a **Opção B (Semantic Caching no Redis)**.

**Killer Justification:**
Em aplicações de IA Generativa em larga escala, **a inferência mais rápida e barata é aquela que você não precisa fazer.** 

O *Semantic Caching* atua como um verdadeiro escudo financeiro (*FinOps Shield*). Ao investirmos alguns milissegundos na borda para vetorizar a intenção, conseguimos interceptar a imensa cauda longa de perguntas sazonais do Grupo Boticário. 

Para mitigar o risco de falsos positivos (como confundir a intenção de consultar pedidos diferentes), desenhamos uma estratégia de **Cache Particionado**: aplicamos o *Semantic Cache* estritamente para o domínio de Dúvidas de Catálogo e Regras de Negócio (RAG). Para o subgrafo de APIs Transacionais (pedidos/estoque), que depende de parâmetros exatos (ex: CPF e Número do Pedido), o roteador semântico (Router) dá um *bypass* no cache, garantindo que operações determinísticas sempre batam na fonte da verdade (ERP). Essa combinação maximiza a economia sem comprometer a exatidão das transações.