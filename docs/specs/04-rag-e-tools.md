# Domínio de Conhecimento (RAG) e Ferramentas (Tools)
**Projeto:** Agente de Suporte à Revendedora (Plataforma Agentes GB)
**Arquivo:** `docs/specs/04-rag-e-tools.md`
**Propósito:** Isolar a lógica de ingestão do catálogo, busca vetorial e a simulação (Mock) dos conectores transacionais.

## 1. Geração da Base Sintética (Catálogo)
Criar um arquivo em `data/catalogo_ciclo_15.md` simulando o catálogo em PDF exigido no desafio. O conteúdo deve ter estrutura hierárquica clara para facilitar o chunking.
*   **Conteúdo Mínimo:** Seções de Perfumaria (Boticário e Eudora), Maquiagem e Cuidados. Incluir promoções ativas ("Desconto de 20% no Malbec", "Combo Lily por R$ 199").

## 2. Pipeline de RAG (Retrieval-Augmented Generation)
Implementar um RAG simples, focado em precisão contextual em vez de complexidade de infraestrutura para o MVP.
*   **Vector Store:** Usar ChromaDB local (em memória persistida no disco).
*   **Embeddings:** Utilizar um modelo leve e local (ex: `HuggingFaceEmbeddings` com `all-MiniLM-L6-v2` ou similar via LangChain) para não onerar custos da API (OpenAI/Anthropic) no cálculo de similaridade vetorial.
*   **Chunking:** Utilizar `RecursiveCharacterTextSplitter` com tamanho otimizado para pequenos parágrafos de catálogo.

## 3. Interface da Tool: Consultar Catálogo
A função que será exposta ao LangGraph como ferramenta.
*   **Nome:** `consultar_catalogo`
*   **Descrição (LLM Input):** "Use esta ferramenta para buscar informações sobre produtos, preços e promoções do Ciclo atual."
*   **Comportamento:** Recebe uma `query` em texto, executa a busca de similaridade no Vector Store e retorna uma string formatada concatenando os `page_content` dos top-K resultados.

## 4. Interface da Tool: Consultar Pedido (Mock API)
Simulação do banco de dados analítico/transacional do Grupo Boticário.
*   **Nome:** `buscar_status_pedido`
*   **Descrição (LLM Input):** "Use esta ferramenta para consultar o status de entrega, transportadora ou estoque de um pedido. Requer o CPF da revendedora e o ID do pedido."
*   **Contrato de Entrada:** `cpf` (string), `id_pedido` (string).
*   **Comportamento Mock:** 
    *   Um dicionário local (`mock_db`) mapeia `id_pedido` para seus respectivos status.
    *   Se o CPF fornecido pelo modelo (extraído do estado) não coincidir com o CPF "dono" do pedido no Mock, levantar erro de acesso não autorizado (atendendo às regras de proteção de PII).
    *   Retorna JSON serializado em string com as informações de rastreio ou nota fiscal.