# ADR 005: Gestão de Estado (LangGraph Checkpointer) - Redis Cluster vs. PostgreSQL

## 1. Título e Contexto
- **Data:** 22 de Outubro de 2026
- **Status:** Aceito
- **Domínio:** Orquestração de IA / Gestão de Estado

Na Plataforma Agentes GB, a interação via WhatsApp exige que o agente mantenha o contexto da conversa. Se a revendedora pergunta "qual o status do meu último pedido?" e depois "qual a transportadora dele?", o LLM precisa acessar o histórico daquela `thread_id`. 

Na arquitetura TO-BE, desenhada para 500.000 revendedoras simultâneas com *LangGraph Workers* desacoplados consumindo uma fila (Kafka/PubSub), os *Workers* são *stateless* (sem estado). Cada mensagem processada exige que o *Worker* recupere o estado completo do grafo (leitura), faça a inferência, e salve o novo estado (escrita). O desafio é garantir que essa constante operação de I/O não estoure a latência (SLA de TTFT < 2s) e não crie um custo de armazenamento (FinOps) insustentável.

## 2. Opções Consideradas

### Opção A: Banco de Dados Relacional (PostgreSQL / Cloud SQL)

Uso de um banco de dados transacional clássico para persistir o histórico de conversas do LangGraph (ex: utilizando o `AsyncPostgresSaver`).

* **Prós:** Altamente durável (ACID); permite consultas analíticas complexas sobre o histórico de conversas via SQL padrão; tecnologia amplamente dominada pelos times de engenharia corporativos.
* **Contras:** Alto overhead de *Connection Pooling* (500k requisições podem esgotar o pool do Postgres facilmente, exigindo um PgBouncer robusto); latência atrelada ao disco físico (I/O); crescimento infinito da base de dados, exigindo *jobs* pesados (CRON) para expurgar conversas antigas.

### Opção B: Datastore em Memória (Redis Cluster)

Uso de um cluster Redis para armazenar o estado das *threads* como pares de chave-valor. O estado é serializado e salvo na RAM (ex: utilizando integração via `RedisSaver` ou custom checkpointer).

* **Prós:** Latência ultrabaixa (sub-milissegundo), vital para não adicionar atraso antes da chamada ao LLM; suporte nativo a expiração de chaves (TTL - Time-To-Live); elimina o *connection churn* através de multiplexação eficiente (pipelines); o mesmo cluster pode ser reutilizado para o cache semântico e para o Pub/Sub de SSE.
* **Contras:** A memória RAM é financeiramente mais cara que o armazenamento em disco; natureza volátil (embora atenuada por backups RDB/AOF, não é ideal para armazenamento de longo prazo).

## 3. Matriz de Trade-off

| Critério | Opção A (PostgreSQL) | Opção B (Redis Cluster) |
| :--- | :--- | :--- |
| **Latência de Leitura/Escrita** | Média (~10-50ms por operação) | **Mínima** (< 1ms) |
| **Suporte a 500k Conexões/Picos** | Difícil (Requer PgBouncer e réplicas) | **Excelente** (Clusterização escalável) |
| **Gestão de Ciclo de Vida (Limpeza)** | Manual / Exige rotinas auxiliares | **Automática** (TTL nativo) |
| **Custo de Armazenamento** | Baixo (Disco) | Alto (RAM - mitigado pelo TTL) |
| **Risco de Gargalo no SLA (TTFT)** | Alto (I/O bloqueante) | **Nulo** |

## 4. Decisão e Justificativa ("Killer Justification")

**Decisão:** Escolhemos a **Opção B (Redis Cluster)**.

**Killer Justification:**
A decisão fundamenta-se na natureza do nosso domínio: **conversas de suporte no WhatsApp são eventos efêmeros**. Não faz sentido arquitetural ou financeiro tratar o estado ativo do grafo de orquestração (Checkpointer) como um dado relacional perpétuo.

Ao utilizarmos o Postgres para 500.000 sessões ativas, criaríamos um banco de dados que cresceria assustadoramente a cada minuto, com I/O de disco massivo e *connection pools* sobrecarregados, apenas para armazenar conversas que perdem o valor transacional em poucas horas. 

Com o **Redis Cluster**, aplicamos um *Time-To-Live* (TTL) rigoroso nas chaves (por exemplo, 24 horas após a última interação). Isso cria uma mecânica de FinOps perfeita: a memória consumida é apenas a estritamente necessária para as sessões ativas no dia. Assim que a revendedora para de interagir e o ciclo de atenção termina, o Redis apaga o estado automaticamente, sem exigir nenhum *job* de limpeza. Além disso, a latência sub-milissegundo do Redis assegura que os *Workers* restaurem o contexto instantaneamente, garantindo a promessa de devolver o primeiro token (TTFT) em menos de 2 segundos.