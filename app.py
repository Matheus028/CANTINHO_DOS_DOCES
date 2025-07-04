import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from dotenv import load_dotenv
from pathlib import Path # <-- Adicionado

# Encontra o caminho para o arquivo .env e o carrega explicitamente
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

# AGORA OS PRINTS DE DEBUG (PODE REMOVER DEPOIS)
print("--- Inciando teste de depuração ---")
database_url_lida = os.environ.get("DATABASE_URL")
print(f"A variável DATABASE_URL lida foi: {database_url_lida}")
print("--- Fim do teste de depuração ---")

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")

app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize the app with the extension
db.init_app(app)

with app.app_context():
    # Import models to create tables
    import models
    db.create_all()
    logging.info("Database tables created (via Alembic) or updated")
