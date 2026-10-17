"""Pipeline de RAG (Retrieval-Augmented Generation) para o Catálogo do Grupo Boticário."""

from pathlib import Path
from typing import List, Optional
import chromadb
from chromadb.utils import embedding_functions
from langchain_core.tools import tool
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pydantic import BaseModel, Field

# Caminhos padrão do projeto
DEFAULT_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
DEFAULT_CATALOG_PATH = DEFAULT_DATA_DIR / "catalogo_ciclo_15.md"
DEFAULT_CHROMA_DIR = DEFAULT_DATA_DIR / "chromadb"

COLLECTION_NAME = "catalogo_ciclo_15"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"

# Singleton global para cache do cliente ChromaDB
_collection_instance: Optional[chromadb.Collection] = None


class CatalogQueryInput(BaseModel):
    """Parâmetros de entrada para a consulta semântica ao catálogo."""

    query: str = Field(
        ...,
        description="Termo ou pergunta sobre produtos, marcas, códigos, valores ou promoções do catálogo do ciclo atual.",
        examples=["promoção do Malbec", "preço do combo lily", "shampoo eudora siage"],
    )


def _get_embedding_function() -> embedding_functions.SentenceTransformerEmbeddingFunction:
    """Retorna a função de embedding local leve baseada em sentence-transformers."""
    return embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBEDDING_MODEL_NAME
    )


def ingest_catalog(
    collection: chromadb.Collection,
    catalog_path: Optional[Path] = None,
    chunk_size: int = 600,
    chunk_overlap: int = 120,
) -> int:
    """Lê o arquivo Markdown do catálogo, realiza o chunking e indexa no ChromaDB."""
    target_path = catalog_path or DEFAULT_CATALOG_PATH

    if not target_path.exists():
        raise FileNotFoundError(f"Arquivo de catálogo não encontrado em: {target_path}")

    content = target_path.read_text(encoding="utf-8")

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n## ", "\n### ", "\n\n", "\n", " "],
        keep_separator=True,
    )

    chunks: List[str] = text_splitter.split_text(content)

    ids = [f"chunk_{i:04d}" for i in range(len(chunks))]
    metadatas = [
        {"source": target_path.name, "chunk_index": i}
        for i in range(len(chunks))
    ]

    # Armazena os chunks no ChromaDB
    collection.add(
        documents=chunks,
        ids=ids,
        metadatas=metadatas,
    )

    return len(chunks)


def get_or_create_vectorstore(
    persist_directory: Optional[Path] = None,
    catalog_path: Optional[Path] = None,
) -> chromadb.Collection:
    """Inicializa ou recupera a coleção vetorial no ChromaDB persistido localmente."""
    global _collection_instance

    if _collection_instance is not None:
        return _collection_instance

    chroma_dir = persist_directory or DEFAULT_CHROMA_DIR
    chroma_dir.mkdir(parents=True, exist_ok=True)

    client = chromadb.PersistentClient(path=str(chroma_dir))
    embedding_fn = _get_embedding_function()

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_fn,
        metadata={"hnsw:space": "cosine"},
    )

    # Ingestão idempotente: só insere dados se a coleção estiver vazia
    if collection.count() == 0:
        ingest_catalog(collection, catalog_path=catalog_path)

    _collection_instance = collection
    return _collection_instance


def _consultar_catalogo_core(query: str, k: int = 3) -> str:
    """Executa a busca de similaridade vetorial no catálogo e formata os trechos relevantes."""
    query_limpa = query.strip()
    if not query_limpa:
        return "Nenhum termo de busca fornecido para consulta ao catálogo."

    collection = get_or_create_vectorstore()
    results = collection.query(
        query_texts=[query_limpa],
        n_results=k,
    )

    documents = results.get("documents", [[]])[0]
    if not documents:
        return f"Nenhuma informação encontrada no catálogo para o termo: '{query_limpa}'."

    blocos: List[str] = []
    for i, doc in enumerate(documents, start=1):
        blocos.append(f"--- Trecho do Catálogo [{i}] ---\n{doc.strip()}")

    return "\n\n".join(blocos)


@tool(
    "consultar_catalogo",
    args_schema=CatalogQueryInput,
    return_direct=False,
)
def consultar_catalogo(query: str, k: int = 3) -> str:
    """Use esta ferramenta para buscar informações sobre produtos, preços e promoções do Ciclo atual."""
    return _consultar_catalogo_core(query=query, k=k)
