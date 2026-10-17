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

### Requisitos

- Python 3.10 ou superior
- Node.js 20 e npm

Não é necessário instalar Docker ou PostgreSQL para desenvolvimento: os passos abaixo usam SQLite e salvam o banco em `storage/voxmind.db`.

### Backend

No terminal 1, a partir da raiz do repositório:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e '.[dev]'
mkdir -p ../storage
export DATABASE_URL="sqlite:///../storage/voxmind.db"
export JWT_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

Mantenha esse terminal aberto. A chave gerada precisa continuar definida nesse terminal para a API. A documentação interativa fica em <http://localhost:8000/docs> e o health check em <http://localhost:8000/health>.

### Frontend

No terminal 2, a partir da raiz do repositório:

```bash
cd frontend
npm ci
npm run dev -- --port 5175
```

Abra <http://localhost:5175>. O frontend usa a API em `http://localhost:8000` por padrão. O Vite pode escolher outra porta se `5175` já estiver ocupada; nesse caso, use o endereço mostrado no terminal.

Ao abrir uma análise sem relatório, o VoxMind transcreve o áudio do vídeo com `faster-whisper` (modelo `tiny`, CPU) e usa os segmentos com timestamps para gerar as métricas. O primeiro processamento baixa o modelo do Hugging Face e pode levar alguns minutos; configure `VOXMIND_WHISPER_MODEL` antes de iniciar o backend para escolher outro modelo. Vídeos precisam conter uma faixa de áudio. Planos gratuitos com pouca memória podem não conseguir executar o modelo; para transcrição automática, prefira rodar localmente ou usar um servidor com memória suficiente.

### Testes

Com o ambiente virtual do backend ativado:

```bash
cd backend
pytest -q
```

Para verificar o build de produção do frontend:

```bash
cd frontend
npm run build
```

No cadastro, a senha deve ter pelo menos 8 caracteres. Para usar PostgreSQL local em vez do SQLite, consulte `docker-compose.yml` e configure `DATABASE_URL` com a URL do banco antes de executar as migrações.
