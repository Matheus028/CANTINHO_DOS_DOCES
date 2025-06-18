from flask import render_template, request, redirect, url_for, flash
from datetime import datetime, date, timedelta
from app import app, db
from models import *
import uuid

def init_default_data():
    """Initialize default data if none exists"""
    # Initialize default recipe if none exists
    if not Receita.query.filter_by(ativa=True).first():
        receita = Receita(
            nome="Receita Padrão Balas Baianas",
            balas_por_receita=60,
            custo_por_bala=1.0,
            ativa=True
        )
        db.session.add(receita)
        db.session.commit()
        
        # Add default ingredients
        ingredientes_padrao = [
            {"nome": "açúcar", "quantidade": 500, "unidade": "g"},
            {"nome": "água", "quantidade": 250, "unidade": "ml"},
            {"nome": "gengibre", "quantidade": 50, "unidade": "g"},
            {"nome": "cravo", "quantidade": 10, "unidade": "unidade(s)"},
            {"nome": "canela", "quantidade": 2, "unidade": "colher(es)"},
        ]
        
        for ing in ingredientes_padrao:
            ingrediente = IngredienteReceita(
                receita_id=receita.id,
                nome=ing["nome"],
                quantidade=ing["quantidade"],
                unidade=ing["unidade"]
            )
            db.session.add(ingrediente)
        
        db.session.commit()
    
    # Initialize price configurations if none exist with updated prices
    if not ConfiguracaoPreco.query.first():
        precos_padrao = [
            # Venda Direta - Updated prices as requested
            {"canal": "venda_direta", "tipo_pacote": "pacote_3", "quantidade_balas": 3, "preco": 6.00},
            {"canal": "venda_direta", "tipo_pacote": "pacote_6", "quantidade_balas": 6, "preco": 10.00},
            {"canal": "venda_direta", "tipo_pacote": "pacote_10", "quantidade_balas": 10, "preco": 15.00},
            # Restaurante - Unchanged
            {"canal": "restaurante", "tipo_pacote": "preco_unitario", "quantidade_balas": 1, "preco": 1.90},
            # iFood - Updated prices as requested
            {"canal": "ifood", "tipo_pacote": "pacote_3", "quantidade_balas": 3, "preco": 9.00},
            {"canal": "ifood", "tipo_pacote": "pacote_6", "quantidade_balas": 6, "preco": 17.00},
            {"canal": "ifood", "tipo_pacote": "pacote_10", "quantidade_balas": 10, "preco": 23.00},
        ]
        
        for preco in precos_padrao:
            config = ConfiguracaoPreco(**preco)
            db.session.add(config)
        
        db.session.commit()

# Initialize data on first run
with app.app_context():
    init_default_data()

def get_receita_ativa():
    return Receita.query.filter_by(ativa=True).first()

def get_ingredientes_receita():
    receita = get_receita_ativa()
    if receita:
        return receita.ingredientes
    return []

def get_socias():
    return ["Você", "Rosangela", "Janira"]

def get_precos_venda():
    precos = {}
    configs = ConfiguracaoPreco.query.filter_by(ativo=True).all()
    
    for config in configs:
        if config.canal not in precos:
            precos[config.canal] = {}
        precos[config.canal][config.tipo_pacote] = config.preco
    
    return precos

def calcular_capacidade_producao(socia_nome):
    receita = get_receita_ativa()
    if not receita:
        return 0
    
    ingredientes_receita = receita.ingredientes
    if not ingredientes_receita:
        return 0
    
    capacidade_minima = float('inf')
    
    for ingrediente in ingredientes_receita:
        estoque = EstoqueInsumo.query.filter_by(
            socia_nome=socia_nome,
            ingrediente=ingrediente.nome
        ).first()
        
        if estoque and estoque.quantidade > 0:
            receitas_possiveis = int(estoque.quantidade / ingrediente.quantidade)
            capacidade_minima = min(capacidade_minima, receitas_possiveis)
        else:
            return 0
    
    return capacidade_minima if capacidade_minima != float('inf') else 0

def calcular_taxa_ifood(valor_bruto):
    """Calcula taxa do iFood: 26.20% + R$ 1.00 se valor < R$ 20.00"""
    taxa_percentual = valor_bruto * 0.262
    taxa_fixa = 1.00 if valor_bruto < 20.00 else 0.00
    return taxa_percentual + taxa_fixa

@app.route('/')
def index():
    # Get dashboard data
    receita = get_receita_ativa()
    socias = get_socias()
    
    # Calculate current production capacities
    capacidades_atuais = {}
    for socia in socias:
        cap_receitas = calcular_capacidade_producao(socia)
        if cap_receitas > 0:
            capacidades_atuais[socia] = {
                'receitas': cap_receitas,
                'balas': cap_receitas * receita.balas_por_receita if receita else 0
            }
    
    # Get candy stock
    estoque_balas = {}
    total_balas_estoque = 0
    balas_db = EstoqueBala.query.all()
    for bala in balas_db:
        estoque_balas[bala.detentor] = bala.quantidade
        total_balas_estoque += bala.quantidade
    
    # Get recent sales
    ultimas_vendas = Venda.query.order_by(Venda.data_venda.desc()).limit(5).all()
    
    # Get financial data
    capital_giro = 0
    lucros_pendentes = {'Você': 0, 'Rosangela': 0, 'Janira': 0}
    
    transacoes = TransacaoFinanceira.query.all()
    for t in transacoes:
        if t.tipo == 'aporte':
            capital_giro += t.valor
        elif t.tipo == 'lucro_pendente':
            if 'Você' in t.descricao:
                lucros_pendentes['Você'] = t.valor
            elif 'Rosangela' in t.descricao:
                lucros_pendentes['Rosangela'] = t.valor
            elif 'Janira' in t.descricao:
                lucros_pendentes['Janira'] = t.valor
    
    # Get overdue accounts
    contas_vencidas = ContaPagar.query.filter(
        ContaPagar.status == 'Pendente',
        ContaPagar.data_vencimento <= date.today()
    ).all()
    
    # Get pending iFood payments
    pendentes_ifood = ContaReceber.query.filter_by(status='Pendente').all()
    
    dados = {
        'estoque_balas_prontas': estoque_balas,
        'financeiro': {
            'capital_de_giro': capital_giro,
            'lucros_pendentes': lucros_pendentes,
            'contas_a_receber_ifood': pendentes_ifood
        },
        'vendas': Venda.query.all()
    }
    
    return render_template('index.html',
                         dados=dados,
                         total_balas_estoque=total_balas_estoque,
                         capacidades_atuais=capacidades_atuais,
                         ultimas_vendas=ultimas_vendas,
                         contas_vencidas=contas_vencidas)

@app.route('/estoque', methods=['GET', 'POST'])
def estoque():
    if request.method == 'POST':
        socia = request.form.get('socia')
        insumo = request.form.get('insumo')
        quantidade = float(request.form.get('quantidade', 0))
        
        # Get unit from recipe
        receita = get_receita_ativa()
        unidade = 'g'  # default
        for ing in receita.ingredientes:
            if ing.nome == insumo:
                unidade = ing.unidade
                break
        
        # Update or create stock
        estoque = EstoqueInsumo.query.filter_by(
            socia_nome=socia,
            ingrediente=insumo
        ).first()
        
        if estoque:
            estoque.quantidade += quantidade
        else:
            estoque = EstoqueInsumo(
                socia_nome=socia,
                ingrediente=insumo,
                quantidade=quantidade,
                unidade=unidade
            )
            db.session.add(estoque)
        
        db.session.commit()
        flash(f'Adicionado {quantidade} {unidade} de {insumo} para {socia}', 'success')
    
    # Get stock data
    receita = get_receita_ativa()
    socias = get_socias()
    ingredientes_receita = receita.ingredientes if receita else []
    
    estoque_insumos = {}
    capacidade_producao = {}
    
    for socia in socias:
        estoques = EstoqueInsumo.query.filter_by(socia_nome=socia).all()
        estoque_insumos[socia] = []
        
        for estoque in estoques:
            # Calculate possible recipes
            ingrediente_receita = next(
                (ing for ing in ingredientes_receita if ing.nome == estoque.ingrediente),
                None
            )
            
            receitas_possiveis = 0
            if ingrediente_receita and ingrediente_receita.quantidade > 0:
                receitas_possiveis = int(estoque.quantidade / ingrediente_receita.quantidade)
            
            estoque_insumos[socia].append({
                'ingrediente': estoque.ingrediente,
                'quantidade': estoque.quantidade,
                'unidade': estoque.unidade,
                'receitas_possiveis': receitas_possiveis
            })
        
        capacidade_producao[socia] = calcular_capacidade_producao(socia)
    
    # Get candy stock
    estoque_balas = {}
    total_balas = 0
    balas_db = EstoqueBala.query.all()
    for bala in balas_db:
        estoque_balas[bala.detentor] = bala.quantidade
        total_balas += bala.quantidade
    
    # Generate alerts
    alertas_estoque = []
    for socia, insumos in estoque_insumos.items():
        for insumo in insumos:
            if insumo['receitas_possiveis'] == 0:
                alertas_estoque.append(f"{socia}: {insumo['ingrediente']} esgotado")
            elif insumo['receitas_possiveis'] <= 2:
                alertas_estoque.append(f"{socia}: {insumo['ingrediente']} baixo ({insumo['receitas_possiveis']} receitas)")
    
    dados = {
        'estoque_insumos': estoque_insumos,
        'capacidade_producao': capacidade_producao,
        'estoque_balas': estoque_balas,
        'total_balas': total_balas,
        'alertas_estoque': alertas_estoque,
        'socias': socias,
        'ingredientes_receita': ingredientes_receita,
        'receita': receita
    }
    
    return render_template('estoque.html', dados=dados)

@app.route('/producao', methods=['GET', 'POST'])
def producao():
    if request.method == 'POST':
        socia_produtora = request.form.get('socia_produtora')
        receitas_a_produzir = int(request.form.get('receitas_a_produzir', 0))
        
        receita = get_receita_ativa()
        if not receita:
            flash('Erro: Nenhuma receita ativa encontrada', 'error')
            return redirect(url_for('producao'))
        
        # Check capacity
        capacidade = calcular_capacidade_producao(socia_produtora)
        if receitas_a_produzir > capacidade:
            flash(f'Erro: Capacidade máxima é {capacidade} receitas', 'error')
            return redirect(url_for('producao'))
        
        # Consume ingredients
        for ingrediente in receita.ingredientes:
            estoque = EstoqueInsumo.query.filter_by(
                socia_nome=socia_produtora,
                ingrediente=ingrediente.nome
            ).first()
            
            if estoque:
                consumo = ingrediente.quantidade * receitas_a_produzir
                estoque.quantidade -= consumo
                if estoque.quantidade < 0:
                    estoque.quantidade = 0
        
        # Add to candy stock
        balas_produzidas = receitas_a_produzir * receita.balas_por_receita
        estoque_bala = EstoqueBala.query.filter_by(detentor=socia_produtora).first()
        
        if estoque_bala:
            estoque_bala.quantidade += balas_produzidas
        else:
            estoque_bala = EstoqueBala(
                detentor=socia_produtora,
                quantidade=balas_produzidas
            )
            db.session.add(estoque_bala)
        
        # Record production
        producao = Producao(
            socia_produtora=socia_produtora,
            receitas_produzidas=receitas_a_produzir,
            balas_produzidas=balas_produzidas
        )
        db.session.add(producao)
        
        db.session.commit()
        
        flash(f'Produção registrada: {receitas_a_produzir} receitas = {balas_produzidas} balas', 'success')
        return redirect(url_for('producao'))
    
    receita = get_receita_ativa()
    socias = get_socias()
    
    # Get recipe data for display
    receita_padrao = {}
    unidades = {}
    if receita:
        for ing in receita.ingredientes:
            receita_padrao[ing.nome] = ing.quantidade
            unidades[ing.nome] = ing.unidade
    
    # Get stock data for JS
    estoque_insumos = {}
    for socia in socias:
        estoques = EstoqueInsumo.query.filter_by(socia_nome=socia).all()
        estoque_insumos[socia] = {e.ingrediente: e.quantidade for e in estoques}
    
    dados = {
        'estoque_insumos': estoque_insumos
    }
    
    return render_template('producao.html',
                         dados=dados,
                         socias=socias,
                         receita_padrao=receita_padrao,
                         unidades=unidades,
                         balas_por_receita=receita.balas_por_receita if receita else 60)

@app.route('/vendas', methods=['GET', 'POST'])
def vendas():
    if request.method == 'POST':
        socia_produtora = request.form.get('socia_produtora')
        estoque_saida = request.form.get('estoque_saida')
        canal_venda = request.form.get('canal_venda')
        
        # Calculate sale details based on channel
        total_balas = 0
        valor_bruto = 0
        
        if canal_venda == 'restaurante':
            total_balas = int(request.form.get('quantidade_balas', 0))
            preco_config = ConfiguracaoPreco.query.filter_by(
                canal='restaurante',
                tipo_pacote='preco_unitario',
                ativo=True
            ).first()
            valor_bruto = total_balas * preco_config.preco if preco_config else 0
        
        else:
            tipo_pacote = request.form.get('tipo_pacote')
            preco_config = ConfiguracaoPreco.query.filter_by(
                canal=canal_venda,
                tipo_pacote=tipo_pacote,
                ativo=True
            ).first()
            
            if preco_config:
                total_balas = preco_config.quantidade_balas
                valor_bruto = preco_config.preco
        
        # Calculate costs and profit
        receita = get_receita_ativa()
        custo = total_balas * receita.custo_por_bala if receita else total_balas * 1.0
        
        # Apply iFood fees
        valor_liquido = valor_bruto
        if canal_venda == 'ifood':
            taxa_ifood = calcular_taxa_ifood(valor_bruto)
            valor_liquido = valor_bruto - taxa_ifood
        
        lucro_liquido = valor_liquido - custo
        
        # Check stock availability
        estoque_bala = EstoqueBala.query.filter_by(detentor=estoque_saida).first()
        if not estoque_bala or estoque_bala.quantidade < total_balas:
            flash('Erro: Estoque insuficiente', 'error')
            return redirect(url_for('vendas'))
        
        # Update stock
        estoque_bala.quantidade -= total_balas
        
        # Create sale record
        id_venda = f"VND{datetime.now().strftime('%Y%m%d%H%M%S')}"
        venda = Venda(
            id_venda=id_venda,
            socia_produtora=socia_produtora,
            estoque_saida=estoque_saida,
            canal=canal_venda,
            total_balas=total_balas,
            valor_bruto=valor_bruto,
            custo=custo,
            lucro_liquido=lucro_liquido,
            fonte_ifood=request.form.get('fonte_ifood'),
            id_recebivel=request.form.get('id_recebivel')
        )
        db.session.add(venda)
        
        # Add financial transaction
        transacao = TransacaoFinanceira(
            tipo='venda',
            descricao=f'Venda {canal_venda} - {total_balas} balas',
            valor=valor_liquido
        )
        db.session.add(transacao)
        
        # Create receivable for iFood
        if canal_venda == 'ifood':
            data_prevista_str = request.form.get('data_prevista')
            data_prevista = datetime.strptime(data_prevista_str, '%Y-%m-%d').date() if data_prevista_str else date.today() + timedelta(days=14)
            
            conta_receber = ContaReceber(
                venda_id=venda.id,
                fonte_ifood=request.form.get('fonte_ifood', 'iFood Geral'),
                valor_a_receber=valor_bruto,
                data_prevista=data_prevista
            )
            db.session.add(conta_receber)
        
        db.session.commit()
        
        flash(f'Venda registrada: {total_balas} balas por R$ {valor_bruto:.2f}', 'success')
        return redirect(url_for('vendas'))
    
    # Get display data
    socias = get_socias()
    detentores_estoque = []
    estoque_balas_prontas = {}
    
    balas_db = EstoqueBala.query.filter(EstoqueBala.quantidade > 0).all()
    for bala in balas_db:
        detentores_estoque.append(bala.detentor)
        estoque_balas_prontas[bala.detentor] = bala.quantidade
    
    precos_venda = get_precos_venda()
    vendedores_ifood = ["Vendedor A", "Vendedor B", "Vendedor C"]
    
    dados = {
        'estoque_balas_prontas': estoque_balas_prontas
    }
    
    return render_template('vendas.html',
                         dados=dados,
                         socias=socias,
                         detentores_estoque=detentores_estoque,
                         precos_venda=precos_venda,
                         vendedores_ifood=vendedores_ifood)

@app.route('/financeiro')
def financeiro():
    # Calculate capital
    capital_giro = 0
    transacoes = TransacaoFinanceira.query.all()
    for t in transacoes:
        capital_giro += t.valor
    
    # Get pending receivables
    contas_a_receber_ifood = ContaReceber.query.filter_by(status='Pendente').all()
    
    # Get pending payables
    contas_a_pagar = ContaPagar.query.filter_by(status='Pendente').all()
    
    # Get recent transactions
    transacoes_recentes = TransacaoFinanceira.query.order_by(
        TransacaoFinanceira.data_transacao.desc()
    ).limit(10).all()
    
    # Check for overdue payments
    pagamentos_vencidos = ContaReceber.query.filter(
        ContaReceber.status == 'Pendente',
        ContaReceber.data_prevista <= date.today()
    ).all()
    
    dados = {
        'financeiro': {
            'capital_de_giro': capital_giro,
            'lucro_pendente_voce': 0,  # Would need calculation logic
            'lucro_pendente_socias': {},  # Would need calculation logic
            'contas_a_receber_ifood': contas_a_receber_ifood,
            'contas_a_pagar': contas_a_pagar,
            'transacoes': transacoes_recentes
        }
    }
    
    return render_template('financeiro.html',
                         dados=dados,
                         pagamentos_vencidos=pagamentos_vencidos)

@app.route('/confirmar_recebimento/<int:conta_id>', methods=['POST'])
def confirmar_recebimento(conta_id):
    conta = ContaReceber.query.get_or_404(conta_id)
    conta.status = 'Recebido'
    conta.data_recebimento = datetime.utcnow()
    
    # Add financial transaction
    transacao = TransacaoFinanceira(
        tipo='recebimento_ifood',
        descricao=f'Recebimento iFood - {conta.fonte_ifood}',
        valor=conta.valor_a_receber
    )
    db.session.add(transacao)
    
    db.session.commit()
    flash(f'Recebimento de R$ {conta.valor_a_receber:.2f} confirmado', 'success')
    return redirect(url_for('financeiro'))

@app.route('/pagar_conta/<int:conta_id>', methods=['POST'])
def pagar_conta(conta_id):
    conta = ContaPagar.query.get_or_404(conta_id)
    conta.status = 'Pago'
    conta.data_pagamento = datetime.utcnow()
    
    # Add financial transaction
    transacao = TransacaoFinanceira(
        tipo='pagamento_direto',
        descricao=conta.descricao,
        valor=-conta.valor  # Negative for expense
    )
    db.session.add(transacao)
    
    db.session.commit()
    flash(f'Conta de R$ {conta.valor:.2f} paga', 'success')
    return redirect(url_for('financeiro'))

@app.route('/adicionar_aporte', methods=['POST'])
def adicionar_aporte():
    valor = float(request.form.get('valor', 0))
    descricao = request.form.get('descricao')
    
    transacao = TransacaoFinanceira(
        tipo='aporte',
        descricao=descricao,
        valor=valor
    )
    db.session.add(transacao)
    db.session.commit()
    
    flash(f'Aporte de R$ {valor:.2f} adicionado', 'success')
    return redirect(url_for('financeiro'))

@app.route('/compra_credito', methods=['POST'])
def compra_credito():
    descricao = request.form.get('descricao')
    valor = float(request.form.get('valor', 0))
    data_vencimento_str = request.form.get('data_vencimento')
    
    data_vencimento = datetime.strptime(data_vencimento_str, '%Y-%m-%d').date() if data_vencimento_str else None
    
    # Create payable account
    conta = ContaPagar(
        descricao=descricao,
        valor=valor,
        data_vencimento=data_vencimento,
        tipo='credito'
    )
    db.session.add(conta)
    
    # Add immediate transaction (received goods/services)
    transacao = TransacaoFinanceira(
        tipo='compra_credito',
        descricao=f'Compra no crédito: {descricao}',
        valor=-valor
    )
    db.session.add(transacao)
    
    db.session.commit()
    flash(f'Compra no crédito registrada: R$ {valor:.2f}', 'success')
    return redirect(url_for('financeiro'))

@app.route('/receita')
def receita():
    receita_obj = get_receita_ativa()
    ingredientes = receita_obj.ingredientes if receita_obj else []
    
    receita_atual = {}
    unidades_atual = {}
    
    for ing in ingredientes:
        receita_atual[ing.nome] = ing.quantidade
        unidades_atual[ing.nome] = ing.unidade
    
    return render_template('receita.html',
                         receita_obj=receita_obj,
                         receita_atual=receita_atual,
                         unidades_atual=unidades_atual)

@app.route('/atualizar_receita', methods=['POST'])
def atualizar_receita():
    receita = get_receita_ativa()
    if not receita:
        flash('Erro: Nenhuma receita ativa encontrada', 'error')
        return redirect(url_for('receita'))
    
    # Update existing ingredients
    for ingrediente in receita.ingredientes:
        field_name = f'qtd_{ingrediente.nome}'
        if field_name in request.form:
            nova_quantidade = float(request.form.get(field_name, 0))
            ingrediente.quantidade = nova_quantidade
    
    # Add new ingredients
    novos_ingredientes = request.form.getlist('novo_ingrediente[]')
    novas_quantidades = request.form.getlist('nova_quantidade[]')
    novas_unidades = request.form.getlist('nova_unidade[]')
    
    for i, nome in enumerate(novos_ingredientes):
        if nome and i < len(novas_quantidades) and i < len(novas_unidades):
            novo_ingrediente = IngredienteReceita(
                receita_id=receita.id,
                nome=nome.lower(),
                quantidade=float(novas_quantidades[i]),
                unidade=novas_unidades[i]
            )
            db.session.add(novo_ingrediente)
    
    db.session.commit()
    flash('Receita atualizada com sucesso', 'success')
    return redirect(url_for('receita'))

@app.route('/historico_vendas')
def historico_vendas():
    vendas = Venda.query.order_by(Venda.data_venda.desc()).all()
    return render_template('historico_vendas.html', vendas=vendas)

@app.route('/configuracoes', methods=['GET', 'POST'])
def configuracoes():
    if request.method == 'POST':
        # Update price configuration
        canal = request.form.get('canal')
        tipo_pacote = request.form.get('tipo_pacote')
        quantidade_balas = int(request.form.get('quantidade_balas', 0))
        preco = float(request.form.get('preco', 0))
        
        # Update existing or create new
        config = ConfiguracaoPreco.query.filter_by(
            canal=canal,
            tipo_pacote=tipo_pacote
        ).first()
        
        if config:
            config.quantidade_balas = quantidade_balas
            config.preco = preco
            config.updated_at = datetime.utcnow()
        else:
            config = ConfiguracaoPreco(
                canal=canal,
                tipo_pacote=tipo_pacote,
                quantidade_balas=quantidade_balas,
                preco=preco
            )
            db.session.add(config)
        
        db.session.commit()
        flash('Configuração de preço atualizada', 'success')
    
    # Get current configurations
    configs = ConfiguracaoPreco.query.filter_by(ativo=True).order_by(
        ConfiguracaoPreco.canal, ConfiguracaoPreco.tipo_pacote
    ).all()
    
    return render_template('configuracoes.html', configs=configs)
