from flask import render_template, request, redirect, url_for, flash, jsonify
from app import app, db
from models import (
    Receita, IngredienteReceita, EstoqueInsumo, EstoqueBala, 
    Producao, Venda, ContasReceber, LucrosPendentes, CapitalGiro, 
    PrecoVenda, TransacaoFinanceira, ContasPagar, init_default_data
)
from datetime import datetime, date
import logging

# Initialize default data on first run
with app.app_context():
    init_default_data()

# Constants
SOCIAS = ['Rosangela', 'Janira', 'Outros']
VENDEDORES_IFOOD = ['Rosangela', 'Janira']

@app.route('/')
def index():
    """Dashboard main page"""
    try:
        # Get all data for dashboard
        receitas = Receita.query.filter_by(ativa=True).all()
        vendas = Venda.query.order_by(Venda.data_venda.desc()).limit(5).all()
        ultimas_vendas = Venda.query.order_by(Venda.data_venda.desc()).limit(10).all()
        
        # Calculate stock
        estoque_balas = {}
        total_balas_estoque = 0
        for estoque in EstoqueBala.query.all():
            key = f"{estoque.detentor} - {estoque.receita.nome}"
            estoque_balas[key] = estoque.quantidade
            total_balas_estoque += estoque.quantidade
        
        # Calculate production capacity
        capacidades_atuais = {}
        for socia in SOCIAS:
            capacidade = calcular_capacidade_producao(socia)
            if capacidade['receitas'] > 0:
                capacidades_atuais[socia] = capacidade
        
        # Get pending profits
        lucros_pendentes = {}
        for lucro in LucrosPendentes.query.filter_by(status='Pendente').all():
            if lucro.socia not in lucros_pendentes:
                lucros_pendentes[lucro.socia] = 0
            lucros_pendentes[lucro.socia] += lucro.valor
        
        # Get capital
        capital = CapitalGiro.query.first()
        capital_valor = capital.valor if capital else 0
        
        # Get overdue accounts
        contas_vencidas = ContasReceber.query.filter(
            ContasReceber.status == 'Pendente',
            ContasReceber.data_vencimento < date.today()
        ).all()
        
        # Prepare data structure for template compatibility
        dados = {
            'vendas': vendas,
            'estoque_balas_prontas': estoque_balas,
            'financeiro': {
                'capital_de_giro': capital_valor,
                'lucros_pendentes': lucros_pendentes,
                'contas_a_receber_ifood': ContasReceber.query.all()
            }
        }
        
        return render_template('index.html',
                             dados=dados,
                             total_balas_estoque=total_balas_estoque,
                             capacidades_atuais=capacidades_atuais,
                             ultimas_vendas=ultimas_vendas,
                             contas_vencidas=contas_vencidas)
                             
    except Exception as e:
        logging.error(f"Error in index route: {e}")
        flash('Erro ao carregar dashboard', 'error')
        return render_template('index.html', dados={'vendas': [], 'estoque_balas_prontas': {}, 'financeiro': {'capital_de_giro': 0, 'lucros_pendentes': {}}})

@app.route('/receitas')
def receitas_multiplas():
    """Multiple recipes management page"""
    receitas = Receita.query.all()
    return render_template('receitas_multiplas.html', receitas=receitas)

@app.route('/receitas/nova', methods=['GET', 'POST'])
def nova_receita():
    """Create new recipe"""
    if request.method == 'POST':
        try:
            nome = request.form.get('nome')
            descricao = request.form.get('descricao', '')
            balas_por_receita = int(request.form.get('balas_por_receita', 40))
            
            # Check if recipe already exists
            if Receita.query.filter_by(nome=nome).first():
                flash('Já existe uma receita com este nome', 'error')
                return redirect(url_for('nova_receita'))
            
            # Create recipe
            receita = Receita(
                nome=nome,
                descricao=descricao,
                balas_por_receita=balas_por_receita,
                ativa=True
            )
            db.session.add(receita)
            db.session.flush()
            
            # Add ingredients
            ingredientes = request.form.getlist('ingrediente_nome')
            quantidades = request.form.getlist('ingrediente_quantidade')
            unidades = request.form.getlist('ingrediente_unidade')
            
            for i, nome_ing in enumerate(ingredientes):
                if nome_ing.strip():
                    ingrediente = IngredienteReceita(
                        receita_id=receita.id,
                        nome=nome_ing.strip().lower().replace(' ', '_'),
                        quantidade=float(quantidades[i]),
                        unidade=unidades[i]
                    )
                    db.session.add(ingrediente)
            
            # Initialize stock for all partners
            for socia in SOCIAS:
                # Initialize ingredient stock
                for ingrediente in receita.ingredientes:
                    if not EstoqueInsumo.query.filter_by(socia=socia, nome_insumo=ingrediente.nome).first():
                        estoque = EstoqueInsumo(
                            socia=socia,
                            nome_insumo=ingrediente.nome,
                            quantidade=0,
                            unidade=ingrediente.unidade
                        )
                        db.session.add(estoque)
                
                # Initialize candy stock
                estoque_bala = EstoqueBala(
                    detentor=socia,
                    receita_id=receita.id,
                    quantidade=0
                )
                db.session.add(estoque_bala)
            
            db.session.commit()
            flash('Receita criada com sucesso!', 'success')
            return redirect(url_for('receitas_multiplas'))
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error creating recipe: {e}")
            flash('Erro ao criar receita', 'error')
    
    return render_template('nova_receita.html')

@app.route('/receita/<int:receita_id>')
def editar_receita(receita_id):
    """Edit specific recipe"""
    receita = Receita.query.get_or_404(receita_id)
    
    # Get current ingredients as dict for compatibility
    receita_atual = {}
    unidades_atual = {}
    for ing in receita.ingredientes:
        receita_atual[ing.nome] = ing.quantidade
        unidades_atual[ing.nome] = ing.unidade
    
    return render_template('receita.html',
                         receita_obj=receita,
                         receita_atual=receita_atual,
                         unidades_atual=unidades_atual,
                         receita_id=receita_id)

@app.route('/receita/<int:receita_id>/atualizar', methods=['POST'])
def atualizar_receita(receita_id):
    """Update specific recipe"""
    try:
        receita = Receita.query.get_or_404(receita_id)
        
        # Update existing ingredients
        for ingrediente in receita.ingredientes:
            qtd_field = f'qtd_{ingrediente.nome}'
            if qtd_field in request.form:
                ingrediente.quantidade = float(request.form[qtd_field])
        
        # Add new ingredients
        novos_ingredientes = request.form.getlist('novo_ingrediente[]')
        novas_quantidades = request.form.getlist('nova_quantidade[]')
        novas_unidades = request.form.getlist('nova_unidade[]')
        
        for i, nome in enumerate(novos_ingredientes):
            if nome.strip():
                nome_normalizado = nome.strip().lower().replace(' ', '_')
                
                # Check if ingredient already exists
                if not any(ing.nome == nome_normalizado for ing in receita.ingredientes):
                    novo_ingrediente = IngredienteReceita(
                        receita_id=receita.id,
                        nome=nome_normalizado,
                        quantidade=float(novas_quantidades[i]),
                        unidade=novas_unidades[i]
                    )
                    db.session.add(novo_ingrediente)
                    
                    # Add to all partners' stock
                    for socia in SOCIAS:
                        if not EstoqueInsumo.query.filter_by(socia=socia, nome_insumo=nome_normalizado).first():
                            estoque = EstoqueInsumo(
                                socia=socia,
                                nome_insumo=nome_normalizado,
                                quantidade=0,
                                unidade=novas_unidades[i]
                            )
                            db.session.add(estoque)
        
        receita.atualizada_em = datetime.utcnow()
        db.session.commit()
        flash('Receita atualizada com sucesso!', 'success')
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error updating recipe: {e}")
        flash('Erro ao atualizar receita', 'error')
    
    return redirect(url_for('editar_receita', receita_id=receita_id))

@app.route('/producao', methods=['GET', 'POST'])
def producao():
    """Production management"""
    if request.method == 'POST':
        try:
            socia_produtora = request.form.get('socia_produtora')
            receita_id = int(request.form.get('receita_id', 1))  # Default to first recipe
            receitas_a_produzir = int(request.form.get('receitas_a_produzir'))
            
            receita = Receita.query.get(receita_id)
            if not receita:
                flash('Receita não encontrada', 'error')
                return redirect(url_for('producao'))
            
            # Check if production is possible
            capacidade = calcular_capacidade_producao(socia_produtora, receita_id)
            if receitas_a_produzir > capacidade['receitas']:
                flash('Quantidade excede a capacidade de produção disponível', 'error')
                return redirect(url_for('producao'))
            
            # Consume ingredients
            for ingrediente in receita.ingredientes:
                estoque = EstoqueInsumo.query.filter_by(
                    socia=socia_produtora,
                    nome_insumo=ingrediente.nome
                ).first()
                if estoque:
                    estoque.quantidade -= ingrediente.quantidade * receitas_a_produzir
            
            # Add to candy stock
            estoque_bala = EstoqueBala.query.filter_by(
                detentor=socia_produtora,
                receita_id=receita_id
            ).first()
            if not estoque_bala:
                estoque_bala = EstoqueBala(
                    detentor=socia_produtora,
                    receita_id=receita_id,
                    quantidade=0
                )
                db.session.add(estoque_bala)
            
            balas_produzidas = receitas_a_produzir * receita.balas_por_receita
            estoque_bala.quantidade += balas_produzidas
            
            # Record production
            producao = Producao(
                socia_produtora=socia_produtora,
                receita_id=receita_id,
                receitas_produzidas=receitas_a_produzir,
                balas_produzidas=balas_produzidas
            )
            db.session.add(producao)
            
            db.session.commit()
            flash(f'Produção registrada: {balas_produzidas} balas de {receita.nome}!', 'success')
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error in production: {e}")
            flash('Erro ao registrar produção', 'error')
        
        return redirect(url_for('producao'))
    
    # GET request
    receitas = Receita.query.filter_by(ativa=True).all()
    receita_padrao = receitas[0] if receitas else None
    
    if receita_padrao:
        receita_dict = {ing.nome: ing.quantidade for ing in receita_padrao.ingredientes}
        unidades = {ing.nome: ing.unidade for ing in receita_padrao.ingredientes}
        
        # Get stock data
        dados = {'estoque_insumos': {}}
        for socia in SOCIAS:
            dados['estoque_insumos'][socia] = {}
            for ingrediente in receita_padrao.ingredientes:
                estoque = EstoqueInsumo.query.filter_by(
                    socia=socia,
                    nome_insumo=ingrediente.nome
                ).first()
                dados['estoque_insumos'][socia][ingrediente.nome] = estoque.quantidade if estoque else 0
    else:
        receita_dict = {}
        unidades = {}
        dados = {'estoque_insumos': {}}
    
    return render_template('producao.html',
                         socias=SOCIAS,
                         receitas=receitas,
                         receita_padrao=receita_dict,
                         unidades=unidades,
                         balas_por_receita=receita_padrao.balas_por_receita if receita_padrao else 40,
                         dados=dados)

@app.route('/vendas', methods=['GET', 'POST'])
def vendas():
    """Sales management"""
    if request.method == 'POST':
        try:
            socia_produtora = request.form.get('socia_produtora')
            estoque_saida = request.form.get('estoque_saida')
            canal_venda = request.form.get('canal_venda')
            receita_id = int(request.form.get('receita_id', 1))  # Default to first recipe
            
            # Get quantity and price based on channel
            if canal_venda == 'restaurante':
                quantidade_balas = int(request.form.get('quantidade_balas'))
                preco = PrecoVenda.query.filter_by(canal=canal_venda, tipo_pacote='preco_unitario').first()
                valor_bruto = quantidade_balas * preco.preco if preco else 0
                tipo_pacote = 'unitario'
            else:
                tipo_pacote = request.form.get('tipo_pacote')
                preco_obj = PrecoVenda.query.filter_by(canal=canal_venda, tipo_pacote=tipo_pacote).first()
                if not preco_obj:
                    flash('Preço não encontrado para este pacote', 'error')
                    return redirect(url_for('vendas'))
                
                valor_bruto = preco_obj.preco
                # Extract quantity from package name
                import re
                match = re.search(r'(\d+)', tipo_pacote)
                quantidade_balas = int(match.group(1)) if match else 1
            
            # Check stock
            estoque_bala = EstoqueBala.query.filter_by(
                detentor=estoque_saida,
                receita_id=receita_id
            ).first()
            
            if not estoque_bala or estoque_bala.quantidade < quantidade_balas:
                flash('Estoque insuficiente', 'error')
                return redirect(url_for('vendas'))
            
            # Calculate costs and profit
            receita = Receita.query.get(receita_id)
            custo = quantidade_balas * receita.custo_por_bala
            
            # Apply iFood fees if needed
            lucro_liquido = valor_bruto - custo
            if canal_venda == 'ifood':
                taxa_percentual = valor_bruto * 0.262
                taxa_fixa = 1.00 if valor_bruto < 20.00 else 0.00
                taxa_total = taxa_percentual + taxa_fixa
                valor_liquido = valor_bruto - taxa_total
                lucro_liquido = valor_liquido - custo
            
            # Update stock
            estoque_bala.quantidade -= quantidade_balas
            
            # Create sale record
            venda = Venda(
                socia_produtora=socia_produtora,
                estoque_saida=estoque_saida,
                receita_id=receita_id,
                canal_venda=canal_venda,
                tipo_pacote=tipo_pacote,
                quantidade_balas=quantidade_balas,
                valor_bruto=valor_bruto,
                custo=custo,
                lucro_liquido=lucro_liquido
            )
            
            # iFood specific fields
            if canal_venda == 'ifood':
                venda.fonte_ifood = request.form.get('fonte_ifood')
                venda.id_recebivel = request.form.get('id_recebivel')
                data_prevista_str = request.form.get('data_prevista')
                if data_prevista_str:
                    venda.data_prevista = datetime.strptime(data_prevista_str, '%Y-%m-%d').date()
                
                # Create receivable account
                if venda.id_recebivel:
                    conta = ContasReceber(
                        venda_id=venda.id,
                        descricao=f'iFood - {venda.id_recebivel}',
                        valor=valor_bruto,
                        data_vencimento=venda.data_prevista or date.today(),
                        fonte=venda.fonte_ifood,
                        status='Pendente'
                    )
                    db.session.add(conta)
            
            db.session.add(venda)
            
            # Add profit to pending profits
            if lucro_liquido > 0:
                lucro_pendente = LucrosPendentes(
                    socia=socia_produtora,
                    descricao=f'Venda {canal_venda} - {quantidade_balas} balas',
                    valor=lucro_liquido,
                    origem=f'Venda #{venda.id}',
                    status='Pendente'
                )
                db.session.add(lucro_pendente)
            
            db.session.commit()
            flash(f'Venda registrada com sucesso! Lucro: R$ {lucro_liquido:.2f}', 'success')
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error in sales: {e}")
            flash('Erro ao registrar venda', 'error')
        
        return redirect(url_for('vendas'))
    
    # GET request
    receitas = Receita.query.filter_by(ativa=True).all()
    
    # Get stock data
    estoque_balas = {}
    detentores_estoque = []
    for estoque in EstoqueBala.query.filter(EstoqueBala.quantidade > 0).all():
        key = f"{estoque.detentor} - {estoque.receita.nome}"
        estoque_balas[key] = estoque.quantidade
        if estoque.detentor not in detentores_estoque:
            detentores_estoque.append(estoque.detentor)
    
    # Get pricing
    precos_venda = {}
    for preco in PrecoVenda.query.all():
        if preco.canal not in precos_venda:
            precos_venda[preco.canal] = {}
        precos_venda[preco.canal][preco.tipo_pacote] = preco.preco
    
    dados = {'estoque_balas_prontas': estoque_balas}
    
    return render_template('vendas.html',
                         socias=SOCIAS,
                         receitas=receitas,
                         detentores_estoque=detentores_estoque,
                         precos_venda=precos_venda,
                         vendedores_ifood=VENDEDORES_IFOOD,
                         dados=dados)

@app.route('/historico-vendas')
def historico_vendas():
    """Sales history"""
    vendas = Venda.query.order_by(Venda.data_venda.desc()).all()
    
    # Add computed fields for template compatibility
    for venda in vendas:
        venda.id_venda = venda.id
        venda.total_balas = venda.quantidade_balas
    
    return render_template('historico_vendas.html', vendas=vendas)

@app.route('/financeiro', methods=['GET', 'POST'])
def financeiro():
    """Financial management"""
    if request.method == 'POST':
        try:
            acao = request.form.get('acao')
            
            if acao == 'adicionar_lucro':
                socia = request.form.get('socia')
                descricao = request.form.get('descricao')
                valor = float(request.form.get('valor'))
                
                lucro = LucrosPendentes(
                    socia=socia,
                    descricao=descricao,
                    valor=valor,
                    origem='Adição Manual',
                    status='Pendente'
                )
                db.session.add(lucro)
                db.session.commit()
                flash(f'Lucro de R$ {valor:.2f} adicionado para {socia}', 'success')
            
            elif acao == 'pagar_lucro':
                lucro_id = int(request.form.get('lucro_id'))
                lucro = LucrosPendentes.query.get(lucro_id)
                if lucro:
                    lucro.status = 'Pago'
                    db.session.commit()
                    flash('Lucro marcado como pago', 'success')
            
            elif acao == 'adicionar_aporte':
                valor = float(request.form.get('valor'))
                descricao = request.form.get('descricao')
                
                # Update capital
                capital = CapitalGiro.query.first()
                if not capital:
                    capital = CapitalGiro(valor=valor)
                    db.session.add(capital)
                else:
                    capital.valor += valor
                
                # Record transaction
                transacao = TransacaoFinanceira(
                    tipo='Aporte',
                    descricao=descricao,
                    valor=valor
                )
                db.session.add(transacao)
                db.session.commit()
                flash(f'Aporte de R$ {valor:.2f} adicionado', 'success')
                
            elif acao == 'compra_credito':
                valor = float(request.form.get('valor'))
                descricao = request.form.get('descricao')
                data_vencimento_str = request.form.get('data_vencimento')
                
                # Create payable account
                data_vencimento = None
                if data_vencimento_str:
                    data_vencimento = datetime.strptime(data_vencimento_str, '%Y-%m-%d').date()
                
                conta = ContasPagar(
                    descricao=descricao,
                    valor=valor,
                    data_vencimento=data_vencimento,
                    tipo='Compra no crédito',
                    status='Pendente'
                )
                db.session.add(conta)
                
                # Record transaction
                transacao = TransacaoFinanceira(
                    tipo='Compra no crédito',
                    descricao=descricao,
                    valor=-valor  # Negative because it's an expense
                )
                db.session.add(transacao)
                db.session.commit()
                flash(f'Compra no crédito de R$ {valor:.2f} registrada', 'success')
                
            elif acao == 'adicionar_lucro':
                socia = request.form.get('socia')
                descricao = request.form.get('descricao')
                valor = float(request.form.get('valor'))
                
                lucro = LucrosPendentes(
                    socia=socia,
                    descricao=descricao,
                    valor=valor,
                    origem='Adição Manual',
                    status='Pendente'
                )
                db.session.add(lucro)
                db.session.commit()
                flash(f'Lucro de R$ {valor:.2f} adicionado para {socia}', 'success')
                
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error in financial: {e}")
            flash('Erro na operação financeira', 'error')
        
        return redirect(url_for('financeiro'))
    
    # GET request
    capital = CapitalGiro.query.first()
    lucros_pendentes = LucrosPendentes.query.filter_by(status='Pendente').all()
    contas_receber = ContasReceber.query.filter_by(status='Pendente').all()
    contas_pagar = ContasPagar.query.filter_by(status='Pendente').all()
    transacoes = TransacaoFinanceira.query.order_by(TransacaoFinanceira.data_transacao.desc()).limit(10).all()
    
    # Group profits by partner
    lucros_pendentes_dict = {}
    for lucro in lucros_pendentes:
        if lucro.socia not in lucros_pendentes_dict:
            lucros_pendentes_dict[lucro.socia] = 0
        lucros_pendentes_dict[lucro.socia] += lucro.valor
    
    return render_template('financeiro.html',
                         capital=capital,
                         lucros_pendentes=lucros_pendentes_dict,
                         contas_receber=contas_receber,
                         contas_pagar=contas_pagar,
                         transacoes=transacoes,
                         socias=SOCIAS)

@app.route('/financeiro/pagar/<int:conta_id>', methods=['POST'])
def pagar_conta(conta_id):
    """Pay a bill"""
    try:
        conta = ContasPagar.query.get(conta_id)
        if not conta:
            return jsonify({'success': False, 'message': 'Conta não encontrada'})
        
        if conta.status == 'Pago':
            return jsonify({'success': False, 'message': 'Conta já foi paga'})
        
        # Update account status
        conta.status = 'Pago'
        conta.data_pagamento = datetime.utcnow()
        
        # Update capital
        capital = CapitalGiro.query.first()
        if capital:
            capital.valor -= conta.valor
        
        # Record transaction
        transacao = TransacaoFinanceira(
            tipo='Pagamento',
            descricao=f'Pagamento: {conta.descricao}',
            valor=-conta.valor
        )
        db.session.add(transacao)
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error paying bill: {e}")
        return jsonify({'success': False, 'message': 'Erro ao processar pagamento'})

@app.route('/configuracoes-precos', methods=['GET', 'POST'])
def configuracoes_precos():
    """Price configuration management"""
    if request.method == 'POST':
        try:
            acao = request.form.get('acao')
            
            if acao == 'salvar_preco':
                canal = request.form.get('canal')
                tipo_pacote = request.form.get('tipo_pacote')
                qtd_balas = int(request.form.get('qtd_balas'))
                preco = float(request.form.get('preco'))
                
                # Check if price configuration already exists
                preco_existente = PrecoVenda.query.filter_by(canal=canal, tipo_pacote=tipo_pacote).first()
                
                if preco_existente:
                    preco_existente.quantidade_balas = qtd_balas
                    preco_existente.preco = preco
                    preco_existente.updated_at = datetime.utcnow()
                    flash('Preço atualizado com sucesso', 'success')
                else:
                    novo_preco = PrecoVenda(
                        canal=canal,
                        tipo_pacote=tipo_pacote,
                        quantidade_balas=qtd_balas,
                        preco=preco,
                        ativo=True
                    )
                    db.session.add(novo_preco)
                    flash('Novo preço adicionado com sucesso', 'success')
                
                db.session.commit()
                
            elif acao == 'atualizar_preco':
                preco_id = int(request.form.get('preco_id'))
                qtd_balas = int(request.form.get('qtd_balas'))
                preco = float(request.form.get('preco'))
                
                preco_obj = PrecoVenda.query.get(preco_id)
                if preco_obj:
                    preco_obj.quantidade_balas = qtd_balas
                    preco_obj.preco = preco
                    preco_obj.updated_at = datetime.utcnow()
                    db.session.commit()
                    flash('Preço atualizado com sucesso', 'success')
                
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error in price configuration: {e}")
            flash('Erro ao salvar configuração de preço', 'error')
        
        return redirect(url_for('configuracoes_precos'))
    
    # GET request
    precos_atuais = PrecoVenda.query.order_by(PrecoVenda.canal, PrecoVenda.tipo_pacote).all()
    
    return render_template('configuracoes_precos.html', precos_atuais=precos_atuais)

@app.route('/configuracoes-precos/toggle/<int:preco_id>', methods=['POST'])
def toggle_preco(preco_id):
    """Toggle price active status"""
    try:
        preco = PrecoVenda.query.get(preco_id)
        if not preco:
            return jsonify({'success': False, 'message': 'Preço não encontrado'})
        
        preco.ativo = not preco.ativo
        preco.updated_at = datetime.utcnow()
        db.session.commit()
        
        status = 'ativado' if preco.ativo else 'desativado'
        return jsonify({'success': True, 'message': f'Preço {status} com sucesso'})
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error toggling price: {e}")
        return jsonify({'success': False, 'message': 'Erro ao alterar status'})

@app.route('/estoque', methods=['GET', 'POST'])
def estoque():
    """Stock management"""
    if request.method == 'POST':
        try:
            acao = request.form.get('acao')
            
            if acao == 'atualizar_insumo':
                socia = request.form.get('socia')
                nome_insumo = request.form.get('nome_insumo')
                quantidade = float(request.form.get('quantidade'))
                
                estoque = EstoqueInsumo.query.filter_by(socia=socia, nome_insumo=nome_insumo).first()
                if estoque:
                    estoque.quantidade = quantidade
                    db.session.commit()
                    flash('Estoque de insumo atualizado', 'success')
                else:
                    flash('Insumo não encontrado', 'error')
            
            elif acao == 'atualizar_bala':
                detentor = request.form.get('detentor')
                receita_id = int(request.form.get('receita_id'))
                quantidade = int(request.form.get('quantidade'))
                
                estoque = EstoqueBala.query.filter_by(detentor=detentor, receita_id=receita_id).first()
                if estoque:
                    estoque.quantidade = quantidade
                    db.session.commit()
                    flash('Estoque de balas atualizado', 'success')
                else:
                    flash('Estoque não encontrado', 'error')
                    
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error in stock: {e}")
            flash('Erro ao atualizar estoque', 'error')
        
        return redirect(url_for('estoque'))
    
    # GET request
    receitas = Receita.query.filter_by(ativa=True).all()
    estoque_insumos = EstoqueInsumo.query.all()
    estoque_balas = EstoqueBala.query.all()
    
    return render_template('estoque.html',
                         socias=SOCIAS,
                         receitas=receitas,
                         estoque_insumos=estoque_insumos,
                         estoque_balas=estoque_balas)

def calcular_capacidade_producao(socia, receita_id=None):
    """Calculate production capacity for a partner"""
    if receita_id:
        receita = Receita.query.get(receita_id)
    else:
        receita = Receita.query.filter_by(ativa=True).first()
    
    if not receita:
        return {'receitas': 0, 'balas': 0}
    
    capacidade_minima = float('inf')
    
    for ingrediente in receita.ingredientes:
        estoque = EstoqueInsumo.query.filter_by(
            socia=socia,
            nome_insumo=ingrediente.nome
        ).first()
        
        if not estoque or estoque.quantidade <= 0:
            capacidade_minima = 0
            break
        
        receitas_possiveis = estoque.quantidade // ingrediente.quantidade
        capacidade_minima = min(capacidade_minima, receitas_possiveis)
    
    if capacidade_minima == float('inf'):
        capacidade_minima = 0
    
    return {
        'receitas': int(capacidade_minima),
        'balas': int(capacidade_minima * receita.balas_por_receita)
    }

# API endpoints for JavaScript
@app.route('/api/capacidade/<socia>')
def api_capacidade(socia):
    """API endpoint for production capacity"""
    receita_id = request.args.get('receita_id', type=int)
    capacidade = calcular_capacidade_producao(socia, receita_id)
    return jsonify(capacidade)

@app.route('/api/precos/<canal>')
def api_precos(canal):
    """API endpoint for pricing by channel"""
    precos = PrecoVenda.query.filter_by(canal=canal).all()
    result = {}
    for preco in precos:
        result[preco.tipo_pacote] = preco.preco
    return jsonify(result)

@app.context_processor
def utility_processor():
    """Make utility functions available in templates"""
    return dict(enumerate=enumerate, len=len, int=int, float=float)

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500
