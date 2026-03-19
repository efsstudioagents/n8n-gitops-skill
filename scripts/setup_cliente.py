#!/usr/bin/env python3
"""
setup_cliente.py — Cria estrutura completa de repositórios GitHub para novo cliente n8n

Uso:
    python setup_cliente.py --org minha-org --cliente xyz --nome "Nome do Cliente"

Argumentos:
    --org         Organização ou usuário do GitHub (obrigatório)
    --cliente     Código curto do cliente, ex: xyz (obrigatório)
    --nome        Nome completo do cliente (obrigatório)
    --token-file  Caminho para o arquivo com o GitHub token
                  (padrão: ~/.config/n8n-gitops/github-token)

O script cria:
  GitHub: n8n-{cliente} (OPS) e n8n-{cliente}-adm (ADM)
  OPS:    README, context/, agentes/ com exemplos e prompt base, workflows/
  ADM:    README, infra/vps.md, acessos/credenciais.md, sql/schema.md, sql/queries.md
"""

import argparse
import base64
import json
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

DEFAULT_TOKEN_FILE = Path.home() / ".config/n8n-gitops/github-token"

# ─── Templates de conteúdo ────────────────────────────────────────────────────

def tpl_ops_readme(cliente, nome, org):
    return f"""# n8n-{cliente} — Workflows e Agentes

Repositório OPS do cliente **{nome}**.

## Estrutura

```
agentes/           → Documentação de cada agente (escopo, prompt, changelog)
context/           → Contexto da empresa e produtos
workflows/         → Backup automático dos workflows n8n
```

## Convenções

- Prompts versionados: `v1.0.md` → `v1.0.1` (fix) → `v1.1.0` (feature)
- Arquivos de exemplo: sufixo `_example.md`
- Workflows: backup incremental por `versionId`, formato JSON importável direto no n8n
"""

def tpl_adm_readme(cliente, nome):
    return f"""# n8n-{cliente}-adm — Infra e Acessos

Repositório ADM do cliente **{nome}** (acesso restrito).

## Estrutura

```
infra/             → Servidores, IPs, Docker Swarm / compose files
acessos/           → API keys e logins de serviços
sql/               → Schema do banco e queries importantes
```
"""

def tpl_companhia(nome):
    return f"""# Sobre a Empresa

**Nome:** {nome}
**Segmento:** [ex: E-commerce / SaaS / Serviços]
**Site:** https://

## Descrição

[Descreva aqui o que a empresa faz, seu público-alvo e diferenciais.]

## Contexto para os Agentes

[Informações que os agentes precisam saber sobre a empresa para atender bem.]
"""

def tpl_produtos():
    return """# Produtos e Serviços

## [Nome do Produto/Serviço 1]

**Descrição:** [O que é]
**Público:** [Para quem]
**Preço:** [Faixa de preço ou modelo]
**Detalhes:** [Informações adicionais relevantes para os agentes]

---

## [Nome do Produto/Serviço 2]

**Descrição:**
**Público:**
**Preço:**
"""

def tpl_escopo_example():
    return """# Escopo do Agente: [nome-funcao]

## O que faz

[Descrição clara e objetiva da função do agente.]

## Limitações

- [O agente NÃO faz X]
- [O agente NÃO acessa Y]

## Regras de negócio

1. [Regra importante 1]
2. [Regra importante 2]

## Fontes de dados

- [Tabela ou API que o agente consulta]
"""

def tpl_esquema_example():
    return """# Esquema de Dados: [nome-funcao]

## Tabelas utilizadas

### usuarios
```sql
SELECT id, nome, email, telefone, created_at
FROM usuarios
WHERE id = $1;
```

### interacoes
```sql
SELECT * FROM interacoes
WHERE usuario_id = $1
ORDER BY created_at DESC
LIMIT 10;
```

## Queries principais

[Descreva as queries mais importantes que o agente usa e por quê.]
"""

def tpl_changelog_example():
    return """# Changelog — [nome-funcao]

## v1.0.0 — [data]

- Versão inicial
- [Feature principal]

## Como versionar

- `v1.0.X` — correções de bug ou ajuste de tom
- `v1.X.0` — nova funcionalidade ou mudança de escopo
- `vX.0.0` — reescrita completa
"""

def tpl_prompt_example():
    return """# Prompt Base — v1.0

<AgentInstructions>

## Identidade

Você é [Nome do Agente], assistente da [Nome da Empresa].

## Objetivo

[Descreva o objetivo principal do agente em 1-2 frases.]

## Comportamento

- Seja direto e objetivo nas respostas
- Use linguagem adequada ao perfil do cliente
- Em caso de dúvida, pergunte antes de assumir

## Limitações

- Não forneça informações que não estejam na base de conhecimento
- Não faça promessas que não possa cumprir
- Em casos complexos, transfira para atendimento humano

## Fluxo principal

1. [Passo 1]
2. [Passo 2]
3. [Passo 3]

## Transferência para humano

Transfira quando:
- O cliente solicitar explicitamente
- O problema não puder ser resolvido pelo agente
- [Critério específico do cliente]

</AgentInstructions>
"""

def tpl_vps(cliente, nome):
    return f"""# Infraestrutura — {nome}

## Instância n8n

**URL:** https://[seu-dominio]
**Servidor:** [IP]

## Stacks Docker / Compose

### n8n (editor + webhook + worker)

```yaml
version: "3.7"
services:
  n8n_editor:
    image: n8nio/n8n:latest
    environment:
      - N8N_HOST=[seu-dominio]
      - N8N_PROTOCOL=https
      - N8N_PORT=5678
      - DB_TYPE=postgresdb
      - DB_POSTGRESDB_HOST=postgres
      - DB_POSTGRESDB_DATABASE=n8n_{cliente}
      - DB_POSTGRESDB_USER=n8n_{cliente}
      - DB_POSTGRESDB_PASSWORD=[senha]
      - QUEUE_BULL_REDIS_HOST=redis
      - QUEUE_BULL_REDIS_DB=[numero-db]
      - EXECUTIONS_MODE=queue
```

## Serviços Compartilhados

[Liste aqui quais serviços (postgres, redis, etc.) são compartilhados com outros clientes
e onde está a documentação deles.]
"""

def tpl_credenciais(cliente, nome):
    return f"""# Credenciais — {nome}

> ⚠️ Documento confidencial. Acesso restrito.

## n8n

- **URL:** https://[seu-dominio]
- **API Key:** [adicionar]

## Banco de Dados / Supabase

- **URL:** [adicionar]
- **Anon Key:** [adicionar]
- **Service Role Key:** [adicionar]

## WhatsApp / Mensageria

- **Instância:** {cliente}
- **Token:** [adicionar]
- **Número:** [adicionar]

## Outros Serviços

| Serviço | Login | Senha/Key | Notas |
|---------|-------|-----------|-------|
| [ex: OpenAI] | - | [key] | - |
"""

def tpl_schema(cliente):
    return f"""# Schema do Banco — {cliente}

## Tabelas Base

### usuarios
```sql
CREATE TABLE IF NOT EXISTS usuarios (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  nome TEXT,
  email TEXT,
  telefone TEXT,
  metadata JSONB DEFAULT '{{}}',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### interacoes
```sql
CREATE TABLE IF NOT EXISTS interacoes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  usuario_id UUID REFERENCES usuarios(id),
  canal TEXT,
  mensagem TEXT,
  resposta TEXT,
  metadata JSONB DEFAULT '{{}}',
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### atendimento_humano
```sql
CREATE TABLE IF NOT EXISTS atendimento_humano (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  usuario_id UUID REFERENCES usuarios(id),
  motivo TEXT,
  status TEXT DEFAULT 'pendente',
  atendente TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### documents (RAG / pgvector)
```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  content TEXT,
  metadata JSONB DEFAULT '{{}}',
  embedding vector(1536),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX ON documents USING ivfflat (embedding vector_cosine_ops);

CREATE OR REPLACE FUNCTION match_documents(
  query_embedding vector(1536),
  match_threshold FLOAT,
  match_count INT
)
RETURNS TABLE (id UUID, content TEXT, metadata JSONB, similarity FLOAT)
LANGUAGE plpgsql AS $$
BEGIN
  RETURN QUERY
  SELECT d.id, d.content, d.metadata,
    1 - (d.embedding <=> query_embedding) AS similarity
  FROM documents d
  WHERE 1 - (d.embedding <=> query_embedding) > match_threshold
  ORDER BY d.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;
```

## Trigger: updated_at automático
```sql
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_updated_at_usuarios
  BEFORE UPDATE ON usuarios
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER set_updated_at_atendimento_humano
  BEFORE UPDATE ON atendimento_humano
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();
```

## Tabelas específicas do cliente

[Adicionar tabelas exclusivas aqui]
"""

def tpl_queries(cliente):
    return f"""# Queries Importantes — {cliente}

## Buscar usuário por telefone
```sql
SELECT * FROM usuarios WHERE telefone = '+55...' LIMIT 1;
```

## Histórico recente de interações
```sql
SELECT * FROM interacoes
WHERE usuario_id = '[uuid]'
ORDER BY created_at DESC
LIMIT 20;
```

## Atendimentos pendentes
```sql
SELECT u.nome, u.telefone, a.motivo, a.created_at
FROM atendimento_humano a
JOIN usuarios u ON u.id = a.usuario_id
WHERE a.status = 'pendente'
ORDER BY a.created_at ASC;
```

## Busca semântica (RAG)
```sql
SELECT content, metadata,
  1 - (embedding <=> '[vetor]'::vector) AS similarity
FROM documents
WHERE 1 - (embedding <=> '[vetor]'::vector) > 0.7
ORDER BY embedding <=> '[vetor]'::vector
LIMIT 5;
```
"""

# ─── Funções GitHub ────────────────────────────────────────────────────────────

def gh_request(method, path, token, data=None):
    url = f"https://api.github.com{path}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(
        url, data=body, method=method,
        headers={
            "Authorization": f"token {token}",
            "Content-Type": "application/json",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "n8n-gitops-setup",
        }
    )
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        raise RuntimeError(f"GitHub API {method} {path} → {e.code}: {body}")

def repo_exists(token, org, repo):
    try:
        gh_request("GET", f"/repos/{org}/{repo}", token)
        return True
    except RuntimeError:
        return False

def create_repo(token, org, name, description):
    print(f"  → Criando repo: {org}/{name}")
    # Tenta criar na organização; se não for org, tenta como user
    for endpoint in [f"/orgs/{org}/repos", "/user/repos"]:
        try:
            gh_request("POST", endpoint, token, {
                "name": name,
                "private": True,
                "description": description,
                "auto_init": False,
            })
            print(f"    ✓ Criado")
            return
        except RuntimeError as e:
            if "already exists" in str(e) or "name already exists" in str(e):
                print(f"    ⚠ Já existe, continuando...")
                return
            if endpoint == f"/orgs/{org}/repos":
                continue  # Tenta como user
            raise

def create_file(token, org, repo, path, message, content):
    encoded = base64.b64encode(content.encode()).decode()
    print(f"    + {path}")
    try:
        gh_request("PUT", f"/repos/{org}/{repo}/contents/{path}", token, {
            "message": message,
            "content": encoded,
        })
    except RuntimeError as e:
        if "sha" in str(e).lower() or "422" in str(e):
            print(f"      ⚠ Arquivo já existe, pulando")
        else:
            raise

def wait_repo_ready(token, org, repo, max_wait=30):
    for i in range(max_wait):
        if repo_exists(token, org, repo):
            return True
        time.sleep(1)
    return False

# ─── Setup principal ──────────────────────────────────────────────────────────

def setup_ops(token, org, cliente, nome):
    repo = f"n8n-{cliente}"
    print(f"\n[OPS] {org}/{repo}")

    create_repo(token, org, repo, f"n8n workflows — {nome} (OPS)")
    wait_repo_ready(token, org, repo)

    files = {
        "README.md": tpl_ops_readme(cliente, nome, org),
        "context/companhia_example.md": tpl_companhia(nome),
        "context/produtos_example.md": tpl_produtos(),
        "agentes/nome-funcao_example/escopo_example.md": tpl_escopo_example(),
        "agentes/nome-funcao_example/esquema_example.md": tpl_esquema_example(),
        "agentes/nome-funcao_example/changelog_example.md": tpl_changelog_example(),
        "agentes/nome-funcao_example/prompt/v1.0_example.md": tpl_prompt_example(),
        "workflows/.gitkeep": "",
    }

    for path, content in files.items():
        create_file(token, org, repo, path, "init: estrutura base", content)

    print(f"  ✓ OPS completo → https://github.com/{org}/{repo}")

def setup_adm(token, org, cliente, nome):
    repo = f"n8n-{cliente}-adm"
    print(f"\n[ADM] {org}/{repo}")

    create_repo(token, org, repo, f"n8n infra e acessos — {nome} (ADM)")
    wait_repo_ready(token, org, repo)

    files = {
        "README.md": tpl_adm_readme(cliente, nome),
        "infra/vps.md": tpl_vps(cliente, nome),
        "acessos/credenciais.md": tpl_credenciais(cliente, nome),
        "sql/schema.md": tpl_schema(cliente),
        "sql/queries.md": tpl_queries(cliente),
    }

    for path, content in files.items():
        create_file(token, org, repo, path, "init: estrutura base", content)

    print(f"  ✓ ADM completo → https://github.com/{org}/{repo}")

# ─── Entrypoint ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Cria estrutura GitOps de repositórios GitHub para novo cliente n8n"
    )
    parser.add_argument("--org", required=True,
        help="Organização ou usuário do GitHub (ex: minha-empresa)")
    parser.add_argument("--cliente", required=True,
        help="Código curto do cliente (ex: xyz)")
    parser.add_argument("--nome", required=True,
        help="Nome completo do cliente (ex: 'Empresa XYZ')")
    parser.add_argument("--token-file", default=str(DEFAULT_TOKEN_FILE),
        help=f"Caminho para o arquivo com o GitHub token (padrão: {DEFAULT_TOKEN_FILE})")
    args = parser.parse_args()

    cliente = args.cliente.lower().strip()
    nome = args.nome.strip()
    org = args.org.strip()
    token_path = Path(args.token_file).expanduser()

    if not token_path.exists():
        print(f"\nErro: Token não encontrado em {token_path}")
        print(f"Crie o arquivo com:")
        print(f"  mkdir -p {token_path.parent} && echo 'ghp_...' > {token_path}")
        sys.exit(1)

    token = token_path.read_text().strip()
    if not token:
        print("Erro: Arquivo de token está vazio.")
        sys.exit(1)

    print(f"\n{'='*50}")
    print(f" Setup: {nome} ({cliente}) em {org}")
    print(f"{'='*50}")

    setup_ops(token, org, cliente, nome)
    setup_adm(token, org, cliente, nome)

    print(f"\n{'='*50}")
    print(f" ✅ Concluído!")
    print(f"{'='*50}")
    print(f"\n OPS: https://github.com/{org}/n8n-{cliente}")
    print(f" ADM: https://github.com/{org}/n8n-{cliente}-adm")
    print(f"\nPróximos passos:")
    print(f"  1. Preencher acessos/credenciais.md com credenciais reais")
    print(f"  2. Preencher infra/vps.md com IP do servidor")
    print(f"  3. Preencher context/ com dados reais da empresa")
    print(f"  4. Criar workflow de backup no n8n do cliente")
    print(f"  5. Adicionar tabelas específicas em sql/schema.md\n")

if __name__ == "__main__":
    main()
