# ADR 008: Estratégia de Segurança e Prevenção de Vazamento (Guardrails) - System Prompt vs. Output Guardrail Models

## 1. Título e Contexto

- **Data:** 22 de Outubro de 2026
- **Status:** Aceito
- **Domínio:** Segurança (AppSec) / AI Engineering

Conforme o requisito de "Segurança / Guardrails" da Plataforma Agentes GB, o assistente virtual não pode, sob nenhuma hipótese, fornecer informações de margem de lucro de outras revendedoras ou vazar Dados Pessoais (PII - sujeito à LGPD). Com 500.000 revendedoras acessando o sistema, o volume de interações e as tentativas maliciosas de manipular o comportamento da IA (*Prompt Injection* / *Jailbreak*) aumentam estatisticamente.

O desafio arquitetural é: como garantir conformidade estrita de nível corporativo e mitigar o risco de alucinações tóxicas do LLM sem destruir a latência da experiência em *streaming* (SLA de TTFT < 2s) e sem encarecer o custo transacional por mensagem.

## 2. Opções Consideradas

### Opção A: Regras no System Prompt e Validação Lexical (Regex/Heurística)

A segurança é garantida inserindo regras rígidas no prompt do Orquestrador (ex: *"Você é um assistente seguro. Nunca revele a margem de lucro. Nunca cite CPFs"*). Na saída, aplica-se uma camada simples de código usando Expressões Regulares (RegEx) para mascarar padrões numéricos que pareçam CPFs ou cartões de crédito.

* **Prós:** Adiciona zero custo de inferência (FinOps); não adiciona nenhuma latência na entrega dos tokens de saída (*streaming* flui instantaneamente).

* **Contras:** Altamente vulnerável a ataques de *Prompt Injection* (técnicas de ofuscação onde o usuário engana o LLM para ignorar as instruções iniciais); RegEx é engessado e não compreende contexto semântico (pode bloquear um código de produto que se pareça com um CPF ou deixar passar um vazamento textual estruturado de forma atípica).

### Opção B: Output Guardrails Semânticos (Modelos Especializados na Saída)

Após a síntese da resposta pelo agente orquestrador, os tokens passam por uma camada de validação semântica baseada em modelos pequenos e especialistas em segurança (ex: LlamaGuard, NeMo Guardrails ou um classificador de classificação de texto próprio hospedado no edge). Só após a aprovação desse modelo de Guardrail, os chunks são publicados no tópico do Redis Pub/Sub para envio via SSE à revendedora.

* **Prós:** Segurança robusta contra *Prompt Injection*; compreensão contextual avançada do que constitui um vazamento de margem de negócio ou PII; alinhamento total aos padrões de *Responsible AI* corporativos.

* **Contras:** Introduz latência extra antes da emissão do primeiro token (o Guardrail precisa avaliar um "buffer" de tokens antes de liberar); aumenta o custo de processamento (LLMOps) pois exige a execução de um segundo modelo neural para cada interação de saída.

## 3. Matriz de Trade-off

| Critério | Opção A (Prompt + Regex) | Opção B (Output Guardrail Model) | 
| ----- | ----- | ----- | 
| **Proteção contra Prompt Injection** | Muito Baixa | **Alta** | 
| **Acurácia na Detecção de PII/Negócio** | Baixa (Risco de Falsos Positivos) | **Alta** (Compreensão de contexto) | 
| **Custo de Execução (FinOps)** | **Nulo** | Médio (Pode ser mitigado com SLMs rápidos) | 
| **Latência no TTFT** | **Inexistente** | Média (Requer estratégia de *Buffering* no SSE) | 
| **Conformidade (LGPD/Enterprise)** | Fraca | **Excelente** | 

## 4. Decisão e Justificativa ("Killer Justification")

**Decisão:** Escolhemos a **Opção B (Output Guardrails Semânticos)** integrados ao nó final de Síntese do LangGraph (conforme desenhado no `system-design-500k.md`).

**Killer Justification:**
Em aplicações corporativas na escala de 500 mil usuários, **o risco financeiro e reputacional de um vazamento de dados (LGPD) ou de estratégia de negócio supera infinitamente o custo computacional de mitigá-lo.** 

Confiar a segurança sistêmica apenas ao *System Prompt* de um modelo generativo é uma falha arquitetural, pois LLMs são probabilísticos e suscetíveis a "esquecer" instruções iniciais sob manipulação (*Jailbreak*).

Para resolver o *trade-off* da latência imposta pelo Guardrail e não quebrar a experiência de *streaming* (SSE), aplicamos uma técnica de **Streaming Buffering Validation**: o Guardrail não espera o LLM gerar a frase inteira. Ele avalia janelas deslizantes (*sliding windows*) de tokens (ex: a cada 10 tokens gerados) utilizando um SLM super rápido e cacheado no cluster Kubernetes. Se a janela de texto for segura, ela é liberada no Redis Pub/Sub. Se o Guardrail detectar violação de margem de lucro ou PII no meio do processo, o fluxo corta a emissão, recusa a resposta e substitui por uma mensagem padrão de segurança (*Fallback Reject*). Isso protege a marca O Boticário e mantém a percepção de resposta em tempo real.