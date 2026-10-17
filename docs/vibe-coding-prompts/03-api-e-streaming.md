Aja como um Engenheiro de Software Especialista. Leia a spec @03-api-e-streaming.md.

1. Primeiro, crie o arquivo src/api/schemas.py implementando estritamente os modelos Pydantic definidos.

2. Em seguida, crie o arquivo src/api/routes.py configurando o endpoint FastAPI POST /api/v1/chat/stream.

3. Implemente a rota retornando um StreamingResponse. Para testar agora, crie um mock de um gerador assíncrono que faz um yield no formato SSE (Server-Sent Events) enviando a frase 'Teste de streaming SSE' palavra por palavra, com um delay de 0.5s entre elas. Ainda não integre o LangGraph, quero apenas validar a rota e os contratos.