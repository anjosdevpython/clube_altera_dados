# Phase 3: Auditoria Centralizada - Context

**Gathered:** 2026-06-05
**Status:** Ready for planning

<domain>
## Phase Boundary

Cada operação CRM completa (sucesso ou falha após `executar_com_retry`) dispara um HTTP POST silencioso para um endpoint configurável em `crm_config.json`. Supervisores conseguem ver o histórico de operações de todos os operadores sem coletar logs manualmente. Falha no envio nunca bloqueia nem atrasa a operação principal.

</domain>

<decisions>
## Implementation Decisions

### D-LOG-01: Payload do POST de auditoria

**Decisão:** Payload JSON mínimo essencial — CPF mascarado por LGPD:

```json
{
  "cpf": "***XXXXX-XX",
  "operador": "<login_funcionario global>",
  "tipo_operacao": "SENHA | EMAIL | SENHA E EMAIL",
  "resultado": "sucesso | erro",
  "timestamp": "<ISO 8601, datetime.utcnow().isoformat()>",
  "mensagem_erro": "<str(err) apenas quando resultado=erro; omitido no sucesso>"
}
```

**Mascaramento do CPF:** primeiros 3 dígitos substituídos por `***`, mantendo os 8 finais com traço (ex: `***12345-67`). Garante correlação suficiente para auditoria sem expor o CPF completo.

**Campos NÃO incluídos na v1:** `nome_maquina`, `versao_app`, `duracao_operacao_segundos` — deferred para v2.

---

### D-LOG-02: Schema de configuração em crm_config.json

**Decisão:** Adicionar apenas a chave `webhook_url` (string):

```json
{
  "usuario": "...",
  "senha": "...",
  "webhook_url": "https://n8n.example.com/webhook/auditoria"
}
```

**Comportamento quando ausente:** se `webhook_url` não existir na config (ou for string vazia), o envio é ignorado silenciosamente — zero logs de erro, zero impacto na operação. Ativa ligando/desliga removendo a chave.

**Sem `webhook_headers` na v1:** endpoint de destino será n8n (sem autenticação header necessária para MVP). Deferred se autenticação for exigida futuramente.

---

### D-LOG-03: Cobertura da auditoria — quais eventos disparam o POST

**Decisão:** Apenas operações CRM completas disparam o POST:

| Evento | Dispara POST? |
|--------|---------------|
| `executar_com_retry()` termina com sucesso (else branch) | ✅ resultado=sucesso |
| `executar_com_retry()` lança exceção (except branch) | ✅ resultado=erro |
| Falha de login Zanthus (usuário/senha errado) | ❌ não dispara |
| Erro técnico Zanthus | ❌ não dispara |
| CPF com formato inválido (validação local) | ❌ não dispara |

**Rationale:** Falha Zanthus é pré-operação — não há operação CRM a auditar. Apenas operações que chegaram ao CRM são relevantes para supervisores.

---

### D-LOG-04: Mecanismo de envio — fire-and-forget

**Decisão:** Disparar em daemon thread separada. Nunca bloquear o fluxo principal:

```python
def _enviar_log_auditoria(payload: dict):
    webhook_url = _carregar_crm_config_webhook()  # retorna None se ausente
    if not webhook_url:
        return
    def _post():
        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(webhook_url, data=data,
                                         headers={"Content-Type": "application/json"})
            urllib.request.urlopen(req, timeout=5)
        except Exception:
            pass  # silencioso — nunca logar nem propagar
    threading.Thread(target=_post, daemon=True).start()
```

**Timeout:** 5 segundos (igual ao update-checker existente).  
**Falha:** capturada com `except Exception: pass` — completamente silenciosa.  
**Dependências:** `urllib.request` (já importado), `json` (já importado), `threading` (já importado).

---

### D-LOG-05: Ponto de chamada em iniciar()

Chamar `_enviar_log_auditoria(payload)` nos 3 pares de try/except/else de `iniciar()`:

```
change_password try/except/else → except: resultado="erro", mensagem=str(err)
                                → else:   resultado="sucesso"
change_email    try/except/else → except: resultado="erro", mensagem=str(err)
                                → else:   resultado="sucesso"
change_all      try/except/else → except: resultado="erro", mensagem=str(err)
                                → else:   resultado="sucesso"
```

A chamada deve ser inserida **antes** de `reset_values()` no `else` (para que `cpf`, `login_funcionario`, `tipo_alterado` ainda estejam disponíveis), e **antes** de `mostrar_btn_tentar_novamente()` no `except`.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Arquivo principal
- `CLUBE_modif.py` — único arquivo a modificar; ler integralmente antes de editar
- `.planning/REQUIREMENTS.md` — LOG-01 define os critérios de sucesso da fase

### Padrões de referência no código
- `_carregar_crm_config()` (linha ~529) — padrão de leitura do `crm_config.json`; criar `_carregar_crm_config_webhook()` no mesmo estilo
- Update-checker (linha ~706) — padrão existente de `urllib.request.urlopen` com timeout=5; seguir o mesmo estilo
- `executar_com_retry()` — ponto de integração: o caller em `iniciar()` tem try/except/else que é onde inserir as chamadas de auditoria

### Configuração externa
- `crm_config.json` — arquivo de config (nunca comitar; gitignored); novo campo `webhook_url`

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `urllib.request` + `urllib.error`: já importados — usar para o POST de auditoria sem dependências novas
- `json`: já importado — usar para `json.dumps(payload)`
- `threading`: já importado — usar para o daemon thread fire-and-forget
- `_carregar_crm_config()`: modelo para criar `_carregar_crm_config_webhook()` que retorna a URL ou None

### Established Patterns
- `crm_config.json` como single source of config: não hardcodar URLs no código
- `try: ... except Exception: pass` para operações secundárias que não devem interromper o fluxo
- Daemon threads para operações background (já usado no threading geral da automação)

### Integration Points
- `iniciar()` método principal: 3 branches try/except/else para change_password, change_email, change_all — cada um recebe 2 chamadas de auditoria (except + else)
- Globals disponíveis no momento do disparo: `cpf`, `login_funcionario`, `change_password`, `change_email`, `change_all`

</code_context>

<specifics>
## Specific Ideas

- Endpoint de destino será n8n (a definir a URL depois) — implementar agora com `webhook_url` vazio/ausente no config, funcionando imediatamente quando a URL for adicionada
- CPF mascarado: manter suficiente para correlação com o CRM (`***12345-67`) sem expor dado completo
- A fase é totalmente não-visível para o operador — sem logs adicionais na UI, sem delays, sem mensagens

</specifics>

<deferred>
## Deferred Ideas

- `webhook_headers` para autenticação Bearer/API key — adicionar se endpoint exigir auth (v2)
- `nome_maquina`, `versao_app`, `duracao_operacao` no payload — métricas operacionais (v2)
- Auditoria de tentativas Zanthus falhas — track de acesso, não de operação CRM (v2)
- Painel web de supervisão (já no backlog v2 do ROADMAP.md)

</deferred>

---

*Phase: 3-Auditoria Centralizada*
*Context gathered: 2026-06-05*
