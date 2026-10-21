# ADR-001: Gestão de Estado e Memória em Larga Escala

**Data:** 17/10/2026

**Status:** Aceito

## Contexto
O agente precisa manter o contexto da conversa isolado por revendedora (`session_id` ou `thread_id`). Para o MVP local, armazenar esse estado na memória RAM resolve o problema. Contudo, o sistema deve ser desenhado para escalar até 500 mil revendedoras simultâneas, cenário onde instâncias múltiplas do FastAPI precisarão compartilhar o estado da conversa, e manter históricos longos estourará a janela de contexto do LLM.

## Decisão
1. **MVP:** O checkpointer do LangGraph é o **Redis** (`AsyncRedisSaver`, pacote `langgraph-checkpoint-redis`), executado em container `redis:8` no `docker-compose` e configurado via `REDIS_URL`, com TTL das sessões (`CHECKPOINT_TTL_MINUTES`). O estado sobrevive a reinícios da API e pode ser compartilhado entre réplicas.
   - **Fallback:** sem `REDIS_URL` (testes/dev local) ou com Redis indisponível na subida, o grafo utiliza o `MemorySaver` nativo, registrando aviso, sem interromper o atendimento.
2. **Arquitetura TO-BE (Escala):** Evolução do Redis single-node para um **cluster Redis** gerenciado.
3. **Gerenciamento de Histórico (Sliding Window):** Em vez de injetar todo o histórico a cada chamada, manteremos apenas as últimas N interações brutas no Redis. Mensagens antigas serão sumarizadas por um LLM menor (processo assíncrono) para persistência de longo prazo no BigQuery.

## Consequências
*   **Positivas:** O código do MVP permanece simples de testar, mas a arquitetura já prevê resiliência, baixa latência na recuperação de estado distribuído (Redis) e controle estrito de custos com tokens (FinOps).
*   **Negativas:** A transição para Redis exigirá gestão de infraestrutura adicional (Helm charts, clusters) no ambiente produtivo.