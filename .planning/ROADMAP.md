# Roadmap — Clube Altera Dados

**3 fases** | **7 requisitos mapeados** | Todos os requisitos v1 cobertos ✓

---

## Visão Geral

| # | Fase | Meta | Requisitos | Critérios de Sucesso |
|---|------|------|------------|----------------------|
| 1 | Robustez da Automação ✓ | Playwright não falha silenciosamente | ROB-01, ROB-02, ROB-03, ROB-04 | 4/4 ✓ (UAT pendente) |
| 2 | UX Operacional | Operador nunca fica perdido | UX-01, UX-02 | 3 |
| 3 | Auditoria Centralizada | Supervisores têm visibilidade das operações | LOG-01 | 3 |

---

### Phase 1: Robustez da Automação
**Goal:** O operador nunca recebe "deu erro" sem saber o que aconteceu — falhas têm diagnóstico, screenshots e retries automáticos.
**Mode:** mvp
**Success Criteria:**
1. Uma falha de seletor CSS no CRM gera screenshot salvo em AppData e mensagem específica no log da UI
2. Uma falha de rede (timeout) dispara 3 tentativas automáticas antes de exibir erro ao operador
3. Mudança de classe CSS no CRM não quebra a automação (fallback de seletor ativo)
4. Cada tipo de falha (CPF inexistente, sessão expirada, timeout, elemento faltando) exibe mensagem distinta na UI

**Requirements:** ROB-01, ROB-02, ROB-03, ROB-04

---

### Phase 2: UX Operacional
**Goal:** O operador acompanha o progresso etapa a etapa e consegue retentar sem reiniciar o programa.
**Mode:** mvp
**Success Criteria:**
1. Log de status exibe ícone de check (✓) por etapa concluída (Zanthus → CRM → Busca CPF → Alteração → Confirmação)
2. Após qualquer falha, botão "Tentar novamente" aparece sem fechar/reabrir o programa
3. Um novo operador consegue completar a operação sem treinamento adicional observando apenas o log de status

**Requirements:** UX-01, UX-02

---

### Phase 3: Auditoria Centralizada
**Goal:** Supervisores têm visibilidade das operações realizadas por todos os operadores sem precisar coletar logs manualmente.
**Mode:** mvp
**Success Criteria:**
1. Cada operação (sucesso ou falha) envia POST para endpoint configurado em `crm_config.json`
2. Falha no envio do log não bloqueia nem atrasa a operação principal
3. Endpoint, headers e payload são configuráveis sem recompilar o executável

**Requirements:** LOG-01

---

## Sequência Recomendada

Fase 1 → Fase 2 → Fase 3

Fase 1 deve vir primeiro porque corrige os problemas mais críticos relatados pelos operadores. Fase 2 melhora a experiência após ter uma base estável. Fase 3 requer um endpoint de destino para ser configurado.

## v2 Backlog (fora do escopo atual)

- Operação em lote via CSV
- Suporte multi-portal (drivers plugáveis)
- Auto-update silencioso
- Painel web de supervisão
