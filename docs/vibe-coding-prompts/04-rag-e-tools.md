Agora vamos construir a camada de dados baseada na spec @04-rag-e-tools.md.

1. Crie o arquivo data/catalogo_ciclo_15.md com os dados sintéticos de Boticário e Eudora conforme solicitado.

2. Crie o arquivo src/tools/order_status.py implementando o mock da função buscar_status_pedido. Não esqueça da validação de autorização (comparar o CPF).

3. Crie o arquivo src/rag/retriever.py configurando o ChromaDB em memória local, utilizando os embeddings locais do HuggingFace (all-MiniLM-L6-v2). Implemente a função consultar_catalogo.
Utilize tipagem estrita (Type Hints) em todas as funções, pois elas serão usadas como Tools do LangChain/LangGraph em seguida."