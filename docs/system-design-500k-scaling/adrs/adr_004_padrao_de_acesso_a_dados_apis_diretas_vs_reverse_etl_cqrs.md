# ADR 004: Padrão de Acesso a Dados (Tools) - APIs Transacionais Diretas vs. CQRS e Reverse ETL

## 1. Título e Contexto
- **Data:** 22 de Outubro de 2026
- **Status:** Aceito
- **Domínio:** Engenharia de Dados / Integração de APIs

No contexto de suporte à Revendedora (Plataforma Agentes GB), os *LangGraph Workers* precisam consumir dados reais utilizando *Tools* (ferramentas do LLM). As intenções variam entre consultar informações transacionais críticas (ex: "Qual o status do meu pedido de hoje?") e dados analíticos consolidados (ex: "Quantos pontos faltam para eu bater a meta do Ciclo 15?"). 

Com 500.000 revendedoras acessando simultaneamente, cada chamada de *Tool* orquestrada pelo LLM pode gerar um pico brutal de requisições de leitura. O desafio é definir a arquitetura de integração de dados que evite indisponibilizar os sistemas legados (ERP/OMS) e que não comprometa a latência (TTFT < 2s), garantindo o controle rigoroso da performance e custo.

## 2. Opções Consideradas

### Opção A: Acesso via APIs Diretas (Synchronous API Gateway)
Todas as *Tools* do LangGraph batem diretamente nos sistemas de origem. Para pedidos/estoque, o agente consulta a API do ERP/OMS. Para metas e indicadores, o agente faz consultas via API que batem diretamente no Data Lake (BigQuery).
* **Prós:** Arquitetura simples de desenvolver no MVP; os dados acessados estão sempre 100% atualizados (consistência forte).
* **Contras:** Alto risco de causar um *DDoS* (Negação de Serviço) nos sistemas internos (ERP) durante picos (ex: Black Friday). Além disso, consultar um banco OLAP (BigQuery) em tempo real via agente gera latência de vários segundos, quebrando a experiência de *streaming* (SLA de TTFT < 2s).

### Opção B: Arquitetura Híbrida (CQRS + Reverse ETL)
Segregação de responsabilidades de leitura baseada no perfil da informação:
1. **Dados Transacionais (Pedidos/Estoque):** Consulta em tempo real nas APIs do ERP, mas protegidas estritamente por *Circuit Breakers* e limitadores de taxa (Rate Limiting).
2. **Dados Analíticos (Indicadores do Ciclo/Perfil):** O agente não acessa o BigQuery. Em vez disso, *pipelines* batch (Airflow/dbt) realizam a extração do Data Lake e injetam em um banco de dados operacional de leitura rápida (*FastDB* - ex: PostgreSQL ou Firestore) - padrão conhecido como *Reverse ETL*.
* **Prós:** Protege sistemas core legados; latência de leitura analítica cai de segundos para milissegundos; isola gargalos de processamento.
* **Contras:** Complexidade arquitetural moderada; introduz *Eventual Consistency* (consistência eventual) para os dados analíticos (as metas da revendedora podem ter defasagem de alguns minutos/horas dependendo do *job* do Airflow).

## 3. Matriz de Trade-off

| Critério | Opção A (APIs Diretas para Tudo) | Opção B (Híbrida: CQRS + Reverse ETL) |
| :--- | :--- | :--- |
| **Proteção de Sistemas Legados (ERP)** | Péssima (Risco de queda em massa) | **Excelente** (Rate Limits + Offload de leitura) |
| **Latência para Dados Analíticos** | Alta (Segundos - inviabiliza TTFT) | **Baixa** (Milissegundos via FastDB) |
| **Consistência dos Dados Analíticos** | Forte (Tempo real) | **Eventual** (Sincronização em Batch/Micro-batch) |
| **Esforço de Engenharia de Dados** | Baixo | **Alto** (Requer Airflow/dbt pipelines) |
| **Custo de Consultas (FinOps)** | Alto (Cobrança por query no BQ) | **Otimizado** (Leitura barata no FastDB) |

## 4. Decisão e Justificativa ("Killer Justification")

**Decisão:** Escolhemos a **Opção B (Arquitetura Híbrida com CQRS e Reverse ETL)**.

**Killer Justification:**
A regra de ouro ao plugar LLMs autônomos em infraestruturas corporativas é: **você não deve permitir que um aumento imprevisível de intenções dos usuários derrube a operação primária da empresa**.

Ao adotarmos a segregação (CQRS), criamos "barreiras de contenção". As *Tools* de consultas analíticas (como acompanhamento de metas do ciclo e progresso de pontos) representam grande parte do volume de interações. Retirar essa carga de leitura do ERP/BigQuery e movê-la para um *FastDB* via *Reverse ETL* não apenas salva a empresa de gargalos técnicos, como derruba o custo (FinOps). 

A pequena defasagem (*Eventual Consistency*) introduzida nos dados do ciclo é um *trade-off* de negócio totalmente aceitável (ex: a revendedora ver a pontuação atualizada com 15 minutos de atraso é preferível a ela não conseguir usar o agente por *timeout*). Por outro lado, para a *Tool* de status de pedido e disponibilidade de estoque, mantemos o acesso direto à API do OMS, garantindo que a revendedora não venda um produto esgotado, mas sempre isolado por *Circuit Breakers* para prevenir falhas em cascata.