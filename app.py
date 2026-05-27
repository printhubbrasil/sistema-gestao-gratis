import sys
import os
import json
import time
from datetime import timedelta
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, session
import database as db

# Carrega .env se existir (desenvolvimento local)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Garante encoding UTF-8 no terminal Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

app = Flask(__name__)

# ─── DADOS DA EMPRESA (via env vars) ──────────────────────────────────────────
@app.context_processor
def inject_empresa():
    return dict(
        empresa_nome     = os.environ.get('EMPRESA_NOME',      'Minha Gráfica'),
        empresa_cidade   = os.environ.get('EMPRESA_CIDADE',    'Cidade — UF'),
        empresa_telefone = os.environ.get('EMPRESA_TELEFONE',  '(00) 00000-0000'),
        empresa_site     = os.environ.get('EMPRESA_SITE',      'minhagrafica.com.br'),
    )

# Chave secreta: defina SECRET_KEY no .env em produção
_secret = os.environ.get('SECRET_KEY', '')
if not _secret:
    import secrets
    _secret = secrets.token_hex(32)
app.secret_key = _secret

# ─── CONFIGURAÇÕES DE SEGURANÇA ───────────────────────────────────────────────

app.config['MAX_CONTENT_LENGTH']        = 5 * 1024 * 1024   # upload máx 5 MB
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=8)
app.config['SESSION_COOKIE_HTTPONLY']   = True
app.config['SESSION_COOKIE_SAMESITE']  = 'Lax'
# Em produção com HTTPS, ativar: app.config['SESSION_COOKIE_SECURE'] = True

# ─── RATE LIMITING (login brute force) ────────────────────────────────────────
# {ip: [tentativas, timestamp_primeiro_bloqueio]}
_login_tentativas: dict = {}
_MAX_TENTATIVAS = 5
_BLOQUEIO_SEGUNDOS = 900  # 15 minutos

def _checar_rate_limit(ip: str) -> bool:
    """Retorna True se o IP está bloqueado."""
    if ip not in _login_tentativas:
        return False
    tentativas, desde = _login_tentativas[ip]
    if tentativas >= _MAX_TENTATIVAS:
        if time.time() - desde < _BLOQUEIO_SEGUNDOS:
            return True
        del _login_tentativas[ip]
    return False

def _registrar_falha(ip: str):
    if ip not in _login_tentativas:
        _login_tentativas[ip] = [0, time.time()]
    _login_tentativas[ip][0] += 1

def _limpar_tentativas(ip: str):
    _login_tentativas.pop(ip, None)

# ─── HEADERS DE SEGURANÇA ─────────────────────────────────────────────────────

@app.after_request
def adicionar_headers_seguranca(response):
    response.headers['X-Frame-Options']        = 'SAMEORIGIN'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-XSS-Protection']       = '1; mode=block'
    response.headers['Referrer-Policy']        = 'strict-origin-when-cross-origin'
    return response

# ─── AUTENTICAÇÃO ─────────────────────────────────────────────────────────────

_ROTAS_PUBLICAS = {'login', 'static'}

@app.before_request
def verificar_login():
    if request.endpoint in _ROTAS_PUBLICAS:
        return
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'usuario_id' in session:
        return redirect(url_for('home'))
    if request.method == 'POST':
        ip = request.remote_addr
        if _checar_rate_limit(ip):
            flash('Muitas tentativas. Tente novamente em 15 minutos.', 'danger')
            return render_template('login.html')
        usuario = db.auth_get_usuario_by_login(request.form.get('login', '').strip())
        if usuario and db.auth_verificar_senha(usuario, request.form.get('senha', '')):
            _limpar_tentativas(ip)
            session.permanent = True
            session['usuario_id']   = usuario['id']
            session['usuario_nome'] = usuario['nome']
            session['nivel']        = usuario['nivel']
            return redirect(url_for('home'))
        _registrar_falha(ip)
        flash('Login ou senha incorretos.', 'danger')
    return render_template('login.html')

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('login'))

# ─── ADMIN — USUÁRIOS ─────────────────────────────────────────────────────────

@app.route('/admin/usuarios')
def admin_usuarios():
    if session.get('nivel') != 'admin':
        flash('Acesso restrito a administradores.', 'danger')
        return redirect(url_for('home'))
    lista = db.auth_get_usuarios()
    return render_template('admin/usuarios.html', usuarios=lista)

@app.route('/admin/usuarios/novo', methods=['GET', 'POST'])
def admin_novo_usuario():
    if session.get('nivel') != 'admin':
        flash('Acesso restrito a administradores.', 'danger')
        return redirect(url_for('home'))
    if request.method == 'POST':
        db.auth_criar_usuario(request.form)
        flash('Usuário criado!', 'success')
        return redirect(url_for('admin_usuarios'))
    return render_template('admin/form_usuario.html', usuario=None)

@app.route('/admin/usuarios/<int:id>/editar', methods=['GET', 'POST'])
def admin_editar_usuario(id):
    if session.get('nivel') != 'admin':
        flash('Acesso restrito a administradores.', 'danger')
        return redirect(url_for('home'))
    usuario = db.auth_get_usuario(id)
    if request.method == 'POST':
        db.auth_atualizar_usuario(id, request.form)
        flash('Usuário atualizado!', 'success')
        return redirect(url_for('admin_usuarios'))
    return render_template('admin/form_usuario.html', usuario=usuario)

@app.route('/admin/usuarios/<int:id>/toggle', methods=['POST'])
def admin_toggle_usuario(id):
    if session.get('nivel') != 'admin':
        return jsonify({'ok': False}), 403
    ativo = int(request.json.get('ativo', 1))
    db.auth_toggle_usuario(id, ativo)
    return jsonify({'ok': True})

# ─── BACKUP ───────────────────────────────────────────────────────────────────

@app.route('/admin/backup/download')
def admin_backup_download():
    if session.get('nivel') != 'admin':
        flash('Acesso restrito a administradores.', 'danger')
        return redirect(url_for('home'))
    import shutil, tempfile
    from flask import send_file
    from datetime import datetime
    db_path = os.path.join(os.path.dirname(__file__), os.environ.get('DATABASE_PATH', 'grafica.db'))
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M')
    nome = f'grafica_backup_{timestamp}.db'
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    shutil.copy2(db_path, tmp.name)
    tmp.close()
    return send_file(tmp.name, as_attachment=True, download_name=nome, mimetype='application/octet-stream')

# ─── HOME ─────────────────────────────────────────────────────────────────────

@app.route('/')
def home():
    stats = db.get_stats()
    # dados ponto de equilíbrio para widget do dashboard
    pec_custos       = db.pec_get_custos()
    pec_total        = sum(c['valor'] for c in pec_custos if c['ativo'])
    overhead_pct     = float(db.prec_get_config('overhead_pct', 0))
    invest_venda_pct = float(db.prec_get_config('invest_venda_pct', 0))
    markup_padrao    = float(db.prec_get_config('markup_padrao', 2.5))
    m   = markup_padrao
    iv  = invest_venda_pct / 100
    oh  = overhead_pct / 100
    fator   = m * (1 + iv)
    mc_pct  = (fator - (1 + oh)) / fator if fator > 0 else 0
    fat_min = (pec_total / mc_pct) if mc_pct > 0 else 0
    fat_mes = stats.get('faturamento_mes', 0)
    pec_pct = min(int((fat_mes / fat_min * 100) if fat_min > 0 else 0), 100)
    pec = dict(
        total=pec_total,
        fat_min=fat_min,
        fat_mes=fat_mes,
        mc_pct=mc_pct * 100,
        pct=pec_pct,
        atingido=fat_mes >= fat_min and fat_min > 0,
        sem_config=pec_total == 0,
    )
    return render_template('home.html', stats=stats, pec=pec)

# ─── CLIENTES ─────────────────────────────────────────────────────────────────

@app.route('/clientes')
def clientes():
    busca = request.args.get('q')
    lista = db.get_clientes(busca)
    return render_template('clientes/lista.html', clientes=lista, busca=busca)

@app.route('/clientes/novo', methods=['GET', 'POST'])
def novo_cliente():
    if request.method == 'POST':
        db.criar_cliente(request.form)
        flash('Cliente cadastrado com sucesso!', 'success')
        return redirect(url_for('clientes'))
    return render_template('clientes/form.html', cliente=None)

@app.route('/clientes/<int:id>/editar', methods=['GET', 'POST'])
def editar_cliente(id):
    cliente = db.get_cliente(id)
    if request.method == 'POST':
        db.atualizar_cliente(id, request.form)
        flash('Cliente atualizado!', 'success')
        return redirect(url_for('clientes'))
    return render_template('clientes/form.html', cliente=cliente)

@app.route('/clientes/<int:id>/excluir', methods=['POST'])
def excluir_cliente(id):
    db.excluir_cliente(id)
    flash('Cliente removido.', 'info')
    return redirect(url_for('clientes'))

@app.route('/clientes/api')
def api_clientes():
    lista = db.get_clientes(request.args.get('q'))
    return jsonify(lista)

# ─── PRODUTOS ─────────────────────────────────────────────────────────────────

@app.route('/produtos')
def produtos():
    busca = request.args.get('q')
    lista = db.get_produtos(busca)
    categorias = db.get_categorias()
    return render_template('produtos/lista.html', produtos=lista, categorias=categorias, busca=busca)

@app.route('/produtos/novo', methods=['GET', 'POST'])
def novo_produto():
    if request.method == 'POST':
        precos = json.loads(request.form.get('precos_json', '[]'))
        variacoes = json.loads(request.form.get('variacoes_json', '[]'))
        categorias_sel = request.form.getlist('categorias_sel')
        db.criar_produto(request.form, precos, variacoes, categorias_sel)
        flash('Produto cadastrado!', 'success')
        return redirect(url_for('produtos'))
    return render_template('produtos/form.html', produto=None)

@app.route('/produtos/<int:id>/editar', methods=['GET', 'POST'])
def editar_produto(id):
    produto = db.get_produto(id)
    if request.method == 'POST':
        precos = json.loads(request.form.get('precos_json', '[]'))
        variacoes = json.loads(request.form.get('variacoes_json', '[]'))
        categorias_sel = request.form.getlist('categorias_sel')
        db.atualizar_produto(id, request.form, precos, variacoes, categorias_sel)
        flash('Produto atualizado!', 'success')
        return redirect(url_for('produtos'))
    return render_template('produtos/form.html', produto=produto)

@app.route('/produtos/<int:id>/excluir', methods=['POST'])
def excluir_produto(id):
    db.excluir_produto(id)
    flash('Produto removido.', 'info')
    return redirect(url_for('produtos'))

@app.route('/produtos/api')
def api_produtos():
    lista = db.get_produtos(request.args.get('q'))
    return jsonify(lista)

@app.route('/produtos/<int:id>/precos')
def api_produto_precos(id):
    p = db.get_produto_precos(id)
    return jsonify(p) if p else ('', 404)

# ─── PEDIDOS ─────────────────────────────────────────────────────────────────

@app.route('/pedidos')
def pedidos():
    status = request.args.get('status')
    busca = request.args.get('q')
    lista = db.get_pedidos(status, busca)
    return render_template('pedidos/lista.html', pedidos=lista, status=status, busca=busca)

@app.route('/pedidos/novo', methods=['GET', 'POST'])
def novo_pedido():
    if request.method == 'POST':
        itens = json.loads(request.form.get('itens_json', '[]'))
        pedido_id = db.criar_pedido(request.form, itens)
        flash(f'Pedido #{pedido_id} criado!', 'success')
        return redirect(url_for('pedidos'))
    clientes = db.get_clientes()
    produtos = db.get_produtos()
    return render_template('pedidos/form.html', pedido=None, clientes=clientes, produtos=produtos)

@app.route('/pedidos/<int:id>/editar', methods=['GET', 'POST'])
def editar_pedido(id):
    pedido = db.get_pedido(id)
    if request.method == 'POST':
        itens = json.loads(request.form.get('itens_json', '[]'))
        db.atualizar_pedido(id, request.form, itens)
        flash('Pedido atualizado!', 'success')
        return redirect(url_for('pedidos'))
    clientes = db.get_clientes()
    produtos = db.get_produtos()
    return render_template('pedidos/form.html', pedido=pedido, clientes=clientes, produtos=produtos)

@app.route('/pedidos/<int:id>/status', methods=['POST'])
def atualizar_status_pedido(id):
    db.atualizar_status_pedido(id, request.json.get('status'))
    return jsonify({'ok': True})

@app.route('/pedidos/<int:id>/excluir', methods=['POST'])
def excluir_pedido(id):
    db.excluir_pedido(id)
    flash('Pedido removido.', 'info')
    return redirect(url_for('pedidos'))

@app.route('/pedidos/<int:id>')
def ver_pedido(id):
    pedido = db.get_pedido(id)
    return render_template('pedidos/detalhe.html', pedido=pedido)

@app.route('/pedidos/<int:id>/imprimir')
def imprimir_pedido(id):
    pedido = db.get_pedido(id)
    return render_template('pedidos/imprimir.html', pedido=pedido)

# ─── ORÇAMENTOS ───────────────────────────────────────────────────────────────

@app.route('/orcamentos')
def orcamentos():
    status = request.args.get('status')
    busca = request.args.get('q')
    lista = db.get_orcamentos(status, busca)
    return render_template('orcamentos/lista.html', orcamentos=lista, status=status, busca=busca)

@app.route('/orcamentos/novo', methods=['GET', 'POST'])
def novo_orcamento():
    if request.method == 'POST':
        itens = json.loads(request.form.get('itens_json', '[]'))
        orc_id, numero = db.criar_orcamento(request.form, itens)
        flash(f'Orçamento {numero} criado!', 'success')
        return redirect(url_for('ver_orcamento', id=orc_id))
    clientes = db.get_clientes()
    produtos = db.get_produtos()
    return render_template('orcamentos/form.html', orcamento=None, clientes=clientes, produtos=produtos)

@app.route('/orcamentos/<int:id>/editar', methods=['GET', 'POST'])
def editar_orcamento(id):
    orcamento = db.get_orcamento(id)
    if request.method == 'POST':
        itens = json.loads(request.form.get('itens_json', '[]'))
        db.atualizar_orcamento(id, request.form, itens)
        flash('Orçamento atualizado!', 'success')
        return redirect(url_for('ver_orcamento', id=id))
    clientes = db.get_clientes()
    produtos = db.get_produtos()
    return render_template('orcamentos/form.html', orcamento=orcamento, clientes=clientes, produtos=produtos)

@app.route('/orcamentos/<int:id>')
def ver_orcamento(id):
    orcamento = db.get_orcamento(id)
    return render_template('orcamentos/detalhe.html', orcamento=orcamento)

@app.route('/orcamentos/<int:id>/imprimir')
def imprimir_orcamento(id):
    orcamento = db.get_orcamento(id)
    return render_template('orcamentos/imprimir.html', orcamento=orcamento)

@app.route('/orcamentos/<int:id>/converter', methods=['POST'])
def converter_orcamento(id):
    pedido_id = db.converter_orcamento_pedido(id)
    flash(f'Orçamento convertido! Pedido #{pedido_id} criado.', 'success')
    return redirect(url_for('ver_pedido', id=pedido_id))

@app.route('/orcamentos/<int:id>/excluir', methods=['POST'])
def excluir_orcamento(id):
    db.excluir_orcamento(id)
    flash('Orçamento removido.', 'info')
    return redirect(url_for('orcamentos'))

# ─── PRECIFICAÇÃO ────────────────────────────────────────────────────────────

@app.route('/precificacao')
def precificacao():
    calculos = db.prec_get_calculos()
    return render_template('precificacao/index.html', calculos=calculos)

@app.route('/precificacao/configuracoes', methods=['GET', 'POST'])
def prec_configuracoes():
    if request.method == 'POST':
        db.prec_set_config('mo_taxa_min', request.form.get('mo_taxa_min', '1.67'))
        db.prec_set_config('overhead_pct', request.form.get('overhead_pct', '0'))
        db.prec_set_config('invest_venda_pct', request.form.get('invest_venda_pct', '0'))
        db.prec_set_config('acrilico_corte_peca', request.form.get('acrilico_corte_peca', '0'))
        db.prec_set_config('apostila_capa_plastico_custo', request.form.get('apostila_capa_plastico_custo', '0'))
        ates   = request.form.getlist('espiral_faixa_ate[]')
        custos = request.form.getlist('espiral_faixa_custo[]')
        faixas = []
        for a, c in zip(ates, custos):
            try:
                faixas.append({'ate': int(a), 'custo': float(c)})
            except (ValueError, TypeError):
                pass
        faixas.sort(key=lambda x: x['ate'])
        db.prec_set_config('apostila_espiral_faixas', json.dumps(faixas))
        flash('Configurações salvas!', 'success')
        return redirect(url_for('prec_configuracoes'))
    papeis = db.prec_get_papeis()
    maquinas = db.prec_get_maquinas()
    acabamentos = db.prec_get_acabamentos_papel()
    acabamentos_uv = db.prec_get_acabamentos_uv_eco()
    papelao = db.prec_get_papelao()
    midias_bobina = db.prec_get_midias_bobina()
    acrilicos = db.prec_get_acrilicos()
    mo_taxa = db.prec_get_config('mo_taxa_min', '1.67')
    overhead_pct = db.prec_get_config('overhead_pct', '0')
    invest_venda_pct = db.prec_get_config('invest_venda_pct', '0')
    acrilico_corte_peca = db.prec_get_config('acrilico_corte_peca', '0')
    apostila_capa_plastico_custo = db.prec_get_config('apostila_capa_plastico_custo', '0')
    _faixas_raw = db.prec_get_config('apostila_espiral_faixas', '[]')
    try:
        apostila_espiral_faixas = json.loads(_faixas_raw) or []
    except Exception:
        apostila_espiral_faixas = []
    if not apostila_espiral_faixas:
        apostila_espiral_faixas = [{'ate': 50, 'custo': 0}, {'ate': 100, 'custo': 0}]
    maquinas_corte = db.prec_get_maquinas_corte()
    return render_template('precificacao/configuracoes.html',
                           papeis=papeis, maquinas=maquinas,
                           acabamentos=acabamentos, acabamentos_uv=acabamentos_uv,
                           papelao=papelao, midias_bobina=midias_bobina,
                           acrilicos=acrilicos, maquinas_corte=maquinas_corte,
                           mo_taxa=mo_taxa, overhead_pct=overhead_pct,
                           invest_venda_pct=invest_venda_pct,
                           acrilico_corte_peca=acrilico_corte_peca,
                           apostila_capa_plastico_custo=apostila_capa_plastico_custo,
                           apostila_espiral_faixas=apostila_espiral_faixas)

@app.route('/precificacao/acrilico/novo', methods=['POST'])
def prec_novo_acrilico():
    db.prec_salvar_acrilico(request.form)
    flash('Chapa de acrílico cadastrada!', 'success')
    return redirect(url_for('prec_configuracoes') + '#acrilicos')

@app.route('/precificacao/acrilico/<int:id>/editar', methods=['POST'])
def prec_editar_acrilico(id):
    db.prec_salvar_acrilico(request.form, id)
    flash('Chapa atualizada!', 'success')
    return redirect(url_for('prec_configuracoes') + '#acrilicos')

@app.route('/precificacao/acrilico/<int:id>/excluir', methods=['POST'])
def prec_excluir_acrilico(id):
    db.prec_excluir_acrilico(id)
    return redirect(url_for('prec_configuracoes') + '#acrilicos')

@app.route('/precificacao/maquina-corte/nova', methods=['POST'])
def prec_nova_maquina_corte():
    db.prec_salvar_maquina_corte(request.form)
    flash('Equipamento de corte cadastrado!', 'success')
    return redirect(url_for('prec_configuracoes') + '#acrilicos')

@app.route('/precificacao/maquina-corte/<int:id>/editar', methods=['POST'])
def prec_editar_maquina_corte(id):
    db.prec_salvar_maquina_corte(request.form, id)
    flash('Equipamento atualizado!', 'success')
    return redirect(url_for('prec_configuracoes') + '#acrilicos')

@app.route('/precificacao/maquina-corte/<int:id>/excluir', methods=['POST'])
def prec_excluir_maquina_corte(id):
    db.prec_excluir_maquina_corte(id)
    return redirect(url_for('prec_configuracoes') + '#acrilicos')

@app.route('/precificacao/papel/novo', methods=['POST'])
def prec_novo_papel():
    db.prec_salvar_papel(request.form)
    flash('Papel cadastrado!', 'success')
    return redirect(url_for('prec_configuracoes') + '#papeis')

@app.route('/precificacao/papel/<int:id>/editar', methods=['POST'])
def prec_editar_papel(id):
    db.prec_salvar_papel(request.form, id)
    flash('Papel atualizado!', 'success')
    return redirect(url_for('prec_configuracoes') + '#papeis')

@app.route('/precificacao/papel/<int:id>/excluir', methods=['POST'])
def prec_excluir_papel(id):
    db.prec_excluir_papel(id)
    return redirect(url_for('prec_configuracoes') + '#papeis')

@app.route('/precificacao/midia-bobina/nova', methods=['POST'])
def prec_nova_midia_bobina():
    db.prec_salvar_midia_bobina(request.form)
    flash('Mídia cadastrada!', 'success')
    return redirect(url_for('prec_configuracoes') + '#midias')

@app.route('/precificacao/midia-bobina/<int:id>/editar', methods=['POST'])
def prec_editar_midia_bobina(id):
    db.prec_salvar_midia_bobina(request.form, id)
    flash('Mídia atualizada!', 'success')
    return redirect(url_for('prec_configuracoes') + '#midias')

@app.route('/precificacao/midia-bobina/<int:id>/excluir', methods=['POST'])
def prec_excluir_midia_bobina(id):
    db.prec_excluir_midia_bobina(id)
    return redirect(url_for('prec_configuracoes') + '#midias')

@app.route('/precificacao/maquina/nova', methods=['POST'])
def prec_nova_maquina():
    db.prec_salvar_maquina(request.form)
    flash('Máquina cadastrada!', 'success')
    return redirect(url_for('prec_configuracoes') + '#maquinas')

@app.route('/precificacao/maquina/<int:id>/editar', methods=['POST'])
def prec_editar_maquina(id):
    db.prec_salvar_maquina(request.form, id)
    flash('Máquina atualizada!', 'success')
    return redirect(url_for('prec_configuracoes') + '#maquinas')

@app.route('/precificacao/maquina/<int:id>/excluir', methods=['POST'])
def prec_excluir_maquina(id):
    db.prec_excluir_maquina(id)
    return redirect(url_for('prec_configuracoes') + '#maquinas')

@app.route('/precificacao/acabamento/novo', methods=['POST'])
def prec_novo_acabamento():
    db.prec_salvar_acabamento(request.form)
    flash('Acabamento cadastrado!', 'success')
    return redirect(url_for('prec_configuracoes') + '#acabamentos')

@app.route('/precificacao/acabamento/<int:id>/editar', methods=['POST'])
def prec_editar_acabamento(id):
    db.prec_salvar_acabamento(request.form, id)
    flash('Acabamento atualizado!', 'success')
    return redirect(url_for('prec_configuracoes') + '#acabamentos')

@app.route('/precificacao/acabamento/<int:id>/excluir', methods=['POST'])
def prec_excluir_acabamento(id):
    db.prec_excluir_acabamento(id)
    return redirect(url_for('prec_configuracoes') + '#acabamentos')

@app.route('/precificacao/acabamento-uv/novo', methods=['POST'])
def prec_novo_acabamento_uv():
    db.prec_salvar_acabamento(request.form)
    flash('Acabamento UV/Eco cadastrado!', 'success')
    return redirect(url_for('prec_configuracoes') + '#acabamentos-uv')

@app.route('/precificacao/acabamento-uv/<int:id>/editar', methods=['POST'])
def prec_editar_acabamento_uv(id):
    db.prec_salvar_acabamento(request.form, id)
    flash('Acabamento UV/Eco atualizado!', 'success')
    return redirect(url_for('prec_configuracoes') + '#acabamentos-uv')

@app.route('/precificacao/acabamento-uv/<int:id>/excluir', methods=['POST'])
def prec_excluir_acabamento_uv(id):
    db.prec_excluir_acabamento(id)
    return redirect(url_for('prec_configuracoes') + '#acabamentos-uv')

@app.route('/precificacao/papelao/novo', methods=['POST'])
def prec_novo_papelao():
    db.prec_salvar_papelao(request.form)
    flash('Papelão cadastrado!', 'success')
    return redirect(url_for('prec_configuracoes') + '#papelao')

@app.route('/precificacao/papelao/<int:id>/editar', methods=['POST'])
def prec_editar_papelao(id):
    db.prec_salvar_papelao(request.form, id)
    flash('Papelão atualizado!', 'success')
    return redirect(url_for('prec_configuracoes') + '#papelao')

@app.route('/precificacao/papelao/<int:id>/excluir', methods=['POST'])
def prec_excluir_papelao(id):
    db.prec_excluir_papelao(id)
    return redirect(url_for('prec_configuracoes') + '#papelao')

@app.route('/precificacao/papelao-tamanho/novo', methods=['POST'])
def prec_novo_tamanho_papelao():
    db.prec_salvar_tamanho_papelao(request.form)
    return redirect(url_for('prec_configuracoes') + '#papelao')

@app.route('/precificacao/papelao-tamanho/<int:id>/excluir', methods=['POST'])
def prec_excluir_tamanho_papelao(id):
    db.prec_excluir_tamanho_papelao(id)
    return redirect(url_for('prec_configuracoes') + '#papelao')

@app.route('/precificacao/api/papeis')
def api_prec_papeis():
    return jsonify(db.prec_get_papeis())

@app.route('/precificacao/api/maquinas')
def api_prec_maquinas():
    return jsonify(db.prec_get_maquinas())

@app.route('/precificacao/api/acabamentos')
def api_prec_acabamentos():
    return jsonify(db.prec_get_acabamentos())

@app.route('/precificacao/calcular')
def prec_calcular():
    papeis = db.prec_get_papeis()
    maquinas = db.prec_get_maquinas()
    acabamentos = db.prec_get_acabamentos_papel()
    acabamentos_uv = db.prec_get_acabamentos_uv_eco()
    papelao = db.prec_get_papelao()
    midias_bobina = db.prec_get_midias_bobina()
    acrilicos = db.prec_get_acrilicos()
    mo_taxa = db.prec_get_config('mo_taxa_min', '1.67')
    overhead_pct = db.prec_get_config('overhead_pct', '0')
    invest_venda_pct = db.prec_get_config('invest_venda_pct', '0')
    acrilico_corte_peca = db.prec_get_config('acrilico_corte_peca', '0')
    apostila_capa_plastico_custo = db.prec_get_config('apostila_capa_plastico_custo', '0')
    _faixas_raw2 = db.prec_get_config('apostila_espiral_faixas', '[]')
    try:
        apostila_espiral_faixas = json.loads(_faixas_raw2) or []
    except Exception:
        apostila_espiral_faixas = []
    maquinas_corte = db.prec_get_maquinas_corte()
    return render_template('precificacao/calculadora.html',
                           papeis=papeis, maquinas=maquinas,
                           acabamentos=acabamentos, acabamentos_uv=acabamentos_uv,
                           papelao=papelao, midias_bobina=midias_bobina,
                           acrilicos=acrilicos, maquinas_corte=maquinas_corte,
                           acrilico_corte_peca=acrilico_corte_peca,
                           apostila_capa_plastico_custo=apostila_capa_plastico_custo,
                           apostila_espiral_faixas=apostila_espiral_faixas,
                           mo_taxa=mo_taxa, overhead_pct=overhead_pct,
                           invest_venda_pct=invest_venda_pct)

@app.route('/precificacao/salvar', methods=['POST'])
def prec_salvar():
    dados = request.json
    id = db.prec_salvar_calculo(dados)
    return jsonify({'ok': True, 'id': id})

@app.route('/precificacao/salvar_produto', methods=['POST'])
def prec_salvar_produto():
    dados = request.json
    produto_id = db.prec_criar_produto_da_calc(dados)
    return jsonify({'ok': True, 'id': produto_id})

@app.route('/precificacao/ficha')
def prec_ficha():
    import json as _json
    from datetime import datetime
    raw = request.args.get('dados', '{}')
    try:
        dados = _json.loads(raw)
    except Exception:
        dados = {}
    now = datetime.now().strftime('%d/%m/%Y %H:%M')
    return render_template('precificacao/ficha.html', dados=dados, now=now)

@app.route('/precificacao/<int:id>')
def prec_ver_calculo(id):
    calculo = db.prec_get_calculo(id)
    return render_template('precificacao/resultado.html', calculo=calculo)

@app.route('/precificacao/<int:id>/ficha')
def prec_ficha_salvo(id):
    import json as _json
    from datetime import datetime
    calculo = db.prec_get_calculo(id)
    if not calculo:
        return 'Cálculo não encontrado', 404
    dados = calculo.get('dados', {})
    now = datetime.now().strftime('%d/%m/%Y %H:%M')
    return render_template('precificacao/ficha.html', dados=dados, now=now)

# ─── PONTO DE EQUILÍBRIO ──────────────────────────────────────────────────────

@app.route('/precificacao/ponto-equilibrio')
def pec_index():
    custos = db.pec_get_custos()
    total  = sum(c['valor'] for c in custos)
    overhead_pct    = float(db.prec_get_config('overhead_pct', 0))
    invest_venda_pct = float(db.prec_get_config('invest_venda_pct', 0))
    markup_padrao   = float(db.prec_get_config('markup_padrao', 2.5))
    categorias      = db.PEC_CATEGORIAS
    return render_template('precificacao/ponto_equilibrio.html',
        custos=custos, total=total,
        overhead_pct=overhead_pct, invest_venda_pct=invest_venda_pct,
        markup_padrao=markup_padrao, categorias=categorias)

@app.route('/precificacao/custo-fixo/novo', methods=['POST'])
def pec_novo_custo():
    db.pec_salvar_custo(request.form)
    if request.form.get('_from_custos'):
        return redirect(url_for('custos') + '#fixos')
    return redirect(url_for('pec_index'))

@app.route('/precificacao/custo-fixo/<int:id>/editar', methods=['POST'])
def pec_editar_custo(id):
    db.pec_salvar_custo(request.form, id=id)
    if request.form.get('_from_custos'):
        return redirect(url_for('custos') + '#fixos')
    return redirect(url_for('pec_index'))

@app.route('/precificacao/custo-fixo/<int:id>/excluir', methods=['POST'])
def pec_excluir_custo(id):
    db.pec_excluir_custo(id)
    if request.form.get('_from_custos'):
        return redirect(url_for('custos') + '#fixos')
    return redirect(url_for('pec_index'))

# ─── NF-e IMPORTAÇÃO ──────────────────────────────────────────────────────────

@app.route('/nfe/importar')
def nfe_importar():
    historico = db.nfe_get_historico()
    return render_template('nfe/importar.html', historico=historico, nfe=None, insumos=None)

@app.route('/nfe/importar/upload', methods=['POST'])
def nfe_upload():
    f = request.files.get('xml_file')
    if not f or not f.filename.lower().endswith('.xml'):
        flash('Envie um arquivo .xml de NF-e.', 'danger')
        return redirect(url_for('nfe_importar'))
    try:
        dados = db.nfe_parse_xml(f.read())
    except Exception as e:
        flash(f'Erro ao ler o XML: {e}', 'danger')
        return redirect(url_for('nfe_importar'))
    insumos = db.nfe_get_todos_insumos()
    for item in dados['itens']:
        item['mapeamento'] = db.nfe_get_mapeamento(dados['cnpj'], item['codigo'])
    historico = db.nfe_get_historico()
    return render_template('nfe/importar.html', historico=historico, nfe=dados, insumos=insumos)

@app.route('/nfe/importar/confirmar', methods=['POST'])
def nfe_confirmar():
    form = request.form
    n = int(form.get('n_itens', 0))
    header = {
        'cnpj':         form.get('cnpj', ''),
        'nome':         form.get('nome_emitente', ''),
        'numero_nf':    form.get('numero_nf', ''),
        'data_emissao': form.get('data_emissao', ''),
        'valor_total':  float(form.get('valor_total', 0) or 0),
    }
    itens_mapeados = []
    for i in range(n):
        acao = form.get(f'acao_{i}', 'ignorar')
        if acao == 'ignorar':
            continue
        tipo       = form.get(f'tipo_{i}', '')
        codigo     = form.get(f'codigo_{i}', '')
        descricao  = form.get(f'descricao_{i}', '')
        quantidade = float(form.get(f'quantidade_{i}', 0) or 0)
        unidade    = form.get(f'unidade_{i}', 'UN')
        valor_unit = float(form.get(f'valor_unit_{i}', 0) or 0)
        if acao == 'criar_novo':
            nome_novo  = (form.get(f'novo_nome_{i}', '') or descricao).strip()
            insumo_id  = db.nfe_criar_insumo(tipo, nome_novo, valor_unit)
        else:
            insumo_id = int(form.get(f'insumo_id_{i}', 0) or 0)
        if not tipo or not insumo_id:
            continue
        itens_mapeados.append({
            'codigo': codigo, 'descricao': descricao,
            'quantidade': quantidade, 'unidade': unidade,
            'valor_unit': valor_unit, 'insumo_tipo': tipo, 'insumo_id': insumo_id,
        })
    if not itens_mapeados:
        flash('Nenhum item foi vinculado. Vincule ao menos um item antes de confirmar.', 'danger')
        return redirect(url_for('nfe_importar'))
    db.nfe_importar(header, itens_mapeados)
    flash(f'NF-e importada! {len(itens_mapeados)} insumo(s) com custo e estoque atualizados.', 'success')
    return redirect(url_for('nfe_importar'))

# ─── PRODUÇÃO ─────────────────────────────────────────────────────────────────

@app.route('/producao')
def producao():
    fila = db.get_fila_producao()
    return render_template('producao/fila.html', fila=fila)

@app.route('/producao/<int:id>/status', methods=['POST'])
def atualizar_status_producao(id):
    db.atualizar_status_producao(id, request.json.get('status'))
    return jsonify({'ok': True})

# ─── FINANCEIRO ──────────────────────────────────────────────────────────────

@app.route('/financeiro')
def financeiro():
    resumo = db.get_resumo_financeiro()
    return render_template('financeiro/resumo.html', resumo=resumo)

@app.route('/financeiro/caixa')
def caixa():
    caixa_atual = db.get_caixa_atual()
    lancamentos = db.get_lancamentos_caixa(caixa_atual['id'] if caixa_atual else None)
    historico = db.get_historico_caixas()
    return render_template('financeiro/caixa.html', caixa=caixa_atual, lancamentos=lancamentos, historico=historico)

@app.route('/financeiro/caixa/abrir', methods=['POST'])
def abrir_caixa():
    db.abrir_caixa(request.form)
    flash('Caixa aberto!', 'success')
    return redirect(url_for('caixa'))

@app.route('/financeiro/caixa/fechar', methods=['POST'])
def fechar_caixa():
    db.fechar_caixa(request.form.get('caixa_id'))
    flash('Caixa fechado!', 'success')
    return redirect(url_for('caixa'))

@app.route('/financeiro/caixa/lancamento', methods=['POST'])
def novo_lancamento():
    db.criar_lancamento(request.form)
    return redirect(url_for('caixa'))

@app.route('/financeiro/caixa/lancamento/<int:id>/excluir', methods=['POST'])
def excluir_lancamento(id):
    db.excluir_lancamento(id)
    return redirect(url_for('caixa'))

@app.route('/financeiro/fornecedores')
def fornecedores():
    busca = request.args.get('q')
    lista = db.get_fornecedores(busca)
    return render_template('financeiro/fornecedores.html', fornecedores=lista, busca=busca)

@app.route('/financeiro/fornecedores/novo', methods=['GET', 'POST'])
def novo_fornecedor():
    if request.method == 'POST':
        db.criar_fornecedor(request.form)
        flash('Fornecedor cadastrado!', 'success')
        return redirect(url_for('fornecedores'))
    return render_template('financeiro/form_fornecedor.html', fornecedor=None)

@app.route('/financeiro/fornecedores/<int:id>/editar', methods=['GET', 'POST'])
def editar_fornecedor(id):
    fornecedor = db.get_fornecedor(id)
    if request.method == 'POST':
        db.atualizar_fornecedor(id, request.form)
        flash('Fornecedor atualizado!', 'success')
        return redirect(url_for('fornecedores'))
    return render_template('financeiro/form_fornecedor.html', fornecedor=fornecedor)

@app.route('/financeiro/fornecedores/<int:id>/excluir', methods=['POST'])
def excluir_fornecedor(id):
    db.excluir_fornecedor(id)
    flash('Fornecedor removido.', 'info')
    return redirect(url_for('fornecedores'))

# ─── CENTRAL DE CUSTOS ───────────────────────────────────────────────────────

@app.route('/custos')
def custos():
    from datetime import date
    hoje = date.today()
    mes  = int(request.args.get('mes',  hoje.month))
    ano  = int(request.args.get('ano',  hoje.year))
    cat  = request.args.get('cat', '')
    lista      = db.get_despesas(mes, ano, cat or None)
    resumo     = db.get_resumo_despesas(mes, ano)
    custos_fixos = db.pec_get_custos()
    total_fixos  = sum(c['valor'] for c in custos_fixos)
    return render_template('custos/index.html',
        despesas=lista, resumo=resumo,
        mes=mes, ano=ano, cat=cat,
        categorias=db.DESPESA_CATEGORIAS,
        formas=db.FORMAS_PAGAMENTO,
        custos_fixos=custos_fixos,
        pec_categorias=db.PEC_CATEGORIAS,
        total_fixos=total_fixos,
    )

@app.route('/custos/novo', methods=['POST'])
def nova_despesa():
    db.salvar_despesa(request.form)
    flash('Despesa registrada!', 'success')
    mes = request.form.get('mes_filtro', '')
    ano = request.form.get('ano_filtro', '')
    return redirect(url_for('custos', mes=mes, ano=ano))

@app.route('/custos/<int:id>/editar', methods=['POST'])
def editar_despesa(id):
    db.salvar_despesa(request.form, id=id)
    flash('Despesa atualizada!', 'success')
    mes = request.form.get('mes_filtro', '')
    ano = request.form.get('ano_filtro', '')
    return redirect(url_for('custos', mes=mes, ano=ano))

@app.route('/custos/<int:id>/excluir', methods=['POST'])
def excluir_despesa(id):
    db.excluir_despesa(id)
    flash('Despesa removida.', 'info')
    mes = request.form.get('mes_filtro', '')
    ano = request.form.get('ano_filtro', '')
    return redirect(url_for('custos', mes=mes, ano=ano))

@app.route('/custos/contas')
def contas_pagar():
    from datetime import date
    hoje = date.today()
    mes    = int(request.args.get('mes', hoje.month))
    ano    = int(request.args.get('ano', hoje.year))
    status = request.args.get('status', '')
    contas       = db.get_contas_pagar(status or None, mes, ano)
    resumo       = db.get_resumo_contas(mes, ano)
    fornecedores = db.get_fornecedores()
    return render_template('custos/contas.html',
        contas=contas, resumo=resumo,
        mes=mes, ano=ano, status=status,
        formas=db.FORMAS_PAGAMENTO,
        hoje=hoje.isoformat(),
        fornecedores=fornecedores,
    )

@app.route('/custos/contas/nova', methods=['POST'])
def nova_conta_pagar():
    db.salvar_conta_pagar(request.form)
    flash('Conta cadastrada!', 'success')
    return redirect(url_for('contas_pagar',
        mes=request.form.get('mes_filtro'),
        ano=request.form.get('ano_filtro')))

@app.route('/custos/contas/<int:id>/editar', methods=['POST'])
def editar_conta_pagar(id):
    db.salvar_conta_pagar(request.form, id=id)
    flash('Conta atualizada!', 'success')
    return redirect(url_for('contas_pagar',
        mes=request.form.get('mes_filtro'),
        ano=request.form.get('ano_filtro')))

@app.route('/custos/contas/<int:id>/pagar', methods=['POST'])
def pagar_conta(id):
    from datetime import date
    data_pgto = request.form.get('data_pagamento') or date.today().isoformat()
    db.pagar_conta(id, data_pgto)
    return redirect(url_for('contas_pagar',
        mes=request.form.get('mes_filtro'),
        ano=request.form.get('ano_filtro')))

@app.route('/custos/contas/<int:id>/estornar', methods=['POST'])
def estornar_conta(id):
    db.estornar_conta(id)
    return redirect(url_for('contas_pagar',
        mes=request.form.get('mes_filtro'),
        ano=request.form.get('ano_filtro')))

@app.route('/custos/contas/<int:id>/excluir', methods=['POST'])
def excluir_conta_pagar(id):
    db.excluir_conta_pagar(id)
    flash('Conta removida.', 'info')
    return redirect(url_for('contas_pagar',
        mes=request.form.get('mes_filtro'),
        ano=request.form.get('ano_filtro')))

# ─── NOTAS FISCAIS ───────────────────────────────────────────────────────────

@app.route('/notasfiscais')
def notasfiscais():
    notas = db.get_notasfiscais()
    return render_template('notasfiscais/lista.html', notas=notas)

@app.route('/notasfiscais/emitir', methods=['GET', 'POST'])
def emitir_nf():
    if request.method == 'POST':
        numero = db.criar_nf(request.form)
        flash(f'NF {numero} emitida com sucesso!', 'success')
        return redirect(url_for('notasfiscais'))
    pedidos = db.get_pedidos_sem_nf()
    clientes = db.get_clientes()
    return render_template('notasfiscais/emissao.html', pedidos=pedidos, clientes=clientes)

@app.route('/notasfiscais/<int:id>/excluir', methods=['POST'])
def excluir_nf(id):
    db.excluir_nf(id)
    flash('NF removida.', 'info')
    return redirect(url_for('notasfiscais'))

if __name__ == '__main__':
    db.init_db()
    debug_mode = os.environ.get('IMPRESSA_DEBUG', 'true').lower() == 'true'
    print("\nSistema rodando em: http://localhost:5001")
    print("Pressione Ctrl+C para parar\n")
    app.run(debug=debug_mode, port=5001)
