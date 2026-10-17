Atue como um Engenheiro Full Stack especializado em Python. Leia a especificação [005-frontend.md](file;file:///home/kattson/Documents/case-gb-spec-2/gb-support-agent-case/docs/specs/005-frontend.md) 
Preciso que você crie a interface da nossa aplicação:

Crie o arquivo frontend/app.py implementando o chat com Streamlit.

Implemente o painel lateral para a configuração do CPF (simulando a identidade da revendedora)[cite: 1].

Crie a função de conexão com o FastAPI, garantindo que o requests.post(..., stream=True) processe corretamente as linhas recebidas em formato SSE e limpe o prefixo data:  antes de injetar no chat.

Adicione um arquivo frontend/requirements.txt apenas com as dependências necessárias (streamlit, requests).
Garanta um código limpo, com tratamento de erros na requisição caso a API não esteja no ar.