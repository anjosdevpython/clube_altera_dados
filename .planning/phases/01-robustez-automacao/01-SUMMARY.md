---
phase: 1
plan: 01
subsystem: automacao-playwright
tags: [robustez, screenshots, retry, selectors, error-handling]
dependency_graph:
  requires: []
  provides: [tirar_screenshot_erro, SELECTORS, tentar_seletores, classificar_erro, executar_com_retry]
  affects: [CLUBE_modif.py]
tech_stack:
  added: []
  patterns: [selector-fallback, retry-with-backoff, screenshot-on-error, step-tagged-exceptions]
key_files:
  modified: [CLUBE_modif.py]
decisions:
  - "D-05: tirar_screenshot_erro() chamada ANTES de finalizar_playwright() em todos os excepts"
  - "D-08: CPF nao encontrado distinguido por step='busca_cpf' + PlaywrightTimeoutError, marcado como permanente"
  - "D-09: 3 tentativas, 2s backoff em executar_com_retry()"
  - "D-14/15: SELECTORS dict hardcoded com 2 fallbacks por seletor (16 chaves)"
metrics:
  duration: "~25min"
  completed: "2026-06-05"
  tasks_completed: 11
  tasks_total: 11
  files_modified: 1
---

# Phase 1 Plan 01: Robustez da Automacao — Summary

**One-liner:** Adicionadas screenshots automaticas em falha, retry com backoff, selectors com fallback e classificacao de erros em linguagem simples para o operador.

## Tasks Executadas

| Task | Titulo | Commit | Status |
|------|--------|--------|--------|
| T-01 | Imports e constantes base | 2779d2c | OK |
| T-02 | tirar_screenshot_erro() | c2bcba2 | OK |
| T-03 | mostrar_btn_screenshots() na classe UI | f40c52e | OK |
| T-04 | SELECTORS dict + tentar_seletores() | 7f47a09 | OK |
| T-05 | classificar_erro() | df5facf | OK |
| T-06 | executar_com_retry() | 7eb1b99 | OK |
| T-07 | Refatorar loguin_function_Zanthus() | 27f68d9 | OK |
| T-08 | Refatorar loguin_function() | b1c4f58 | OK |
| T-09 | Refatorar clientes_page() e alterar_dados() | c8fd740 | OK |
| T-10 | Integrar retry em iniciar() + mensagens de sucesso | 8d42156 | OK |
| T-11 | adicionar_log e report_log com screenshot_path opcional | bd37bbd | OK |

## O Que Foi Construido

### Infraestrutura de Erro

- **`tirar_screenshot_erro(prefixo)`** — captura full-page screenshot antes de fechar o browser, salva em `%LOCALAPPDATA%\ClubeAlteraDados\screenshots\`, retorna path ou None.
- **`classificar_erro(e, step)`** — classifica excecoes em `(mensagem_humana, eh_permanente)`. Trata `PlaywrightTimeoutError` antes de `PlaywrightError` (subclasse). CPF nao encontrado = permanente. Erros de rede = transiente.
- **`executar_com_retry(fn, max=3, backoff=2s)`** — executa com retry para erros transientes, loga no arquivo sem exibir traceback na UI, relanca imediatamente em erros permanentes.
- **`_extrair_step_da_excecao(e)`** — extrai `[step=nome]` da mensagem para routing de retry.

### Selectors com Fallback

- **`SELECTORS`** — dict com 16 chaves, 3 seletores cada (primario + 2 fallbacks).
- **`tentar_seletores(page_obj, chave, acao, step, **kwargs)`** — suporta `fill`, `click`, `wait`, `locator`. Loga quando usa fallback. Levanta `PlaywrightError` descritivo se todos falharem.

### Funcoes Refatoradas

- `loguin_function_Zanthus()` — usa `tentar_seletores`, screenshot antes de `finalizar_playwright()`, step tag na excecao.
- `loguin_function()` — idem, sem `page.wait_for_selector` direto.
- `clientes_page()` — usa `tentar_seletores` para todas as operacoes; loop manual apenas para `crm_msg_ok` (`.filter(visible=True)` nao suportado no helper).
- `alterar_dados()` — sem `page.locator()` direto.

### UI

- **`mostrar_btn_screenshots()`** — botao "Abrir pasta de screenshots" que aparece apos erro com screenshot; idempotente (guard `winfo_exists()`).
- **`adicionar_log(msg, tipo, screenshot_path=None)`** — chama `mostrar_btn_screenshots()` quando `screenshot_path` e fornecido e `tipo == "erro"`.
- **`report_log(msg, tipo, screenshot_path=None)`** — repassa `screenshot_path` para o callback.
- Mensagens de sucesso padronizadas: `"✅ {TIPO} alterado com sucesso para CPF {cpf}."`.

## Deviations from Plan

Nenhum — plano executado exatamente como especificado.

## Verificacoes Realizadas

- Syntax check via `ast.parse()`: PASS
- `tentar_seletores` occurrences: 20 (> 15 exigido)
- `executar_com_retry(main_function)` em `iniciar()`: 3 ocorrencias (exato)
- `SELECTORS` keys: 16 (exato)
- Mensagem de sucesso com `"alterado com sucesso para CPF"`: presente
- Import block `PlaywrightError` e `PlaywrightTimeoutError`: presente
- `caminho_screenshots`: definido no escopo do modulo

## Known Stubs

Nenhum.

## Threat Flags

Nenhum novo surface de segurança introduzido. Screenshots sao salvos localmente em `%LOCALAPPDATA%` — sem transmissao de dados.

## Self-Check: PASSED

Todos os 11 commits existem no historico git e o arquivo `CLUBE_modif.py` passa em syntax check.
