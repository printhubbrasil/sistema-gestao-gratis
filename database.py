import os
import sqlite3
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH = os.environ.get('DATABASE_PATH', 'grafica.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()

    c.executescript('''
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT,
            telefone TEXT,
            cpf_cnpj TEXT,
            endereco TEXT,
            cidade TEXT,
            estado TEXT,
            cep TEXT,
            observacoes TEXT,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS categorias_produto (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            imagem TEXT,
            prazo_producao TEXT,
            selo_destaque TEXT DEFAULT 'Nenhum',
            sku TEXT,
            mpn TEXT,
            gtin_ean TEXT,
            como_despachado TEXT DEFAULT 'Todos',
            quem_pode_comprar TEXT DEFAULT 'Todos',
            visivel_painel INTEGER DEFAULT 1,
            visivel_loja INTEGER DEFAULT 1,
            visivel_geral INTEGER DEFAULT 0,
            visivel_orcamento INTEGER DEFAULT 0,
            espec_formato TEXT,
            espec_material TEXT,
            espec_revestimento TEXT,
            espec_acabamento TEXT,
            espec_cores TEXT,
            espec_extras TEXT,
            precisa_arte TEXT DEFAULT 'Não precisa de arte',
            valor_arte REAL DEFAULT 0,
            url_video TEXT,
            descricao_curta TEXT,
            descricao TEXT,
            tipo_preco TEXT DEFAULT 'quantidade',
            desconto_revendedor_tipo TEXT DEFAULT '%',
            desconto_revendedor_valor REAL DEFAULT 0,
            ncm TEXT,
            cfop TEXT,
            cest TEXT,
            icms_origem TEXT DEFAULT '0',
            icms_cst TEXT DEFAULT '00',
            icms_aliquota REAL DEFAULT 0,
            ipi_cst TEXT DEFAULT '00',
            ipi_aliquota REAL DEFAULT 0,
            pis_cst TEXT DEFAULT '01',
            pis_aliquota REAL DEFAULT 0,
            cofins_cst TEXT DEFAULT '01',
            cofins_aliquota REAL DEFAULT 0,
            unidade TEXT DEFAULT 'UN',
            preco REAL DEFAULT 0,
            ativo INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS produto_precos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            produto_id INTEGER REFERENCES produtos(id) ON DELETE CASCADE,
            quantidade REAL,
            qtd_min REAL,
            qtd_max REAL,
            preco_anterior REAL DEFAULT 0,
            preco_venda REAL DEFAULT 0,
            preco_custo REAL DEFAULT 0,
            peso REAL DEFAULT 0,
            largura REAL DEFAULT 0,
            altura REAL DEFAULT 0,
            comprimento REAL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS produto_variacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            produto_id INTEGER REFERENCES produtos(id) ON DELETE CASCADE,
            variacao_tipo TEXT,
            nome TEXT,
            preco_venda REAL DEFAULT 0,
            custo REAL DEFAULT 0,
            forma_cobranca TEXT DEFAULT 'Unidade'
        );

        CREATE TABLE IF NOT EXISTS produto_categorias (
            produto_id INTEGER REFERENCES produtos(id) ON DELETE CASCADE,
            categoria_nome TEXT,
            PRIMARY KEY (produto_id, categoria_nome)
        );

        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER REFERENCES clientes(id),
            status TEXT DEFAULT 'aguardando',
            status_producao TEXT DEFAULT 'aguardando',
            total REAL DEFAULT 0,
            desconto REAL DEFAULT 0,
            observacoes TEXT,
            prazo TEXT,
            forma_pagamento TEXT,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS pedido_itens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pedido_id INTEGER REFERENCES pedidos(id) ON DELETE CASCADE,
            produto_id INTEGER REFERENCES produtos(id),
            descricao TEXT,
            quantidade REAL DEFAULT 1,
            preco_unitario REAL DEFAULT 0,
            subtotal REAL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS caixas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_abertura TEXT,
            valor_abertura REAL DEFAULT 0,
            data_fechamento TEXT,
            valor_fechamento REAL,
            status TEXT DEFAULT 'aberto',
            observacoes TEXT
        );

        CREATE TABLE IF NOT EXISTS lancamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            caixa_id INTEGER REFERENCES caixas(id),
            tipo TEXT NOT NULL,
            categoria TEXT,
            descricao TEXT NOT NULL,
            valor REAL NOT NULL,
            pedido_id INTEGER,
            data TEXT DEFAULT (date('now','localtime')),
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS fornecedores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            contato TEXT,
            telefone TEXT,
            email TEXT,
            cnpj TEXT,
            produto_servico TEXT,
            observacoes TEXT,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS notasfiscais (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero TEXT,
            pedido_id INTEGER,
            cliente_id INTEGER REFERENCES clientes(id),
            cliente_nome TEXT,
            cliente_cpf_cnpj TEXT,
            valor_total REAL,
            descricao_servico TEXT,
            data_emissao TEXT DEFAULT (date('now','localtime')),
            status TEXT DEFAULT 'emitida',
            observacoes TEXT,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );

        -- ── PRECIFICAÇÃO ────────────────────────────────────────────────────

        CREATE TABLE IF NOT EXISTS prec_papeis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            largura REAL NOT NULL,
            altura REAL NOT NULL,
            folhas_resma INTEGER DEFAULT 500,
            custo_resma REAL DEFAULT 0,
            fator_perda REAL DEFAULT 5,
            ativo INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS prec_maquinas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            tipo TEXT NOT NULL DEFAULT 'click',
            boca_cm REAL DEFAULT 33,
            custo_click_toner REAL DEFAULT 0,
            custo_click_manutencao REAL DEFAULT 0,
            custo_click_depreciacao REAL DEFAULT 0,
            custo_m2_material REAL DEFAULT 0,
            custo_m2_impressao REAL DEFAULT 0,
            custo_m2_depreciacao REAL DEFAULT 0,
            ativo INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS prec_acabamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            tipo TEXT NOT NULL DEFAULT 'job',
            custo_base REAL DEFAULT 0,
            unidade TEXT DEFAULT 'job',
            markup REAL DEFAULT 1.0,
            bobina_largura REAL DEFAULT 0,
            bobina_comprimento REAL DEFAULT 0,
            bobina_custo REAL DEFAULT 0,
            ativo INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS prec_papelao (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            largura REAL DEFAULT 0,
            altura REAL DEFAULT 0,
            custo REAL DEFAULT 0,
            ativo INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS prec_papelao_tamanhos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            papelao_id INTEGER NOT NULL,
            nome TEXT NOT NULL,
            largura REAL DEFAULT 0,
            altura REAL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS prec_midias_bobina (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            custo_m2 REAL DEFAULT 0,
            ativo INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS prec_configuracoes (
            chave TEXT PRIMARY KEY,
            valor TEXT
        );

        CREATE TABLE IF NOT EXISTS prec_acrilicos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            largura_cm REAL DEFAULT 0,
            altura_cm REAL DEFAULT 0,
            espessura_mm REAL DEFAULT 3,
            cor TEXT DEFAULT 'Transparente',
            custo REAL DEFAULT 0,
            ativo INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );
    ''')
    # Migração: tabela de equipamentos de corte
    try:
        conn.execute('''CREATE TABLE IF NOT EXISTS prec_maquinas_corte (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            custo_hora REAL DEFAULT 0,
            ativo INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        )''')
        conn.commit()
    except Exception:
        pass

    # Migração: garante tabela prec_acrilicos em bancos já existentes
    try:
        conn.execute('''CREATE TABLE IF NOT EXISTS prec_acrilicos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            largura_cm REAL DEFAULT 0,
            altura_cm REAL DEFAULT 0,
            espessura_mm REAL DEFAULT 3,
            cor TEXT DEFAULT 'Transparente',
            custo REAL DEFAULT 0,
            ativo INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        )''')
        conn.commit()
    except Exception:
        pass

    # Migração: Contas a Pagar
    try:
        conn.execute('''CREATE TABLE IF NOT EXISTS contas_pagar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descricao TEXT NOT NULL,
            fornecedor TEXT,
            valor REAL DEFAULT 0,
            vencimento TEXT NOT NULL,
            pago_em TEXT,
            forma_pagamento TEXT DEFAULT 'boleto',
            observacao TEXT,
            ativo INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        )''')
        conn.commit()
    except Exception:
        pass

    # Migração: Central de Custos — despesas reais datadas
    try:
        conn.execute('''CREATE TABLE IF NOT EXISTS despesas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT NOT NULL,
            descricao TEXT NOT NULL,
            categoria TEXT NOT NULL DEFAULT 'outros',
            valor REAL DEFAULT 0,
            forma_pagamento TEXT DEFAULT 'dinheiro',
            recorrente INTEGER DEFAULT 0,
            observacao TEXT,
            ativo INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        )''')
        conn.commit()
    except Exception:
        pass
    c.executescript('''PRAGMA user_version=1; -- placeholder''')
    c.executescript('''

        CREATE TABLE IF NOT EXISTS pec_custos_fixos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            categoria TEXT NOT NULL DEFAULT 'outros',
            valor REAL DEFAULT 0,
            observacao TEXT,
            ativo INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS prec_calculos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            tipo_produto TEXT,
            quantidade INTEGER,
            custo_total REAL DEFAULT 0,
            markup REAL DEFAULT 2.5,
            preco_venda REAL DEFAULT 0,
            dados_json TEXT,
            status TEXT DEFAULT 'rascunho',
            orcamento_id INTEGER,
            produto_id INTEGER,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS orcamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero TEXT,
            cliente_id INTEGER REFERENCES clientes(id),
            status TEXT DEFAULT 'rascunho',
            total REAL DEFAULT 0,
            desconto REAL DEFAULT 0,
            validade TEXT,
            forma_pagamento TEXT,
            condicoes TEXT,
            observacoes TEXT,
            pedido_id INTEGER,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS orcamento_itens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            orcamento_id INTEGER REFERENCES orcamentos(id) ON DELETE CASCADE,
            produto_id INTEGER REFERENCES produtos(id),
            descricao TEXT,
            quantidade REAL DEFAULT 1,
            preco_unitario REAL DEFAULT 0,
            subtotal REAL DEFAULT 0
        );

        -- ── NF-e IMPORTAÇÃO ─────────────────────────────────────────────────
        CREATE TABLE IF NOT EXISTS nfe_importacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cnpj_emitente TEXT,
            nome_emitente TEXT,
            numero_nf TEXT,
            data_emissao TEXT,
            valor_total REAL DEFAULT 0,
            n_itens INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS nfe_mapeamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cnpj_emitente TEXT NOT NULL,
            codigo_produto TEXT NOT NULL,
            insumo_tipo TEXT NOT NULL,
            insumo_id INTEGER NOT NULL,
            UNIQUE(cnpj_emitente, codigo_produto)
        );

        CREATE TABLE IF NOT EXISTS estoque_insumos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            insumo_tipo TEXT NOT NULL,
            insumo_id INTEGER NOT NULL,
            qtd REAL DEFAULT 0,
            unidade TEXT DEFAULT 'un',
            updated_at TEXT DEFAULT (datetime('now','localtime')),
            UNIQUE(insumo_tipo, insumo_id)
        );

        -- ── AUTENTICAÇÃO ─────────────────────────────────────────────────────
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            login TEXT NOT NULL UNIQUE,
            senha_hash TEXT NOT NULL,
            nivel TEXT DEFAULT 'operador',
            ativo INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );
    ''')

    # Migrations
    try:
        c.execute("ALTER TABLE prec_acabamentos ADD COLUMN categoria TEXT DEFAULT 'papel'")
        conn.commit()
    except Exception:
        pass
    try:
        c.execute("ALTER TABLE prec_papeis ADD COLUMN tamanho_fixo INTEGER DEFAULT 0")
        conn.commit()
    except Exception:
        pass
    try:
        c.execute("ALTER TABLE prec_maquinas ADD COLUMN custo_click_pb REAL DEFAULT 0")
        conn.commit()
    except Exception:
        pass
    try:
        c.execute("ALTER TABLE prec_maquinas ADD COLUMN custo_click_cor REAL DEFAULT 0")
        conn.commit()
    except Exception:
        pass
    try:
        c.execute("ALTER TABLE prec_maquinas ADD COLUMN custo_m2_branco REAL DEFAULT 0")
        conn.commit()
    except Exception:
        pass
    try:
        c.execute("ALTER TABLE prec_maquinas ADD COLUMN custo_m2_verniz REAL DEFAULT 0")
        conn.commit()
    except Exception:
        pass
    try:
        c.execute("ALTER TABLE produto_precos ADD COLUMN qtd_min REAL")
        conn.commit()
    except Exception:
        pass
    try:
        c.execute("ALTER TABLE produto_precos ADD COLUMN qtd_max REAL")
        conn.commit()
    except Exception:
        pass
    try:
        c.execute("ALTER TABLE produtos ADD COLUMN imagem TEXT")
        conn.commit()
    except Exception:
        pass

    # Admin padrão
    c.execute("SELECT COUNT(*) FROM usuarios")
    if c.fetchone()[0] == 0:
        c.execute(
            "INSERT INTO usuarios (nome, login, senha_hash, nivel) VALUES (?, ?, ?, ?)",
            ('Administrador', 'admin', generate_password_hash('admin123', method='pbkdf2:sha256'), 'admin')
        )

    # Categorias padrão
    c.execute("SELECT COUNT(*) FROM categorias_produto")
    if c.fetchone()[0] == 0:
        categorias = ['Cartão de Visita', 'Flyer', 'Banner', 'Adesivo', 'Etiqueta', 'Camiseta', 'Caneca', 'UV Plano', 'Outros']
        for cat in categorias:
            c.execute("INSERT INTO categorias_produto (nome) VALUES (?)", (cat,))

    conn.commit()
    conn.close()

# ─── CLIENTES ───────────────────────────────────────────────────────────────

def get_clientes(busca=None):
    conn = get_db()
    if busca:
        rows = conn.execute(
            "SELECT * FROM clientes WHERE nome LIKE ? OR email LIKE ? OR telefone LIKE ? OR cpf_cnpj LIKE ? ORDER BY nome",
            (f'%{busca}%', f'%{busca}%', f'%{busca}%', f'%{busca}%')
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM clientes ORDER BY nome").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_cliente(id):
    conn = get_db()
    row = conn.execute("SELECT * FROM clientes WHERE id = ?", (id,)).fetchone()
    conn.close()
    return dict(row) if row else None

def criar_cliente(form):
    conn = get_db()
    cur = conn.execute('''INSERT INTO clientes (nome,email,telefone,cpf_cnpj,endereco,cidade,estado,cep,observacoes)
                    VALUES (?,?,?,?,?,?,?,?,?)''',
        (form.get('nome'), form.get('email'), form.get('telefone'), form.get('cpf_cnpj'),
         form.get('endereco'), form.get('cidade'), form.get('estado'), form.get('cep'), form.get('observacoes')))
    conn.commit()
    novo_id = cur.lastrowid
    conn.close()
    return novo_id

def atualizar_cliente(id, form):
    conn = get_db()
    conn.execute('''UPDATE clientes SET nome=?,email=?,telefone=?,cpf_cnpj=?,endereco=?,cidade=?,estado=?,cep=?,observacoes=?
                    WHERE id=?''',
        (form.get('nome'), form.get('email'), form.get('telefone'), form.get('cpf_cnpj'),
         form.get('endereco'), form.get('cidade'), form.get('estado'), form.get('cep'), form.get('observacoes'), id))
    conn.commit()
    conn.close()

def excluir_cliente(id):
    conn = get_db()
    conn.execute("DELETE FROM clientes WHERE id = ?", (id,))
    conn.commit()
    conn.close()

# ─── PRODUTOS ────────────────────────────────────────────────────────────────

def get_produtos(busca=None):
    conn = get_db()
    if busca:
        rows = conn.execute("SELECT * FROM produtos WHERE nome LIKE ? ORDER BY nome",
                           (f'%{busca}%',)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM produtos ORDER BY nome").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_produto(id):
    conn = get_db()
    row = conn.execute("SELECT * FROM produtos WHERE id = ?", (id,)).fetchone()
    if not row:
        conn.close()
        return None
    p = dict(row)
    p['precos'] = [dict(r) for r in conn.execute("SELECT * FROM produto_precos WHERE produto_id=? ORDER BY COALESCE(qtd_min, quantidade)", (id,)).fetchall()]
    p['variacoes'] = [dict(r) for r in conn.execute("SELECT * FROM produto_variacoes WHERE produto_id=? ORDER BY id", (id,)).fetchall()]
    p['categorias'] = [r[0] for r in conn.execute("SELECT categoria_nome FROM produto_categorias WHERE produto_id=?", (id,)).fetchall()]
    conn.close()
    return p

def get_categorias():
    conn = get_db()
    rows = conn.execute("SELECT * FROM categorias_produto ORDER BY nome").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def _salvar_produto_dados(conn, produto_id, form, precos_json, variacoes_json, categorias_lista):
    import json
    conn.execute("DELETE FROM produto_precos WHERE produto_id=?", (produto_id,))
    for p in (precos_json or []):
        conn.execute('''INSERT INTO produto_precos (produto_id,quantidade,qtd_min,qtd_max,preco_anterior,preco_venda,preco_custo,peso,largura,altura,comprimento)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?)''',
            (produto_id, p.get('quantidade'), p.get('qtd_min'), p.get('qtd_max'),
             p.get('preco_anterior'), p.get('preco_venda'),
             p.get('preco_custo'), p.get('peso'), p.get('largura'), p.get('altura'), p.get('comprimento')))

    conn.execute("DELETE FROM produto_variacoes WHERE produto_id=?", (produto_id,))
    for v in (variacoes_json or []):
        if v.get('nome'):
            conn.execute('''INSERT INTO produto_variacoes (produto_id,variacao_tipo,nome,preco_venda,custo,forma_cobranca)
                            VALUES (?,?,?,?,?,?)''',
                (produto_id, v.get('variacao_tipo'), v.get('nome'),
                 float(v.get('preco_venda') or 0), float(v.get('custo') or 0), v.get('forma_cobranca','Unidade')))

    conn.execute("DELETE FROM produto_categorias WHERE produto_id=?", (produto_id,))
    for cat in (categorias_lista or []):
        conn.execute("INSERT INTO produto_categorias (produto_id,categoria_nome) VALUES (?,?)", (produto_id, cat))

def criar_produto(form, precos_json=None, variacoes_json=None, categorias_lista=None, imagem=None):
    import json
    conn = get_db()
    primeiro_preco = (precos_json or [{}])[0].get('preco_venda') or 0
    c = conn.execute('''INSERT INTO produtos
        (nome,imagem,prazo_producao,selo_destaque,sku,mpn,gtin_ean,como_despachado,quem_pode_comprar,
         visivel_painel,visivel_loja,visivel_geral,visivel_orcamento,
         espec_formato,espec_material,espec_revestimento,espec_acabamento,espec_cores,espec_extras,
         precisa_arte,valor_arte,url_video,descricao_curta,descricao,tipo_preco,
         desconto_revendedor_tipo,desconto_revendedor_valor,
         ncm,cfop,cest,icms_origem,icms_cst,icms_aliquota,ipi_cst,ipi_aliquota,
         pis_cst,pis_aliquota,cofins_cst,cofins_aliquota,unidade,preco,ativo)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
        (form.get('nome'), imagem, form.get('prazo_producao'), form.get('selo_destaque','Nenhum'),
         form.get('sku'), form.get('mpn'), form.get('gtin_ean'),
         form.get('como_despachado','Todos'), form.get('quem_pode_comprar','Todos'),
         1 if form.get('visivel_painel') else 0, 1 if form.get('visivel_loja') else 0,
         1 if form.get('visivel_geral') else 0, 1 if form.get('visivel_orcamento') else 0,
         form.get('espec_formato'), form.get('espec_material'), form.get('espec_revestimento'),
         form.get('espec_acabamento'), form.get('espec_cores'), form.get('espec_extras'),
         form.get('precisa_arte','Não precisa de arte'), float(form.get('valor_arte') or 0),
         form.get('url_video'), form.get('descricao_curta'), form.get('descricao'),
         form.get('tipo_preco','quantidade'),
         form.get('desconto_revendedor_tipo','%'), float(form.get('desconto_revendedor_valor') or 0),
         form.get('ncm'), form.get('cfop'), form.get('cest'),
         form.get('icms_origem','0'), form.get('icms_cst','00'), float(form.get('icms_aliquota') or 0),
         form.get('ipi_cst','00'), float(form.get('ipi_aliquota') or 0),
         form.get('pis_cst','01'), float(form.get('pis_aliquota') or 0),
         form.get('cofins_cst','01'), float(form.get('cofins_aliquota') or 0),
         form.get('unidade','UN'), float(primeiro_preco), 1))
    _salvar_produto_dados(conn, c.lastrowid, form, precos_json, variacoes_json, categorias_lista)
    conn.commit()
    conn.close()

def atualizar_produto(id, form, precos_json=None, variacoes_json=None, categorias_lista=None, imagem=None):
    conn = get_db()
    primeiro_preco = (precos_json or [{}])[0].get('preco_venda') or 0
    conn.execute('''UPDATE produtos SET
        nome=?,imagem=?,prazo_producao=?,selo_destaque=?,sku=?,mpn=?,gtin_ean=?,como_despachado=?,quem_pode_comprar=?,
        visivel_painel=?,visivel_loja=?,visivel_geral=?,visivel_orcamento=?,
        espec_formato=?,espec_material=?,espec_revestimento=?,espec_acabamento=?,espec_cores=?,espec_extras=?,
        precisa_arte=?,valor_arte=?,url_video=?,descricao_curta=?,descricao=?,tipo_preco=?,
        desconto_revendedor_tipo=?,desconto_revendedor_valor=?,
        ncm=?,cfop=?,cest=?,icms_origem=?,icms_cst=?,icms_aliquota=?,ipi_cst=?,ipi_aliquota=?,
        pis_cst=?,pis_aliquota=?,cofins_cst=?,cofins_aliquota=?,unidade=?,preco=?,ativo=?
        WHERE id=?''',
        (form.get('nome'), imagem, form.get('prazo_producao'), form.get('selo_destaque','Nenhum'),
         form.get('sku'), form.get('mpn'), form.get('gtin_ean'),
         form.get('como_despachado','Todos'), form.get('quem_pode_comprar','Todos'),
         1 if form.get('visivel_painel') else 0, 1 if form.get('visivel_loja') else 0,
         1 if form.get('visivel_geral') else 0, 1 if form.get('visivel_orcamento') else 0,
         form.get('espec_formato'), form.get('espec_material'), form.get('espec_revestimento'),
         form.get('espec_acabamento'), form.get('espec_cores'), form.get('espec_extras'),
         form.get('precisa_arte','Não precisa de arte'), float(form.get('valor_arte') or 0),
         form.get('url_video'), form.get('descricao_curta'), form.get('descricao'),
         form.get('tipo_preco','quantidade'),
         form.get('desconto_revendedor_tipo','%'), float(form.get('desconto_revendedor_valor') or 0),
         form.get('ncm'), form.get('cfop'), form.get('cest'),
         form.get('icms_origem','0'), form.get('icms_cst','00'), float(form.get('icms_aliquota') or 0),
         form.get('ipi_cst','00'), float(form.get('ipi_aliquota') or 0),
         form.get('pis_cst','01'), float(form.get('pis_aliquota') or 0),
         form.get('cofins_cst','01'), float(form.get('cofins_aliquota') or 0),
         form.get('unidade','UN'), float(primeiro_preco), 1 if form.get('ativo') else 0, id))
    _salvar_produto_dados(conn, id, form, precos_json, variacoes_json, categorias_lista)
    conn.commit()
    conn.close()

def excluir_produto(id):
    conn = get_db()
    conn.execute("DELETE FROM produtos WHERE id = ?", (id,))
    conn.commit()
    conn.close()

# ─── PEDIDOS ─────────────────────────────────────────────────────────────────

def get_pedidos(status=None, busca=None):
    conn = get_db()
    sql = '''SELECT p.*, c.nome as cliente_nome FROM pedidos p
             LEFT JOIN clientes c ON p.cliente_id = c.id'''
    params = []
    where = []
    if status:
        where.append("p.status = ?")
        params.append(status)
    if busca:
        where.append("(c.nome LIKE ? OR CAST(p.id AS TEXT) LIKE ?)")
        params += [f'%{busca}%', f'%{busca}%']
    if where:
        sql += ' WHERE ' + ' AND '.join(where)
    sql += ' ORDER BY p.created_at DESC'
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_pedido(id):
    conn = get_db()
    pedido = conn.execute('''SELECT p.*, c.nome as cliente_nome, c.telefone as cliente_telefone FROM pedidos p
                             LEFT JOIN clientes c ON p.cliente_id = c.id
                             WHERE p.id = ?''', (id,)).fetchone()
    if not pedido:
        conn.close()
        return None
    pedido = dict(pedido)
    itens = conn.execute('''SELECT pi.*, pr.nome as produto_nome, pr.imagem as produto_imagem FROM pedido_itens pi
                            LEFT JOIN produtos pr ON pi.produto_id = pr.id
                            WHERE pi.pedido_id = ?''', (id,)).fetchall()
    pedido['itens'] = [dict(i) for i in itens]
    conn.close()
    return pedido

def criar_pedido(form, itens):
    conn = get_db()
    total = sum(float(i.get('subtotal', 0)) for i in itens)
    desconto = float(form.get('desconto') or 0)
    c = conn.execute('''INSERT INTO pedidos (cliente_id,status,status_producao,total,desconto,observacoes,prazo,forma_pagamento)
                        VALUES (?,?,?,?,?,?,?,?)''',
        (form.get('cliente_id') or None, 'aguardando', 'aguardando',
         total - desconto, desconto, form.get('observacoes'),
         form.get('prazo'), form.get('forma_pagamento')))
    pedido_id = c.lastrowid
    for item in itens:
        if item.get('descricao') or item.get('produto_id'):
            conn.execute('''INSERT INTO pedido_itens (pedido_id,produto_id,descricao,quantidade,preco_unitario,subtotal)
                            VALUES (?,?,?,?,?,?)''',
                (pedido_id, item.get('produto_id') or None, item.get('descricao'),
                 float(item.get('quantidade') or 1), float(item.get('preco_unitario') or 0),
                 float(item.get('subtotal') or 0)))
    conn.commit()
    conn.close()
    return pedido_id

def atualizar_pedido(id, form, itens):
    conn = get_db()
    total = sum(float(i.get('subtotal', 0)) for i in itens)
    desconto = float(form.get('desconto') or 0)
    conn.execute('''UPDATE pedidos SET cliente_id=?,total=?,desconto=?,observacoes=?,prazo=?,forma_pagamento=?,status=?
                    WHERE id=?''',
        (form.get('cliente_id') or None, total - desconto, desconto,
         form.get('observacoes'), form.get('prazo'), form.get('forma_pagamento'),
         form.get('status'), id))
    conn.execute("DELETE FROM pedido_itens WHERE pedido_id = ?", (id,))
    for item in itens:
        if item.get('descricao') or item.get('produto_id'):
            conn.execute('''INSERT INTO pedido_itens (pedido_id,produto_id,descricao,quantidade,preco_unitario,subtotal)
                            VALUES (?,?,?,?,?,?)''',
                (id, item.get('produto_id') or None, item.get('descricao'),
                 float(item.get('quantidade') or 1), float(item.get('preco_unitario') or 0),
                 float(item.get('subtotal') or 0)))
    conn.commit()
    conn.close()

def atualizar_status_pedido(id, status):
    conn = get_db()
    conn.execute("UPDATE pedidos SET status = ? WHERE id = ?", (status, id))
    conn.commit()
    conn.close()

def atualizar_status_producao(id, status):
    conn = get_db()
    conn.execute("UPDATE pedidos SET status_producao = ? WHERE id = ?", (status, id))
    conn.commit()
    conn.close()

def excluir_pedido(id):
    conn = get_db()
    conn.execute("DELETE FROM pedidos WHERE id = ?", (id,))
    conn.commit()
    conn.close()

def get_fila_producao():
    conn = get_db()
    rows = conn.execute('''SELECT p.*, c.nome as cliente_nome FROM pedidos p
                           LEFT JOIN clientes c ON p.cliente_id = c.id
                           WHERE p.status != 'cancelado' AND p.status != 'entregue'
                           ORDER BY p.prazo ASC, p.created_at ASC''').fetchall()
    conn.close()
    return [dict(r) for r in rows]

# ─── FINANCEIRO ──────────────────────────────────────────────────────────────

def get_caixa_atual():
    conn = get_db()
    row = conn.execute("SELECT * FROM caixas WHERE status = 'aberto' ORDER BY id DESC LIMIT 1").fetchone()
    conn.close()
    return dict(row) if row else None

def get_historico_caixas():
    conn = get_db()
    rows = conn.execute("SELECT * FROM caixas ORDER BY id DESC LIMIT 30").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def abrir_caixa(form):
    conn = get_db()
    conn.execute("INSERT INTO caixas (data_abertura, valor_abertura, status) VALUES (datetime('now','localtime'), ?, 'aberto')",
                 (float(form.get('valor_abertura') or 0),))
    conn.commit()
    conn.close()

def fechar_caixa(caixa_id):
    conn = get_db()
    entradas = conn.execute("SELECT COALESCE(SUM(valor),0) FROM lancamentos WHERE caixa_id=? AND tipo='entrada'", (caixa_id,)).fetchone()[0]
    saidas = conn.execute("SELECT COALESCE(SUM(valor),0) FROM lancamentos WHERE caixa_id=? AND tipo='saida'", (caixa_id,)).fetchone()[0]
    abertura = conn.execute("SELECT valor_abertura FROM caixas WHERE id=?", (caixa_id,)).fetchone()[0]
    fechamento = abertura + entradas - saidas
    conn.execute("UPDATE caixas SET status='fechado', data_fechamento=datetime('now','localtime'), valor_fechamento=? WHERE id=?",
                 (fechamento, caixa_id))
    conn.commit()
    conn.close()

def get_lancamentos_caixa(caixa_id):
    if not caixa_id:
        return []
    conn = get_db()
    rows = conn.execute("SELECT * FROM lancamentos WHERE caixa_id = ? ORDER BY created_at DESC", (caixa_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def criar_lancamento(form):
    conn = get_db()
    conn.execute('''INSERT INTO lancamentos (caixa_id,tipo,categoria,descricao,valor,data)
                    VALUES (?,?,?,?,?,date('now','localtime'))''',
        (form.get('caixa_id'), form.get('tipo'), form.get('categoria'),
         form.get('descricao'), float(form.get('valor') or 0)))
    conn.commit()
    conn.close()

def excluir_lancamento(id):
    conn = get_db()
    conn.execute("DELETE FROM lancamentos WHERE id = ?", (id,))
    conn.commit()
    conn.close()

def get_resumo_financeiro():
    conn = get_db()
    hoje = date.today().isoformat()
    mes = hoje[:7]
    entradas_mes = conn.execute("SELECT COALESCE(SUM(valor),0) FROM lancamentos WHERE tipo='entrada' AND data LIKE ?", (f'{mes}%',)).fetchone()[0]
    saidas_mes = conn.execute("SELECT COALESCE(SUM(valor),0) FROM lancamentos WHERE tipo='saida' AND data LIKE ?", (f'{mes}%',)).fetchone()[0]
    entradas_hoje = conn.execute("SELECT COALESCE(SUM(valor),0) FROM lancamentos WHERE tipo='entrada' AND data=?", (hoje,)).fetchone()[0]
    saidas_hoje = conn.execute("SELECT COALESCE(SUM(valor),0) FROM lancamentos WHERE tipo='saida' AND data=?", (hoje,)).fetchone()[0]
    pedidos_abertos = conn.execute("SELECT COUNT(*) FROM pedidos WHERE status NOT IN ('entregue','cancelado')").fetchone()[0]
    total_clientes = conn.execute("SELECT COUNT(*) FROM clientes").fetchone()[0]
    ultimos = conn.execute("SELECT l.*, cx.data_abertura FROM lancamentos l LEFT JOIN caixas cx ON l.caixa_id=cx.id ORDER BY l.created_at DESC LIMIT 10").fetchall()
    conn.close()
    return {
        'entradas_mes': entradas_mes,
        'saidas_mes': saidas_mes,
        'saldo_mes': entradas_mes - saidas_mes,
        'entradas_hoje': entradas_hoje,
        'saidas_hoje': saidas_hoje,
        'saldo_hoje': entradas_hoje - saidas_hoje,
        'pedidos_abertos': pedidos_abertos,
        'total_clientes': total_clientes,
        'ultimos_lancamentos': [dict(r) for r in ultimos],
    }

# ─── FORNECEDORES ─────────────────────────────────────────────────────────────

def get_fornecedores(busca=None):
    conn = get_db()
    if busca:
        rows = conn.execute("SELECT * FROM fornecedores WHERE nome LIKE ? OR produto_servico LIKE ? ORDER BY nome",
                           (f'%{busca}%', f'%{busca}%')).fetchall()
    else:
        rows = conn.execute("SELECT * FROM fornecedores ORDER BY nome").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_fornecedor(id):
    conn = get_db()
    row = conn.execute("SELECT * FROM fornecedores WHERE id = ?", (id,)).fetchone()
    conn.close()
    return dict(row) if row else None

def criar_fornecedor(form):
    conn = get_db()
    conn.execute('''INSERT INTO fornecedores (nome,contato,telefone,email,cnpj,produto_servico,observacoes)
                    VALUES (?,?,?,?,?,?,?)''',
        (form.get('nome'), form.get('contato'), form.get('telefone'), form.get('email'),
         form.get('cnpj'), form.get('produto_servico'), form.get('observacoes')))
    conn.commit()
    conn.close()

def atualizar_fornecedor(id, form):
    conn = get_db()
    conn.execute('''UPDATE fornecedores SET nome=?,contato=?,telefone=?,email=?,cnpj=?,produto_servico=?,observacoes=?
                    WHERE id=?''',
        (form.get('nome'), form.get('contato'), form.get('telefone'), form.get('email'),
         form.get('cnpj'), form.get('produto_servico'), form.get('observacoes'), id))
    conn.commit()
    conn.close()

def excluir_fornecedor(id):
    conn = get_db()
    conn.execute("DELETE FROM fornecedores WHERE id = ?", (id,))
    conn.commit()
    conn.close()

# ─── NOTAS FISCAIS ───────────────────────────────────────────────────────────

def get_notasfiscais():
    conn = get_db()
    rows = conn.execute("SELECT * FROM notasfiscais ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_pedidos_sem_nf():
    conn = get_db()
    rows = conn.execute('''SELECT p.*, c.nome as cliente_nome FROM pedidos p
                           LEFT JOIN clientes c ON p.cliente_id = c.id
                           WHERE p.id NOT IN (SELECT pedido_id FROM notasfiscais WHERE pedido_id IS NOT NULL)
                           AND p.status != 'cancelado'
                           ORDER BY p.created_at DESC''').fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_proximo_numero_nf():
    conn = get_db()
    row = conn.execute("SELECT MAX(CAST(numero AS INTEGER)) FROM notasfiscais").fetchone()[0]
    conn.close()
    return str((row or 0) + 1).zfill(6)

def criar_nf(form):
    conn = get_db()
    numero = get_proximo_numero_nf()
    conn.execute('''INSERT INTO notasfiscais (numero,pedido_id,cliente_id,cliente_nome,cliente_cpf_cnpj,valor_total,descricao_servico,status,observacoes)
                    VALUES (?,?,?,?,?,?,?,?,?)''',
        (numero, form.get('pedido_id') or None, form.get('cliente_id') or None,
         form.get('cliente_nome'), form.get('cliente_cpf_cnpj'),
         float(form.get('valor_total') or 0), form.get('descricao_servico'),
         'emitida', form.get('observacoes')))
    conn.commit()
    conn.close()
    return numero

def excluir_nf(id):
    conn = get_db()
    conn.execute("DELETE FROM notasfiscais WHERE id = ?", (id,))
    conn.commit()
    conn.close()

# ─── PRECIFICAÇÃO — CONFIGURAÇÕES ────────────────────────────────────────────

# ─── PONTO DE EQUILÍBRIO ────────────────────────────────────────────────────

PEC_CATEGORIAS = {
    'pessoal':      'Pessoal',
    'instalacoes':  'Instalações',
    'utilidades':   'Utilidades',
    'servicos':     'Serviços Externos',
    'financeiro':   'Financeiro',
    'marketing':    'Marketing',
    'outros':       'Outros',
}

def pec_get_custos():
    conn = get_db()
    rows = conn.execute("SELECT * FROM pec_custos_fixos WHERE ativo=1 ORDER BY categoria, nome").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def pec_salvar_custo(form, id=None):
    conn = get_db()
    campos = (
        form.get('nome', '').strip(),
        form.get('categoria', 'outros'),
        float(form.get('valor') or 0),
        form.get('observacao', '').strip(),
    )
    if id:
        conn.execute("UPDATE pec_custos_fixos SET nome=?,categoria=?,valor=?,observacao=? WHERE id=?", campos + (id,))
    else:
        conn.execute("INSERT INTO pec_custos_fixos (nome,categoria,valor,observacao) VALUES (?,?,?,?)", campos)
    conn.commit()
    conn.close()

def pec_excluir_custo(id):
    conn = get_db()
    conn.execute("UPDATE pec_custos_fixos SET ativo=0 WHERE id=?", (id,))
    conn.commit()
    conn.close()

def pec_get_total():
    conn = get_db()
    r = conn.execute("SELECT COALESCE(SUM(valor),0) FROM pec_custos_fixos WHERE ativo=1").fetchone()
    conn.close()
    return r[0] if r else 0

def prec_get_config(chave, default=None):
    conn = get_db()
    r = conn.execute("SELECT valor FROM prec_configuracoes WHERE chave=?", (chave,)).fetchone()
    conn.close()
    return r[0] if r else default

def prec_set_config(chave, valor):
    conn = get_db()
    conn.execute("INSERT OR REPLACE INTO prec_configuracoes (chave,valor) VALUES (?,?)", (chave, str(valor)))
    conn.commit()
    conn.close()

# ─── CENTRAL DE CUSTOS ───────────────────────────────────────────────────────

DESPESA_CATEGORIAS = {
    'combustivel':      'Combustível',
    'aluguel':          'Aluguel',
    'energia':          'Energia Elétrica',
    'agua':             'Água',
    'internet':         'Internet / Telefone',
    'impostos':         'Impostos e Taxas',
    'folha':            'Folha de Pagamento',
    'prolabore':        'Pró-labore',
    'insumos':          'Insumos e Materiais',
    'manutencao':       'Manutenção e Reparos',
    'bancario':         'Taxas Bancárias',
    'marketing':        'Marketing',
    'equipamentos':     'Equipamentos',
    'terceiros':        'Terceiros e Serviços',
    'outros':           'Outros',
}

FORMAS_PAGAMENTO = {
    'dinheiro':   'Dinheiro',
    'pix':        'PIX',
    'debito':     'Débito',
    'credito':    'Crédito',
    'boleto':     'Boleto',
    'transferencia': 'Transferência',
}

def get_despesas(mes=None, ano=None, categoria=None):
    conn = get_db()
    conds = ["ativo=1"]
    params = []
    if mes and ano:
        conds.append("strftime('%Y-%m', data) = ?")
        params.append(f"{int(ano):04d}-{int(mes):02d}")
    if categoria:
        conds.append("categoria = ?")
        params.append(categoria)
    where = " AND ".join(conds)
    rows = conn.execute(
        f"SELECT * FROM despesas WHERE {where} ORDER BY data DESC, id DESC",
        params
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def salvar_despesa(form, id=None):
    conn = get_db()
    campos = (
        form.get('data', ''),
        form.get('descricao', '').strip(),
        form.get('categoria', 'outros'),
        float(form.get('valor') or 0),
        form.get('forma_pagamento', 'dinheiro'),
        1 if form.get('recorrente') else 0,
        form.get('observacao', '').strip(),
    )
    if id:
        conn.execute(
            "UPDATE despesas SET data=?,descricao=?,categoria=?,valor=?,forma_pagamento=?,recorrente=?,observacao=? WHERE id=?",
            campos + (id,)
        )
    else:
        conn.execute(
            "INSERT INTO despesas (data,descricao,categoria,valor,forma_pagamento,recorrente,observacao) VALUES (?,?,?,?,?,?,?)",
            campos
        )
    conn.commit()
    conn.close()

def excluir_despesa(id):
    conn = get_db()
    conn.execute("UPDATE despesas SET ativo=0 WHERE id=?", (id,))
    conn.commit()
    conn.close()

def get_resumo_despesas(mes, ano):
    conn = get_db()
    periodo = f"{int(ano):04d}-{int(mes):02d}"
    total_mes = conn.execute(
        "SELECT COALESCE(SUM(valor),0) FROM despesas WHERE ativo=1 AND strftime('%Y-%m',data)=?",
        (periodo,)
    ).fetchone()[0]
    total_ano = conn.execute(
        "SELECT COALESCE(SUM(valor),0) FROM despesas WHERE ativo=1 AND strftime('%Y',data)=?",
        (str(int(ano)),)
    ).fetchone()[0]
    por_categoria = conn.execute(
        "SELECT categoria, SUM(valor) as total FROM despesas WHERE ativo=1 AND strftime('%Y-%m',data)=? GROUP BY categoria ORDER BY total DESC",
        (periodo,)
    ).fetchall()
    conn.close()
    return {
        'total_mes': total_mes,
        'total_ano': total_ano,
        'por_categoria': [dict(r) for r in por_categoria],
    }

# ─── CONTAS A PAGAR ──────────────────────────────────────────────────────────

def get_contas_pagar(status_filtro=None, mes=None, ano=None):
    import datetime
    conn = get_db()
    hoje = datetime.date.today().isoformat()
    conds = ["ativo=1"]
    params = []
    if status_filtro == 'pendente':
        conds.append("pago_em IS NULL AND vencimento >= ?")
        params.append(hoje)
    elif status_filtro == 'vencido':
        conds.append("pago_em IS NULL AND vencimento < ?")
        params.append(hoje)
    elif status_filtro == 'pago':
        conds.append("pago_em IS NOT NULL")
    if mes and ano:
        conds.append("strftime('%Y-%m', vencimento) = ?")
        params.append(f"{int(ano):04d}-{int(mes):02d}")
    where = " AND ".join(conds)
    rows = conn.execute(
        f"SELECT * FROM contas_pagar WHERE {where} ORDER BY vencimento ASC, id DESC",
        params
    ).fetchall()
    conn.close()
    hoje_d = datetime.date.today()
    result = []
    for r in rows:
        d = dict(r)
        if d['pago_em']:
            d['status'] = 'pago'
        elif d['vencimento'] < hoje:
            d['status'] = 'vencido'
        else:
            d['status'] = 'pendente'
        result.append(d)
    return result

def salvar_conta_pagar(form, id=None):
    conn = get_db()
    campos = (
        form.get('descricao', '').strip(),
        form.get('fornecedor', '').strip(),
        float(form.get('valor') or 0),
        form.get('vencimento', ''),
        form.get('forma_pagamento', 'boleto'),
        form.get('observacao', '').strip(),
    )
    if id:
        conn.execute(
            "UPDATE contas_pagar SET descricao=?,fornecedor=?,valor=?,vencimento=?,forma_pagamento=?,observacao=? WHERE id=?",
            campos + (id,)
        )
    else:
        conn.execute(
            "INSERT INTO contas_pagar (descricao,fornecedor,valor,vencimento,forma_pagamento,observacao) VALUES (?,?,?,?,?,?)",
            campos
        )
    conn.commit()
    conn.close()

def pagar_conta(id, data_pagamento):
    conn = get_db()
    conn.execute("UPDATE contas_pagar SET pago_em=? WHERE id=?", (data_pagamento, id))
    conn.commit()
    conn.close()

def estornar_conta(id):
    conn = get_db()
    conn.execute("UPDATE contas_pagar SET pago_em=NULL WHERE id=?", (id,))
    conn.commit()
    conn.close()

def excluir_conta_pagar(id):
    conn = get_db()
    conn.execute("UPDATE contas_pagar SET ativo=0 WHERE id=?", (id,))
    conn.commit()
    conn.close()

def get_resumo_contas(mes=None, ano=None):
    import datetime
    conn = get_db()
    hoje = datetime.date.today().isoformat()
    conds_base = ["ativo=1"]
    params_base = []
    if mes and ano:
        conds_base.append("strftime('%Y-%m', vencimento) = ?")
        params_base.append(f"{int(ano):04d}-{int(mes):02d}")
    w = " AND ".join(conds_base)
    total_pendente = conn.execute(
        f"SELECT COALESCE(SUM(valor),0) FROM contas_pagar WHERE {w} AND pago_em IS NULL AND vencimento >= ?",
        params_base + [hoje]
    ).fetchone()[0]
    total_vencido = conn.execute(
        f"SELECT COALESCE(SUM(valor),0) FROM contas_pagar WHERE {w} AND pago_em IS NULL AND vencimento < ?",
        params_base + [hoje]
    ).fetchone()[0]
    total_pago = conn.execute(
        f"SELECT COALESCE(SUM(valor),0) FROM contas_pagar WHERE {w} AND pago_em IS NOT NULL",
        params_base
    ).fetchone()[0]
    conn.close()
    return {'pendente': total_pendente, 'vencido': total_vencido, 'pago': total_pago}

# ─── PAPÉIS ──────────────────────────────────────────────────────────────────

def prec_get_papeis():
    conn = get_db()
    rows = conn.execute("SELECT * FROM prec_papeis WHERE ativo=1 ORDER BY nome").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def prec_get_papel(id):
    conn = get_db()
    r = conn.execute("SELECT * FROM prec_papeis WHERE id=?", (id,)).fetchone()
    conn.close()
    return dict(r) if r else None

def prec_salvar_papel(form, id=None):
    conn = get_db()
    tamanho_fixo = 1 if form.get('tamanho_fixo') else 0
    campos = (form.get('nome'), float(form.get('largura') or 0), float(form.get('altura') or 0),
              int(form.get('folhas_resma') or 500), float(form.get('custo_resma') or 0),
              float(form.get('fator_perda') or 5), tamanho_fixo)
    if id:
        conn.execute('''UPDATE prec_papeis SET nome=?,largura=?,altura=?,folhas_resma=?,custo_resma=?,fator_perda=?,tamanho_fixo=? WHERE id=?''',
                     campos + (id,))
    else:
        conn.execute('''INSERT INTO prec_papeis (nome,largura,altura,folhas_resma,custo_resma,fator_perda,tamanho_fixo) VALUES (?,?,?,?,?,?,?)''', campos)
    conn.commit()
    conn.close()

def prec_excluir_papel(id):
    conn = get_db()
    conn.execute("UPDATE prec_papeis SET ativo=0 WHERE id=?", (id,))
    conn.commit()
    conn.close()

# ─── ACRÍLICOS ───────────────────────────────────────────────────────────────

def prec_get_acrilicos():
    conn = get_db()
    rows = conn.execute("SELECT * FROM prec_acrilicos WHERE ativo=1 ORDER BY nome").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def prec_salvar_acrilico(form, id=None):
    conn = get_db()
    campos = (
        form.get('nome'),
        float(form.get('largura_cm') or 0),
        float(form.get('altura_cm') or 0),
        float(form.get('espessura_mm') or 3),
        form.get('cor') or 'Transparente',
        float(form.get('custo') or 0),
    )
    if id:
        conn.execute(
            'UPDATE prec_acrilicos SET nome=?,largura_cm=?,altura_cm=?,espessura_mm=?,cor=?,custo=? WHERE id=?',
            campos + (id,))
    else:
        conn.execute(
            'INSERT INTO prec_acrilicos (nome,largura_cm,altura_cm,espessura_mm,cor,custo) VALUES (?,?,?,?,?,?)',
            campos)
    conn.commit()
    conn.close()

def prec_excluir_acrilico(id):
    conn = get_db()
    conn.execute("UPDATE prec_acrilicos SET ativo=0 WHERE id=?", (id,))
    conn.commit()
    conn.close()

# ─── EQUIPAMENTOS DE CORTE ───────────────────────────────────────────────────

def prec_get_maquinas_corte():
    conn = get_db()
    rows = conn.execute("SELECT * FROM prec_maquinas_corte WHERE ativo=1 ORDER BY nome").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def prec_salvar_maquina_corte(form, id=None):
    conn = get_db()
    campos = (form.get('nome'), float(form.get('custo_hora') or 0))
    if id:
        conn.execute('UPDATE prec_maquinas_corte SET nome=?,custo_hora=? WHERE id=?', campos + (id,))
    else:
        conn.execute('INSERT INTO prec_maquinas_corte (nome,custo_hora) VALUES (?,?)', campos)
    conn.commit()
    conn.close()

def prec_excluir_maquina_corte(id):
    conn = get_db()
    conn.execute("UPDATE prec_maquinas_corte SET ativo=0 WHERE id=?", (id,))
    conn.commit()
    conn.close()

# ─── MÍDIAS EM BOBINA ────────────────────────────────────────────────────────

def prec_get_midias_bobina():
    conn = get_db()
    rows = conn.execute("SELECT * FROM prec_midias_bobina WHERE ativo=1 ORDER BY nome").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def prec_salvar_midia_bobina(form, id=None):
    conn = get_db()
    campos = (form.get('nome'), float(form.get('custo_m2') or 0))
    if id:
        conn.execute('UPDATE prec_midias_bobina SET nome=?,custo_m2=? WHERE id=?', campos + (id,))
    else:
        conn.execute('INSERT INTO prec_midias_bobina (nome,custo_m2) VALUES (?,?)', campos)
    conn.commit()
    conn.close()

def prec_excluir_midia_bobina(id):
    conn = get_db()
    conn.execute("UPDATE prec_midias_bobina SET ativo=0 WHERE id=?", (id,))
    conn.commit()
    conn.close()

# ─── MÁQUINAS ────────────────────────────────────────────────────────────────

def prec_get_maquinas():
    conn = get_db()
    rows = conn.execute("SELECT * FROM prec_maquinas WHERE ativo=1 ORDER BY nome").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def prec_get_maquina(id):
    conn = get_db()
    r = conn.execute("SELECT * FROM prec_maquinas WHERE id=?", (id,)).fetchone()
    conn.close()
    return dict(r) if r else None

def prec_salvar_maquina(form, id=None):
    conn = get_db()
    tipo = form.get('tipo', 'click')
    if tipo == 'bobina':
        m2_impressao  = float(form.get('custo_m2_impressao_bob') or 0)
        m2_depreciacao = float(form.get('custo_m2_depreciacao_bob') or 0)
    else:
        m2_impressao  = float(form.get('custo_m2_impressao') or 0)
        m2_depreciacao = float(form.get('custo_m2_depreciacao') or 0)
    m2_branco  = float(form.get('custo_m2_branco') or 0) if tipo == 'm2' else 0
    m2_verniz  = float(form.get('custo_m2_verniz') or 0) if tipo == 'm2' else 0
    campos = (form.get('nome'), tipo, float(form.get('boca_cm') or 33),
              float(form.get('custo_click_toner') or 0),
              float(form.get('custo_click_manutencao') or 0),
              float(form.get('custo_click_depreciacao') or 0),
              0,  # custo_m2_material — vem das Mídias em Bobina, não da máquina
              m2_impressao,
              m2_depreciacao,
              float(form.get('custo_click_pb') or 0),
              float(form.get('custo_click_cor') or 0),
              m2_branco,
              m2_verniz)
    if id:
        conn.execute('''UPDATE prec_maquinas SET nome=?,tipo=?,boca_cm=?,
            custo_click_toner=?,custo_click_manutencao=?,custo_click_depreciacao=?,
            custo_m2_material=?,custo_m2_impressao=?,custo_m2_depreciacao=?,
            custo_click_pb=?,custo_click_cor=?,custo_m2_branco=?,custo_m2_verniz=?
            WHERE id=?''',
            campos + (id,))
    else:
        conn.execute('''INSERT INTO prec_maquinas (nome,tipo,boca_cm,
            custo_click_toner,custo_click_manutencao,custo_click_depreciacao,
            custo_m2_material,custo_m2_impressao,custo_m2_depreciacao,
            custo_click_pb,custo_click_cor,custo_m2_branco,custo_m2_verniz)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)''', campos)
    conn.commit()
    conn.close()

def prec_excluir_maquina(id):
    conn = get_db()
    conn.execute("UPDATE prec_maquinas SET ativo=0 WHERE id=?", (id,))
    conn.commit()
    conn.close()

# ─── ACABAMENTOS ─────────────────────────────────────────────────────────────

def prec_get_acabamentos(categoria=None):
    conn = get_db()
    if categoria:
        rows = conn.execute("SELECT * FROM prec_acabamentos WHERE ativo=1 AND categoria=? ORDER BY nome", (categoria,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM prec_acabamentos WHERE ativo=1 ORDER BY nome").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def prec_get_acabamentos_papel():
    return prec_get_acabamentos(categoria='papel')

def prec_get_acabamentos_uv_eco():
    return prec_get_acabamentos(categoria='uv_eco')

def prec_get_acabamento(id):
    conn = get_db()
    r = conn.execute("SELECT * FROM prec_acabamentos WHERE id=?", (id,)).fetchone()
    conn.close()
    return dict(r) if r else None

def prec_salvar_acabamento(form, id=None):
    conn = get_db()
    tipo = form.get('tipo', 'job')
    if tipo == 'wireo':
        bob_comp  = float(form.get('wireo_rolo_aneis') or 0)
        bob_custo = float(form.get('wireo_rolo_custo') or 0)
        custo_base = (bob_custo / bob_comp) if bob_comp > 0 else 0
        unidade = 'anel'
        markup = float(form.get('wireo_markup') or 2.0)
    elif tipo == 'hora':
        bob_comp = bob_custo = 0
        custo_base = float(form.get('custo_base') or 0)
        unidade = 'hora'
        markup = float(form.get('hora_markup') or 1.0)
    elif tipo == 'unidade':
        bob_comp = bob_custo = 0
        custo_base = float(form.get('custo_base') or 0)
        unidade = form.get('unidade', 'unidade')
        markup = float(form.get('unidade_markup') or 1.0)
    elif tipo == 'job':
        bob_comp = bob_custo = 0
        custo_base = float(form.get('custo_base') or 0)
        unidade = 'job'
        markup = float(form.get('job_markup') or 1.0)
    else:  # bobina
        bob_comp  = float(form.get('bobina_comprimento') or 0)
        bob_custo = float(form.get('bobina_custo') or 0)
        custo_base = float(form.get('custo_base') or 0)
        unidade = form.get('unidade', 'job')
        markup = float(form.get('markup') or 1.0)
    categoria = form.get('categoria', 'papel')
    campos = (form.get('nome'), tipo, custo_base, unidade,
              markup,
              float(form.get('bobina_largura') or 0),
              bob_comp, bob_custo, categoria)
    if id:
        conn.execute('''UPDATE prec_acabamentos SET nome=?,tipo=?,custo_base=?,unidade=?,markup=?,
            bobina_largura=?,bobina_comprimento=?,bobina_custo=?,categoria=? WHERE id=?''', campos + (id,))
    else:
        conn.execute('''INSERT INTO prec_acabamentos (nome,tipo,custo_base,unidade,markup,
            bobina_largura,bobina_comprimento,bobina_custo,categoria) VALUES (?,?,?,?,?,?,?,?,?)''', campos)
    conn.commit()
    conn.close()

def prec_excluir_acabamento(id):
    conn = get_db()
    conn.execute("UPDATE prec_acabamentos SET ativo=0 WHERE id=?", (id,))
    conn.commit()
    conn.close()

# ─── PAPELÃO PARA CAPA DURA ──────────────────────────────────────────────────

def prec_get_papelao():
    conn = get_db()
    rows = conn.execute("SELECT * FROM prec_papelao WHERE ativo=1 ORDER BY nome").fetchall()
    result = []
    for r in rows:
        d = dict(r)
        tamanhos = conn.execute(
            "SELECT * FROM prec_papelao_tamanhos WHERE papelao_id=? ORDER BY nome", (r['id'],)
        ).fetchall()
        d['tamanhos'] = [dict(t) for t in tamanhos]
        result.append(d)
    conn.close()
    return result

def prec_salvar_tamanho_papelao(form):
    conn = get_db()
    conn.execute(
        "INSERT INTO prec_papelao_tamanhos (papelao_id, nome, largura, altura) VALUES (?,?,?,?)",
        (int(form.get('papelao_id')), form.get('nome',''),
         float(form.get('largura') or 0), float(form.get('altura') or 0))
    )
    conn.commit()
    conn.close()

def prec_excluir_tamanho_papelao(id):
    conn = get_db()
    conn.execute("DELETE FROM prec_papelao_tamanhos WHERE id=?", (id,))
    conn.commit()
    conn.close()

def prec_salvar_papelao(form, id=None):
    conn = get_db()
    campos = (form.get('nome', ''), float(form.get('largura') or 0),
              float(form.get('altura') or 0), float(form.get('custo') or 0))
    if id:
        conn.execute("UPDATE prec_papelao SET nome=?,largura=?,altura=?,custo=? WHERE id=?",
                     campos + (id,))
    else:
        conn.execute("INSERT INTO prec_papelao (nome,largura,altura,custo) VALUES (?,?,?,?)", campos)
    conn.commit()
    conn.close()

def prec_excluir_papelao(id):
    conn = get_db()
    conn.execute("UPDATE prec_papelao SET ativo=0 WHERE id=?", (id,))
    conn.commit()
    conn.close()

# ─── CÁLCULOS SALVOS ─────────────────────────────────────────────────────────

def prec_criar_produto_da_calc(dados):
    conn = get_db()
    nome = dados.get('nome') or 'Produto sem nome'
    unidade = dados.get('unidade', 'UN')
    faixas = dados.get('faixas', [])
    preco_base = faixas[0]['preco'] if faixas else dados.get('preco_venda', 0)
    tipo_preco = 'quantidade' if faixas else 'simples'
    c = conn.execute(
        'INSERT INTO produtos (nome, unidade, preco, ativo, tipo_preco) VALUES (?, ?, ?, 1, ?)',
        (nome, unidade, preco_base, tipo_preco))
    produto_id = c.lastrowid
    for f in faixas:
        conn.execute(
            'INSERT INTO produto_precos (produto_id, quantidade, preco_venda, preco_custo) VALUES (?, ?, ?, ?)',
            (produto_id, f.get('qtd'), f.get('preco'), f.get('custo')))
    conn.commit()
    conn.close()
    return produto_id

def prec_salvar_calculo(dados):
    import json
    conn = get_db()
    c = conn.execute('''INSERT INTO prec_calculos (nome,tipo_produto,quantidade,custo_total,markup,preco_venda,dados_json,status)
                        VALUES (?,?,?,?,?,?,?,?)''',
        (dados.get('nome'), dados.get('tipo_produto'), dados.get('quantidade'),
         dados.get('custo_total'), dados.get('markup'), dados.get('preco_venda'),
         json.dumps(dados), 'salvo'))
    id = c.lastrowid
    conn.commit()
    conn.close()
    return id

def prec_get_calculos():
    conn = get_db()
    rows = conn.execute("SELECT * FROM prec_calculos ORDER BY created_at DESC LIMIT 50").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def prec_get_calculo(id):
    import json
    conn = get_db()
    r = conn.execute("SELECT * FROM prec_calculos WHERE id=?", (id,)).fetchone()
    conn.close()
    if not r:
        return None
    d = dict(r)
    try:
        d['dados'] = json.loads(d['dados_json'])
    except Exception:
        d['dados'] = {}
    return d

# ─── ORÇAMENTOS ──────────────────────────────────────────────────────────────

def _proximo_numero_orc():
    conn = get_db()
    ano = date.today().year
    row = conn.execute("SELECT COUNT(*) FROM orcamentos WHERE numero LIKE ?", (f'ORC-{ano}-%',)).fetchone()[0]
    conn.close()
    return f'ORC-{ano}-{str(row + 1).zfill(3)}'

def get_orcamentos(status=None, busca=None):
    conn = get_db()
    sql = '''SELECT o.*, c.nome as cliente_nome FROM orcamentos o
             LEFT JOIN clientes c ON o.cliente_id = c.id'''
    params = []
    where = []
    if status:
        where.append("o.status = ?")
        params.append(status)
    if busca:
        where.append("(c.nome LIKE ? OR o.numero LIKE ?)")
        params += [f'%{busca}%', f'%{busca}%']
    if where:
        sql += ' WHERE ' + ' AND '.join(where)
    sql += ' ORDER BY o.created_at DESC'
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_orcamento(id):
    conn = get_db()
    orc = conn.execute('''SELECT o.*, c.nome as cliente_nome, c.email as cliente_email,
                          c.telefone as cliente_telefone, c.cpf_cnpj as cliente_cpf_cnpj,
                          c.endereco as cliente_endereco, c.cidade as cliente_cidade,
                          c.estado as cliente_estado
                          FROM orcamentos o
                          LEFT JOIN clientes c ON o.cliente_id = c.id
                          WHERE o.id = ?''', (id,)).fetchone()
    if not orc:
        conn.close()
        return None
    orc = dict(orc)
    itens = conn.execute('''SELECT oi.*, p.nome as produto_nome, p.imagem as produto_imagem FROM orcamento_itens oi
                            LEFT JOIN produtos p ON oi.produto_id = p.id
                            WHERE oi.orcamento_id = ?''', (id,)).fetchall()
    orc['itens'] = [dict(i) for i in itens]
    conn.close()
    return orc

def criar_orcamento(form, itens):
    conn = get_db()
    numero = _proximo_numero_orc()
    total = sum(float(i.get('subtotal', 0)) for i in itens)
    desconto = float(form.get('desconto') or 0)
    c = conn.execute('''INSERT INTO orcamentos
        (numero,cliente_id,status,total,desconto,validade,forma_pagamento,condicoes,observacoes)
        VALUES (?,?,?,?,?,?,?,?,?)''',
        (numero, form.get('cliente_id') or None, 'rascunho',
         total - desconto, desconto, form.get('validade'),
         form.get('forma_pagamento'), form.get('condicoes'), form.get('observacoes')))
    orc_id = c.lastrowid
    for item in itens:
        if item.get('descricao') or item.get('produto_id'):
            conn.execute('''INSERT INTO orcamento_itens (orcamento_id,produto_id,descricao,quantidade,preco_unitario,subtotal)
                            VALUES (?,?,?,?,?,?)''',
                (orc_id, item.get('produto_id') or None, item.get('descricao'),
                 float(item.get('quantidade') or 1), float(item.get('preco_unitario') or 0),
                 float(item.get('subtotal') or 0)))
    conn.commit()
    conn.close()
    return orc_id, numero

def atualizar_orcamento(id, form, itens):
    conn = get_db()
    total = sum(float(i.get('subtotal', 0)) for i in itens)
    desconto = float(form.get('desconto') or 0)
    conn.execute('''UPDATE orcamentos SET cliente_id=?,status=?,total=?,desconto=?,validade=?,
                    forma_pagamento=?,condicoes=?,observacoes=? WHERE id=?''',
        (form.get('cliente_id') or None, form.get('status', 'rascunho'),
         total - desconto, desconto, form.get('validade'),
         form.get('forma_pagamento'), form.get('condicoes'), form.get('observacoes'), id))
    conn.execute("DELETE FROM orcamento_itens WHERE orcamento_id = ?", (id,))
    for item in itens:
        if item.get('descricao') or item.get('produto_id'):
            conn.execute('''INSERT INTO orcamento_itens (orcamento_id,produto_id,descricao,quantidade,preco_unitario,subtotal)
                            VALUES (?,?,?,?,?,?)''',
                (id, item.get('produto_id') or None, item.get('descricao'),
                 float(item.get('quantidade') or 1), float(item.get('preco_unitario') or 0),
                 float(item.get('subtotal') or 0)))
    conn.commit()
    conn.close()

def converter_orcamento_pedido(orc_id):
    conn = get_db()
    orc = conn.execute("SELECT * FROM orcamentos WHERE id=?", (orc_id,)).fetchone()
    if not orc:
        conn.close()
        return None
    orc = dict(orc)
    c = conn.execute('''INSERT INTO pedidos (cliente_id,status,status_producao,total,desconto,observacoes,forma_pagamento)
                        VALUES (?,?,?,?,?,?,?)''',
        (orc['cliente_id'], 'aguardando', 'aguardando',
         orc['total'], orc['desconto'], orc['observacoes'], orc['forma_pagamento']))
    pedido_id = c.lastrowid
    itens = conn.execute("SELECT * FROM orcamento_itens WHERE orcamento_id=?", (orc_id,)).fetchall()
    for i in itens:
        conn.execute('''INSERT INTO pedido_itens (pedido_id,produto_id,descricao,quantidade,preco_unitario,subtotal)
                        VALUES (?,?,?,?,?,?)''',
            (pedido_id, i['produto_id'], i['descricao'], i['quantidade'], i['preco_unitario'], i['subtotal']))
    conn.execute("UPDATE orcamentos SET status='aprovado', pedido_id=? WHERE id=?", (pedido_id, orc_id))
    conn.commit()
    conn.close()
    return pedido_id

def excluir_orcamento(id):
    conn = get_db()
    conn.execute("DELETE FROM orcamentos WHERE id = ?", (id,))
    conn.commit()
    conn.close()

def get_produto_precos(id):
    conn = get_db()
    produto = conn.execute("SELECT id,nome,preco,unidade,prazo_producao,tipo_preco FROM produtos WHERE id=?", (id,)).fetchone()
    if not produto:
        conn.close()
        return None
    p = dict(produto)
    p['precos'] = [dict(r) for r in conn.execute(
        "SELECT * FROM produto_precos WHERE produto_id=? ORDER BY COALESCE(qtd_min, quantidade)", (id,)).fetchall()]
    p['variacoes'] = [dict(r) for r in conn.execute(
        "SELECT * FROM produto_variacoes WHERE produto_id=? ORDER BY id", (id,)).fetchall()]
    conn.close()
    return p

def get_stats():
    conn = get_db()
    hoje = date.today().isoformat()
    mes = hoje[:7]
    pedidos_hoje = conn.execute("SELECT COUNT(*) FROM pedidos WHERE date(created_at)=?", (hoje,)).fetchone()[0]
    pedidos_abertos = conn.execute("SELECT COUNT(*) FROM pedidos WHERE status NOT IN ('entregue','cancelado')").fetchone()[0]
    faturamento_mes = conn.execute("SELECT COALESCE(SUM(valor),0) FROM lancamentos WHERE tipo='entrada' AND data LIKE ?", (f'{mes}%',)).fetchone()[0]
    faturamento_hoje = conn.execute("SELECT COALESCE(SUM(valor),0) FROM lancamentos WHERE tipo='entrada' AND data=?", (hoje,)).fetchone()[0]
    total_clientes = conn.execute("SELECT COUNT(*) FROM clientes").fetchone()[0]
    ultimos_pedidos = conn.execute('''SELECT p.*, c.nome as cliente_nome FROM pedidos p
                                      LEFT JOIN clientes c ON p.cliente_id=c.id
                                      ORDER BY p.created_at DESC LIMIT 5''').fetchall()
    conn.close()
    return {
        'pedidos_hoje': pedidos_hoje,
        'pedidos_abertos': pedidos_abertos,
        'faturamento_mes': faturamento_mes,
        'faturamento_hoje': faturamento_hoje,
        'total_clientes': total_clientes,
        'ultimos_pedidos': [dict(r) for r in ultimos_pedidos],
    }


# ─── NF-e IMPORTAÇÃO ─────────────────────────────────────────────────────────

import xml.etree.ElementTree as ET

_NFE_NS = 'http://www.portalfiscal.inf.br/nfe'

def nfe_parse_xml(xml_bytes):
    def t(tag): return f'{{{_NFE_NS}}}{tag}'
    root = ET.fromstring(xml_bytes)
    inf = root.find(f'.//{t("infNFe")}')
    if inf is None:
        raise ValueError("Arquivo não reconhecido como NF-e")
    emit = inf.find(t('emit'))
    ide  = inf.find(t('ide'))
    cnpj = emit.findtext(t('CNPJ'), '') if emit is not None else ''
    nome = emit.findtext(t('xNome'), '') if emit is not None else ''
    num_nf = ide.findtext(t('nNF'), '') if ide is not None else ''
    dh_emi = ''
    if ide is not None:
        dh_emi = ide.findtext(t('dhEmi'), ide.findtext(t('dEmi'), '') or '')
    vNF_el = inf.find(f'.//{t("vNF")}')
    valor_total = float(vNF_el.text) if vNF_el is not None else 0.0
    itens = []
    for det in inf.findall(t('det')):
        prod = det.find(t('prod'))
        if prod is None:
            continue
        itens.append({
            'codigo':     prod.findtext(t('cProd'), ''),
            'descricao':  prod.findtext(t('xProd'), ''),
            'quantidade': float(prod.findtext(t('qCom'), '0') or 0),
            'unidade':    prod.findtext(t('uCom'), 'UN'),
            'valor_unit': float(prod.findtext(t('vUnCom'), '0') or 0),
            'valor_total': float(prod.findtext(t('vProd'), '0') or 0),
        })
    return {
        'cnpj':        cnpj,
        'nome':        nome,
        'numero_nf':   num_nf,
        'data_emissao': dh_emi[:10] if dh_emi else '',
        'valor_total': valor_total,
        'itens':       itens,
    }


def nfe_get_mapeamento(cnpj, codigo):
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM nfe_mapeamentos WHERE cnpj_emitente=? AND codigo_produto=?",
        (cnpj, codigo)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def nfe_get_todos_insumos():
    conn = get_db()
    papeis      = [dict(r) for r in conn.execute("SELECT id, nome FROM prec_papeis WHERE ativo=1 ORDER BY nome").fetchall()]
    acabamentos = [dict(r) for r in conn.execute("SELECT id, nome FROM prec_acabamentos WHERE ativo=1 ORDER BY nome").fetchall()]
    papelao     = [dict(r) for r in conn.execute("SELECT id, nome FROM prec_papelao WHERE ativo=1 ORDER BY nome").fetchall()]
    midias      = [dict(r) for r in conn.execute("SELECT id, nome FROM prec_midias_bobina WHERE ativo=1 ORDER BY nome").fetchall()]
    conn.close()
    return {'papel': papeis, 'acabamento': acabamentos, 'papelao': papelao, 'midia': midias}


def _nfe_norm(s):
    """Normaliza nome para comparação: maiúsculo, sem acento, espaços colapsados."""
    import re, unicodedata
    s = (s or '').upper().strip()
    s = ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
    return re.sub(r'\s+', ' ', s)


def nfe_match_por_nome(descricao):
    """Procura um insumo já cadastrado cujo nome bata com a descrição da NF-e.
    Casa por nome exato (normalizado) ou nome do insumo contido na descrição.
    Retorna {insumo_tipo, insumo_id, nome} do melhor match, ou None."""
    alvo = _nfe_norm(descricao)
    if not alvo:
        return None
    melhor = None
    for tipo, lista in nfe_get_todos_insumos().items():
        for ins in lista:
            nome_norm = _nfe_norm(ins['nome'])
            if len(nome_norm) < 4:
                continue
            if nome_norm == alvo or nome_norm in alvo:
                tamanho = len(nome_norm)
                if melhor is None or tamanho > melhor['_len']:
                    melhor = {'insumo_tipo': tipo, 'insumo_id': ins['id'], 'nome': ins['nome'], '_len': tamanho}
    if melhor:
        melhor.pop('_len', None)
    return melhor


_CUSTO_FIELDS = {
    'papel':      ('prec_papeis',        'custo_resma'),
    'acabamento': ('prec_acabamentos',   'custo_base'),
    'papelao':    ('prec_papelao',       'custo'),
    'midia':      ('prec_midias_bobina', 'custo_m2'),
}


def _nfe_parse_papel_nome(nome):
    """Extrai medida (mm -> cm) e folhas/pacote do nome do papel e devolve o nome LIMPO.
    Ex.: 'DUPLEX 250 GRS BATTAGLIA 660 X 960 MM C/ 150.0 FL' -> ('DUPLEX 250 GRS BATTAGLIA', 66.0, 96.0, 150)"""
    import re
    larg = alt = 0.0
    folhas = 0
    limpo = nome or ''
    m = re.search(r'(\d+(?:[.,]\d+)?)\s*[xX]\s*(\d+(?:[.,]\d+)?)\s*MM', limpo, re.IGNORECASE)
    if m:
        larg = round(float(m.group(1).replace(',', '.')) / 10.0, 1)
        alt  = round(float(m.group(2).replace(',', '.')) / 10.0, 1)
        limpo = limpo[:m.start()] + ' ' + limpo[m.end():]
    # extrai e remove o pacote "C/ 150.0 FL"
    mf = re.search(r'\bC/\s*(\d+(?:[.,]\d+)?)\s*FL\b', limpo, re.IGNORECASE)
    if mf:
        folhas = int(float(mf.group(1).replace(',', '.')))
    limpo = re.sub(r'\bC/\s*\d+(?:[.,]\d+)?\s*FL\b', '', limpo, flags=re.IGNORECASE)
    limpo = re.sub(r'\s+', ' ', limpo).strip(' -–—·,')
    return limpo, larg, alt, folhas


def nfe_criar_insumo(tipo, nome, custo):
    conn = get_db()
    c = conn.cursor()
    if tipo == 'papel':
        nome_limpo, larg, alt, folhas = _nfe_parse_papel_nome(nome)
        folhas = folhas or 500
        # custo recebido é por FOLHA (NF-e em FL); custo da resma = por folha × folhas do pacote
        c.execute("INSERT INTO prec_papeis (nome, largura, altura, folhas_resma, custo_resma) VALUES (?,?,?,?,?)",
                  (nome_limpo or nome, larg, alt, folhas, custo * folhas))
    elif tipo == 'acabamento':
        c.execute("INSERT INTO prec_acabamentos (nome, tipo, custo_base, unidade) VALUES (?,?,?,?)", (nome, 'job', custo, 'job'))
    elif tipo == 'papelao':
        c.execute("INSERT INTO prec_papelao (nome, custo) VALUES (?,?)", (nome, custo))
    elif tipo == 'midia':
        c.execute("INSERT INTO prec_midias_bobina (nome, custo_m2) VALUES (?,?)", (nome, custo))
    else:
        conn.close()
        return None
    new_id = c.lastrowid
    conn.commit()
    conn.close()
    return new_id


def nfe_importar(header, itens_mapeados):
    conn = get_db()
    c = conn.cursor()
    c.execute(
        "INSERT INTO nfe_importacoes (cnpj_emitente, nome_emitente, numero_nf, data_emissao, valor_total, n_itens) VALUES (?,?,?,?,?,?)",
        (header['cnpj'], header['nome'], header['numero_nf'], header['data_emissao'], header['valor_total'], len(itens_mapeados))
    )
    for item in itens_mapeados:
        tipo = item['insumo_tipo']
        iid  = item['insumo_id']
        # upsert mapping
        c.execute(
            """INSERT INTO nfe_mapeamentos (cnpj_emitente, codigo_produto, insumo_tipo, insumo_id)
               VALUES (?,?,?,?)
               ON CONFLICT(cnpj_emitente, codigo_produto)
               DO UPDATE SET insumo_tipo=excluded.insumo_tipo, insumo_id=excluded.insumo_id""",
            (header['cnpj'], item['codigo'], tipo, iid)
        )
        # update insumo cost
        if tipo == 'papel':
            # NF-e vem em FL (valor por folha); custo_resma = valor/folha × folhas da resma cadastrada
            fr = c.execute("SELECT folhas_resma FROM prec_papeis WHERE id=?", (iid,)).fetchone()
            folhas = (fr[0] if fr and fr[0] else 1)
            c.execute("UPDATE prec_papeis SET custo_resma=? WHERE id=?", (item['valor_unit'] * folhas, iid))
        elif tipo in _CUSTO_FIELDS:
            table, field = _CUSTO_FIELDS[tipo]
            c.execute(f"UPDATE {table} SET {field}=? WHERE id=?", (item['valor_unit'], iid))
        # update stock (upsert: add qty)
        c.execute(
            """INSERT INTO estoque_insumos (insumo_tipo, insumo_id, qtd, unidade)
               VALUES (?,?,?,?)
               ON CONFLICT(insumo_tipo, insumo_id)
               DO UPDATE SET qtd=qtd+excluded.qtd, unidade=excluded.unidade,
                             updated_at=datetime('now','localtime')""",
            (tipo, iid, item['quantidade'], item['unidade'])
        )
    conn.commit()
    conn.close()


def nfe_get_historico():
    conn = get_db()
    rows = conn.execute("SELECT * FROM nfe_importacoes ORDER BY created_at DESC LIMIT 50").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def estoque_get_todos():
    conn = get_db()
    rows = conn.execute("""
        SELECT e.insumo_tipo, e.insumo_id, e.qtd, e.unidade, e.updated_at,
            CASE e.insumo_tipo
                WHEN 'papel'      THEN (SELECT nome FROM prec_papeis WHERE id=e.insumo_id)
                WHEN 'acabamento' THEN (SELECT nome FROM prec_acabamentos WHERE id=e.insumo_id)
                WHEN 'papelao'    THEN (SELECT nome FROM prec_papelao WHERE id=e.insumo_id)
                WHEN 'midia'      THEN (SELECT nome FROM prec_midias_bobina WHERE id=e.insumo_id)
            END AS nome
        FROM estoque_insumos e
        ORDER BY e.insumo_tipo, nome
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ─── AUTENTICAÇÃO ────────────────────────────────────────────────────────────

def auth_get_usuario_by_login(login):
    conn = get_db()
    row = conn.execute("SELECT * FROM usuarios WHERE login = ? AND ativo = 1", (login,)).fetchone()
    conn.close()
    return dict(row) if row else None

def auth_verificar_senha(usuario, senha):
    return check_password_hash(usuario['senha_hash'], senha)

def auth_get_usuarios():
    conn = get_db()
    rows = conn.execute(
        "SELECT id, nome, login, nivel, ativo, created_at FROM usuarios ORDER BY nome"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def auth_get_usuario(id):
    conn = get_db()
    row = conn.execute(
        "SELECT id, nome, login, nivel, ativo FROM usuarios WHERE id = ?", (id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None

def auth_criar_usuario(form):
    conn = get_db()
    conn.execute(
        "INSERT INTO usuarios (nome, login, senha_hash, nivel) VALUES (?, ?, ?, ?)",
        (form.get('nome'), form.get('login'),
         generate_password_hash(form.get('senha'), method='pbkdf2:sha256'), form.get('nivel', 'operador'))
    )
    conn.commit()
    conn.close()

def auth_atualizar_usuario(id, form):
    conn = get_db()
    nova_senha = form.get('senha', '').strip()
    if nova_senha:
        conn.execute(
            "UPDATE usuarios SET nome=?, login=?, senha_hash=?, nivel=? WHERE id=?",
            (form.get('nome'), form.get('login'),
             generate_password_hash(nova_senha, method='pbkdf2:sha256'), form.get('nivel', 'operador'), id)
        )
    else:
        conn.execute(
            "UPDATE usuarios SET nome=?, login=?, nivel=? WHERE id=?",
            (form.get('nome'), form.get('login'), form.get('nivel', 'operador'), id)
        )
    conn.commit()
    conn.close()

def auth_toggle_usuario(id, ativo):
    conn = get_db()
    conn.execute("UPDATE usuarios SET ativo=? WHERE id=?", (ativo, id))
    conn.commit()
    conn.close()
