---
status: partial
phase: 1-Robustez-Automação
source: [01-VERIFICATION.md]
started: 2026-06-05
updated: 2026-06-05
---

## Current Test

[aguardando teste humano na máquina da loja]

## Tests

### 1. Botão "Abrir pasta de screenshots" aparece após erro
Executar com CPF inexistente (ex: 12345678901) e confirmar que:
- Um arquivo `.png` é criado em `%LOCALAPPDATA%\ClubeAlteraDados\screenshots\`
- O botão "Abrir pasta de screenshots" aparece na janela da UI após o erro
- Clicar no botão abre o Explorer na pasta correta

expected: Botão visível na UI; arquivo PNG presente na pasta de screenshots
result: [pending]

### 2. Mensagem de erro sem traceback Python
Após qualquer falha do Playwright, confirmar que:
- O log da UI mostra texto legível em português (ex: "CPF não encontrado no sistema CRM...")
- Nenhum stack trace Python aparece na UI (apenas no pyerrors.log)

expected: Mensagem clara em português; sem "Traceback (most recent call last):" na UI
result: [pending]

### 3. Retry visível no log
Simular falha transitória (ex: desligar VPN/internet antes de rodar, ou usar rede lenta):
- O log deve exibir "Tentativa 1/3 falhou: ... Aguardando 2s antes de tentar novamente..."
- Após 3 falhas: "Todas as 3 tentativas falharam."

expected: 3 tentativas visíveis no log com intervalo de ~2s entre elas
result: [pending]

## Summary

total: 3
passed: 0
issues: 0
pending: 3
skipped: 0
blocked: 0

## Gaps
