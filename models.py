from datetime import datetime
from app import db
from sqlalchemy import text

class Receita(db.Model):
    __tablename__ = 'receitas'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False, unique=True)
    descricao = db.Column(db.Text)
    balas_por_receita = db.Column(db.Integer, default=40)
    custo_por_bala = db.Column(db.Float, default=1.0)
    ativa = db.Column(db.Boolean, default=True)
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
    preco = db.Column(db.Float, nullable=False)
    
    __table_args__ = (db.UniqueConstraint('canal', 'tipo_pacote', name='uq_canal_pacote'),)

def init_default_data():
    """Initialize default data for the system"""
    
    # Default recipe
    if not Receita.query.filter_by(nome='Bala Baiana Tradicional').first():
        receita_tradicional = Receita(
            nome='Bala Baiana Tradicional',
            descricao='Receita tradicional de bala baiana',
            balas_por_receita=40,
            custo_por_bala=1.0,
            ativa=True
        )
        db.session.add(receita_tradicional)
        db.session.flush()
        
        # Default ingredients
        ingredientes_default = [
            ('acucar', 500, 'g'),
            ('agua', 200, 'ml'),
            ('gengibre', 50, 'g'),
            ('cravo', 10, 'g'),
            ('canela', 15, 'g')
        ]
        
        for nome, qtd, unidade in ingredientes_default:
            ingrediente = IngredienteReceita(
                receita_id=receita_tradicional.id,
                nome=nome,
                quantidade=qtd,
                unidade=unidade
            )
            db.session.add(ingrediente)
    
    # Default pricing
    precos_default = [
        ('restaurante', 'preco_unitario', 2.50),
        ('ifood', 'pacote_3', 8.00),
        ('ifood', 'pacote_6', 15.00),
        ('ifood', 'pacote_12', 28.00),
        ('presencial', 'pacote_3', 7.00),
        ('presencial', 'pacote_6', 13.00),
        ('presencial', 'pacote_12', 25.00),
    ]
    
    for canal, tipo, preco in precos_default:
        if not PrecoVenda.query.filter_by(canal=canal, tipo_pacote=tipo).first():
            preco_obj = PrecoVenda(canal=canal, tipo_pacote=tipo, preco=preco)
            db.session.add(preco_obj)
    
    # Initialize capital de giro
    if not CapitalGiro.query.first():
        capital = CapitalGiro(valor=0)
        db.session.add(capital)
    
    # Default stock for partners
    socias = ['Rosangela', 'Janira', 'Outros']
    receita_id = Receita.query.filter_by(nome='Bala Baiana Tradicional').first().id
    
    for socia in socias:
        # Initialize ingredient stock
        ingredientes_default = ['acucar', 'agua', 'gengibre', 'cravo', 'canela']
        for ingrediente in ingredientes_default:
            if not EstoqueInsumo.query.filter_by(socia=socia, nome_insumo=ingrediente).first():
                unidade = 'g' if ingrediente != 'agua' else 'ml'
                estoque = EstoqueInsumo(
                    socia=socia,
                    nome_insumo=ingrediente,
                    quantidade=0,
                    unidade=unidade
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
