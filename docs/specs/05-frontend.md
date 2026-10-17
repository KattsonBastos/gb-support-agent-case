# Interface de Simulação (UX)
**Projeto:** Agente de Suporte à Revendedora (Plataforma Agentes GB)
**Arquivo:** `docs/specs/05-frontend.md`
**Propósito:** Definir os requisitos para o frontend em Streamlit que simulará o canal de atendimento da Revendedora.

## 1. Stack Tecnológica
*   **Framework:** Streamlit (`streamlit`).
*   **Comunicação:** Biblioteca `requests` para chamadas HTTP e consumo de Server-Sent Events (SSE).

## 2. Componentes Visuais (Layout)
*   **Sidebar (Painel Lateral):**
    *   Título: "Configuração da Sessão".
    *   Input para o `CPF` da revendedora (Simulando a autenticação). Este CPF deve ser salvo no estado do Streamlit para ser enviado nas requisições.
    *   Botão para "Limpar Histórico" (Gera um novo `session_id` e limpa a tela).
*   **Área Principal (Chat):**
    *   Utilizar os componentes nativos `st.chat_message` e `st.chat_input`.
    *   O histórico de mensagens do lado do cliente deve ser mantido utilizando `st.session_state` para que as mensagens não desapareçam quando o Streamlit recarregar a tela.

## 3. Consumo da API (Streaming SSE)
*   **Endpoint:** O frontend deve fazer um `POST` para `http://localhost:8000/api/v1/chat/stream`.
*   **Payload:** O corpo da requisição deve enviar o `session_id` (gerado aleatoriamente no início da sessão), a `message` (texto do input) e o `cpf` (configurado na sidebar).
*   **Leitura do Stream:** O Streamlit deve iterar sobre os chunks de resposta do FastAPI. Como a API devolve o formato SSE (`data: {texto}\n\n`), o frontend deve extrair apenas a string útil e atualizá-la iterativamente no componente de chat usando um placeholder vazio para criar o efeito de "digitação em tempo real".