# ADR 003: Mensageria e Desacoplamento - Apache Kafka vs. Google Cloud Pub/Sub

## 1. Título e Contexto
**Data:** 22 de Outubro de 2026
**Status:** Aceito
**Domínio:** Integração / Mensageria

A transição da Plataforma Agentes GB para suportar 500.000 revendedoras simultâneas baseia-se em um modelo *Event-Driven*. O tráfego de entrada (Webhooks do WhatsApp) é validado na borda e depositado em um *Message Broker*. Os *LangGraph Workers* consomem essas mensagens de forma assíncrona. Além disso, a arquitetura prevê que os eventos de telemetria e o fim das interações sejam enviados para o Data Lake (BigQuery) via mensageria (Streaming Ingestion).

O desafio central é escolher a tecnologia de *Broker* que suporte altíssimo *throughput* e picos de acessos imprevisíveis (sazonalidade de vendas, como Dia das Mães e Black Friday), garantindo a integração fluida com o ecossistema de dados, sem estourar o orçamento de operações (FinOps) e infraestrutura.

## 2. Opções Consideradas

### Opção A: Apache Kafka (Gerenciado - ex: Confluent Cloud ou MSK)
O padrão ouro para *event streaming* de alta performance. Baseado em um log distribuído imutável, particionamento rígido e retenção de longo prazo.
* **Prós:** Latência ultrabaixa (sub-milissegundo); garantia estrita de ordenação por partição; ecossistema gigantesco; excelente para replays de dados complexos.
* **Contras:** Alto custo de base (*always-on*), pois você paga por clusters e instâncias provisionadas, o que é ineficiente para tráfego com vales e picos (sazonalidade). Exige alto conhecimento operacional (Platform Engineering) para balancear partições (*rebalancing*) durante picos de 500k acessos. Integração com BigQuery exige manutenção de conectores dedicados (Kafka Connect).

### Opção B: Google Cloud Pub/Sub
Serviço de mensageria totalmente gerenciado, *serverless* e global do Google Cloud. Utiliza um modelo de tópicos e assinaturas (*Publish-Subscribe*).
* **Prós:** Escalabilidade instantânea e transparente (absorve de 0 a milhões de mensagens por segundo sem configuração prévia); custo estritamente baseado no volume de dados trafegados (FinOps); integração nativa e sem código (*Direct to BigQuery* ou via Dataflow) para o Data Lake.
* **Contras:** Latência ligeiramente maior que o Kafka (dezenas de milissegundos, mas ainda perfeitamente aceitável para o nosso TTFT < 2s). A ordenação global de mensagens não é garantida por padrão (requer o uso de *Ordering Keys*, que pode limitar o *throughput* se mal desenhado).

## 3. Matriz de Trade-off

| Critério | Opção A (Apache Kafka) | Opção B (GCP Pub/Sub) |
| :--- | :--- | :--- |
| **Custo para Tráfego de Pico (Bursty)** | Alto (Requer super-provisionamento) | **Otimizado** (Pay-per-byte/Serverless) |
| **Overhead Operacional** | Alto (Gestão de partições e nós) | **Mínimo** (Totalmente gerenciado) |
| **Integração com Data Lake (BigQuery)** | Complexa (Kafka Connect / Workers extras) | **Nativa / Transparente** |
| **Latência** | Excelente (< 5ms) | **Muito Boa** (~20-50ms) |
| **Garantia de Ordem** | Nativa (Por partição) | **Requer chaves específicas** |

## 4. Decisão e Justificativa ("Killer Justification")

**Decisão:** Escolhemos a **Opção B (Google Cloud Pub/Sub)**.

**Killer Justification:**
A adoção do GCP Pub/Sub é justificada por dois pilares fundamentais da nossa arquitetura TO-BE: **FinOps (Elasticidade) e Integração Analítica.** 

O tráfego de revendedoras é extremamente sazonal. Manter um cluster Kafka provisionado para suportar o pico de 500.000 conexões ativas custaria milhares de dólares por mês, mesmo de madrugada, quando o acesso é próximo a zero. Com o Pub/Sub, o custo acompanha exatamente a curva de uso real (Serverless), eliminando o desperdício de infraestrutura ociosa. 

A falta de ordenação estrita global do Pub/Sub não é um bloqueio para nós, pois delegamos a gestão de estado e idempotência para o **Redis (LangGraph Checkpointer)**. O *thread_id* garante o contexto da conversa, e as chaves de idempotência na borda descartam os *retries* do WhatsApp. 

Por fim, a capacidade do Pub/Sub de despejar dados de telemetria diretamente no BigQuery (ou via um pipeline leve de Dataflow) atende perfeitamente ao requisito de integrar a IA ao Data Lake corporativo, sem a necessidade de gerenciar nós adicionais de Kafka Connect.