# VoxMind

Aplicação para análise de apresentações, com frontend React/Vite e API FastAPI.

## Publicar no Render

O arquivo `render.yaml` configura a publicação da API, do frontend estático, do PostgreSQL e de um disco persistente para uploads.

1. Envie este repositório para GitHub, GitLab ou Bitbucket.
2. No Render, selecione **New > Blueprint** e conecte o repositório.
3. Revise os recursos e preços mostrados pelo Render antes de confirmar. O serviço da API precisa de plano pago para manter o disco persistente; o PostgreSQL também pode gerar cobrança.
4. Confirme a criação. O Render gera `JWT_SECRET_KEY`, executa as migrações antes do deploy da API e constrói o frontend.
5. Aguarde os serviços `voxmind-api` e `voxmind-frontend` ficarem disponíveis. A API deve responder `{"status":"ok"}` em `/health`; a documentação fica em `/docs`.

O Blueprint usa os domínios `voxmind-api.onrender.com` e `voxmind-frontend.onrender.com`. Se o Render atribuir domínios diferentes, atualize `VITE_API_URL` no frontend e `CORS_ORIGINS` na API para os domínios efetivamente atribuídos e faça um novo deploy de ambos.

O disco `/var/data` preserva arquivos enviados entre deploys. A base local SQLite não é usada no deploy; o PostgreSQL do Render recebe as migrações Alembic.

## Desenvolvimento local

Consulte `docker-compose.yml` para iniciar o PostgreSQL. No backend, defina `DATABASE_URL` e `JWT_SECRET_KEY` (com pelo menos 32 caracteres), instale o projeto com `pip install -e '.[dev]'` e execute `uvicorn app.main:app --reload`. No frontend, use `npm ci` e `npm run dev`.
