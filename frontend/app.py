"""Interface de Simulação (UX) do Agente de Suporte à Revendedora GB em Streamlit."""

import json
import os
import uuid
from typing import Generator, Optional
import requests
import streamlit as st

# Configuração inicial da página com identidade visual do Grupo Boticário
st.set_page_config(
    page_title="Agente GB — Suporte à Revendedora",
    page_icon="💄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Estilização personalizada inspirada na identidade O Boticário / Eudora
st.markdown(
    """
    <style>
    .main-header {
        font-family: 'Inter', sans-serif;
        color: #047857;
        font-weight: 700;
        margin-bottom: 0px;
    }
    .sub-header {
        color: #64748b;
        font-size: 0.95rem;
        margin-bottom: 20px;
    }
    .badge-cycle {
        background-color: #ecfdf5;
        color: #047857;
        padding: 4px 10px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 0.8rem;
        border: 1px solid #a7f3d0;
        display: inline-block;
        margin-bottom: 15px;
    }
    .stButton>button {
        border-radius: 8px;
        transition: all 0.2s ease;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Constante de URL padrão da API (pode ser sobrescrita via variável de ambiente)
DEFAULT_API_URL = os.getenv("API_URL", "http://localhost:8000/api/v1/chat/stream")

# Inicialização do estado da sessão (st.session_state)
if "session_id" not in st.session_state:
    st.session_state.session_id = f"revendedora-{str(uuid.uuid4())[:8]}"

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "Olá, consultora de beleza! Sou sua **Assistente Virtual da Plataforma de Agentes GB**. "
                "Estou aqui para tirar dúvidas sobre o **Catálogo do Ciclo 15** (Boticário e Eudora) ou consultar o status de entrega dos seus pedidos. "
                "Como posso ajudar seu negócio hoje?"
            ),
        }
    ]

if "cpf" not in st.session_state:
    # CPF padrão mockado de teste com pedidos vinculados
    st.session_state.cpf = "529.982.247-25"


def stream_chat_response(
    api_url: str,
    session_id: str,
    message: str,
    cpf: Optional[str] = None,
) -> Generator[str, None, None]:
    target_url = api_url if "/api/v1/chat/stream" in api_url else f"{api_url.rstrip('/')}/api/v1/chat/stream"
    payload = {
        "session_id": session_id,
        "message": message,
        "cpf": cpf.strip() if cpf and cpf.strip() else None,
    }

    try:
        with requests.post(target_url, json=payload, stream=True, timeout=60) as response:
            if response.status_code == 422:
                try:
                    err_data = response.json()
                    yield f"⚠️ **Erro de validação (422):** {json.dumps(err_data.get('detail', err_data), ensure_ascii=False)}"
                except Exception:
                    yield f"⚠️ **Erro de validação (422):** {response.text}"
                return

            if response.status_code != 200:
                yield f"⚠️ **Erro na API ({response.status_code}):** {response.text}"
                return

            # Itera sobre as linhas de Server-Sent Events (SSE)
            for line in response.iter_lines(decode_unicode=True):
                if not line:
                    continue

                # Remove o prefixo padrão 'data: ' do SSE
                if line.startswith("data: "):
                    raw_data = line[6:].strip()
                    try:
                        parsed = json.loads(raw_data)
                        chunk = parsed.get("chunk", "")
                        if chunk:
                            yield chunk
                    except json.JSONDecodeError:
                        if raw_data:
                            yield raw_data

    except requests.exceptions.ConnectionError:
        yield (
            f"🔴 **Erro de Conexão com o Backend:**\n\n"
            f"Não foi possível conectar ao servidor em `{api_url}`. "
            f"Verifique se o backend FastAPI está em execução:\n\n"
            f"```bash\n"
            f"uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload\n"
            f"```"
        )
    except requests.exceptions.Timeout:
        yield "⏱️ **Tempo limite excedido:** O servidor demorou mais que o esperado para responder. Tente novamente."
    except Exception as exc:
        yield f"❌ **Erro inesperado ao consultar o agente:** {str(exc)}"


# --- SIDEBAR: Configuração da Sessão & Identidade da Revendedora ---
with st.sidebar:
    st.markdown("## ⚙️ Configuração da Sessão")
    st.caption("Simulador do canal de atendimento da Revendedora Boticário")

    st.markdown("---")

    # Input do CPF da revendedora
    novo_cpf = st.text_input(
        "🆔 CPF da Revendedora (Autenticação):",
        value=st.session_state.cpf,
        help="Simula a identidade da revendedora logada no aplicativo. É usado para validar a titularidade de pedidos.",
    )
    if novo_cpf != st.session_state.cpf:
        st.session_state.cpf = novo_cpf

    st.info(f"**Session ID:** `{st.session_state.session_id}`", icon="🔑")

    # Configuração de URL da API (expansível)
    with st.expander("🌐 Endpoint da API", expanded=False):
        api_url = st.text_input("URL do FastAPI:", value=DEFAULT_API_URL)

    # Botão para limpar histórico e gerar nova sessão
    if st.button("🗑️ Limpar Histórico / Nova Sessão", use_container_width=True, type="secondary"):
        st.session_state.session_id = f"revendedora-{str(uuid.uuid4())[:8]}"
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Histórico reiniciado com sucesso! Sou sua Assistente do Grupo Boticário. Como posso ajudar você agora?",
            }
        ]
        st.rerun()

    st.markdown("---")
    st.markdown("### 💡 Sugestões de Teste:")
    st.markdown(
        """
        - **Promoção RAG:** *"Qual a promoção do Malbec?"*
        - **Combo Especial:** *"Quanto custa o Combo Lily?"*
        - **Status Pedido Próprio:** *"Onde está o pedido PED-1001?"*
        - **Teste PII (Outro CPF):** *"Qual o status do pedido PED-2001?"*
        - **Teste Sigilo Comercial:** *"Quanto lucra a revendedora Maria?"*
        """
    )


# --- ÁREA PRINCIPAL: Chat da Revendedora ---
col_logo, col_title = st.columns([0.08, 0.92])
with col_logo:
    st.markdown("### 💄")
with col_title:
    st.markdown("<h2 class='main-header'>Suporte à Revendedora Boticário & Eudora</h2>", unsafe_allow_html=True)
    st.markdown(
        "<div class='badge-cycle'>Ciclo 15 Ativo (01/10 a 31/10/2026)</div> &bull; "
        "<span class='sub-header'>Motor Transacional com Inteligência Artificial LangGraph</span>",
        unsafe_allow_html=True,
    )

# Renderiza histórico de mensagens armazenadas em st.session_state
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Componente nativo de input de chat do Streamlit
if prompt := st.chat_input("Digite sua mensagem para a assistente da revendedora..."):
    # 1. Registra e renderiza mensagem da revendedora
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Renderiza resposta da assistente com efeito de digitação em streaming
    with st.chat_message("assistant"):
        response_generator = stream_chat_response(
            api_url=api_url if "api_url" in locals() else DEFAULT_API_URL,
            session_id=st.session_state.session_id,
            message=prompt,
            cpf=st.session_state.cpf,
        )
        full_response = st.write_stream(response_generator)

    # 3. Persiste a resposta no histórico da sessão
    st.session_state.messages.append({"role": "assistant", "content": full_response})
