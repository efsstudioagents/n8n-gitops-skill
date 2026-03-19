# n8n GitOps — Claude Code Skill

> GitOps para instâncias n8n: backup incremental de workflows no GitHub, estrutura de repositórios OPS/ADM por cliente, e automação de setup.

Skill para agências e times que gerenciam **múltiplas instâncias n8n para diferentes clientes**, usando GitHub como repositório central de workflows, documentação e infraestrutura.

---

## O que essa skill faz

- **Backup incremental automático** — salva workflows do n8n no GitHub apenas quando há mudanças (compara `versionId`), em formato JSON importável direto no n8n, sem wrappers
- **Estrutura GitOps por cliente** — dois repos por cliente: `n8n-{cliente}` (OPS, acesso do time) e `n8n-{cliente}-adm` (ADM, acesso restrito)
- **Setup automatizado** — script Python que cria toda a estrutura de repos e arquivos em segundos
- **Diagnóstico de bugs** — guia para corrigir os problemas mais comuns (backup salvando tudo toda vez, loop infinito por slug duplicado)
- **Schema Supabase** — padrão de tabelas base para agentes de IA com pgvector para RAG

---

## Instalação

### 1. Copiar a skill para o diretório do Claude Code

```bash
cp -r n8n-gitops-skill ~/.claude/skills/n8n-gitops
```

### 2. Criar o slash command `/n8n`

```bash
mkdir -p ~/.claude/commands
```

Crie o arquivo `~/.claude/commands/n8n.md`:

```markdown
---
description: Gerencia n8n + GitHub (backup, clientes, repos ADM/OPS)
argument-hint: "[setup-cliente --org {org} --cliente xyz --nome 'Nome'] | [fix-backup] | [status]"
allowed-tools: Bash(python*), Bash(curl*), Bash(cat*)
---

Você é um especialista em n8n GitOps. Leia o guia da skill:

<skill>
@~/.claude/skills/n8n-gitops/SKILL.md
</skill>

O usuário digitou: `$ARGUMENTS`

Se os argumentos contiverem `setup-cliente`: extraia --org, --cliente e --nome e execute:
`python ~/.claude/skills/n8n-gitops/scripts/setup_cliente.py --org {org} --cliente {cliente} --nome "{nome}"`

Se os argumentos contiverem `fix-backup`: siga o processo da skill para corrigir o workflow de backup.

Se vazio ou `status`: liste o que a skill pode fazer.

Para qualquer outra tarefa n8n/GitHub: execute diretamente usando o conhecimento da skill.
```

### 3. Salvar o GitHub token

```bash
mkdir -p ~/.config/n8n-gitops
echo "ghp_seu_token_aqui" > ~/.config/n8n-gitops/github-token
chmod 600 ~/.config/n8n-gitops/github-token
```

### 4. Reiniciar o Claude Code

O comando `/n8n` aparece no autocomplete após reiniciar.

---

## Uso

### Criar estrutura para novo cliente

```bash
# Via slash command
/n8n setup-cliente --org minha-empresa --cliente xyz --nome "Empresa XYZ"

# Via script direto
python ~/.claude/skills/n8n-gitops/scripts/setup_cliente.py \
  --org minha-empresa \
  --cliente xyz \
  --nome "Empresa XYZ"
```

Cria automaticamente:

**`n8n-xyz` (OPS):**
```
README.md
context/companhia_example.md
context/produtos_example.md
agentes/nome-funcao_example/
  escopo_example.md
  esquema_example.md
  changelog_example.md
  prompt/
    v1.0_example.md
    changelog.md
workflows/
```

**`n8n-xyz-adm` (ADM):**
```
README.md
infra/vps.md
acessos/credenciais.md
sql/schema.md     ← tabelas base + pgvector
sql/queries.md
```

### Corrigir workflow de backup

```
/n8n fix-backup
```

### Ver o que a skill pode fazer

```
/n8n
```

---

## Workflow de Backup n8n → GitHub

O arquivo `workflows/n8n-backup-gitops.json` contém o workflow pronto para importar no n8n.

**Como configurar após importar:**

### 1. Configurar a API do n8n

Nos nós `1. Listar Workflows` e `6. Export Completo`, preencha:
- **URL** → endereço da sua instância n8n (`https://n8n.seudominio.com/api/v1/workflows`)
- **X-N8N-API-KEY** → sua API Key (Settings → API → Create API Key)

### 2. Conectar o GitHub

Nos nós `3. Buscar GitHub`, `8b. Editar GitHub` e `8c. Criar GitHub`, selecione sua credencial **GitHub API** e ajuste a URL do repo:

```
https://api.github.com/repos/SEU_USUARIO/SEU_REPOSITORIO/contents/...
```

### 3. Notificação (opcional)

O nó `10. Notificar (WhatsApp)` usa a Evolution API. Conecte sua credencial ou remova o nó se não usar.

O backup roda toda sexta-feira às 3h e salva apenas os workflows que foram modificados desde o último backup.

---

**Lógica de pastas (tag-based):**

Os workflows são organizados automaticamente por tag — nenhum mapeamento manual necessário.

| Situação | Pasta |
|---|---|
| Workflow tem tag `cliente-xyz` | `workflows/cliente-xyz/` |
| Workflow tem múltiplas tags | primeira tag = pasta principal |
| Sem nenhuma tag | `workflows/Uncategorized/` |

Toda tag nova vira pasta automaticamente.

---

## Estrutura dos Repos

```
n8n-{cliente}/           → OPS (acesso do time)
  agentes/               → Um diretório por agente
    nome-funcao/
      escopo.md          → O que o agente faz e não faz
      esquema.md         → Queries e estrutura de dados
      changelog.md       → Histórico geral do agente (escopo, esquema, regras)
      prompt/
        v1.0.md          → Prompt versionado
        changelog.md     → Histórico de versões do prompt
  context/               → Contexto da empresa
    companhia.md
    produtos.md
  workflows/             → Backup automático (JSON importável)

n8n-{cliente}-adm/       → ADM (acesso restrito)
  infra/
    vps.md               → Servidores e Docker Compose
  acessos/
    credenciais.md       → API keys e logins
  sql/
    schema.md            → CREATE TABLE statements
    queries.md           → Queries importantes
```

---

## Créditos

Criado por [Erick Fonseca](https://www.instagram.com/erick.fonsec/) · [EFS Studio](https://efsstudio.com.br).

Licença MIT — use, modifique e distribua livremente.
