from datetime import datetime
from app import db

class Receita(db.Model):
    __tablename__ = 'receitas'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False, default="Receita Padrão Balas Baianas")
    balas_por_receita = db.Column(db.Integer, nullable=False, default=60)
    custo_por_bala = db.Column(db.Float, nullable=False, default=1.0)
    ativa = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class IngredienteReceita(db.Model):
    __tablename__ = 'ingredientes_receita'
    id = db.Column(db.Integer, primary_key=True)
    receita_id = db.Column(db.Integer, db.ForeignKey('receitas.id'), nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    quantidade = db.Column(db.Float, nullable=False)
    unidade = db.Column(db.String(20), nullable=False)
    
    receita = db.relationship('Receita', backref='ingredientes')

class EstoqueInsumo(db.Model):
    __tablename__ = 'estoque_insumos'
    id = db.Column(db.Integer, primary_key=True)
    socia_nome = db.Column(db.String(100), nullable=False)
    ingrediente = db.Column(db.String(100), nullable=False)
    quantidade = db.Column(db.Float, nullable=False, default=0)
    unidade = db.Column(db.String(20), nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class EstoqueBala(db.Model):
    __tablename__ = 'estoque_balas'
    id = db.Column(db.Integer, primary_key=True)
    detentor = db.Column(db.String(100), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False, default=0)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Producao(db.Model):
    __tablename__ = 'producoes'
    id = db.Column(db.Integer, primary_key=True)
    socia_produtora = db.Column(db.String(100), nullable=False)
    receitas_produzidas = db.Column(db.Integer, nullable=False)
    balas_produzidas = db.Column(db.Integer, nullable=False)
    data_producao = db.Column(db.DateTime, default=datetime.utcnow)

class Venda(db.Model):
    __tablename__ = 'vendas'
    id = db.Column(db.Integer, primary_key=True)
    id_venda = db.Column(db.String(50), unique=True, nullable=False)
    socia_produtora = db.Column(db.String(100), nullable=False)
    estoque_saida = db.Column(db.String(100), nullable=False)
    canal = db.Column(db.String(50), nullable=False)
    total_balas = db.Column(db.Integer, nullable=False)
    valor_bruto = db.Column(db.Float, nullable=False)
    custo = db.Column(db.Float, nullable=False)
    lucro_liquido = db.Column(db.Float, nullable=False)
    fonte_ifood = db.Column(db.String(100), nullable=True)
    id_recebivel = db.Column(db.String(100), nullable=True)
    data_venda = db.Column(db.DateTime, default=datetime.utcnow)

class ContaReceber(db.Model):
    __tablename__ = 'contas_receber'
    id = db.Column(db.Integer, primary_key=True)
    venda_id = db.Column(db.Integer, db.ForeignKey('vendas.id'), nullable=True)
    fonte_ifood = db.Column(db.String(100), nullable=False)
    valor_a_receber = db.Column(db.Float, nullable=False)
    data_prevista = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='Pendente')
    data_recebimento = db.Column(db.DateTime, nullable=True)
    
    venda = db.relationship('Venda', backref='conta_receber')

class ContaPagar(db.Model):
    __tablename__ = 'contas_pagar'
    id = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String(200), nullable=False)
    valor = db.Column(db.Float, nullable=False)
    data_vencimento = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), default='Pendente')
    tipo = db.Column(db.String(50), nullable=True)
    data_pagamento = db.Column(db.DateTime, nullable=True)

class TransacaoFinanceira(db.Model):
    __tablename__ = 'transacoes_financeiras'
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(50), nullable=False)
    descricao = db.Column(db.String(200), nullable=False)
    valor = db.Column(db.Float, nullable=False)
    data_transacao = db.Column(db.DateTime, default=datetime.utcnow)

class ConfiguracaoPreco(db.Model):
    __tablename__ = 'configuracao_precos'
    id = db.Column(db.Integer, primary_key=True)
    canal = db.Column(db.String(50), nullable=False)
    tipo_pacote = db.Column(db.String(50), nullable=False)
    quantidade_balas = db.Column(db.Integer, nullable=False)
    preco = db.Column(db.Float, nullable=False)
    ativo = db.Column(db.Boolean, default=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
