# Sistema de Gestão para Gráficas

Sistema web completo para gestão de gráficas e impressoras — orçamentos, pedidos, precificação, clientes, estoque e financeiro.

Desenvolvido com Python + Flask + SQLite. Roda localmente no navegador, sem dependências externas.

---

## Funcionalidades

- **Precificação** — calculadora de custo para papel/toner, flexíveis (m²), acrílico UV, encadernados e apostilas
- **Orçamentos** — geração com PDF imprimível e envio por WhatsApp
- **Pedidos** — controle de fila de produção
- **Clientes** — cadastro com histórico, cadastro rápido em qualquer tela e autopreenchimento por CNPJ (BrasilAPI, gratuita)
- **Produtos e Estoque** — catálogo com foto, preço por faixa de quantidade e controle de insumos
- **Importação de NF-e** — suba o XML da nota do fornecedor e atualize custo e estoque dos insumos automaticamente
- **Financeiro** — caixa, despesas, contas a pagar e ponto de equilíbrio
- **Personalização** — nome, cidade, telefone, site e logo da empresa configuráveis pelo painel (logo sai nos PDFs)
- **Usuários** — múltiplos usuários com níveis de acesso (admin / operador)
- **Backup** — download do banco de dados direto pelo painel

---

## Requisitos

- Python 3.10 ou superior
- pip

---

## Instalação

### 1. Clone o repositório

```bash
git clone https://github.com/printhubbrasil/sistema-gestao-gratis.git
cd sistema-gestao-gratis
```

### 2. Crie um ambiente virtual

```bash
python3 -m venv venv
source venv/bin/activate      # Linux / macOS
venv\Scripts\activate         # Windows
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente

```bash
cp .env.example .env
```

Edite o arquivo `.env` com os dados da sua empresa:

```
SECRET_KEY=sua-chave-secreta-aqui
EMPRESA_NOME=Minha Gráfica
EMPRESA_CIDADE=São Paulo — SP
EMPRESA_TELEFONE=(11) 99999-9999
EMPRESA_SITE=minhagrafica.com.br
```

> Gere uma `SECRET_KEY` segura com:
> ```bash
> python3 -c "import secrets; print(secrets.token_hex(32))"
> ```

### 5. Inicie o sistema

```bash
python3 app.py
```

Acesse no navegador: **http://localhost:5001**

---

## Primeiro acesso

Login padrão criado automaticamente:

| Campo | Valor |
|-------|-------|
| Usuário | `admin` |
| Senha | `admin123` |

**Troque a senha imediatamente** em: Admin → Gerenciar Usuários → Editar.

Depois, configure a identidade da empresa (nome, cidade, telefone, site e logo) em: **Admin → Personalização** — sem precisar editar código nem reiniciar.

---

## Estrutura do projeto

```
sistema-grafica/
├── app.py              # Rotas Flask
├── database.py         # Acesso ao banco SQLite
├── requirements.txt    # Dependências Python
├── .env.example        # Modelo de configuração
├── static/
│   ├── css/            # Estilos
│   └── uploads/        # Logo da empresa e fotos de produtos
└── templates/          # Páginas HTML (Jinja2)
    ├── base.html
    ├── login.html
    ├── personalizacao.html
    ├── _modal_cliente.html
    ├── clientes/
    ├── pedidos/
    ├── orcamentos/
    ├── precificacao/
    ├── produtos/
    ├── financeiro/
    ├── custos/
    ├── nfe/
    ├── notasfiscais/
    ├── producao/
    └── admin/
```

---

## Uso em rede local

Para acessar de outros computadores na mesma rede, edite a última linha do `app.py`:

```python
app.run(host='0.0.0.0', port=5001, debug=False)
```

Os outros computadores acessam pelo IP da máquina que roda o servidor, ex: `http://192.168.1.100:5001`

---

## Deploy em VPS (produção)

Para rodar em servidor Linux com nginx + gunicorn:

### 1. Instale as dependências

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt gunicorn
```

### 2. Crie o serviço systemd

```ini
# /etc/systemd/system/sistema-grafica.service
[Unit]
Description=Sistema Grafica
After=network.target

[Service]
User=www-data
WorkingDirectory=/var/www/sistema-grafica
Environment=SCRIPT_NAME=/gestao
Environment=SECRET_KEY=sua-chave-secreta
Environment=DATABASE_PATH=grafica.db
Environment="EMPRESA_NOME=Minha Gráfica"
Environment="EMPRESA_CIDADE=Cidade — UF"
Environment="EMPRESA_TELEFONE=(00) 00000-0000"
Environment="EMPRESA_SITE=minhagrafica.com.br"
ExecStart=/var/www/sistema-grafica/venv/bin/gunicorn --workers 2 --bind 127.0.0.1:5002 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
systemctl daemon-reload
systemctl enable --now sistema-grafica
```

### 3. Configure o nginx

> ⚠️ **Atenção:** adicione o bloco dos arquivos estáticos **antes** das regras genéricas de cache `.css/.js`, caso contrário o sistema abrirá sem estilo.

```nginx
# Arquivos estáticos — deve vir ANTES de qualquer location ~* \.(css|js)
location ^~ /gestao/static/ {
    alias /var/www/sistema-grafica/static/;
    expires 30d;
    add_header Cache-Control "public";
}

# Aplicação
location /gestao/ {
    proxy_pass http://127.0.0.1:5002;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_redirect off;
}
```

O sistema ficará acessível em `https://seudominio.com/gestao/`.

---

## Licença

MIT — use, modifique e distribua livremente.
