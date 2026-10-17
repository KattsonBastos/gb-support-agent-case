Crie uma nova sub-tarefa independente baseada no arquivo [04-rag-e-tools.md](file;file:///home/kattson/Documents/case-gb-spec-2/gb-support-agent-case/docs/specs/04-rag-e-tools.md) 

.Preciso que você crie o ecossistema de conectores:Gere o arquivo data/catalogo_ciclo_15.md com dados sintéticos de produtos e promoções Boticário/Eudora. Lembre-se que ele será usado em um equema de RAG

  Implemente src/tools/order_status.py com o mock da função buscar_status_pedido(cpf, id_pedido), garantindo a validação do CPF que definimos nas regras globais.   Implemente src/rag/retriever.py configurando o ChromaDB local e a função consultar_catalogo. Utilize type hints rigorosos