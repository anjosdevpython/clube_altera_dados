---
phase: 03-auditoria-centralizada
plan: "01"
subsystem: audit-webhook
tags: [auditoria, webhook, log-centralizado, lgpd, fire-and-forget]
dependency_graph:
  requires: [02-02]
  provides: [LOG-01]
  affects: [CLUBE_modif.py]
tech_stack:
  added: []
  patterns: [fire-and-forget daemon thread, urllib.request.urlopen, crm_config.json external config]
key_files:
  created: []
  modified:
    - "CLUBE_modif.py"
decisions:
  - "D-LOG-01: Payload JSON mínimo — CPF mascarado (***XXXXX-XX) por LGPD"
  - "D-LOG-02: webhook_url como chave única no crm_config.json — ausente = silêncio total"
  - "D-LOG-03: Apenas operações CRM completas disparam POST (falha Zanthus = pré-operação)"
  - "D-LOG-04: Fire-and-forget em daemon thread, timeout=5s, except Exception: pass"
  - "D-LOG-05: Chamada nos 3 pares try/except/else de iniciar() antes de reset_values()"
metrics:
  duration: "~15min"
  completed: "2026-06-05"
  tasks_completed: 3
  tasks_total: 3
  files_modified: 1
  commit: "f8c3121"
note: "Fase implementada fora do fluxo gsd-execute-phase. SUMMARY retroativo gerado em fechamento do milestone v1.0."
---

# Phase 3 Plan 01: Auditoria Centralizada — Summary

**One-liner:** Implementado POST silencioso de auditoria por operação CRM — CPF mascarado LGPD, daemon thread fire-and-forget, configurável via crm_config.json sem recompilar.

## Tasks Executadas

| Task | Título | Commit | Status |
|------|--------|--------|--------|
| T-01 | `_mascarar_cpf()` + `_carregar_crm_config_webhook()` | f8c3121 | OK |
| T-02 | `_enviar_log_auditoria(payload)` daemon thread | f8c3121 | OK |
| T-03 | 6 chamadas em `iniciar()` (3× except + 3× else) | f8c3121 | OK |

## O Que Foi Construído

### Funções Adicionadas

- **`_mascarar_cpf(cpf)`** — substitui os 3 primeiros dígitos por `***`, mantendo os 8 finais com traço (ex: `***12345-67`). Garante correlação para auditoria sem expor CPF completo (LGPD).
- **`_carregar_crm_config_webhook()`** — lê `crm_config.json` e retorna `webhook_url` ou `None` se ausente/vazio. Mesmo padrão de `_carregar_crm_config()` existente.
- **`_enviar_log_auditoria(payload)`** — dispara `urllib.request.urlopen` em `threading.Thread(daemon=True)`. Timeout: 5s. `except Exception: pass` — completamente silencioso. Zero impacto no fluxo principal.

### Payload JSON

```json
{
  "cpf": "***12345-67",
  "operador": "<login_funcionario global>",
  "tipo_operacao": "SENHA | EMAIL | SENHA E EMAIL",
  "resultado": "sucesso | erro",
  "timestamp": "<ISO 8601 UTC>",
  "mensagem_erro": "<str(err) apenas quando resultado=erro>"
}
```

### Pontos de Chamada em `iniciar()`

6 inserções nos 3 pares de try/except/else para `change_password`, `change_email`, `change_all`:
- **except branch** → `resultado="erro"`, `mensagem_erro=str(err)`, antes de `mostrar_btn_tentar_novamente()`
- **else branch** → `resultado="sucesso"`, antes de `reset_values()`

### Configuração

Campo `webhook_url` adicionado ao schema de `crm_config.json`:

```json
{
  "usuario": "...",
  "senha": "...",
  "webhook_url": "https://n8n.example.com/webhook/auditoria"
}
```

Ausente ou vazio = envio ignorado silenciosamente. Ativação/desativação sem recompilação.

## Verification Results

- ast.parse() passed — sem erros de sintaxe
- `_enviar_log_auditoria` presente: confirmado
- `_mascarar_cpf` presente: confirmado
- `_carregar_crm_config_webhook` presente: confirmado
- 6 chamadas de auditoria em `iniciar()`: confirmado (3 except + 3 else)
- Dependências: `urllib.request`, `json`, `threading` — todos já importados (zero dependências novas)

## Deviations from Plan

Nenhum — CONTEXT.md seguido exatamente.

## Known Stubs

- `webhook_url` vazio/ausente no crm_config.json de produção — funciona quando a URL for adicionada.
- `webhook_headers` para autenticação: deferred para v2.

## Threat Flags

- POST dispara dados de CPF mascarado para URL externa configurável — endpoint deve ser HTTPS e controlado pela empresa.
- Sem validação da URL no crm_config.json — URL inválida falha silenciosamente (comportamento esperado).

## Self-Check: PASSED

- CLUBE_modif.py modificado: confirmado (commit f8c3121)
- Funções presentes: confirmado
- Sintaxe válida: confirmado
- LOG-01 entregue: confirmado
