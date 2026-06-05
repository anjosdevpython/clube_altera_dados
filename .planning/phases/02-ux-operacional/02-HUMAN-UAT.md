---
status: partial
phase: 2-UX-Operacional
source: [02-VERIFICATION.md]
started: 2026-06-05
updated: 2026-06-05
---

## Current Test

[aguardando teste humano na máquina da loja]

## Tests

### 1. Checkmarks rendem em verde
Executar uma operação completa bem-sucedida e observar o log da UI.

expected: ✓ Zanthus validado → ✓ Login CRM realizado → ✓ CPF {cpf} encontrado → ✓ Dados salvos → ✓ Operação confirmada pelo CRM — todos em texto verde
result: [pending]

### 2. Botão amarelo "🔄 Tentar novamente" aparece após falha Zanthus
Inserir credencial Zanthus inválida e executar.

expected: Após messagebox de erro, botão amarelo "🔄 Tentar novamente" aparece na janela principal (bootstyle="warning")
result: [pending]

### 3. Retry preserva campos e exibe separador
Após falha, clicar em "🔄 Tentar novamente".

expected: (a) CPF, email/senha continuam preenchidos; (b) separador "──── Nova tentativa — HH:MM:SS ────" aparece no log antes de "Iniciando processo..."; (c) automação reinicia
result: [pending]

### 4. Botão some após operação bem-sucedida
Executar operação que falha → clicar "Tentar novamente" → operação tem sucesso.

expected: Botão "🔄 Tentar novamente" desaparece e campos são limpos (reset_values chamado)
result: [pending]

### 5. Separador Unicode renderiza corretamente no Windows
Observar o caractere U+2500 (─) no separador de log.

expected: Caractere "─" renderiza como linha horizontal contínua em fonte Consolas no widget Tkinter (não como "?" ou caixa)
result: [pending]

## Summary

total: 5
passed: 0
issues: 0
pending: 5
skipped: 0
blocked: 0

## Gaps

---

## Observação (não-bloqueante)

O texto do `messagebox.showerror` no branch `change_all` (linha ~1154) ainda diz "Reinicie o programa e tente novamente" — mensagem desatualizada pois o botão de retry já existe. Corrigir em oportunidade futura via commit isolado.
