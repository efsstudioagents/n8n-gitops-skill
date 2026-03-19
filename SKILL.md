---
name: efs-n8n-github
description: |
  Gerenciamento de workflows n8n e estrutura de repositórios GitHub para a EFS Studio e seus clientes.
  Use esta skill sempre que o usuário mencionar: backup de workflows n8n, repositórios de clientes no GitHub,
  estrutura ADM/OPS, corrigir bug de backup incremental, criar repo para novo cliente, migrar workflows,
  acessar API do n8n da EFS ou de clientes, atualizar nós de workflow, extrair schema do Supabase,
  editar ou atualizar prompt de agente, criar nova versão de prompt, criar ou atualizar changelog de prompt,
  ou qualquer tarefa que envolva o GitHub da efsstudioagents ou as instâncias n8n.efsstudioagents.com
  e n8n-{cliente}.efsstudioagents.com.
---

# EFS Studio — n8n + GitHub

## Configuração Inicial

**Antes de executar qualquer tarefa**, verificar se as configurações do usuário estão disponíveis. Se não estiverem, perguntar:

```
Para usar esta skill, preciso de algumas informações:

1. URL da instância n8n principal (ex: https://n8n.suaempresa.com)
2. API Key do n8n (Settings → API → Create API Key)
3. Organização/usuário no GitHub (ex: minhaempresa)
4. GitHub Token (com permissões de repo)
   → Salvar em: ~/.config/efsstudio/github-token
5. Padrão de URL para instâncias de clientes? (ex: https://n8n-{cliente}.suaempresa.com)
```

Após receber, usar esses valores em todas as chamadas da sessão.

---

## Credenciais e Acesso

**GitHub Token**: salvo em `~/.config/efsstudio/github-token`
```bash
GH_TOKEN=$(cat ~/.config/efsstudio/github-token)
```

> Se o arquivo não existir, pedir o token ao usuário e salvar:
> ```bash
> mkdir -p ~/.config/efsstudio
> echo "ghp_seu_token" > ~/.config/efsstudio/github-token
> ```

**n8n principal:**
- URL: fornecida pelo usuário na configuração inicial
- API Key: fornecida pelo usuário ou lida de `acessos/credenciais.md` no repo ADM

**n8n Clientes:**
- Padrão de URL: definido pelo usuário (ex: `https://n8n-{cliente}.suaempresa.com`)
- API keys: pedir ao usuário (cada instância tem a sua)

**Chamadas n8n:**
```bash
curl -s "{N8N_URL}/api/v1/workflows" \
  -H "X-N8N-API-KEY: {chave}"
```

---

## Estrutura de Repositórios GitHub

Cada cliente tem dois repos no GitHub (`efsstudioagents`):

```
n8n-{cliente}        → acesso geral do time (OPS)
n8n-{cliente}-adm    → acesso restrito, apenas heads (ADM)
```

### Repo OPS (`n8n-{cliente}`)
```
agentes/
  nome-funcao_example/       # exemplo de agente
    escopo_example.md        # O que o agente faz, limitações, regras
    esquema_example.md       # SQLs e queries necessárias
    changelog_example.md
    prompt/
      v1.0_example.md        # Base do prompt — template <AgentInstructions>
      changelog.md           # Histórico de versões do prompt
context/
  companhia_example.md       # Sobre a empresa
  produtos_example.md        # Produtos e serviços
workflows/                   # Backup automático toda sexta-feira via n8n
```

### Repo ADM (`n8n-{cliente}-adm`)
```
infra/
  vps.md             # Servidores, IPs, Docker Swarm compose files
acessos/
  credenciais.md     # API keys, logins de serviços (dados reais)
sql/
  schema.md          # CREATE TABLE statements completos
  queries.md         # Queries importantes e funções
```

---

## Repos Atuais

| Repo | Tipo | Conteúdo |
|------|------|----------|
| `n8n-efs` | OPS | EFS Studio — agentes, context, workflows (backup auto) |
| `n8n-efs-adm` | ADM | EFS Studio — infra (Docker Swarm), acessos, SQL (tabelas base) |
| `n8n-hbt` | OPS | Cliente HBT — agentes, context, workflows (backup auto) |
| `n8n-hbt-adm` | ADM | Cliente HBT — infra (stacks exclusivas + ref EFS), acessos, SQL (+ tabelas HBT) |

---

## Infraestrutura Compartilhada vs Exclusiva

- **Stacks compartilhadas** (documentadas em `n8n-efs-adm/infra/vps.md`):
  postgres, redis, rabbitmq, evolution_api
- **Stacks exclusivas EFS** (em `n8n-efs-adm`):
  n8n_editor, n8n_webhook, n8n_worker
- **Stacks exclusivas HBT** (em `n8n-hbt-adm`, com referência ao repo EFS):
  n8n_editor_hbt, n8n_webhook_hbt, n8n_worker_hbt
- **Redis DB isolation**: EFS usa DB=2, HBT usa DB=3

---

## Criar Estrutura para Novo Cliente (Automatizado)

Use o script `scripts/setup_cliente.py` para criar tudo de uma vez:

```bash
python ~/.claude/skills/efs-n8n-github/scripts/setup_cliente.py \
  --cliente xyz \
  --nome "Nome do Cliente"
```

O script cria automaticamente:
- Repos `n8n-xyz` (OPS) e `n8n-xyz-adm` (ADM) com descrições
- OPS: `README.md`, `context/companhia_example.md`, `context/produtos_example.md`, `agentes/nome-funcao_example/` completo com prompt base, `workflows/.gitkeep`
- ADM: `README.md`, `infra/vps.md`, `acessos/credenciais.md`, `sql/schema.md` (tabelas base + pgvector), `sql/queries.md`

Após rodar, preencher manualmente:
1. `acessos/credenciais.md` com credenciais reais
2. `infra/vps.md` com IP do servidor e número do Redis DB
3. `context/` com dados reais da empresa
4. Criar e configurar o workflow de backup no n8n do cliente
5. Adicionar tabelas específicas em `sql/schema.md`

---

## Criar Estrutura para Novo Cliente (Manual)

### 1. Criar repos
```bash
GH_TOKEN=$(cat ~/.config/efsstudio/github-token)
CLIENTE="xyz"  # 3 letras

# OPS
curl -s -X POST "https://api.github.com/user/repos" \
  -H "Authorization: token $GH_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"n8n-${CLIENTE}\",\"private\":true,\"description\":\"n8n workflows — ${CLIENTE} (OPS)\"}"

# ADM
curl -s -X POST "https://api.github.com/user/repos" \
  -H "Authorization: token $GH_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"n8n-${CLIENTE}-adm\",\"private\":true,\"description\":\"n8n infra e acessos — ${CLIENTE} (ADM)\"}"
```

### 2. Atualizar descrição de repo existente
```bash
/usr/bin/curl -s -X PATCH "https://api.github.com/repos/efsstudioagents/n8n-${CLIENTE}" \
  -H "Authorization: token $GH_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"description\":\"n8n workflows — ${CLIENTE} (OPS)\"}" | /usr/bin/jq -r '.description'
```

### 3. Criar arquivos base
Use a função auxiliar:
```bash
gh_create() {
  local repo=$1 path=$2 msg=$3 content=$4
  /usr/bin/curl -s -X PUT "https://api.github.com/repos/efsstudioagents/${repo}/contents/${path}" \
    -H "Authorization: token $GH_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"message\":\"${msg}\",\"content\":\"${content}\"}" | /usr/bin/jq -r '.content.path // .message'
}

# Exemplo
gh_create "n8n-${CLIENTE}" "README.md" "{mensagem}" "$(printf '# n8n-%s\n' "$CLIENTE" | base64)"
```

Arquivos a criar no OPS: `README.md`, `agentes/README.md`, `context/companhia_example.md`, `context/produtos_example.md`

Arquivos a criar no ADM: `README.md`, `infra/vps.md`, `acessos/credenciais.md`, `sql/schema.md`, `sql/queries.md`

> **Atenção**: sempre usar `/usr/bin/curl` e `/usr/bin/jq` (caminhos absolutos) — evita erros de "command not found" em funções shell no macOS.

---

## Workflow de Backup n8n → GitHub

### Arquitetura atual (versão corrigida)

O backup é incremental por `versionId`. O workflow lista workflows do n8n, compara o `versionId` com o arquivo no GitHub, e só salva se mudou.

**Formato de arquivo**: `workflows/{slug}.json` — nome limpo, sem `__ID`, JSON diretamente importável no n8n.

**Nós críticos:**

**Nó `2. Split + Organizar`** — monta o caminho com slug limpo:
```js
const slug = w.name.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '');
return { json: { ...w, githubPath: `workflows/${slug}.json` } };
```

**Nó `4. Comparar versionId`** — lê `versionId` direto do JSON (não via `__meta`):
```js
const parsed = JSON.parse(Buffer.from(githubContent, 'base64').toString('utf8'));
const githubVersionId = parsed.versionId || null;
```

**Nó `7. Montar JSON`** — salva JSON limpo importável, com `versionId` no topo:
```js
const cleanWorkflow = { ...workflowData };
delete cleanWorkflow.id;          // n8n ignora na importação
delete cleanWorkflow.createdAt;
delete cleanWorkflow.updatedAt;
// NÃO usar wrapper {__meta, workflow} — impede importação direta
return [{ json: { content: JSON.stringify(cleanWorkflow, null, 2), ... } }];
```

### Bug: backup salva todos os workflows toda vez

**Causa**: o nó `3. Buscar GitHub` tem URL hardcoded apontando para o repo errado. O nó compara o `versionId` do n8n com o arquivo no GitHub — se o repo estiver errado, a comparação sempre falha e salva tudo.

**Diagnóstico:**
```bash
curl -s "https://n8n-{cliente}.efsstudioagents.com/api/v1/workflows/{id}" \
  -H "X-N8N-API-KEY: {chave}" | jq '[.nodes[] | {name, url: .parameters.url}] | map(select(.url))'
```
Verificar se o nó `3. Buscar GitHub` aponta para o repo correto do cliente.

**Correção**: atualizar URL do nó 3, `n8nBaseUrl` no nó 7, e repositório nos nós 8b/8c:
```bash
# Baixar workflow atual
curl -s "https://n8n-{cliente}.efsstudioagents.com/api/v1/workflows/{id}" \
  -H "X-N8N-API-KEY: {chave}" > /tmp/wf.json

# Corrigir
jq '
  .nodes = [.nodes[] |
    if .name == "3. Buscar GitHub" then
      .parameters.url = "=https://api.github.com/repos/efsstudioagents/n8n-{cliente}/contents/{{ $json.githubPath }}"
    elif .name == "7. Montar JSON" then
      .parameters.jsCode = (.parameters.jsCode | gsub("n8nBaseUrl:   '\''https://n8n.efsstudioagents.com'\''"; "n8nBaseUrl:   '\''https://n8n-{cliente}.efsstudioagents.com'\''"))
    elif .name == "8b. Editar GitHub" then
      .parameters.repository.value = "n8n-{cliente}" |
      .parameters.repository.cachedResultName = "n8n-{cliente}" |
      .parameters.repository.cachedResultUrl = "https://github.com/efsstudioagents/n8n-{cliente}"
    elif .name == "8c. Criar GitHub" then
      .parameters.repository.value = "n8n-{cliente}" |
      .parameters.repository.cachedResultName = "n8n-{cliente}" |
      .parameters.repository.cachedResultUrl = "https://github.com/efsstudioagents/n8n-{cliente}"
    else . end
  ]
' /tmp/wf.json > /tmp/wf-fixed.json

# Publicar
PAYLOAD=$(jq '{name, nodes, connections, settings: {executionOrder: .settings.executionOrder, errorWorkflow: .settings.errorWorkflow, callerPolicy: .settings.callerPolicy}, staticData}' /tmp/wf-fixed.json)

curl -s -X PUT "https://n8n-{cliente}.efsstudioagents.com/api/v1/workflows/{id}" \
  -H "X-N8N-API-KEY: {chave}" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD" | jq '{id, name, updatedAt}'
```

### Bug: loop infinito no backup (workflows com slug duplicado)

**Causa**: dois workflows com o mesmo nome geram o mesmo slug/caminho de arquivo. O backup entra em loop tentando comparar/salvar o mesmo arquivo.

**Diagnóstico:**
```bash
# Listar todos os workflows e verificar duplicatas de nome
curl -s "https://n8n-{cliente}.efsstudioagents.com/api/v1/workflows?limit=100" \
  -H "X-N8N-API-KEY: {chave}" | jq '[.data[] | {id, name}] | sort_by(.name)'
```

**Correção**: deletar ou renomear o workflow duplicado via API:
```bash
# Deletar
curl -s -X DELETE "https://n8n-{cliente}.efsstudioagents.com/api/v1/workflows/{id}" \
  -H "X-N8N-API-KEY: {chave}"
```

> **Atenção**: o n8n UI pode mostrar "Total 1" mesmo havendo duplicatas — sempre confirmar via API.

---

## Extrair Schema do Supabase

Para popular `sql/schema.md` e `sql/queries.md` nos repos ADM:

```bash
SUPABASE_URL="https://{project}.supabase.co"
SERVICE_KEY="{service_role_key}"

# Listar tabelas disponíveis
curl -s "${SUPABASE_URL}/rest/v1/" \
  -H "apikey: ${SERVICE_KEY}" \
  -H "Authorization: Bearer ${SERVICE_KEY}" | jq 'keys'

# Ver colunas de uma tabela (limit=1 para não trazer dados)
curl -s "${SUPABASE_URL}/rest/v1/{tabela}?select=*&limit=1" \
  -H "apikey: ${SERVICE_KEY}" \
  -H "Authorization: Bearer ${SERVICE_KEY}" | jq '.[0] | keys'
```

Para o schema completo (CREATE TABLE), pedir ao usuário que exporte diretamente do Supabase Dashboard → Table Editor → cada tabela tem opção de ver SQL.

### Tabelas padrão (ambos EFS e HBT)
`usuarios`, `interacoes`, `atendimento_humano`, `documents` (pgvector para RAG)

### Tabelas exclusivas HBT
`faturas_recuperacao`, `carrinho_abandonado`, `product_cache`

---

## Migrar Conteúdo Entre Repos

Para arquivos normais (usa endpoint raw para evitar problemas de parsing com jq):
```bash
# Listar arquivos
FILES=$(curl -s "https://api.github.com/repos/efsstudioagents/{repo-origem}/git/trees/main?recursive=1" \
  -H "Authorization: token $GH_TOKEN" | jq -r '.tree[] | select(.type == "blob") | .path')

while IFS= read -r filepath; do
  # Download raw
  RAW=$(/usr/bin/curl -s "https://raw.githubusercontent.com/efsstudioagents/{repo-origem}/main/${filepath}" \
    -H "Authorization: token $GH_TOKEN")
  ENCODED=$(echo "$RAW" | base64)

  # Upload para destino
  /usr/bin/curl -s -X PUT "https://api.github.com/repos/efsstudioagents/{repo-destino}/contents/${filepath}" \
    -H "Authorization: token $GH_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"message\":\"migrate: ${filepath}\",\"content\":\"${ENCODED}\"}" | /usr/bin/jq -r '.content.path // .message'
done <<< "$FILES"
```

Para arquivos grandes (>50KB), usar Python para evitar "argument list too long":
```python
import json, base64, urllib.request

with open("/tmp/arquivo.json", "rb") as f:
    content = base64.b64encode(f.read()).decode()

with open(os.path.expanduser("~/.config/efsstudio/github-token")) as f:
    token = f.read().strip()

path = "workflows/pasta/arquivo.json"
payload = json.dumps({"message": f"{mensagem}", "content": content}).encode()
req = urllib.request.Request(
    f"https://api.github.com/repos/efsstudioagents/{repo}/contents/{path}",
    data=payload,
    headers={"Authorization": f"token {token}", "Content-Type": "application/json"},
    method="PUT"
)
with urllib.request.urlopen(req) as r:
    res = json.loads(r.read())
    print("✓", res["content"]["path"])
```

---

## Atualizar Arquivo Existente no GitHub

Para atualizar (não criar), é necessário o SHA atual do arquivo:
```bash
SHA=$(/usr/bin/curl -s "https://api.github.com/repos/efsstudioagents/{repo}/contents/{path}" \
  -H "Authorization: token $GH_TOKEN" | /usr/bin/jq -r '.sha')

/usr/bin/curl -s -X PUT "https://api.github.com/repos/efsstudioagents/{repo}/contents/{path}" \
  -H "Authorization: token $GH_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"message\":\"update: {path}\",\"content\":\"$(echo 'conteudo' | base64)\",\"sha\":\"$SHA\"}"
```

---

## Deletar Arquivos Antigos do GitHub

Útil para limpar arquivos com sufixo `__ID` após migrar para nomes limpos:
```bash
# Listar arquivos com padrão específico
FILES=$(/usr/bin/curl -s "https://api.github.com/repos/efsstudioagents/{repo}/git/trees/main?recursive=1" \
  -H "Authorization: token $GH_TOKEN" | /usr/bin/jq -r '.tree[] | select(.type == "blob" and (.path | contains("__"))) | .path')

while IFS= read -r filepath; do
  SHA=$(/usr/bin/curl -s "https://api.github.com/repos/efsstudioagents/{repo}/contents/${filepath}" \
    -H "Authorization: token $GH_TOKEN" | /usr/bin/jq -r '.sha')

  /usr/bin/curl -s -X DELETE "https://api.github.com/repos/efsstudioagents/{repo}/contents/${filepath}" \
    -H "Authorization: token $GH_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"message\":\"cleanup: remove ${filepath}\",\"sha\":\"${SHA}\"}" | /usr/bin/jq -r '.commit.message // .message'
done <<< "$FILES"
```

---

## Editar Prompt de Agente no GitHub

Quando o usuário pedir para editar/atualizar/corrigir o prompt de um agente:

**NUNCA** editar o JSON de backup em `workflows/`. O backup é gerado automaticamente pelo n8n — editar ele manualmente não tem efeito nenhum.

### Regras obrigatórias
1. **Sempre criar um novo arquivo de versão** — nunca sobrescrever a versão atual. Ex: se a atual é `v1.4.2.md`, criar `v1.4.3.md`
2. **Sempre criar/atualizar `changelog.md`** na mesma pasta com a descrição da atualização

### Estrutura da pasta prompt
```
agentes/{nome-do-agente}/prompt/
  v1.0.md
  v1.4.2.md          ← versão atual (não editar)
  v1.4.3.md          ← nova versão criada com a mudança
  changelog.md       ← histórico de todas as versões
```

### Formato do changelog.md
```markdown
# Changelog — Prompt {Nome do Agente}

## v1.4.3 — DD/MM/AA
- Descrição da mudança

## v1.4.2 — DD/MM/AA
- ...
```

### Helpers Python reutilizáveis
```python
import json, base64, urllib.request, urllib.parse, os

with open(os.path.expanduser("~/.config/efsstudio/github-token")) as f:
    token = f.read().strip()

def gh_get(repo, filepath):
    """Retorna (conteúdo_str, sha). sha=None se arquivo não existe."""
    url = f"https://api.github.com/repos/efsstudioagents/{repo}/contents/{urllib.parse.quote(filepath)}"
    req = urllib.request.Request(url, headers={"Authorization": f"token {token}"})
    try:
        with urllib.request.urlopen(req) as r:
            meta = json.loads(r.read())
            return base64.b64decode(meta['content']).decode(), meta['sha']
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None, None
        raise

def gh_put(repo, filepath, message, content_str, sha=None):
    """Cria ou atualiza arquivo no GitHub."""
    payload = {"message": message, "content": base64.b64encode(content_str.encode()).decode()}
    if sha:
        payload["sha"] = sha
    data = json.dumps(payload).encode()
    url = f"https://api.github.com/repos/efsstudioagents/{repo}/contents/{urllib.parse.quote(filepath)}"
    req = urllib.request.Request(url, data=data, headers={"Authorization": f"token {token}", "Content-Type": "application/json"}, method="PUT")
    with urllib.request.urlopen(req) as r:
        res = json.loads(r.read())
        print("✓", res["content"]["path"])
```

### Fluxo de atualização de prompt
```python
# 1. Baixar versão atual
old_content, _ = gh_get(repo, "agentes/{nome}/prompt/v1.4.2.md")

# 2. Aplicar edição
new_content = old_content  # modificar aqui

# 3. Criar nova versão
gh_put(repo, "agentes/{nome}/prompt/v1.4.3.md", "{mensagem}", new_content)

# 4. Atualizar changelog
changelog, changelog_sha = gh_get(repo, "agentes/{nome}/prompt/changelog.md")
entry = "## v1.4.3 — DD/MM/AA\n- Descrição da mudança\n\n"
if changelog:
    new_changelog = changelog.replace("# Changelog", "# Changelog\n\n" + entry, 1)
else:
    new_changelog = f"# Changelog — Prompt {{Nome do Agente}}\n\n{entry}"
gh_put(repo, "agentes/{nome}/prompt/changelog.md", "{mensagem}", new_changelog, sha=changelog_sha)
```

---

## Preencher credenciais.md com dados do n8n

Ao atualizar `acessos/credenciais.md` de um cliente, puxar a lista de credenciais via API para saber o que já existe no n8n, cruzar com os valores já conhecidos (stacks, vps.md) e deixar `_preencher_` apenas no que realmente falta.

### 1. Listar credenciais do n8n
```bash
curl -s "https://n8n-{cliente}.efsstudioagents.com/api/v1/credentials" \
  -H "X-N8N-API-KEY: {chave}" | jq '[.data[] | {name, type}]'
```

> A API retorna apenas metadados (nome, tipo, id) — **nunca os valores reais**. Os valores devem ser cruzados com o que já está documentado nas stacks ou fornecidos pelo usuário.

### 2. Valores já conhecidos (sem precisar perguntar)

| Dado | Fonte |
|------|-------|
| Redis senha | `infra/stacks/redis.yml` → `--requirepass` |
| Redis DB | `vps.md` → DB=2 (EFS) / DB=3 (HBT) |
| Postgres senha | `infra/stacks/postgres.yml` → `POSTGRES_PASSWORD` |
| Evolution API Key | `infra/stacks/evolution_api.yml` → `AUTHENTICATION_API_KEY` |
| n8n Encryption Key | `infra/stacks/n8n_editor_{cliente}.yml` → `N8N_ENCRYPTION_KEY` |
| URLs e domínios | `vps.md` → seção Domínios |

### 3. Valores que requerem input do usuário
OpenAI API Key, Supabase URL + keys, GitHub PAT, Google OAuth tokens, Telegram Bot Token, Tavily, Apify, Gemini, Cloudflare API Token, SMTP credentials.

### 4. Fluxo ao executar sync de credenciais para um cliente
1. Puxar lista de credenciais via API
2. Ler stacks em `infra/stacks/` para extrair valores conhecidos
3. Montar `credenciais.md` com valores preenchidos onde possível
4. Deixar `_preencher_` apenas no que não foi encontrado
5. Atualizar o arquivo no GitHub (buscar SHA antes de fazer PUT)
