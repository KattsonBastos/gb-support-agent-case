# ADR 006: FinOps e Estratégia de Inferência - Pay-as-you-go vs. Provisioned Throughput (vLLM)

## 1. Título e Contexto
- **Data:** 22 de Outubro de 2026
- **Status:** Aceito
- **Domínio:** AI Engineering / FinOps

Na arquitetura TO-BE da Plataforma Agentes GB, projetada para suportar 500.000 revendedoras simultâneas, o volume de tokens gerados e processados cresce exponencialmente. No MVP, a utilização de APIs gerenciadas em modelo sob demanda (ex: OpenAI GPT-4o ou Vertex AI Gemini no modelo *Pay-as-you-go*) era viável. 

Entretanto, em altíssima escala, o modelo *Pay-as-you-go* apresenta dois riscos críticos: 
1. **Risco Financeiro (FinOps):** O custo cresce linearmente com o tráfego. Em picos sazonais (ex: Black Friday, Dia das Mães), a fatura de nuvem pode inviabilizar o ROI do assistente.
2. **Risco de Resiliência:** Provedores de IA impõem limites estritos de *Tokens Per Minute* (TPM) e *Requests Per Minute* (RPM). Um pico de 500k acessos certamente estouraria as cotas padrão, causando falhas em cascata (*HTTP 429 Too Many Requests*).

## 2. Opções Consideradas

### Opção A: Managed APIs com Pay-as-you-go (Cenário Atual/MVP)

Uso contínuo de APIs de terceiros pagando exclusivamente pelo volume de tokens de input/output consumidos.

* **Prós:** Zero esforço de infraestrutura (Serverless AI); acesso imediato aos modelos mais inteligentes do mercado (State-of-the-Art).
* **Contras:** Custo linear e imprevisível; altíssimo risco de *Rate Limiting* (TPM/RPM) durante campanhas de Venda Direta; latência (TTFT) variável dependendo da carga na rede do provedor.

### Opção B: Provisioned Throughput / Self-Hosted Open Weights (vLLM no GKE)

Substituição parcial do modelo de cobrança, reservando capacidade de processamento dedicada (ex: *Provisioned Throughput* na Vertex AI/Azure) ou hospedando modelos Open Source de alta eficiência (ex: Llama 3 / Mistral) em clusters Kubernetes próprios utilizando motores de inferência otimizados (vLLM / TGI).

* **Prós:** Custo fixo e previsível, independentemente do volume de requisições geradas no pico (achatamento da curva de custos); eliminação de limites de TPM impostos por terceiros; controle absoluto sobre a latência (TTFT) e privacidade dos dados (LGPD isolada no cluster).
* **Contras:** Requer provisionamento prévio de GPUs (NVIDIA H100/A100) que possuem alto custo de base e podem ficar ociosas de madrugada; exige forte conhecimento de LLMOps e MLOps para manter o cluster atualizado e otimizado.

## 3. Matriz de Trade-off

| Critério | Opção A (Pay-as-you-go) | Opção B (Provisioned / Self-Hosted vLLM) |
| :--- | :--- | :--- |
| **Previsibilidade de Custos (FinOps)** | Péssima (Custo linear e infinito) | **Excelente** (Custo fixo por infraestrutura) |
| **Proteção contra Rate Limits (TPM/RPM)** | Baixa (Depende de cotas da nuvem) | **Alta** (Capacidade dedicada/isolada) |
| **Complexidade de Infraestrutura (LLMOps)** | **Mínima** | Alta (Gestão de GPUs e Node Pools) |
| **Latência P95 (TTFT)** | Variável (Concorrência global) | **Estável e Controlada** |

## 4. Decisão e Justificativa ("Killer Justification")

**Decisão:** Escolhemos a **Opção B (Estratégia Híbrida com Self-Hosted vLLM / Provisioned Throughput)** como alvo para a arquitetura TO-BE.

**Killer Justification:**
Em engenharia de escala, **o custo linear é o maior inimigo da sustentabilidade de um produto**. 

Para resolver as intenções transacionais do dia a dia da revendedora Boticário (ex: "Qual o status do pedido?" ou "Resuma o catálogo"), não precisamos de um modelo de raciocínio de 1 trilhão de parâmetros custando dezenas de dólares por milhão de tokens.

Ao adotarmos clusters Kubernetes equipados com GPUs e rodando um motor de inferência otimizado como o **vLLM** para hospedar modelos menores e focados (ex: Llama 3 8B-Instruct ou modelos fine-tunados internamente), nós passamos a pagar pelo "tempo de máquina" e não pelo token. Durante um pico de acessos, o custo da nossa infraestrutura permanece idêntico, maximizando o ROI e eliminando completamente os bloqueios de TPM (*Rate Limits*). Mantemos as APIs *Pay-as-you-go* apenas como mecanismo de *fallback* ou para intenções altamente ambíguas roteadas pelo nosso *Decision Model* (conforme ADR 001). Essa é a verdadeira essência de FinOps aplicado à IA Generativa.