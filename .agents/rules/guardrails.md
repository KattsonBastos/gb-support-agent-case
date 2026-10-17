---
trigger: always_on
---

Regras Globais do Workspace (Agentes GB):

1. Zero Vazamento de PII: Em nenhuma implementação de Tool ou nó de decisão você deve permitir que um CPF acesse dados de pedidos vinculados a outro CPF. O isolamento por session_id e cpf é absoluto.   

2. Sigilo Comercial: O agente gerado NÃO PODE calcular, estimar ou fornecer informações sobre margens de lucro de outras revendedoras.   

3.Padrão de Resposta: Todas as rotas de chat devem prever formatação Server-Sent Events (SSE) nativamente.  