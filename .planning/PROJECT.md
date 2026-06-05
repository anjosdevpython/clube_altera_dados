# Clube Altera Dados

## What This Is

Ferramenta desktop interna para operadores da Mini Preço automatizarem a alteração de senha e email de clientes no CRM Bnex (Grupo Mini Preço), sem precisar navegar manualmente pelo sistema. O operador informa o CPF do cliente e os novos dados; um robô Playwright realiza a operação em background enquanto o operador acompanha o status em tempo real.

**Versão atual:** 1.0.12  
**Repositório:** anjosdevpython/clube_altera_dados  
**Distribuição:** PyInstaller → `.exe` + `updater.exe` separado

## Core Value

Operadores de atendimento conseguem alterar senha/email de clientes em segundos, com feedback visual em tempo real e rastreabilidade da operação — sem acesso manual ao CRM e sem depender de TI.

## Context

- **Usuários:** 10+ operadores simultâneos em máquinas Windows separadas
- **Sistemas integrados:** Portal Zanthus (validação de login do operador) + CRM Bnex (alteração de dados)
- **Conta de serviço CRM:** Compartilhada (GUSTAVO.ALVES), lida de `crm_config.json` externo
- **Auditoria:** Log local (`pyhistloc.txt`) com funcionário + CPF + timestamp; deve evoluir para log centralizado
- **Auto-update:** GitHub Releases API — operadores recebem notificação e podem atualizar sem TI

## Problem Statement

A versão atual tem quatro pontos críticos de dor:

1. **Falhas silenciosas** — erros do Playwright não ficam claros (CPF não encontrado, sessão expirada, elemento não localizado)
2. **Instabilidade** — seletores CSS/XPath frágeis; mudanças no HTML do CRM quebram a automação sem aviso
3. **Update complicado** — 10+ operadores, distribuição de nova versão é manual/frágil
4. **UX confusa** — operadores erram o fluxo; status messages não são suficientemente guiadas

## Requirements

### Validated

- ✓ Alterar senha de cliente por CPF — existente
- ✓ Alterar email de cliente por CPF — existente
- ✓ Alterar senha + email simultaneamente — existente
- ✓ Validação de login via Zanthus — existente
- ✓ Credenciais Zanthus criptografadas e reutilizadas — existente
- ✓ Log local de operações — existente
- ✓ Auto-update via GitHub Releases — existente
- ✓ Tema claro/escuro — existente

### Active

- [ ] Screenshot automático da tela do navegador em caso de falha
- [ ] Mensagens de erro descritivas por tipo de falha (CPF inexistente, sessão expirada, timeout, elemento não encontrado)
- [ ] Retry automático com backoff para falhas transitórias de rede
- [ ] Validação de elementos da página via múltiplos seletores (fallback robusto)
- [ ] Log centralizado em servidor (HTTP POST) além do log local
- [ ] Suporte a operação em lote (CSV/planilha de CPFs)
- [ ] Suporte a outros portais além do Bnex (arquitetura extensível)
- [ ] Update silencioso/automático em background para times grandes

### Out of Scope

- Interface web — ferramenta é desktop-only por design (acesso ao Windows da loja)
- Acesso autenticado por operador ao CRM — usa conta de serviço compartilhada por decisão da empresa
- Integração com banco de dados interno — não há acesso direto ao DB do CRM

## Key Decisions

| Decisão | Racional | Outcome |
|---------|----------|---------|
| Playwright headless | CRM não tem API; automação de UI é única opção | Em uso |
| Fernet com chave derivada do COMPUTERNAME | Senha do operador não trafega em texto claro; chave é por máquina | Em uso |
| Secrets em arquivos externos (.gitignored) | Evitar exposição de credenciais no repositório | Corrigido em 2025-06 |
| Auto-update via updater.exe separado | Permite substituir o exe principal sem precisar fechar o updater | Em uso |
| Log centralizado | Auditoria de 10+ operadores não pode depender de logs locais | — Pendente |
| Suporte multi-portal | Arquitetura atual é acoplada ao Bnex; extensão requer refatoração | — Pendente |

## Evolution

Este documento evolui em transições de fase e marcos.

**Após cada transição de fase** (via `/gsd-transition`):
1. Requisitos invalidados? → Mover para Out of Scope
2. Requisitos validados? → Mover para Validated com referência à fase
3. Novos requisitos? → Adicionar em Active
4. Decisões a registrar? → Adicionar em Key Decisions

---
*Última atualização: 2025-06-05 — inicialização do projeto GSD*
