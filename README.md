# Sistema de Gestão para Gráficas

Sistema web completo para gestão de gráficas e impressoras — orçamentos, pedidos, precificação, clientes, estoque e financeiro.

Desenvolvido com Python + Flask + SQLite. Roda localmente no navegador, sem dependências externas.

---

## Funcionalidades

- **Precificação** — calculadora de custo para papel/toner, flexíveis (m²), acrílico UV, encadernados e apostilas
- **Orçamentos** — geração com PDF imprimível e envio por WhatsApp
- **Pedidos** — controle de fila de produção
- **Clientes** — cadastro com histórico
- **Produtos e Estoque** — catálogo de produtos e controle de insumos
- **Financeiro** — contas a pagar e ponto de equilíbrio
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
git clone https://github.com/seu-usuario/sistema-grafica.git
cd sistema-grafica
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

---

## Estrutura do projeto

```
sistema-grafica/
├── app.py              # Rotas Flask
├── database.py         # Acesso ao banco SQLite
├── requirements.txt    # Dependências Python
├── .env.example        # Modelo de configuração
├── static/
│   └── css/            # Estilos
└── templates/          # Páginas HTML (Jinja2)
    ├── base.html
    ├── login.html
    ├── clientes/
    ├── pedidos/
    ├── orcamentos/
    ├── precificacao/
    ├── produtos/
    ├── financeiro/
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

## Licença

MIT — use, modifique e distribua livremente.
