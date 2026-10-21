# Diagramas de Sequência: Casos de Uso Core
**Projeto:** Agente de Suporte à Revendedora (Plataforma Agentes GB)

**Propósito:** Mapear a jornada técnica dos três casos de uso principais, evidenciando as decisões de orquestração (LangGraph), as restrições de negócio (Guardrails) e a latência percebida (Streaming SSE).

## 1. Caso de Uso: Consulta ao Catálogo (Fase de Pré-Venda)

**Cenário:** A revendedora está interagindo com um cliente e precisa saber rapidamente detalhes de um produto ou se ele está em promoção no ciclo atual.

**Desafio Técnico:** O orquestrador deve decidir não usar uma API transacional, mas sim realizar uma busca vetorial no catálogo do ciclo (fonte original em PDF, transcrita em Markdown no MVP para ingestão).

```mermaid
sequenceDiagram
    autonumber
    actor R as Revendedora
    participant UX as Frontend (Streamlit / Simulador Web)
    participant API as FastAPI
    participant LG as LangGraph (Orquestrador)
    participant RAG as VectorDB (ChromaDB Local)

    R->>UX: Digita: "O Malbec está na promoção no ciclo 15?"
    UX->>API: POST /api/v1/chat/stream {session_id, message}
    
    rect rgb(240, 248, 255)
        Note right of API: Orquestração e Raciocínio
        API->>LG: Aciona grafo (.astream_events v2)
        LG->>LG: Recupera histórico da sessão no Redis (thread_id)
        LG->>LG: LLM decide usar a Tool 'consultar_catalogo'
    end

    rect rgb(255, 250, 205)
        Note right of LG: Pipeline RAG
        LG->>RAG: Gera embedding local (all-MiniLM-L6-v2) e busca: "Malbec promoção ciclo 15"
        RAG-->>LG: Retorna Top-3 Chunks de Texto do PDF do Catálogo
    end

    rect rgb(240, 255, 240)
        Note right of LG: Síntese e Retorno
        LG->>LG: Sintetiza resposta usando os chunks recuperados
        LG-->>API: Stream dos tokens da resposta (on_chat_model_stream)
        API-->>UX: Yield via Server-Sent Events (SSE) data: {"chunk": "..."}
    end
    UX-->>R: Exibe mensagem: "Sim, o Malbec está com 20% de desconto..."
```
**Explicação da Decisão:** Este fluxo mostra que o LangGraph trata a base de conhecimento não como um passo obrigatório prévio (If/Else), mas como uma *Tool* à disposição do LLM. Isso reduz a latência e consumo de tokens quando a pergunta não exige leitura do catálogo.

---

## 2. Caso de Uso: Consulta Transacional (Fase de Fechamento/Pós-Venda)

**Cenário:** A revendedora precisa rastrear um pedido que o cliente final está cobrando.

**Desafio Técnico:** Extrair os parâmetros corretos do texto (Ex: Código do Pedido) e invocar a função Mock com injeção mandatória do CPF autenticado na sessão, sem confiar em CPFs digitados no chat.

```mermaid
sequenceDiagram
    autonumber
    actor R as Revendedora
    participant UX as Frontend (Streamlit / Simulador Web)
    participant API as FastAPI
    participant LG as LangGraph (Orquestrador)
    participant Tool as Mock API (Pedidos)

    R->>UX: Digita: "Onde está meu pedido PED-1001?"
    UX->>API: POST /api/v1/chat/stream {session_id, cpf: "52998224725", message}
    
    rect rgb(240, 248, 255)
        Note right of API: Raciocínio com Contexto
        API->>LG: Aciona grafo passando session_id e CPF da sessão
        LG->>LG: Carrega estado do Redis pelo thread_id
        LG->>LG: LLM extrai ID "PED-1001" e emite tool_call 'buscar_status_pedido'
    end

    alt CPF presente na sessão
        rect rgb(255, 240, 245)
            Note right of LG: Ação Transacional Segura (ADR-003)
            LG->>LG: Nó 'executar_api' sobrescreve args com o CPF da sessão
            LG->>Tool: Invoca buscar_status_pedido(cpf="52998224725", id_pedido="PED-1001")
            Tool->>Tool: Valida se pedido pertence ao CPF da sessão (Controle PII)
            Tool-->>LG: Retorna payload JSON: {status: "sucesso", status_entrega: "Em transporte"}
        end
    else CPF ausente na sessão
        rect rgb(255, 228, 225)
            Note right of LG: Bloqueio de Segurança Determinístico
            LG->>LG: Nó 'executar_api' identifica ausência de CPF na sessão
            LG-->>LG: Retorna ToolMessage de erro: CPF_SESSAO_AUSENTE (Tool não é invocada)
        end
    end

    rect rgb(240, 255, 240)
        Note right of LG: Formatação Final
        LG->>LG: Converte retorno estruturado em linguagem natural amigável
        LG-->>API: Stream dos tokens da resposta
        API-->>UX: Yield via Server-Sent Events (SSE) data: {"chunk": "..."}
    end
    UX-->>R: Exibe: "Seu pedido PED-1001 está Em transporte via Jadlog..."
```
**Explicação da Decisão:** A validação de quem é o dono do pedido não fica a cargo da "boa vontade" do LLM. O CPF é extraído da requisição autenticada da API e repassado compulsoriamente para a Tool pelo nó `executar_api` (ADR-003). Se a sessão não contiver CPF, a Tool nem sequer é executada. Isso blinda completamente o sistema contra ataques de *Prompt Injection* onde o usuário tentaria pedir dados de terceiros.

---

## 3. Caso de Uso: Disparo de Guardrail (Proteção de Margem/PII)

**Cenário:** A revendedora tenta utilizar o assistente de forma indevida, perguntando informações sigilosas sobre outras consultoras ou tentando calcular margens de lucro indevidas.

**Desafio Técnico:** O sistema deve abortar a execução de Tools e retornar uma negativa imediata e educada, conforme a exigência estrita do case.

```mermaid
sequenceDiagram
    autonumber
    actor R as Revendedora
    participant UX as Frontend (Streamlit / Simulador Web)
    participant API as FastAPI
    participant LG as LangGraph (Orquestrador)

    R->>UX: Digita: "Qual a margem de lucro da revendedora Maria?"
    UX->>API: POST /api/v1/chat/stream {session_id, message}
    
    rect rgb(240, 248, 255)
        Note right of API: Filtro Primário (System Prompt)
        API->>LG: Aciona grafo
        LG->>LG: Injeta System Prompt contendo as regras invioláveis de Segurança
    end

    rect rgb(255, 228, 225)
        Note right of LG: Atuação do Guardrail Cognitivo
        LG->>LG: LLM reconhece a violação da regra de Margem/PII
        LG->>LG: Orquestrador decide NÃO acionar nenhuma Tool
    end

    rect rgb(240, 255, 240)
        Note right of LG: Resposta Segura
        LG->>LG: Gera resposta de recusa elegante
        LG-->>API: Stream dos tokens da recusa
        API-->>UX: Yield via Server-Sent Events (SSE) data: {"chunk": "..."}
    end
    UX-->>R: Exibe: "Informações comerciais e margens de lucro de outras revendedoras são confidenciais..."
```
**Explicação da Decisão:** Este diagrama ilustra o padrão de Defesa em Profundidade, demonstrando que não há desperdício de latência nem de custos (FinOps) com chamadas desnecessárias ao banco de dados. A requisição maliciosa ou fora de escopo é encerrada precocemente na camada cognitiva do LangGraph.