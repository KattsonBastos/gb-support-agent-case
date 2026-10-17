Atue como um Engenheiro DevOps Especialista em IA. Nossa aplicação já está estruturada com um backend (FastAPI \+ LangGraph) na pasta raiz/src e um frontend (Streamlit) na pasta frontend/. Precisamos dockerizar essa arquitetura para a entrega do MVP.

Crie os arquivos de infraestrutura Docker seguindo estritamente estas diretrizes:

1. **Crie um arquivo .dockerignore na raiz:**  
   * Ignore pastas como \_\_pycache\_\_, .venv, .git, \*.sqlite3 (exceto a pasta de dados montada), .env e arquivos do sistema operacional para evitar builds pesados.  
2. **Crie o Dockerfile para a API (na raiz do projeto):**  
   * Use a imagem base python:3.11-slim.  
   * Defina o diretório de trabalho como /app.  
   * Copie o requirements.txt da raiz e instale as dependências (FastAPI, LangGraph, LangFuse, etc.).  
   * Copie as pastas src/ e data/ para dentro do /app.  
   * Exponha a porta 8000.  
   * O comando de inicialização deve ser: uvicorn src.api.routes:app \--host 0.0.0.0 \--port 8000.  
3. **Crie o Dockerfile para o Frontend (dentro da pasta frontend/):**  
   * Use a imagem base python:3.11-slim.  
   * Defina o diretório de trabalho como /app.  
   * Copie o requirements.txt do frontend e instale as dependências (streamlit, requests).  
   * Copie o arquivo app.py.  
   * Exponha a porta 8501.  
   * O comando de inicialização deve ser: streamlit run app.py \--server.port=8501 \--server.address=0.0.0.0.  
4. **Crie o docker-compose.yml na raiz do projeto orquestrando os serviços:**  
   * **Network:** Crie uma rede interna (bridge) chamada agentes-network para que os containers se comuniquem isoladamente.  
   * **Serviço api:**  
     * Faça o build usando o Dockerfile da raiz.  
     * Mapeie a porta 8000:8000.  
     * **Volumes (Crucial):** Mapeie um volume local ./data:/app/data para garantir que o banco de dados do VectorStore (ChromaDB/RAG) e o arquivo de estado SQLite do LangGraph não sejam perdidos ao derrubar o container.  
     * Passe as variáveis de ambiente (ex: chaves do LangFuse para rastreamento, OpenAI/Google API Keys) lendo do arquivo .env local.  
     * Conecte na agentes-network.  
   * **Serviço frontend:**  
     * Faça o build apontando para a pasta ./frontend.  
     * Mapeie a porta 8501:8501.  
     * **Variável de Ambiente:** Injete API\_URL=http\://api:8000 (utilizando o nome do serviço para resolução DNS interna) para que o Streamlit saiba onde buscar o endpoint de Streaming SSE.  
     * Conecte na agentes-network.  
     * Configure o depends\_on apontando para o serviço api, garantindo que o frontend só suba quando o backend estiver disponível.

