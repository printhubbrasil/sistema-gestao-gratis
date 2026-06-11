# Sistema de Gestão para Gráficas — Inicialização para o Claude

Este arquivo é lido automaticamente pelo Claude Code ao abrir o projeto.
Ele instrui o Claude sobre como ajudar qualquer pessoa a configurar, usar e personalizar este sistema.

---

## O que é este sistema

Sistema web completo para gestão de gráficas e impressoras digitais, desenvolvido em Python + Flask + SQLite.

**O que ele faz:**
- Calcula custo e preço de venda de qualquer produto gráfico (papel, flexíveis, acrílico, encadernados, apostilas)
- Gera orçamentos com PDF imprimível e link de WhatsApp
- Controla pedidos e fila de produção
- Cadastra clientes com histórico completo, cadastro rápido em modal e autopreenchimento por CNPJ (BrasilAPI)
- Gerencia produtos (com foto e preço por faixa de quantidade), estoque de insumos e fornecedores
- Importa XML de NF-e de fornecedor para atualizar custo e estoque dos insumos
- Controla financeiro: caixa, despesas, contas a pagar, ponto de equilíbrio
- Personalização pelo painel: nome, cidade, telefone, site e logo da empresa (logo sai nos PDFs)
- Suporta múltiplos usuários com níveis de acesso (admin / operador)
- Faz backup do banco de dados direto pelo painel

**Tecnologias:**
- Backend: Python 3 + Flask
- Banco de dados: SQLite (arquivo local, zero configuração)
- Frontend: HTML + CSS + JavaScript puro (sem frameworks externos)
- Templates: Jinja2

**Não requer:** Docker, banco externo, serviços em nuvem, Node.js, npm.

---

## FLUXO DE PRIMEIRO USO — siga esta ordem obrigatoriamente

Quando o usuário pedir ajuda para configurar ou rodar o sistema pela primeira vez, execute cada passo abaixo em sequência. Não pule etapas.

---

### ETAPA 1 — Apresentação

Apresente-se e explique o que vai acontecer. Use uma linguagem acolhedora e direta. Exemplo:

> "Olá! Vou te ajudar a configurar o sistema de gestão da sua gráfica. São só algumas perguntas e em poucos minutos o sistema vai estar rodando no seu computador. Vamos lá?"

---

### ETAPA 2 — Coletar dados da empresa

Pergunte **tudo de uma vez**, em uma única mensagem, para não deixar o usuário esperando várias rodadas de perguntas:

1. **Nome da empresa** — como vai aparecer nos orçamentos e pedidos (ex: Gráfica Central)
2. **Cidade e estado** — no formato "Cidade — UF" (ex: Campinas — SP)
3. **Telefone** — com DDD (ex: (19) 99999-9999)
4. **Site** — domínio da empresa, ou "não tenho" se não tiver
5. **Nome do usuário admin** — sugestão: `admin` (pode ser qualquer palavra sem espaço)
6. **Senha de acesso** — mínimo 8 caracteres, ela vai usar para entrar no sistema

---

### ETAPA 3 — Verificar pré-requisitos

Antes de instalar qualquer coisa, verifique se o Python 3 está instalado:

```bash
python3 --version
```

- Se retornar `Python 3.10` ou superior: perfeito, pode continuar.
- Se retornar erro ou versão inferior: oriente o usuário a instalar o Python 3 em **python.org/downloads** antes de continuar.

---

### ETAPA 4 — Criar o ambiente virtual e instalar dependências

Execute em sequência:

```bash
python3 -m venv venv
```

Ativar o ambiente:
```bash
# macOS / Linux:
source venv/bin/activate

# Windows:
venv\Scripts\activate
```

Instalar dependências:
```bash
pip install -r requirements.txt
```

Se der erro de permissão no Windows, tente:
```bash
pip install -r requirements.txt --user
```

---

### ETAPA 5 — Criar o arquivo .env

Gere uma SECRET_KEY aleatória:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Crie o arquivo `.env` na raiz do projeto com os dados coletados na Etapa 2:

```
SECRET_KEY=<chave gerada acima>
EMPRESA_NOME=<nome da empresa>
EMPRESA_CIDADE=<cidade — UF>
EMPRESA_TELEFONE=<telefone>
EMPRESA_SITE=<site ou deixar em branco>
DATABASE_PATH=grafica.db
```

**Importante:** nunca commite o `.env` no git — ele já está no `.gitignore`.

---

### ETAPA 6 — Personalizar o usuário administrador

Edite a linha do usuário padrão em `database.py` (linha próxima de `INSERT INTO usuarios`):

```python
('Administrador', '<login escolhido>', generate_password_hash('<senha escolhida>', method='pbkdf2:sha256'), 'admin')
```

Substitua `<login escolhido>` e `<senha escolhida>` pelos dados informados na Etapa 2.

> **Atenção:** isso só funciona se o banco `grafica.db` ainda não existir. Se ele já existir (sistema já rodou antes), oriente o usuário a ir em Admin → Gerenciar Usuários → Editar para trocar a senha.

---

### ETAPA 7 — Iniciar o sistema

```bash
python3 app.py
```

O terminal deve mostrar algo como:
```
* Running on http://127.0.0.1:5001
```

Abra o navegador em: **http://localhost:5001**

A tela de login deve aparecer com o nome da empresa que foi configurado.

> **Windows:** alternativamente, dê dois cliques no `iniciar.bat` na pasta do projeto — ele instala o Flask se faltar e inicia o sistema.

---

### ETAPA 8 — Confirmar que funcionou

Verifique:
- [ ] A tela de login apareceu com o nome correto da empresa
- [ ] O login com usuário e senha configurados funcionou
- [ ] O dashboard abriu sem erros

Se qualquer item falhar, leia o erro no terminal e resolva antes de continuar. Os erros mais comuns estão na seção de Solução de Problemas mais abaixo.

---

### ETAPA 9 — Orientação inicial de uso

Após confirmar que o sistema está funcionando, explique brevemente os próximos passos para o usuário começar a usar:

1. **Personalizar a empresa** → Admin → Personalização (nome, cidade, telefone, site e logo — o logo aparece nos PDFs)
2. **Configurar máquinas e papéis** → Precificação → Configurações
3. **Cadastrar primeiros clientes** → Clientes → Novo Cliente
4. **Testar um orçamento** → Orçamentos → Novo Orçamento
5. **Trocar a senha** → Admin → Gerenciar Usuários → Editar (recomendado fazer agora)

---

## ESTRUTURA DO PROJETO

```
sistema-grafica/
│
├── app.py                  # Todas as rotas e lógica da aplicação
├── database.py             # Funções de acesso ao banco SQLite
├── requirements.txt        # Dependências Python
├── .env                    # Configurações locais (não vai pro git)
├── .env.example            # Modelo do .env para novos usuários
├── .gitignore              # Arquivos ignorados pelo git
├── CLAUDE.md               # Este arquivo
├── README.md               # Documentação pública
│
├── static/
│   ├── css/
│   │   └── style.css       # Todo o CSS do sistema
│   └── uploads/            # Logo da empresa e fotos de produtos (criada em runtime)
│
└── templates/
    ├── base.html           # Layout base (navbar, sidebar, estrutura)
    ├── login.html          # Tela de login
    ├── home.html           # Dashboard principal
    ├── personalizacao.html # Nome, dados e logo da empresa
    ├── _modal_cliente.html # Modal de cadastro rápido de cliente (reutilizável)
    │
    ├── clientes/
    │   ├── lista.html
    │   └── form.html
    │
    ├── orcamentos/
    │   ├── lista.html
    │   ├── form.html
    │   ├── detalhe.html
    │   └── imprimir.html   # PDF do orçamento
    │
    ├── pedidos/
    │   ├── lista.html
    │   ├── form.html
    │   ├── detalhe.html
    │   └── imprimir.html
    │
    ├── precificacao/
    │   ├── index.html
    │   ├── calculadora.html  # Calculadora de custo (principal)
    │   ├── configuracoes.html
    │   ├── resultado.html
    │   └── ficha.html        # Ficha interna de custo
    │
    ├── produtos/
    │   ├── lista.html
    │   └── form.html
    │
    ├── financeiro/
    │   ├── resumo.html
    │   ├── caixa.html
    │   ├── fornecedores.html
    │   └── form_fornecedor.html
    │
    ├── custos/
    │   ├── index.html      # Despesas variáveis
    │   └── contas.html     # Contas a pagar
    │
    ├── nfe/
    │   └── importar.html   # Importação de XML de NF-e
    │
    ├── notasfiscais/
    │   └── emissao.html    # Notas emitidas para clientes
    │
    ├── producao/
    │   └── fila.html
    │
    └── admin/
        ├── usuarios.html
        └── form_usuario.html
```

---

## MAPA DE ROTAS

| Rota | Função em app.py | Descrição |
|------|-----------------|-----------|
| `/` | `home()` | Dashboard |
| `/clientes` | `clientes()` | Lista de clientes |
| `/clientes/novo` | `novo_cliente()` | Cadastrar cliente |
| `/orcamentos` | `orcamentos()` | Lista de orçamentos |
| `/orcamentos/novo` | `novo_orcamento()` | Criar orçamento |
| `/pedidos` | `pedidos()` | Fila de pedidos |
| `/precificacao` | `precificacao()` | Histórico de cálculos |
| `/precificacao/calculadora` | `calculadora()` | Calculadora de custo |
| `/precificacao/configuracoes` | `prec_configuracoes()` | Configurar papéis, máquinas, acabamentos |
| `/precificacao/ponto-equilibrio` | `ponto_equilibrio()` | Análise de custos fixos |
| `/produtos` | `produtos()` | Catálogo de produtos |
| `/financeiro` | `financeiro()` | Resumo financeiro |
| `/custos` | `custos()` | Despesas variáveis |
| `/custos/contas` | `contas_pagar()` | Contas a pagar |
| `/nfe/importar` | `nfe_importar()` | Importar XML de NF-e |
| `/notasfiscais` | `notasfiscais()` | Notas emitidas p/ clientes |
| `/personalizacao` | `personalizacao()` | Nome, dados e logo da empresa |
| `/admin/usuarios` | `admin_usuarios()` | Gerenciar usuários |
| `/admin/backup/download` | `admin_backup_download()` | Baixar backup do banco |
| `/login` | `login()` | Tela de login |
| `/logout` | `logout()` | Logout |

---

## COMO FAZER MODIFICAÇÕES COMUNS

### Alterar cores do sistema
Edite as variáveis no topo de `static/css/style.css`:
```css
:root {
  --primaria: #E94560;      /* cor principal (botões, destaques) */
  --secundaria: #F5A623;    /* cor secundária (laranja) */
  --sucesso: #10B981;       /* verde */
  --aviso: #F59E0B;         /* amarelo de alerta */
  --perigo: #EF4444;        /* vermelho de erro */
  --fundo: #F1F5F9;         /* fundo da página */
  --card-bg: #FFFFFF;       /* fundo dos cards */
  --sidebar-bg: #16213E;    /* fundo da barra lateral */
}
```

### Adicionar campo em orçamentos
1. `templates/orcamentos/form.html` — adicionar o input no formulário
2. `templates/orcamentos/imprimir.html` — mostrar o campo no PDF
3. `database.py` — adicionar a coluna na tabela `orcamentos` e nas funções `salvar_orcamento` e `get_orcamento`
4. `app.py` — passar o novo campo no `request.form` dentro da rota `/orcamentos/novo`

### Adicionar novo módulo (ex: agenda de entregas)
1. Crie `templates/entregas/lista.html` e `templates/entregas/form.html`
2. Adicione as funções de banco em `database.py`
3. Adicione as rotas em `app.py`
4. Adicione o link no menu em `templates/base.html`

### Alterar o nome da empresa sem editar código
Vá em **Admin → Personalização** no próprio painel: nome, cidade, telefone, site e logo, sem reiniciar nada. O que for salvo ali tem prioridade sobre o `.env` (que segue valendo como padrão inicial).

### Criar novo usuário
Admin → Gerenciar Usuários → Novo Usuário. Escolha o nível:
- **Admin**: acesso total, incluindo configurações e backup
- **Operador**: acesso ao dia a dia (clientes, pedidos, orçamentos), sem configurações

---

## CONFIGURAÇÃO DA CALCULADORA DE CUSTO

A calculadora é o coração do sistema. Antes de calcular qualquer coisa, o usuário precisa cadastrar:

**Em Precificação → Configurações:**

1. **Papéis** — nome, gramatura, tamanho, custo por folha ou por m²
2. **Máquinas** — nome, tipo (click/m²), custo por click ou por m²
3. **Acabamentos** — laminação, wire-o, verniz, corte, etc.
4. **Configurações gerais** — markup padrão, mão de obra por hora, overhead

**Tipos de produto que a calculadora suporta:**
- **Papel Impresso** — toner digital, flyer, cartão, folder
- **Flexíveis** — banner, adesivo, lona, UV plano (custo por m²)
- **Acrílico UV** — chapas com impressão UV plana
- **Encadernados** — livros com miolo + capa, múltiplos componentes
- **Apostilas** — miolo impresso com capa plástica ou impressa, opção de espiral

---

## BACKUP E SEGURANÇA

**Fazer backup manual:**
Admin → Gerenciar Usuários → botão "Baixar Backup" — faz download do arquivo `grafica_backup_YYYY-MM-DD.db`

**Restaurar backup:**
Renomeie o arquivo baixado para `grafica.db` e substitua o arquivo na pasta do sistema. Reinicie o servidor.

**Segurança do login:**
- O sistema bloqueia o IP após 5 tentativas erradas de login por 15 minutos
- As senhas são armazenadas com hash pbkdf2:sha256 (nunca em texto puro)
- A sessão expira em 8 horas de inatividade

---

## USAR EM REDE LOCAL (vários computadores)

Para que outros computadores da mesma rede acessem o sistema, edite a última linha do `app.py`:

```python
# Antes:
app.run(debug=False, port=5001)

# Depois:
app.run(host='0.0.0.0', debug=False, port=5001)
```

Os outros computadores acessam pelo IP da máquina que roda o servidor:
```
http://192.168.x.x:5001
```

Para descobrir o IP da máquina servidora:
```bash
# macOS / Linux:
ifconfig | grep "inet " | grep -v 127.0.0.1

# Windows:
ipconfig | findstr "IPv4"
```

---

## SOLUÇÃO DE PROBLEMAS

### "Address already in use" ao iniciar
Outro processo está usando a porta 5001. Encerre-o ou troque a porta em `app.py`:
```python
app.run(debug=False, port=5002)  # troque para qualquer porta livre
```

### Tela em branco ou sem estilo (CSS não carrega)
Verifique se o servidor está rodando (`python3 app.py` no terminal). Se estiver rodando em VPS com nginx, consulte a seção de Deploy no README.md — há uma configuração específica de nginx necessária para os arquivos estáticos.

### "ModuleNotFoundError: No module named 'flask'"
O ambiente virtual não está ativo. Execute:
```bash
source venv/bin/activate   # macOS / Linux
venv\Scripts\activate      # Windows
```
Depois tente `python3 app.py` novamente.

### Login não funciona com a senha definida
Se o banco `grafica.db` já existia antes de editar o `database.py`, a senha padrão continua sendo `admin123`. Acesse com essa senha e troque em Admin → Gerenciar Usuários → Editar.

### Dados não aparecem após reiniciar
Normal — o banco SQLite persiste os dados automaticamente. Se os dados sumiram, pode ter ocorrido um erro ao criar o banco. Verifique se o arquivo `grafica.db` existe na pasta do projeto.

### Erro 500 (Internal Server Error)
Leia o erro completo no terminal onde o servidor está rodando — ele indica exatamente o que falhou.

---

## BOAS PRÁTICAS AO MODIFICAR O SISTEMA

- Sempre reinicie o servidor após editar `app.py` ou `database.py`
- Faça backup do `grafica.db` antes de qualquer modificação no banco
- Templates HTML não precisam reiniciar o servidor — recarregue o navegador (F5)
- O arquivo `static/css/style.css` também não precisa reiniciar — use Ctrl+Shift+R para forçar o recarregamento do cache no navegador
- Nunca commite `.env` ou `grafica.db` no git
- Se for hospedar em VPS, use uma `SECRET_KEY` longa e aleatória — nunca use a padrão

---

## QUANDO O USUÁRIO PEDIR PARA ADICIONAR FUNCIONALIDADES

Siga este padrão para qualquer nova funcionalidade:

1. **Entenda o requisito** — pergunte o que o usuário quer ver e como quer usar
2. **Planeje o banco** — adicione tabelas/colunas em `database.py` com migration segura (use `ALTER TABLE` ou `CREATE TABLE IF NOT EXISTS`)
3. **Crie as rotas** — adicione em `app.py` seguindo o padrão GET/POST existente
4. **Crie os templates** — siga o estilo visual de `base.html` usando `{% extends 'base.html' %}`
5. **Teste** — verifique que funciona antes de declarar pronto
6. **Não quebre o existente** — teste as funcionalidades adjacentes após cada mudança
