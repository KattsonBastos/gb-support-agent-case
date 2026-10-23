# ADR 009: Estratégia de Busca do RAG (Catálogo) - Semantic Search vs. Busca Híbrida com Re-ranking

## 1. Título e Contexto

- **Data:** 22 de Outubro de 2026
- **Status:** Aceito
- **Domínio:** AI Engineering / Recuperação de Informação (RAG)

Na Plataforma Agentes GB, a funcionalidade de consulta de catálogos promocionais (ex: "Quais as promoções de Malbec neste ciclo?") é o núcleo da assistência à revendedora. Essa etapa utiliza a arquitetura RAG (Retrieval-Augmented Generation). 

O desafio é que catálogos de cosméticos e perfumaria misturam **intenções semânticas** (ex: "perfume amadeirado barato") com **termos exatos e SKUs** (ex: "Malbec Gold 100ml", "Lily", "código 12345"). Utilizar apenas a busca vetorial tradicional (Dense Embeddings) frequentemente resulta em perda de precisão lexical, pois o modelo vetorial pode considerar "Arbo" e "Malbec" semanticamente próximos (ambos são fragrâncias masculinas), trazendo o contexto errado para o prompt do LLM e gerando alucinações nas respostas de vendas.

## 2. Opções Consideradas

### Opção A: Busca Vetorial Simples (Dense Embeddings + Cosine Similarity)

Uso padrão de modelos de embedding (ex: text-embedding-3-small ou Vertex Gecko) para vetorizar os chunks do PDF do catálogo e buscar no Vector DB utilizando apenas similaridade de cosseno.

* **Prós:** Arquitetura simples; latência de recuperação ultrabaixa (< 20ms); baixo custo computacional (apenas um modelo de embedding na entrada).
* **Contras:** Péssima performance para correspondência de palavras-chave exatas (Nomes de Marcas, Códigos de Produto). Falha em distinguir produtos da mesma categoria se a intenção do usuário for muito específica lexicalmente.

### Opção B: Busca Híbrida (Vector + Sparse/BM25) com Re-ranking (Cross-Encoder)

Implementação de um pipeline de recuperação em dois estágios:
1. **Recuperação (Retriever):** O Vector DB (ex: Pinecone / Vertex AI Search) executa uma Busca Híbrida, combinando *Dense Embeddings* (para capturar o significado) com *Sparse Embeddings / BM25* (para capturar palavras exatas). Trazemos um pool maior de documentos (ex: Top 20).
2. **Re-ranking:** Os 20 documentos recuperados são passados por um modelo *Cross-Encoder* (ex: Cohere Rerank ou BGE-Reranker) que cruza a query do usuário com cada documento simultaneamente para recalcular a relevância, entregando apenas o Top 3 para o LLM.

* **Prós:** Precisão ("Precision@K") altíssima, o padrão ouro do estado da arte em RAG; resolve o problema de SKUs e nomes próprios (Lexical) sem perder a compreensão de contexto (Semântico).
* **Contras:** Aumenta a latência geral de recuperação (adiciona \~100-200ms do modelo de Re-ranking); eleva a complexidade da pipeline de dados (MLOps) e introduz um custo computacional secundário na inferência.

## 3. Matriz de Trade-off

| Critério | Opção A (Busca Vetorial Simples) | Opção B (Híbrida + Re-ranking) | 
| ----- | ----- | ----- | 
| **Precisão em Nomes Próprios / SKUs** | Baixa | **Altíssima** | 
| **Compreensão Semântica** | Alta | **Alta** | 
| **Latência de Recuperação** | **Muito Baixa (< 20ms)** | Média (\~150ms) | 
| **Custo Computacional (FinOps)** | **Baixo** | Médio (Custo do Cross-Encoder) | 
| **Risco de Alucinação do LLM** | Alto (Contexto sujo) | **Muito Baixo** (Contexto super-refinado) | 

## 4. Decisão e Justificativa ("Killer Justification")

**Decisão:** Escolhemos a **Opção B (Busca Híbrida com Re-ranking)**, conforme mapeado na Seção 3 do `system-design-500k.md` ("A Esteira do RAG").

**Killer Justification:**
No contexto de Venda Direta do Grupo Boticário, **errar um produto recomendado ou confundir uma promoção é financeiramente inaceitável**. A confiança da revendedora no Agente é o ativo mais valioso da plataforma.

Entregar para o LLM Orquestrador um contexto sujo que contenha informações de "Arbo" quando a revendedora perguntou explicitamente de "Malbec", só porque o Vector DB achou os vetores similares, destrói a experiência. A Busca Híbrida assegura que a palavra exata "Malbec" tenha peso (BM25), enquanto o vetor entende o conceito de "promoção".

O acréscimo de \~150ms de latência e os centavos adicionais processando o *Cross-Encoder* são um trade-off excepcionalmente vantajoso. Ao filtrar o ruído e enviar apenas o Top 3 absoluto para o prompt final do LLM, nós não apenas evitamos a alucinação, como também **economizamos tokens de contexto na chamada principal**, compensando parcialmente o custo financeiro do Re-ranker. É a engenharia de precisão substituindo a força bruta de contexto.