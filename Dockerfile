# Dockerfile para a API do Agente de Suporte à Revendedora GB (FastAPI + LangGraph)
FROM python:3.11-slim

# Evita geração de bytecode .pyc e garante logs em tempo real
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Instala dependências do sistema necessárias para compilação eventual
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copia e instala as dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copia código-fonte, dados e templates
COPY src/ /app/src/
COPY data/ /app/data/
COPY templates/ /app/templates/

# Expõe a porta padrão do FastAPI
EXPOSE 8000

# Inicialização com uvicorn
CMD ["uvicorn", "src.api.routes:app", "--host", "0.0.0.0", "--port", "8000"]
