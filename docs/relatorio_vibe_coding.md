

# **Relatório de Desenvolvimento: Plataforma Agentes GB**

**Projeto:** Agente de Suporte à Revendedora  
**Objetivo do Documento:** Visão geral de como estruturamos o desenvolvimento usando IA, os principais desafios que enfrentamos e as lições que tiramos do processo.

## **1\. Contexto e Nossa Abordagem**

Para construir a aplicação de forma rápida, mas sem perder o controle da qualidade, dividimos nossa estratégia de uso de IA em duas frentes bem claras:

* **Spec-Driven Development (SDD) para o Core:** Usamos essa abordagem estruturada para construir a solução principal (regras de negócio, fluxo do agente e integrações críticas). Em vez de deixar a IA gerar código livremente, nós ancoramos o modelo em especificações formais, contratos de interface e regras inegociáveis. Isso garantiu que o coração da aplicação nascesse robusto.  
* **Vibe Coding para as Tarefas Auxiliares:** Já para o que ficava em torno da aplicação, soltamos as amarras. Usamos o "Vibe Coding" (geração mais fluida e interativa com a IA) para resolver rápido coisas como a dockerização do projeto, o setup inicial da infraestrutura e a inclusão da esteira de observabilidade com o Langfuse direto no Docker Compose.

Para visualizar melhor, nosso fluxo de trabalho funcionou assim:

```mermaid
flowchart LR  
    Constitution["Constituição & Guardrails\<br/\>(Regras Inegociáveis)"\] \--\> RFC["Especificações\<br/\>(RFCs Modulares)"\]  
    RFC \--\> Skills["Skills do Agente\<br/\>(specify, plan, implement)"\]  
    Skills \--\> VibeCoding["Vibe Coding & Scaffolding\<br/\>(IA Gerando Código)"\]  
    VibeCoding \--\> HITL["Validação Humana &\<br/\>Observabilidade"\]
```

## **2\. Ferramentas Utilizadas**

Simplificamos nosso stack para garantir velocidade sem muita complexidade:

* **Modelos Base (Gemini Flash e Pro):** Usados tanto para discutir decisões de arquitetura e desenhar diagramas (Pro), quanto para a geração pesada de código, testes e refatorações (Flash).  
* **Langfuse:** Nossa ferramenta de observabilidade. Essencial para rastrear os passos de raciocínio do agente, medir latência e monitorar o consumo real do modelo.

## **3\. Nossas Regras Inegociáveis (Guardrails)**

Antes de gerar a primeira linha de código de negócio, estabelecemos limites rígidos para o agente, que a IA precisava respeitar:

> 1. **Zero Vazamento de Dados:** Isolamento absoluto entre os perfis. Sob nenhuma hipótese o agente pode cruzar dados de pedidos ou cadastros de revendedoras diferentes.  
> 2. **Sigilo Comercial:** O agente é travado para não calcular, deduzir ou informar margens de lucro ou faturamentos.  
> 3. **Respostas Fluídas:** A experiência do usuário precisava ser em tempo real. Por isso, toda a comunicação do agente foi desenhada para funcionar em streaming (SSE).

## **4\. Onde a IA mais ajudou no dia a dia**

* **Infraestrutura e DevOps na velocidade da luz:** Usando a abordagem de *Vibe Coding*, pedimos para a IA montar nosso ambiente multi-container do zero. Ela gerou os Dockerfiles da API e do Frontend, configurou a rede interna e já plugou o banco de dados e o Langfuse no Docker Compose de forma praticamente automática.  
* **Mock de Dados Sintéticos:** Para testar a aplicação de forma fidedigna, usamos prompts estruturados para gerar catálogos inteiros de produtos (com descrições e preços) e históricos de pedidos realistas. Isso foi fundamental para validar o isolamento de dados entre diferentes contas.  
* **Documentação e Arquitetura:** A IA adiantou muito o nosso lado ajudando a documentar nossas decisões técnicas e gerando os diagramas de arquitetura (como o próprio C4 Model e ADRs).

## **5\. Desafios Técnicos e Onde Tivemos que "Colocar a Mão na Massa"**

Embora a IA tenha acelerado muito o desenvolvimento, ela patinou em algumas áreas de alta complexidade que exigiram a intervenção humana da nossa equipe técnica:

* **O Desafio do Streaming (FastAPI \+ LangGraph):** A IA teve bastante dificuldade em conectar de forma assíncrona o gerador de eventos do LangGraph com o Streaming do FastAPI. O modelo tentava cuspir eventos internos de log na tela do usuário, quebrando o layout. Tivemos que intervir no código e criar um filtro manual para garantir que apenas o texto final chegasse certinho no frontend.  
* **Isolamento de Sessão:** Durante a criação da máquina de estados, a IA tendia a misturar as sessões. Refatoramos a gestão de threads para garantir que a memória do agente estivesse sempre amarrada unicamente à identidade daquela revendedora específica.  
* **Alucinações e Segurança:** Percebemos que, diante de perguntas maliciosas (ex: "quanto a revendedora X lucrou?"), a IA às vezes tentava "ajudar" inventando dados. A nossa solução foi categórica: tiramos essa responsabilidade do prompt e travamos a segurança **direto no código Python**. Criamos validações que barram a consulta no banco de dados se o CPF não bater, antes mesmo de a informação chegar na IA.

## **6\. Impacto na Produtividade**

O saldo da nossa abordagem híbrida (SDD \+ Vibe Coding) foi extremamente positivo. Nas tarefas de configuração, infraestrutura (Docker) e documentação inicial, sentimos um ganho de tempo na casa dos **75% a 85%**. Já no desenvolvimento da lógica de negócio complexa — onde precisamos revisar mais e ajustar regras —, a redução de tempo foi de cerca de **55%**. No geral, entregamos o escopo em uma fração do tempo que levaríamos no modelo tradicional.

## **7\. Lições Aprendidas**

> 1. **Para lógica de negócio, a IA precisa de trilhos:** O *Vibe Coding* é maravilhoso para infraestrutura e configurações auxiliares. Mas tentar fazer lógica de negócio sem especificação (SDD) só gera gambiarras e muito retrabalho.  
> 2. **Código assíncrono moderno ainda confunde a IA:** Ferramentas muito recentes (como LangGraph) ainda têm particularidades que a IA não domina totalmente. A revisão humana profunda na camada de comunicação (I/O e rede) é obrigatória.  
> 3. **Segurança de verdade se faz no código, não no prompt:** Engenharia de prompt ajuda a guiar o tom do agente, mas blindar vazamento de dados de verdade exige regras estritas programadas no código-fonte das ferramentas.  
> 4. **Observabilidade desde o dia zero salva vidas:** Ter integrado o Langfuse desde o início (facilitado pelo nosso Vibe Coding no Docker) nos poupou dezenas de horas de debug. Conseguíamos ver exatamente onde o agente estava travando ou quais ferramentas ele acionava por debaixo dos panos.