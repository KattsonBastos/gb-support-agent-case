# ADR-001: Gestão de Estado e Memória em Larga Escala
**Data:** [Data de Hoje]
**Status:** Aceito

## Contexto
O agente precisa manter o contexto da conversa isolado por revendedora (`session_id` ou `thread_id`). Para o MVP local, armazenar esse estado na memória RAM resolve o problema. Contudo, o sistema deve ser desenhado para escalar até 500 mil revendedoras simultâneas, cenário onde instâncias múltiplas do FastAPI precisarão compartilhar o estado da conversa, e manter históricos longos estourará a janela de contexto do LLM.

## Decisão
1. **MVP:** Utilizaremos o `MemorySaver` nativo do LangGraph (em memória/SQLite) para agilizar a entrega e os testes locais.
2. **Arquitetura TO-BE (Escala):** A arquitetura final prevê a substituição do checkpointer por um cluster **Redis**.
3. **Gerenciamento de Histórico (Sliding Window):** Em vez de injetar todo o histórico a cada chamada, manteremos apenas as últimas N interações brutas no Redis. Mensagens antigas serão sumarizadas por um LLM menor (processo assíncrono) para persistência de longo prazo no BigQuery.

## Consequências
*   **Positivas:** O código do MVP permanece simples de testar, mas a arquitetura já prevê resiliência, baixa latência na recuperação de estado distribuído (Redis) e controle estrito de custos com tokens (FinOps).
*   **Negativas:** A transição para Redis exigirá gestão de infraestrutura adicional (Helm charts, clusters) no ambiente produtivo.