Atue como um Engenheiro DevOps Especialista em LLMOps. Precisamos de atualizar a nossa infraestrutura dockerizada para incluir o LangFuse self-hosted, cumprindo o requisito de observabilidade da spec [06-observabilidade.md](file;file:///home/kattson/Documents/case-gb-spec-2/gb-support-agent-case/docs/specs/06-observabilidade.md) 

Reescreva o ficheiro `docker-compose.yml` na raiz do projeto para orquestrar os seguintes 4 serviços na rede `agentes-network`:

1. **Serviço `db-langfuse` (PostgreSQL):**  
   * Imagem: `postgres:15`.  
   * Variáveis: `POSTGRES_USER=postgres`, `POSTGRES_PASSWORD=postgres`, `POSTGRES_DB=langfuse`.  
   * Volume: Mapear um volume nomeado `langfuse-db-data:/var/lib/postgresql/data` para persistência.  
2. **Serviço `langfuse`:**  
   * Imagem: `langfuse/langfuse:latest`.  
   * Portas: `3000:3000`.  
   * Depende de: `db-langfuse`.  
   * Variáveis de ligação ao DB: `DATABASE_URL=postgresql://postgres:postgres@db-langfuse:5432/langfuse`.  
   * Variáveis de autenticação: `NEXTAUTH_URL=http://localhost:3000`, `NEXTAUTH_SECRET=mysecret`, `SALT=mysalt`.  
3. **Serviço `api` (O nosso Backend FastAPI):**  
   * Build a partir do diretório raiz.  
   * Portas: `8000:8000`.  
   * Volume: `./data:/app/data` (para o VectorDB local e SQLite).  
   * Variáveis de Ambiente: `LANGFUSE_PUBLIC_KEY=pk-lf-1234567890`, `LANGFUSE_SECRET_KEY=sk-lf-1234567890`, `LANGFUSE_HOST=http://langfuse:3000` (resolução de DNS interna do Docker).  
   * Depende de: `langfuse`.  
4. **Serviço `frontend` (Streamlit):**  
   * Build a partir de `./frontend`.  
   * Portas: `8501:8501`.  
   * Variável: `API_URL=http://api:8000`.  
   * Depende de: `api`.  
     * 

