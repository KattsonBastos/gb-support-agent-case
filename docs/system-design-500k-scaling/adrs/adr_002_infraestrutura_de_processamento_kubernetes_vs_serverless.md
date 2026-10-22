# ADR 002: Infraestrutura de Processamento - Kubernetes (GKE) + KEDA vs. Serverless (Cloud Run)

## 1. Título e Contexto
- **Data:** 22 de Outubro de 2026
- **Status:** Aceito
- **Domínio:** Infraestrutura / Compute

Para suportar o tráfego de até 500.000 revendedoras simultâneas, a arquitetura TO-BE da Plataforma Agentes GB adotou um padrão *Event-Driven* e assíncrono. O tráfego de rede (SSE/Webhooks) é gerenciado na borda pelo API Gateway, enquanto o processamento cognitivo (orquestração do LLM) foi delegado a *LangGraph Workers* que operam em *background*, consumindo tarefas de um *Message Broker* (Kafka ou Pub/Sub) e publicando tokens no Redis Pub/Sub.

O desafio central de infraestrutura é: qual plataforma de *Compute* oferece a melhor relação entre escalabilidade reativa (para não acumular mensagens na fila e estourar o SLA de TTFT < 2s), previsibilidade de custos (FinOps) e suporte robusto a *long-lived connections* e *background processing* baseados em mensageria?

## 2. Opções Consideradas

### Opção A: Serverless Fully Managed (Google Cloud Run / AWS AppRunner)
Uso de contêineres sem servidor gerenciados pela nuvem. Os *Workers* do LangGraph seriam encapsulados em instâncias que escalam de zero a milhares automaticamente.
* **Prós:** Zero overhead de gerenciamento de cluster; provisionamento ultrarrápido; *scale-to-zero* ideal para madrugadas sem acesso.
* **Contras:** Modelo inerentemente orientado a requisições HTTP (Request-Driven). Para consumir filas (Pull/Streaming), é necessário manter a instância "acordada" (*CPU always allocated*), anulando a vantagem de custo do Serverless. Além disso, *cold starts* afetam diretamente o *Time-to-First-Token* (TTFT) no início de picos de acessos; conexões de rede frequentes com Redis/VectorDB sofrem com a volatilidade dos contêineres efêmeros.

### Opção B: Kubernetes + Event-Driven Autoscaling (GKE + KEDA)
Cluster Kubernetes gerenciado (Google Kubernetes Engine) utilizando o KEDA (Kubernetes Event-driven Autoscaling) para escalar os *Pods* dos *Workers* não por uso de CPU, mas pelo *Lag* (profundidade) da fila do Broker.
* **Prós:** Escalabilidade por métrica de negócio (*Queue Lag*); pools de conexão estáveis e persistentes com bancos de dados, Redis e LLM APIs; custo muito mais otimizado em alta escala utilizando instâncias *Spot* ou compromissos de uso (CUDs) para o *baseline* de tráfego; pods "quentes" evitam *cold starts*.
* **Contras:** Maior overhead operacional (Platform Engineering); necessidade de gerenciar atualizações de *Node Pools*; complexidade na configuração inicial do autoscaler customizado.

## 3. Matriz de Trade-off

| Critério | Opção A (Cloud Run - Serverless) | Opção B (GKE + KEDA) |
| :--- | :--- | :--- |
| **Custo em 500k Conexões (Pico)** | Altíssimo (cobrança por vCPU-segundo) | **Otimizado** (Pooling, Spot VMs e CUDs) |
| **Latência Inicial (Cold Starts)** | Alta (risco de violar TTFT < 2s) | **Baixa** (Pré-aquecimento e persistência) |
| **Integração com Mensageria (Pull Model)** | Ruim (Obriga uso de Webhook Push) | **Excelente** (Nativo via *Consumer Groups*) |
| **Estabilidade de Conexão (DB/Redis)** | Baixa (Conexões efêmeras / Connection Churn) | **Alta** (Connection Pooling eficiente no Pod) |
| **Overhead Operacional (DevOps)** | **Baixo** | Alto |

## 4. Decisão e Justificativa ("Killer Justification")

**Decisão:** Escolhemos a **Opção B (Kubernetes GKE + KEDA)**.

**Killer Justification:**
A escolha pelo GKE + KEDA é impulsionada diretamente por uma premissa arquitetural inegociável descrita no `system-design-500k.md`: **O processamento é assíncrono e baseado em um modelo de Pull de mensageria (Kafka/PubSub) para isolar a rede do processamento.**

O Serverless tradicional (Cloud Run) brilha em tráfego HTTP síncrono. No entanto, usar Serverless para *background workers* escutando uma fila de alta vazão é um anti-pattern financeiro e técnico na nuvem. Nós acabaríamos pagando tempo ocioso de CPU alocada ou teríamos que forçar um modelo "Push" (o Pub/Sub batendo via HTTP no Cloud Run), o que derrubaria a segurança dos *Circuit Breakers* e afogaria os instâncias em picos de 500.000 acessos, recriando o exato problema que a fila tenta resolver.

Com **GKE + KEDA**, nós invertemos o controle: o número de réplicas do *LangGraph Worker* sobe e desce proporcionalmente ao tamanho da fila de mensagens (Consumer Lag). Isso garante que só gastamos infraestrutura quando há intenções reais a serem processadas pelo LLM. Além disso, pods Kubernetes permitem manter pools de conexão abertos (e cacheados) com o Pinecone (VectorDB) e o Redis (Checkpointer/PubSub), garantindo uma latência sub-segundo para acesso ao estado, o que seria impossível com o *connection churn* (abre e fecha constante de conexões) do Serverless.