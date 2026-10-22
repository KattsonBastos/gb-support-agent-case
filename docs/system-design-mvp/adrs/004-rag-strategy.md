# ADR-004: Estratégia de Ingestão e Chunking para RAG

- **Data:** 17/10/2026
- **Status:** Aceito

## Contexto
O assistente precisa responder a dúvidas sobre os produtos em promoção no ciclo atual, consumindo uma base sintética que simula um catálogo em PDF. A estratégia de divisão desse texto (chunking) impacta diretamente a precisão da resposta vetorial.

## Decisão
Para a base do catálogo, optou-se por **Chunking Semântico / Estrutural** (baseado em seções e produtos do Markdown) em vez de Chunking de Tamanho Fixo (ex: 500 caracteres rígidos). É utilizado um VectorDB em memória (como ChromaDB ou FAISS) com embeddings locais rápidos e gratuitos (ex: `all-MiniLM-L6-v2` da HuggingFace).

## Consequências
*   **Positivas:** O chunking semântico evita que a descrição de um produto (ex: Malbec) seja cortada ao meio, garantindo que o nome, preço e desconto fiquem no mesmo documento no espaço vetorial. O uso de embeddings locais zera o custo com APIs para a vetorização.
*   **Negativas:** Requer um pré-processamento mais cuidadoso (via `MarkdownHeaderTextSplitter`) em vez de um divisor simples por número de caracteres.