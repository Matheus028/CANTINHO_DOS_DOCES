from datetime import datetime
from app import db
from sqlalchemy import text


class Anotacao(db.Model):
    __tablename__ = 'anotacoes'

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=True) # Título opcional
    conteudo = db.Column(db.Text, nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # socia = db.Column(db.String(50)) # Opcional: Se quiser vincular a uma sócia

class Receita(db.Model):
    __tablename__ = 'receitas'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False, unique=True)
    descricao = db.Column(db.Text)
    balas_por_receita = db.Column(db.Integer, default=28) # Ajustei para 28 como na sua imagem
    custo_por_bala = db.Column(db.Float, default=1.0)
    ativa = db.Column(db.Boolean, default=True)
    is_default = db.Column(db.Boolean, default=False) # <--- NOVO CAMPO: is_default
    criada_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizada_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to ingredients
    ingredientes = db.relationship('IngredienteReceita', back_populates='receita', cascade='all, delete-orphan')

class IngredienteReceita(db.Model):
    __tablename__ = 'ingredientes_receita'
    
    id = db.Column(db.Integer, primary_key=True)
    receita_id = db.Column(db.Integer, db.ForeignKey('receitas.id'), nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    quantidade = db.Column(db.Float, nullable=False)
    unidade = db.Column(db.String(20), nullable=False)
    
    # Relationship back to recipe
    receita = db.relationship('Receita', back_populates='ingredientes')

class EstoqueInsumo(db.Model):
    __tablename__ = 'estoque_insumos'
    
    id = db.Column(db.Integer, primary_key=True)
    socia = db.Column(db.String(50), nullable=False)
    nome_insumo = db.Column(db.String(100), nullable=False)
    quantidade = db.Column(db.Float, default=0)
    unidade = db.Column(db.String(20), nullable=False)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('socia', 'nome_insumo', name='uq_socia_insumo'),)

class EstoqueBala(db.Model):
    __tablename__ = 'estoque_balas'
    
    id = db.Column(db.Integer, primary_key=True)
    detentor = db.Column(db.String(50), nullable=False)
    receita_id = db.Column(db.Integer, db.ForeignKey('receitas.id'), nullable=False)
    quantidade = db.Column(db.Integer, default=0)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    receita = db.relationship('Receita')
    __table_args__ = (db.UniqueConstraint('detentor', 'receita_id', name='uq_detentor_receita'),)

class Producao(db.Model):
    __tablename__ = 'producoes'
    
    id = db.Column(db.Integer, primary_key=True)
    socia_produtora = db.Column(db.String(50), nullable=False)
    receita_id = db.Column(db.Integer, db.ForeignKey('receitas.id'), nullable=False)
    receitas_produzidas = db.Column(db.Integer, nullable=False)
    balas_produzidas = db.Column(db.Integer, nullable=False)
    data_producao = db.Column(db.DateTime, default=datetime.utcnow)
    
    receita = db.relationship('Receita')

class Venda(db.Model):
    __tablename__ = 'vendas'
    
    id = db.Column(db.Integer, primary_key=True)
    socia_produtora = db.Column(db.String(50), nullable=False)
    estoque_saida = db.Column(db.String(50), nullable=False)
    receita_id = db.Column(db.Integer, db.ForeignKey('receitas.id'), nullable=False)
    canal_venda = db.Column(db.String(50), nullable=False)
    tipo_pacote = db.Column(db.String(50))
    quantidade_balas = db.Column(db.Integer, nullable=False)
    valor_bruto = db.Column(db.Float, nullable=False)
    custo = db.Column(db.Float, nullable=False)
    lucro_liquido = db.Column(db.Float, nullable=False)
    data_venda = db.Column(db.DateTime, default=datetime.utcnow)
    
    # iFood specific fields
    fonte_ifood = db.Column(db.String(50))
    id_recebivel = db.Column(db.String(50))
    data_prevista = db.Column(db.Date)
    
    receita = db.relationship('Receita')

class ContasReceber(db.Model):
    __tablename__ = 'contas_receber'
    
    id = db.Column(db.Integer, primary_key=True)
    venda_id = db.Column(db.Integer, db.ForeignKey('vendas.id'))
    descricao = db.Column(db.String(200), nullable=False)
    valor = db.Column(db.Float, nullable=False)
    data_vencimento = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='Pendente')  # Pendente, Recebido
    fonte = db.Column(db.String(50))  # iFood vendor name or other source
    criada_em = db.Column(db.DateTime, default=datetime.utcnow)
    data_recebimento = db.Column(db.DateTime, nullable=True) # Campo para registrar quando foi recebido
    
    venda = db.relationship('Venda')

class LucrosPendentes(db.Model):
    __tablename__ = 'lucros_pendentes'
    
    id = db.Column(db.Integer, primary_key=True)
    socia = db.Column(db.String(50), nullable=False)
    descricao = db.Column(db.String(200), nullable=False)
    valor = db.Column(db.Float, nullable=False)
    data_adicao = db.Column(db.DateTime, default=datetime.utcnow)
    origem = db.Column(db.String(100))  # Manual addition, sale profit, etc.
    status = db.Column(db.String(20), default='Pendente')  # Pendente, Pago

class CapitalGiro(db.Model):
    __tablename__ = 'capital_giro'
    
    id = db.Column(db.Integer, primary_key=True)
    valor = db.Column(db.Float, default=0)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Preços de venda por canal
class PrecoVenda(db.Model):
    __tablename__ = 'precos_venda'
    
    id = db.Column(db.Integer, primary_key=True)
    canal = db.Column(db.String(50), nullable=False)
    tipo_pacote = db.Column(db.String(50), nullable=False)
    quantidade_balas = db.Column(db.Integer, nullable=False, default=1)
    preco = db.Column(db.Float, nullable=False)
    ativo = db.Column(db.Boolean, default=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('canal', 'tipo_pacote', name='uq_canal_pacote'),)

class TransacaoFinanceira(db.Model):
    __tablename__ = 'transacoes_financeiras'
    
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(50), nullable=False)  # Aporte, Compra no crédito, Pagamento, Recebimento Venda, etc.
    descricao = db.Column(db.String(200), nullable=False)
    valor = db.Column(db.Float, nullable=False)
    data_transacao = db.Column(db.DateTime, default=datetime.utcnow)

class ContasPagar(db.Model):
    __tablename__ = 'contas_pagar'
    
    id = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String(200), nullable=False)
    valor = db.Column(db.Float, nullable=False)
    data_vencimento = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), default='Pendente')  # Pendente, Pago
    tipo = db.Column(db.String(50), nullable=True)
    data_pagamento = db.Column(db.DateTime, nullable=True)
    criada_em = db.Column(db.DateTime, default=datetime.utcnow)

def init_default_data():
    """Initialize default data for the system"""
    
    # Default recipe
    if not Receita.query.filter_by(nome='Bala Baiana Tradicional').first():
        receita_tradicional = Receita(
            nome='Bala Baiana Tradicional',
            descricao='Receita tradicional de bala baiana',
            balas_por_receita=28, # Ajustei para 28 como na sua imagem
            custo_por_bala=1.0,
            ativa=True,
            is_default=True # Definir como padrão ao inicializar
        )
        db.session.add(receita_tradicional)
        db.session.flush()
        
        # Default ingredients for RECIPE
        ingredientes_receita_default = [ # Lista para a receita
            ('acucar cristal', 400, 'g'),
            ('coco ralado', 100, 'g'),
            ('leite condensado', 1, 'u'),
            ('vinagre de alcool', 100, 'ml'),
            ('manteiga', 15, 'g'),
            ('glucose', 15, 'g')
        ]
        
        for nome, qtd, unidade in ingredientes_receita_default:
            ingrediente = IngredienteReceita(
                receita_id=receita_tradicional.id,
                nome=nome.strip().lower().replace(' ', '_'), # Normaliza nome aqui
                quantidade=qtd,
                unidade=unidade
            )
            db.session.add(ingrediente)
    
    # Default pricing
    precos_default = [
        ('restaurante', 'preco_unitario', 1.90),
        ('ifood', 'pacote_3', 9.00),
        ('ifood', 'pacote_6', 17.00),
        ('ifood', 'pacote_10', 23.00),
        ('presencial', 'pacote_3', 6.00),
        ('presencial', 'pacote_6', 10.00),
        ('presencial', 'pacote_10', 15.00),
    ]
    
    for canal, tipo, preco in precos_default:
        if not PrecoVenda.query.filter_by(canal=canal, tipo_pacote=tipo).first():
            preco_obj = PrecoVenda(canal=canal, tipo_pacote=tipo, preco=preco)
            db.session.add(preco_obj)
    
    # Initialize capital de giro
    if not CapitalGiro.query.first():
        capital = CapitalGiro(valor=0)
        db.session.add(capital)
    
    # Default stock for partners - AGORA USA A LISTA SOCIAS DO ROUTES.PY PARA COERÊNCIA
    # (Ou defina explicitamente se não quiser depender de SOCIAS de outro arquivo)
    # Aqui, para garantir que 'Matheus' seja o sócio inicial, vamos deixar explícito.
    socias_iniciais_para_estoque = ['Rosangela', 'Janira', 'Matheus'] 
    receita_id = Receita.query.filter_by(nome='Bala Baiana Tradicional').first().id
    
    # Lista de ingredientes para inicializar o estoque, usando os nomes normalizados e unidades corretas
    ingredientes_para_estoque_inicial = [
        ('acucar_cristal', 'g'),
        ('coco_ralado', 'g'),
        ('leite_condensado', 'u'),
        ('vinagre_de_alcool', 'ml'),
        ('manteiga', 'g'),
        ('glucose', 'g')
    ]
    
    for socia in socias_iniciais_para_estoque:
        # Initialize ingredient stock
        for nome_insumo_normalizado, unidade_insumo in ingredientes_para_estoque_inicial:
            if not EstoqueInsumo.query.filter_by(socia=socia, nome_insumo=nome_insumo_normalizado).first():
                estoque = EstoqueInsumo(
                    socia=socia,
                    nome_insumo=nome_insumo_normalizado,
                    quantidade=0,
                    unidade=unidade_insumo 
                )
                db.session.add(estoque)
        
        # Initialize candy stock
        if not EstoqueBala.query.filter_by(detentor=socia, receita_id=receita_id).first():
            estoque_bala = EstoqueBala(
                detentor=socia,
                receita_id=receita_id,
                quantidade=0
            )
            db.session.add(estoque_bala)
    
    db.session.commit()