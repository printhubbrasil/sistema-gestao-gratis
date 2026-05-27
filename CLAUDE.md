# Sistema de Gestão para Gráficas — Guia para o Claude

Este arquivo instrui o Claude Code sobre como ajudar uma nova pessoa a configurar e usar este sistema.

---

## Contexto do projeto

Sistema web completo para gestão de gráficas, desenvolvido em Python + Flask + SQLite.
Roda localmente no computador ou em um servidor VPS.
Não requer banco de dados externo, serviços em nuvem, nem configuração complexa.

Arquivos principais:
- `app.py` — rotas e lógica da aplicação
- `database.py` — acesso ao banco SQLite (criado automaticamente no primeiro uso)
- `templates/` — páginas HTML com Jinja2
- `static/css/style.css` — estilos
- `.env` — configurações da empresa (criado pelo usuário a partir do `.env.example`)

---

## Instruções para o Claude — Primeiro uso

Quando o usuário abrir este repositório pela primeira vez e pedir ajuda para configurar ou rodar o sistema, siga este fluxo obrigatoriamente:

### Passo 1 — Boas-vindas e coleta de dados

Apresente-se e explique o que vai acontecer. Em seguida, pergunte ao usuário os dados da empresa dele. Colete **tudo de uma vez** antes de criar qualquer arquivo:

1. **Nome da empresa** (ex: Gráfica Central)
2. **Cidade e estado** (ex: Campinas — SP)
3. **Telefone** (ex: (19) 99999-9999)
4. **Site** (ex: graficacentral.com.br) — pode ser "sem site" se não tiver
5. **Usuário de login** que quer usar no sistema (padrão sugerido: `admin`)
6. **Senha de acesso** que quer usar (mínimo 6 caracteres)

### Passo 2 — Criar o arquivo .env

Com os dados coletados, crie o arquivo `.env` na raiz do projeto:

```
SECRET_KEY=<gere uma chave aleatória com: python3 -c "import secrets; print(secrets.token_hex(32))">
EMPRESA_NOME=<nome da empresa>
EMPRESA_CIDADE=<cidade — UF>
EMPRESA_TELEFONE=<telefone>
EMPRESA_SITE=<site ou em branco>
DATABASE_PATH=grafica.db
```

Gere a `SECRET_KEY` automaticamente via terminal — não peça para o usuário criar.

### Passo 3 — Personalizar o usuário admin no banco

Edite a linha do usuário padrão em `database.py` para usar o login e senha que o usuário escolheu:

```python
('Administrador', '<login escolhido>', generate_password_hash('<senha escolhida>', method='pbkdf2:sha256'), 'admin')
```

> Isso só tem efeito se o banco ainda não foi criado. Se o banco `grafica.db` já existir, oriente o usuário a acessar Admin → Gerenciar Usuários → Editar para trocar a senha.

### Passo 4 — Instalar dependências e rodar

Execute em sequência:

```bash
python3 -m venv venv
source venv/bin/activate        # macOS / Linux
# ou: venv\Scripts\activate     # Windows
pip install -r requirements.txt
python3 app.py
```

Após o servidor iniciar, abra o navegador em: **http://localhost:5001**

### Passo 5 — Confirmar que funcionou

Verifique se o sistema abriu com o nome da empresa correto na tela de login.
Se não abriu, verifique os erros no terminal e resolva antes de continuar.

---

## Comportamento geral ao trabalhar neste projeto

- Sempre que modificar `app.py`, `database.py` ou qualquer template, reinicie o servidor para as mudanças fazerem efeito (`Ctrl+C` e `python3 app.py` novamente).
- O banco de dados `grafica.db` é criado automaticamente na primeira vez que o sistema roda. Nunca commite esse arquivo no git — ele já está no `.gitignore`.
- O arquivo `.env` contém dados sensíveis — nunca commite esse arquivo no git — ele já está no `.gitignore`.
- Para modificar o visual, edite `static/css/style.css`.
- Para adicionar ou alterar páginas, edite os arquivos em `templates/`.
- Para adicionar novas rotas, edite `app.py` e crie a função + template correspondente.

---

## Estrutura de módulos

| Módulo | Rota | Descrição |
|---|---|---|
| Home / Dashboard | `/` | Resumo geral |
| Clientes | `/clientes` | Cadastro e histórico |
| Orçamentos | `/orcamentos` | Criação e impressão |
| Pedidos | `/pedidos` | Fila de produção |
| Precificação | `/precificacao` | Calculadora de custo e configurações |
| Produtos | `/produtos` | Catálogo |
| Financeiro | `/financeiro` | Caixa, contas, fornecedores |
| Ponto de Equilíbrio | `/precificacao/ponto-equilibrio` | Custos fixos e análise |
| Admin | `/admin/usuarios` | Gerenciar usuários |

---

## Dicas para personalização comum

**Trocar o nome da empresa sem reiniciar:** edite o `.env` e reinicie o servidor.

**Adicionar um novo campo em orçamentos:** edite `templates/orcamentos/form.html` para o formulário e `templates/orcamentos/imprimir.html` para o PDF imprimível.

**Mudar cores:** as variáveis CSS ficam no topo de `static/css/style.css` — procure por `:root {`.

**Fazer backup dos dados:** acesse Admin → Gerenciar Usuários → botão "Baixar Backup" — faz download do banco SQLite com todos os dados.
