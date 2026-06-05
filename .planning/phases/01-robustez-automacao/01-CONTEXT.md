# Phase 1: Robustez da Automação - Context

**Gathered:** 2025-06-05
**Status:** Ready for planning

<domain>
## Phase Boundary

Fazer com que toda falha do Playwright seja rastreável e autodiagnóstica: screenshot automático salvo em AppData, mensagem de erro humanizada por tipo de falha, retry automático para erros transitórios, e seletores com fallbacks hard-coded. O operador nunca recebe "deu erro" sem entender o que aconteceu e o que fazer.

**Em escopo:** ROB-01 (screenshot), ROB-02 (mensagens descritivas), ROB-03 (retry), ROB-04 (seletores fallback)
**Fora do escopo:** UX de progresso por etapa (Fase 2), log centralizado (Fase 3)

</domain>

<decisions>
## Implementation Decisions

### Screenshot de Falha (ROB-01)

- **D-01:** Salvar em `%LOCALAPPDATA%\ClubeAlteraDados\screenshots\` — mesma pasta dos logs, sem necessidade de admin
- **D-02:** Capturar `full_page=True` via `page.screenshot()` do Playwright — página inteira mesmo se rolada
- **D-03:** Manter screenshots para sempre (nunca limpar automaticamente) — supervisor pode precisar de evidência de dias anteriores
- **D-04:** Mostrar botão "Abrir pasta de screenshots" na UI junto com a mensagem de erro — zero atrito para o operador acessar
- **D-05:** `finalizar_playwright()` deve ser chamado DEPOIS do screenshot, não antes — ordem de operações crítica no `except`

### Retry Automático (ROB-03)

- **D-06:** Retry recomeça o fluxo completo do início (Zanthus → login CRM → busca CPF → edição) — mais simples, evita estado inconsistente do browser
- **D-07:** Erros que disparam retry: `TimeoutError` do Playwright (elemento/navegação) e erros de rede/navegação (`NavigationError`, `page.goto` falha)
- **D-08:** CPF não encontrado (`#btnEditar` nunca aparece após timeout) = erro permanente — sem retry; operador precisa verificar o número digitado
- **D-09:** 2 segundos fixos entre tentativas; até 3 tentativas antes de reportar erro definitivo

### Linguagem das Mensagens (ROB-02)

- **D-10:** Destinatário = operador de atendimento — linguagem simples, ação clara
- **D-11:** Traceback Python NÃO aparece na UI; vai apenas para `pyerrors.log` — UI mostra mensagem humanizada
- **D-12:** Classificação por tipo de exceção Playwright:
  - `TimeoutError` → "Timeout aguardando [elemento] — o CRM pode estar lento. Tentando novamente..."
  - `NavigationError` / falha em `goto` → "Erro de conexão — verifique a internet."
  - `#btnEditar` não aparece → "CPF [XXX] não encontrado no CRM. Verifique o número digitado."
  - Qualquer outro `LocatorError` → "Elemento da página não encontrado — o CRM pode ter mudado. Informe o TI."
  - Sessão expirada (detectada por falta de `#Menu` no Zanthus) → "Sessão Zanthus expirada. Faça login novamente."
- **D-13:** Mensagem de sucesso: "✅ [tipo alterado] alterado com sucesso para CPF [número]." — confirma o que foi feito

### Seletores com Fallback (ROB-04)

- **D-14:** Dicionário Python hard-coded `SELECTORS = { 'campo': ['#seletor_primario', 'fallback_1', 'fallback_2'] }` — fácil de ver e manter no código
- **D-15:** 2 seletores alternativos por elemento (além do principal) — cobre mudanças de classe/ID sem excesso de tentativas
- **D-16:** Quando TODOS os seletores falham → screenshot + erro descritivo: "Botão [X] não encontrado. O CRM pode ter mudado. Informe o TI." — sem tentar XPath genérico
- **D-17:** Atualizações de seletor via nova versão pelo desenvolvedor (GitHub Releases) — TI da loja não precisa editar arquivos

### Claude's Discretion

- Estratégia de tentativa dos seletores: tentar primário → fallback 1 → fallback 2 com `try/except` por tentativa; não usar `page.locator().or_()` pois dificulta diagnóstico de qual seletor funcionou

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Código da automação (arquivo principal)
- `CLUBE_modif.py` — arquivo único contendo toda a lógica de automação; funções relevantes: `loguin_function()`, `loguin_function_Zanthus()`, `clientes_page()`, `alterar_dados()`, `finalizar_playwright()`, `report_log()`

### Requirements
- `.planning/REQUIREMENTS.md` — requisitos ROB-01 a ROB-04 com critérios de sucesso da Fase 1
- `.planning/ROADMAP.md` — Phase 1 com success criteria observáveis

### Arquitetura
- `.planning/codebase/ARCHITECTURE.md` — mapa de componentes, fluxo de dados e seletores atuais em uso

### Sem specs externas
Não existem ADRs ou specs externas — decisões capturadas integralmente neste CONTEXT.md.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `report_log(msg, tipo)` — callback global que envia mensagens para a UI; tipos aceitos: `"info"`, `"sucesso"` (verde), adicionar `"erro"` (vermelho) e `"retry"` (amarelo?)
- `caminho_logs` — caminho para `%LOCALAPPDATA%\ClubeAlteraDados\logs\`; screenshots irão em `caminho_screenshots = os.path.join(app_data_dir, "screenshots")`
- `finalizar_playwright()` — fecha browser; deve ser refatorada para aceitar `take_screenshot=True` antes de fechar

### Established Patterns
- Automação em thread background, UI no thread principal — screenshots e erros devem ir via `report_log()` callback para thread-safety
- `try/except Exception as e` em todas as funções de automação — adicionar classificação antes do raise
- Globals do Playwright (`playwright_instance`, `browser`, `context`, `page`) — screenshot precisa de `page` disponível, por isso o order de operações no except é crítico

### Integration Points
- `main_function()` (linha ~356) — ponto de entrada do fluxo de automação; wrapper de retry vai aqui
- `AlterarDadosClientesApp.adicionar_log()` — método da UI que recebe mensagens via `log_callback`; botão "Abrir pasta" deve ser adicionado na área de status quando `tipo == "erro"`

</code_context>

<specifics>
## Specific Ideas

- Screenshot filename convention: `screenshot_YYYYMMDD_HHMMSS_CPF{cpf}.png` — rastreável por CPF e timestamp
- O botão "Abrir pasta de screenshots" pode usar `subprocess.Popen(['explorer', caminho_screenshots])` — nativo Windows, sem deps extras
- Para classificar sessão expirada no Zanthus: verificar se `page.url` contém "login" ou "logout" após o goto — sinal de redirecionamento por expiração

</specifics>

<deferred>
## Deferred Ideas

- UX com progresso por etapa (✓ Zanthus, ✓ Login CRM...) → Fase 2
- Botão "Tentar novamente" na UI após falha → Fase 2
- Log centralizado em servidor via HTTP POST → Fase 3
- Operação em lote via CSV → v2 backlog
- Seletores em JSON externo editável por TI → v2 backlog (usuário preferiu new version flow)

</deferred>

---

*Phase: 1-Robustez-Automação*
*Context gathered: 2025-06-05*
