🍬 Sistema Cantinho dos Doces

Aplicação Flask + PostgreSQL para gestão da loja Cantinho dos Doces (ex.: cadastro de produtos, pedidos e relatórios).
O projeto roda totalmente em containers Docker via Docker Compose.

🚀 Tecnologias

Python 3.11

Flask

PostgreSQL 15

SQLAlchemy

Docker + Compose

📂 Estrutura do projeto
.
├── app.py              # Configuração do Flask e banco
├── main.py             # Ponto de entrada da aplicação
├── models.py           # Modelos do SQLAlchemy
├── routes.py           # Rotas da aplicação
├── requirements.txt    # Dependências Python
├── docker-compose.yml  # Orquestração dos containers
├── Dockerfile          # Build da imagem Flask
├── config/
│   └── web.env         # Variáveis de ambiente do Flask
└── migrations/         # Migrações do banco (Alembic)

⚙️ Pré-requisitos

Docker

Docker Compose

▶️ Como rodar
1. Clone o repositório
git clone https://github.com/SEU-USUARIO/sistema-cantinho-doces.git
cd sistema-cantinho-doces

2. Configure variáveis de ambiente

Crie um arquivo .env na raiz (ou edite config/web.env):

FLASK_ENV=development
DATABASE_URL=postgresql://balas_user:balas_pass@db:5432/balas_db
SECRET_KEY=coloque_uma_chave_secreta_aqui

3. Suba os containers
docker compose up --build -d

4. Acesse no navegador

👉 http://localhost:5000

🛠️ Comandos úteis

Ver logs do Flask:

docker compose logs -f web


Parar containers:

docker compose down


Remover containers + volumes:

docker compose down -v

🧪 Healthcheck

Rota simples para validar se a API está ativa:

GET /ping
→ {"status": "ok"}

-------------------------------------------------------------------------

▶️ Como rodar
🔹 Opção 1: Localmente

Crie um ambiente virtual:

python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows


Instale as dependências:

pip install -r requirements.txt


Configure o .env:

FLASK_ENV=development
DATABASE_URL=postgresql://usuario:senha@localhost:5432/balas_db
SECRET_KEY=sua_chave_aqui


💡 Se quiser testar rápido, pode usar SQLite:
DATABASE_URL=sqlite:///app.db

Rode a aplicação:

python main.py


Acesse em 👉 http://localhost:5000

🔹 Opção 2: Com Docker Compose

Configure config/web.env:

FLASK_ENV=development
DATABASE_URL=postgresql://balas_user:balas_pass@db:5432/balas_db
SECRET_KEY=sua_chave_aqui


Suba os containers:

docker compose up --build -d


Acesse em 👉 http://localhost:5000