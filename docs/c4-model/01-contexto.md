C4Context
    title Diagrama de Contexto (Nível 1) - Plataforma Agentes GB

    Person(revendedora, "Revendedora Boticário", "Interage com o assistente virtual para resolver dúvidas no ciclo de vendas.")
    
    System(motor_ia, "Motor Transacional (Agente)", "Compreende a intenção da revendedora e decide a melhor forma de ajudá-la.")
    
    System_Ext(sis_pedidos, "Sistemas Transacionais (DB/API)", "Fonte de verdade sobre o status de pedidos e estoque físico.")
    System_Ext(sis_catalogo, "Repositório de Catálogos", "Base de PDFs e promoções ativas do ciclo.")

    Rel(revendedora, motor_ia, "Faz perguntas sobre produtos, promoções ou pedidos via", "Chat (WhatsApp/App)")
    Rel(motor_ia, sis_catalogo, "Busca informações técnicas e promoções do ciclo via", "RAG")
    Rel(motor_ia, sis_pedidos, "Consulta de forma autônoma informações da conta via", "Ferramentas (Tools)")