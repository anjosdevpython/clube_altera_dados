# Phase 3: Auditoria Centralizada - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-05
**Phase:** 3-Auditoria Centralizada
**Areas discussed:** Payload do POST, Schema do crm_config.json, Cobertura da auditoria, Destino e formato

---

## Payload do POST

| Option | Description | Selected |
|--------|-------------|----------|
| Mínimo essencial | cpf mascarado, operador, tipo, resultado, timestamp, mensagem_erro (só em falha) | ✓ |
| Completo | Tudo do mínimo + nome_maquina, versao_app, duracao_operacao_segundos | |
| Sem mascaramento de CPF | CPF completo nos 11 dígitos | |

**User's choice:** Mínimo essencial (Recomendado)  
**Notes:** CPF mascarado para LGPD (`***XXXXX-XX`). Campos extras deferred para v2.

---

## Schema do crm_config.json

| Option | Description | Selected |
|--------|-------------|----------|
| Só webhook_url | Chave ausente = envio ignorado silenciosamente | ✓ |
| webhook_url + webhook_enabled | Flag booleana explícita para ativar/desativar | |
| webhook_url + webhook_headers | Dict de headers de autenticação | |

**User's choice:** Só webhook_url (Recomendado)  
**Notes:** Ativar/desligar adicionando ou removendo a chave. Sem flag extra. `webhook_headers` deferred se auth for necessária.

---

## Cobertura da auditoria

| Option | Description | Selected |
|--------|-------------|----------|
| Só operações CRM completas | Apenas when executar_com_retry() termina | ✓ |
| Tudo, incluindo falha Zanthus | Registra até tentativas de login com credencial errada | |

**User's choice:** Só operações CRM completas (Recomendado)  
**Notes:** Falha Zanthus é pré-operação — nada aconteceu no CRM. Cobertura mais limpa para supervisores.

---

## Destino e formato

| Option | Description | Selected |
|--------|-------------|----------|
| Não ainda / usar n8n depois | Implementar agora com webhook_url vazio | ✓ |
| Sim, já tenho a URL | Testar payload com URL real | |

**User's choice:** Não ainda / usar n8n depois  
**Notes:** Endpoint será n8n quando configurado. A implementação funciona imediatamente ao adicionar a URL no crm_config.json.

---

## Claude's Discretion

- Mascaramento exato do CPF: `***XXXXX-XX` (3 asteriscos + 5 dígitos + traço + 2 dígitos)
- Timeout do POST: 5s (igual ao update-checker existente)
- Ponto de inserção nas chamadas: antes de `reset_values()` no else e antes de `mostrar_btn_tentar_novamente()` no except

## Deferred Ideas

- `webhook_headers` para autenticação (v2)
- Campos operacionais: `nome_maquina`, `versao_app`, `duracao_operacao` (v2)
- Auditoria de tentativas Zanthus (v2 / fase separada)
- Painel web de supervisão (já no backlog v2 do ROADMAP.md)
