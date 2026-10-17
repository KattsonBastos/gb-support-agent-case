# Diagramas de Sequência: Casos de Uso Core
**Projeto:** Agente de Suporte à Revendedora (Plataforma Agentes GB)
**Propósito:** Mapear a jornada técnica dos três casos de uso principais, evidenciando as decisões de orquestração (LangGraph), as restrições de negócio (Guardrails) e a latência percebida (Streaming SSE)[cite: 1, 2].

## 1. Caso de Uso: Consulta ao Catálogo (Fase de Pré-Venda)
**Cenário:** A revendedora está interagindo com um cliente e precisa saber rapidamente detalhes de um produto ou se ele está em promoção no ciclo atual.
**Desafio Técnico:** O orquestrador deve decidir não usar uma API transacional, mas sim realizar uma busca vetorial no arquivo sintético do catálogo.

```mermaid
sequenceDiagram
    autonumber
    actor R as Revendedora
    participant UX as Frontend (Streamlit)
    participant API as FastAPI
    participant LG as LangGraph (Orquestrador)
    participant RAG as VectorDB (Catálogo)

    R->>UX: Digita: "O Malbec está na promoção no ciclo 15?"
    UX->>API: POST /chat/stream {session_id, message}
    
    rect rgb(240, 248, 255)
        Note right of API: Orquestração e Raciocínio
        API->>LG: Aciona grafo (.astream_events)
        LG->>LG: Recupera histórico (MessagesState)
        LG->>LG: LLM decide usar a Tool 'consultar_catalogo'
    end

    rect rgb(255, 250, 205)
        Note right of LG: Pipeline RAG
        LG->>RAG: Executa busca semântica: "Malbec promoção ciclo 15"
        RAG-->>LG: Retorna Top-3 Chunks de Texto do PDF Mockado
    end

    rect rgb(240, 255, 240)
        Note right of LG: Síntese e Retorno
        LG->>LG: Sintetiza resposta usando os chunks
        LG-->>API: Stream dos tokens da resposta
        API-->>UX: Yield via Server-Sent Events (SSE)
    end
    UX-->>R: Exibe mensagem: "Sim, o Malbec está com 20% de desconto."
```
**Explicação da Decisão:** Este fluxo mostra que o LangGraph trata a base de conhecimento não como um passo obrigatório (If/Else), mas como uma *Tool* à disposição do LLM. Isso reduz a latência quando a pergunta não exige leitura do catálogo.

---

## 2. Caso de Uso: Consulta Transacional (Fase de Fechamento/Pós-Venda)
**Cenário:** A revendedora precisa consultar o estoque para fechar uma venda ou rastrear um pedido que o cliente final está cobrando.
**Desafio Técnico:** Extrair os parâmetros corretos do texto (Ex: CPF, Código do Pedido) e invocar a função Mock, garantindo que os dados pertencem à revendedora daquela sessão.

```mermaid
sequenceDiagram
    autonumber
    actor R as Revendedora
    participant UX as Frontend (Streamlit)
    participant API as FastAPI
    participant LG as LangGraph (Orquestrador)
    participant Tool as Mock API (Pedidos/Estoque)

    R->>UX: Digita: "Onde está meu pedido 9876?"
    UX->>API: POST /chat/stream {session_id, cpf, message}
    
    rect rgb(240, 248, 255)
        Note right of API: Raciocínio com Contexto
        API->>LG: Aciona grafo
        LG->>LG: Injeta CPF da sessão no contexto base
        LG->>LG: LLM extrai ID "9876" e decide usar 'buscar_status_pedido'
    end

    rect rgb(255, 240, 245)
        Note right of LG: Ação Transacional (Function Calling)
        LG->>Tool: Invoca buscar_status_pedido(cpf_da_sessao, "9876")
        Tool->>Tool: Valida se pedido pertence ao CPF (Controle PII)
        Tool-->>LG: Retorna payload JSON: {status: "Em Transporte", transp: "LogB"}
    end

    rect rgb(240, 255, 240)
        Note right of LG: Formatação Final
        LG->>LG: Converte JSON em linguagem natural
        LG-->>API: Stream dos tokens da resposta
        API-->>UX: Yield via Server-Sent Events (SSE)
    end
    UX-->>R: Exibe: "Seu pedido 9876 já foi enviado via LogB."
```
**Explicação da Decisão:** A validação de quem é o dono do pedido não fica a cargo da "boa vontade" do LLM. O CPF é extraído da requisição autenticada do FastAPI e repassado para a Tool (Passo 5 e 6). Isso blinda o sistema contra ataques de *Prompt Injection* onde o usuário tentaria pedir dados de terceiros.

---

## 3. Caso de Uso: Disparo de Guardrail (Proteção de Margem/PII)
**Cenário:** A revendedora tenta utilizar o assistente de forma indevida, perguntando informações sigilosas sobre outras consultoras ou tentando calcular margens de lucro indevidas.
**Desafio Técnico:** O sistema deve abortar a execução de Tools e retornar uma negativa imediata e educada, conforme a exigência estrita do case.

```mermaid
sequenceDiagram
    autonumber
    actor R as Revendedora
    participant UX as Frontend (Streamlit)
    participant API as FastAPI
    participant LG as LangGraph (Orquestrador)

    R->>UX: Digita: "Qual a margem de lucro da revendedora Maria?"
    UX->>API: POST /chat/stream {session_id, message}
    
    rect rgb(240, 248, 255)
        Note right of API: Filtro Primário (System Prompt)
        API->>LG: Aciona grafo
        LG->>LG: Carrega System Prompt contendo as travas de Segurança
    end

    rect rgb(255, 228, 225)
        Note right of LG: Atuação do Guardrail
        LG->>LG: LLM reconhece a violação da regra de Margem/PII
        LG->>LG: Orquestrador decide NÃO acionar nenhuma Tool
    end

    rect rgb(240, 255, 240)
        Note right of LG: Resposta Segura
        LG->>LG: Gera resposta de recusa
        LG-->>API: Stream dos tokens da recusa
        API-->>UX: Yield via Server-Sent Events (SSE)
    end
    UX-->>R: Exibe: "Desculpe, por questões de segurança e privacidade, não posso fornecer informações sobre margens de lucro ou dados de outras consultoras."
```
**Explicação da Decisão:** Este diagrama ilustra o padrão de Defesa em Profundidade. Mostra para os avaliadores que você não gastou latência e dinheiro (FinOps) chamando o banco de dados desnecessariamente. A requisição maliciosa ou fora de escopo morre rapidamente na camada cognitiva do LangGraph.