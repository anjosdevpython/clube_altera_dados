# Requirements — Clube Altera Dados

## v1 Requirements

### Robustez & Diagnóstico

- [ ] **ROB-01**: Screenshot automático do browser é salvo em AppData quando qualquer passo do Playwright falha
- [ ] **ROB-02**: Cada tipo de falha exibe mensagem específica na UI (CPF não encontrado / sessão expirada / timeout / elemento não localizado / login inválido no CRM)
- [ ] **ROB-03**: Falhas de rede e timeout disparam retry automático (até 3 tentativas com backoff de 2s) antes de reportar erro ao operador
- [ ] **ROB-04**: Seletores do CRM têm fallback (XPath primário + CSS alternativo) para resistir a mudanças no HTML

### Log & Auditoria

- [ ] **LOG-01**: Toda operação bem-sucedida ou com erro envia POST para endpoint de log centralizado (configurável via `crm_config.json`); falha no POST não bloqueia a operação principal

### UX

- [ ] **UX-01**: Log de status mostra progresso por etapa com ícone de check (✓ Logando Zanthus / ✓ Buscando CPF / ✓ Alterando dados / ✓ Confirmado)
- [ ] **UX-02**: Botão "Tentar novamente" aparece na UI após qualquer falha, sem precisar reiniciar o programa

## v2 Requirements (deferred)

- Operação em lote via CSV/planilha de CPFs
- Suporte a outros portais/CRMs além do Bnex (arquitetura de "drivers" plugáveis)
- Auto-update silencioso em background (sem janela de confirmação para times grandes)
- Painel de histórico centralizado (web) para supervisores

## Out of Scope

- Interface web — desktop-only por design de acesso à rede da loja
- Autenticação por operador no CRM — conta de serviço compartilhada é decisão da empresa
- Acesso direto ao banco de dados do CRM — não há acesso disponível

## Traceability

| REQ-ID | Phase |
|--------|-------|
| ROB-01, ROB-02, ROB-03, ROB-04 | Fase 1 |
| UX-01, UX-02 | Fase 2 |
| LOG-01 | Fase 3 |
