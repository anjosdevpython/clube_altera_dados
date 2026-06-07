# Clube Altera Dados

## What This Is

Ferramenta desktop interna para operadores da Mini Preço automatizarem a alteração de senha e email de clientes no CRM Bnex (Grupo Mini Preço), sem precisar navegar manualmente pelo sistema. O operador informa o CPF do cliente e os novos dados; um robô Playwright realiza a operação em background com feedback visual etapa a etapa, retry automático em falhas transitórias, e auditoria centralizada via webhook.

**Versão atual:** 1.0 (milestone GSD v1.0 entregue)  
**Repositório:** anjosdevpython/clube_altera_dados  
**Distribuição:** PyInstaller → `.exe` + `updater.exe` separado

## Core Value

Operadores de atendimento conseguem alterar senha/email de clientes em segundos, com feedback visual em tempo real e rastreabilidade da operação — sem acesso manual ao CRM e sem depender de TI.

## Context

- **Usuários:** 10+ operadores simultâneos em máquinas Windows separadas
- **Sistemas integrados:** Portal Zanthus (validação de login do operador) + CRM Bnex (alteração de dados)
- **Conta de serviço CRM:** Compartilhada (GUSTAVO.ALVES), lida de `crm_config.json` externo
- **Auditoria:** Log local (`pyhistloc.txt`) + HTTP POST webhook configurável para supervisores
- **Auto-update:** GitHub Releases API — operadores recebem notificação e podem atualizar sem TI
- **Estado atual (pós v1.0):** CLUBE_modif.py com 1.241 LOC Python; Playwright headless; ttkbootstrap UI

## Requirements

### Validated

- ✓ Alterar senha de cliente por CPF — existente pré-GSD
- ✓ Alterar email de cliente por CPF — existente pré-GSD
- ✓ Alterar senha + email simultaneamente — existente pré-GSD
- ✓ Validação de login via Zanthus — existente pré-GSD
- ✓ Credenciais Zanthus criptografadas e reutilizadas — existente pré-GSD
- ✓ Log local de operações — existente pré-GSD
- ✓ Auto-update via GitHub Releases — existente pré-GSD
- ✓ Tema claro/escuro — existente pré-GSD
- ✓ Screenshot automático do browser em falha (AppData) — v1.0 (ROB-01)
- ✓ Mensagens de erro descritivas por tipo de falha — v1.0 (ROB-02)
- ✓ Retry automático com backoff 3×2s para falhas transitórias — v1.0 (ROB-03)
- ✓ Validação de elementos via múltiplos seletores com fallback — v1.0 (ROB-04)
- ✓ Log de progresso por etapa com checkmarks (✓ Zanthus → ✓ CRM → ✓ CPF → ✓ Dados) — v1.0 (UX-01)
- ✓ Botão "Tentar novamente" sem reiniciar o programa — v1.0 (UX-02)
- ✓ Auditoria centralizada via POST webhook (fire-and-forget, CPF mascarado LGPD) — v1.0 (LOG-01)

### Active

(Nenhum — próximo milestone a definir via /gsd-new-milestone)

### Out of Scope

- Interface web — desktop-only por design (acesso ao Windows da loja)
- Acesso autenticado por operador ao CRM — usa conta de serviço compartilhada por decisão da empresa
- Integração com banco de dados interno — não há acesso direto ao DB do CRM

## Constraints

- **Tech stack:** Python + Playwright + ttkbootstrap — não alterar sem análise de impacto nos operadores
- **Distribuição:** PyInstaller .exe — sem dependências externas na máquina dos operadores
- **Rede:** Acesso apenas à intranet da loja + CRM Bnex — sem VPN ou portas especiais disponíveis
- **Segredos:** crm_config.json e github_token.txt são gitignored e distribuídos fora do repositório

## Key Decisions

| Decisão | Racional | Outcome |
|---------|----------|---------|
| Playwright headless | CRM não tem API; automação de UI é única opção | ✓ Correto |
| Fernet com chave derivada do COMPUTERNAME | Senha do operador não trafega em texto claro; chave é por máquina | ✓ Correto |
| Secrets em arquivos externos (.gitignored) | Evitar exposição de credenciais no repositório | ✓ Correto |
| Auto-update via updater.exe separado | Permite substituir o exe principal sem precisar fechar o updater | ✓ Correto |
| Screenshot ANTES de finalizar_playwright() em todos os excepts | Garantir screenshot antes do browser fechar | ✓ Correto |
| CPF não encontrado = permanente (step='busca_cpf' + PlaywrightTimeoutError) | Retry de CPF inexistente é inútil | ✓ Correto |
| 3 tentativas, 2s backoff em executar_com_retry() | Falhas de rede costumam resolver em < 6s | ✓ Correto |
| SELECTORS hardcoded com 2 fallbacks por seletor | Entrega rápida de v1 — externalizar em v2 | ⚠️ Revisitar |
| root.after(0, _show) para retry button | Thread-safety Tkinter — padrão estabelecido | ✓ Correto |
| Payload LGPD mínimo — CPF mascarado (***XXXXX-XX) | Auditoria sem expor dado pessoal completo | ✓ Correto |
| webhook_url como única chave no crm_config.json | Ativar/desativar removendo a chave; sem flag extra | ✓ Correto |
| Fire-and-forget em daemon thread | Auditoria não pode bloquear operação principal | ✓ Correto |
| webhook_headers deferred para v2 | Endpoint n8n não exige auth no MVP | — Pendente |

## Evolution

Este documento evolui em transições de fase e marcos.

**Após cada transição de fase** (via `/gsd-transition`):
1. Requisitos invalidados? → Mover para Out of Scope
2. Requisitos validados? → Mover para Validated com referência à fase
3. Novos requisitos? → Adicionar em Active
4. Decisões a registrar? → Adicionar em Key Decisions

**Após cada milestone** (via `/gsd-complete-milestone`):
1. Revisão completa de todas as seções
2. Verificação do Core Value — ainda é a prioridade certa?
3. Auditoria de Out of Scope — razões ainda válidas?
4. Atualização do Context com estado atual

---
*Última atualização: 2026-06-07 após milestone v1.0*
