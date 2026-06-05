# Phase 1: Robustez da Automação — Research

**Researched:** 2026-06-05
**Domain:** Playwright sync API (Python) + Tkinter thread-safe UI patterns
**Confidence:** HIGH — all findings verified against installed playwright source code on this machine

---

## Summary

The app already has the correct structural skeleton: a background `threading.Thread`, a
`log_callback` that marshals UI writes via `root.after(0, fn)`, and a `finalizar_playwright()`
cleanup routine. Phase 1 adds a robustness layer on top of that skeleton: screenshots on
failure, classified error messages, automatic retries, and resilient selector fallbacks.

All four requirements (ROB-01 through ROB-04) are implementable with zero new dependencies.
Playwright's sync API already provides everything needed. The installed version is the
authoritative reference for this research — all class names and signatures below were
confirmed by inspecting the package source at runtime.

**Primary recommendation:** Wrap every automation function in a single `com_retries()`
decorator that handles screenshot-on-failure, error classification, and retry loop. Keep
`SELECTORS` as a plain dict of lists; each element function tries selectors in order with
individual `try/except` blocks.

---

## Playwright Exception Hierarchy (VERIFIED: runtime introspection)

There are exactly **three** exception classes exported from `playwright.sync_api`:

| Class | Inherits from | When raised |
|-------|--------------|-------------|
| `playwright.sync_api.Error` | `Exception` | All Playwright errors not listed below |
| `playwright.sync_api.TimeoutError` | `Error` | `wait_for_selector`, `wait_for_load_state`, `.click(timeout=...)`, `.fill(timeout=...)`, etc. exceed their timeout |
| `playwright.sync_api.WebError` | `SyncBase` (not `Error`) | Represents a web page error event — rarely caught directly |

`TargetClosedError` exists only in `playwright._impl._errors` (internal module). It is NOT
exported from `playwright.sync_api`. To detect it, check `isinstance(e, playwright.sync_api.Error)`
and inspect `e.message` for the string `"Target page, context or browser has been closed"`, or
catch it as `playwright.sync_api.Error`.

**There is no `NavigationError` class in Playwright Python.** Navigation failures (network
errors, SSL errors, unreachable host) raise `playwright.sync_api.Error` with a message
containing strings like `net::ERR_NAME_NOT_RESOLVED`, `net::ERR_CONNECTION_REFUSED`, etc.
The `error.name` attribute (inherited from the JS side) will be `"Error"` for navigation
failures, not a distinct subclass.

### Correct import block

```python
from playwright.sync_api import sync_playwright, Error as PlaywrightError, TimeoutError as PlaywrightTimeoutError
```

### Correct exception catch order

```python
try:
    ...
except PlaywrightTimeoutError as e:
    # TimeoutError IS-A Error, so this must come first
    classificar_erro(e, "timeout")
except PlaywrightError as e:
    # Catches navigation failures, TargetClosedError, LocatorError, etc.
    msg = e.message
    if "net::" in msg or "ERR_" in msg:
        classificar_erro(e, "navigation")
    elif "closed" in msg.lower():
        classificar_erro(e, "target_closed")
    else:
        classificar_erro(e, "generic_playwright")
except Exception as e:
    classificar_erro(e, "unexpected")
```

**Why this order matters:** `PlaywrightTimeoutError` is a subclass of `PlaywrightError`. If you
catch `PlaywrightError` first, `TimeoutError` is swallowed into the wrong branch and retried
incorrectly.

### "Locator" / "Selector" errors

When `page.locator(sel).click()` cannot find the element within the timeout, it raises
`PlaywrightTimeoutError` (not a separate `LocatorError` class). When the locator finds an
element but it is not visible/actionable, it also raises `PlaywrightTimeoutError`. There is no
separate `LocatorError` in this version. Distinguish "element not found" from "navigation
failed" by checking `e.message` for the word `"Timeout"` vs `"net::"`.

---

## ROB-01: Screenshot on Failure

### Safe screenshot call when page may be in error state

```python
# VERIFIED: runtime introspection of playwright.sync_api.Page.screenshot signature
def tirar_screenshot_erro(page, prefixo: str = "erro") -> str | None:
    """
    Tira screenshot de pagina inteira e salva em %LOCALAPPDATA%\\ClubeAlteraDados\\screenshots\\.
    Retorna o caminho salvo, ou None se falhar (page ja fechada, etc.).
    Deve ser chamado ANTES de finalizar_playwright().
    """
    import os
    from datetime import datetime
    try:
        screenshots_dir = os.path.join(
            os.environ.get('LOCALAPPDATA', os.path.expanduser('~\\AppData\\Local')),
            'ClubeAlteraDados', 'screenshots'
        )
        os.makedirs(screenshots_dir, exist_ok=True)

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{prefixo}_{ts}.png"
        filepath = os.path.join(screenshots_dir, filename)

        page.screenshot(path=filepath, full_page=True)
        return filepath
    except Exception as screenshot_exc:
        # Log silently — never let screenshot failure mask the original error
        logging.warning(f"Screenshot falhou: {screenshot_exc}")
        return None
```

**Key points:**
- Call `tirar_screenshot_erro(page, prefixo)` BEFORE calling `finalizar_playwright()`. Once
  `browser.close()` is called, the page object is invalid and `page.screenshot()` will raise.
- `page.screenshot()` can itself raise `PlaywrightError` if the page crashed or the renderer
  process died. Always wrap in `try/except Exception` — never let screenshot failure propagate.
- `full_page=True` is a keyword-only argument (no positional). [VERIFIED: runtime introspection]
- The `path=` argument accepts `str` — no need for `pathlib.Path`. [VERIFIED: runtime introspection]
- `page.screenshot()` returns `bytes` if no `path=` is given; if `path=` is given, it writes
  the file AND returns the bytes. For this use case, always pass `path=`. [VERIFIED: runtime introspection]

### Filename convention

```
erro_20260605_143022.png      # generic error
timeout_cpf_busca_20260605_143022.png   # prefixed by operation step
```

Use `prefixo` to encode the step name (e.g., `"timeout_login_zanthus"`, `"navigation_crm"`).

---

## ROB-02: Descriptive Error Messages

### Classification function

```python
def classificar_erro(e: Exception, tipo: str, step: str = "") -> tuple[str, bool]:
    """
    Retorna (mensagem_para_operador, eh_permanente).
    mensagem_para_operador: texto sem traceback, apto para o log da UI.
    eh_permanente: True = nao tentar retry.
    """
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError, Error as PlaywrightError

    msg = str(e) if not hasattr(e, 'message') else e.message

    if "cpf" in msg.lower() or "cliente nao encontrado" in msg.lower() or "btnEditar" in msg.lower():
        # wait_for_selector("#btnEditar") timeout = CPF nao encontrado no CRM
        return (
            f"CPF nao encontrado no sistema CRM. Verifique se o CPF esta correto e cadastrado no clube.",
            True   # permanente
        )

    if isinstance(e, PlaywrightTimeoutError):
        locais = {
            "login_zanthus": "Timeout ao carregar pagina do Zanthus. O site pode estar lento ou fora do ar.",
            "login_crm":     "Timeout ao carregar pagina do CRM. O site pode estar lento ou fora do ar.",
            "busca_cpf":     "Timeout aguardando resultado da busca do CPF.",
            "salvar":        "Timeout ao aguardar confirmacao do CRM apos salvar.",
            "default":       f"Operacao excedeu o tempo limite na etapa '{step}'. Tente novamente.",
        }
        return (locais.get(step, locais["default"]), False)  # transiente

    if isinstance(e, PlaywrightError):
        raw = e.message
        if "net::" in raw or "ERR_" in raw:
            return (
                f"Falha de conexao com o sistema ({raw.split(chr(10))[0]}). Verifique sua internet.",
                False  # transiente
            )
        if "closed" in raw.lower():
            return (
                "O navegador foi fechado inesperadamente. Tente novamente.",
                False  # transiente
            )
        if "selector" in raw.lower() or "locator" in raw.lower():
            return (
                f"Elemento da pagina nao encontrado na etapa '{step}'. O layout do site pode ter mudado.",
                False  # transiente — mas se todos seletores falharem, vira permanente
            )
        return (f"Erro inesperado do Playwright na etapa '{step}': {raw[:120]}", False)

    # Erro Python puro (FileNotFoundError, ValueError, etc.)
    return (f"Erro interno do programa: {type(e).__name__}: {str(e)[:120]}", True)
```

---

## ROB-03: Retry Wrapper

### Design decision (already locked)

- 3 max attempts, 2 s fixed backoff between attempts
- Retry restarts from the beginning (chama `main_function()` de novo, nao apenas a etapa falha)
- `CPF nao encontrado` = permanente, sem retry
- Traceback vai apenas para o log de arquivo, nao para a UI

### Retry wrapper pattern

```python
import time
import logging
import traceback

def executar_com_retry(funcao_automacao, report_log_fn, max_tentativas: int = 3, backoff_s: float = 2.0):
    """
    Executa funcao_automacao com retry automatico para erros transientes.
    funcao_automacao: callable sem argumentos (use functools.partial ou lambda se precisar de args).
    report_log_fn: callback report_log(msg, tipo).
    Levanta a ultima excecao se todas as tentativas falharem.
    """
    ultimo_erro = None
    for tentativa in range(1, max_tentativas + 1):
        try:
            funcao_automacao()
            return  # sucesso
        except Exception as e:
            ultimo_erro = e
            # Log do traceback completo apenas no arquivo
            logging.error(
                f"Tentativa {tentativa}/{max_tentativas} falhou:\n{traceback.format_exc()}"
            )
            # Classificar o erro
            msg_ui, eh_permanente = classificar_erro(e, step="automacao")

            if eh_permanente:
                report_log_fn(f"Erro permanente: {msg_ui}", "erro")
                raise  # nao tenta retry

            if tentativa < max_tentativas:
                report_log_fn(
                    f"Tentativa {tentativa}/{max_tentativas} falhou: {msg_ui}. "
                    f"Aguardando {backoff_s}s antes de tentar novamente...",
                    "erro"
                )
                time.sleep(backoff_s)
            else:
                report_log_fn(
                    f"Todas as {max_tentativas} tentativas falharam. Ultimo erro: {msg_ui}",
                    "erro"
                )

    raise ultimo_erro
```

### Integration point in `iniciar()` (existing method in `AlterarDadosClientesApp`)

Replace the current bare `main_function()` calls with:

```python
executar_com_retry(
    lambda: main_function(),
    report_log_fn=self.adicionar_log,
    max_tentativas=3,
    backoff_s=2.0
)
```

### Where to take the screenshot within the retry wrapper

The screenshot must happen INSIDE `main_function()` (or the functions it calls), BEFORE
`finalizar_playwright()` is called — because `executar_com_retry` does not have access to
the `page` global. Recommended pattern:

```python
# Inside loguin_function(), clientes_page(), etc. — in their except blocks:
except Exception as e:
    caminho = tirar_screenshot_erro(page, prefixo=f"erro_{step_name}")
    if caminho:
        report_log(f"Screenshot salvo: {caminho}", "info")
    finalizar_playwright()
    raise  # re-raise so the retry wrapper sees it
```

---

## ROB-04: SELECTORS Dict with 2 Fallbacks — Sequential try/except

### Design decision (already locked)

- `SELECTORS` is a top-level dict in the module, mapping step names to a list of selectors
  (primary + 2 fallbacks = up to 3 per element)
- Try each selector with individual `try/except` — not with `.or_()`
- On failure of ALL selectors: screenshot + descriptive error, raise immediately (no XPath fallback)
- Log WHICH selector succeeded (for diagnostics when sites change)

### SELECTORS dict structure

```python
SELECTORS = {
    # Zanthus
    "zanthus_usuario":  ["#USUARIO",         "input[name='USUARIO']",    "input[name='usuario']"],
    "zanthus_senha":    ["#SENHA",            "input[name='SENHA']",      "input[name='senha']"],
    "zanthus_submit":   ['//input[@type="submit" and @value=" Entrar "]', 'input[type="submit"]', 'button[type="submit"]'],
    "zanthus_menu":     ["#Menu",             ".menu-principal",          "[id*='Menu']"],

    # CRM (Bnex)
    "crm_usuario":      ["#Usuario",          "input[name='Usuario']",    "input[name='usuario']"],
    "crm_senha":        ["#Senha",            "input[name='Senha']",      "input[name='senha']"],
    "crm_btn_entrar":   ["#btnEntrar",        "button[type='submit']",    "input[type='submit']"],
    "crm_cpf_campo":    ["#cpfcliente",       "input[name='cpfcliente']", "input[placeholder*='CPF']"],
    "crm_btn_editar":   ["#btnEditar",        ".btn-editar",              "button:has-text('Editar')"],
    "crm_nome":         ["#Nome",             "input[name='Nome']",       "input[id*='Nome']"],
    "crm_email":        ["#Email",            "input[name='Email']",      "input[type='email']"],
    "crm_confirmar_email": ["#ConfirmarEmail","input[name='ConfirmarEmail']","input[placeholder*='onfirm']"],
    "crm_nova_senha":   ["#Senha",            "input[name='Senha']",      "input[type='password']"],
    "crm_confirmar_senha": ["#ConfirmarSenha","input[name='ConfirmarSenha']","input[placeholder*='onfirm']"],
    "crm_btn_salvar":   ["#btnSalvar",        "button:has-text('Salvar')", "input[value='Salvar']"],
    "crm_msg_ok":       ["#lnkMensagemOK",    ".mensagem-ok",             "[id*='MensagemOK']"],
}
```

### Helper function: try selectors sequentially

```python
def tentar_seletores(page, chave: str, acao: str, step: str = "", **kwargs):
    """
    Tenta cada seletor em SELECTORS[chave] em ordem.
    acao: 'fill', 'click', 'wait', 'locator' (retorna o Locator sem interagir)
    kwargs: passados para fill() ou click()
    Retorna o valor retornado pela acao (Locator se acao='locator', None para fill/click/wait).
    Levanta PlaywrightError com mensagem descritiva se TODOS os seletores falharem.
    """
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError, Error as PlaywrightError
    seletores = SELECTORS.get(chave, [])
    if not seletores:
        raise ValueError(f"Chave '{chave}' nao encontrada em SELECTORS")

    erros = []
    for i, sel in enumerate(seletores):
        try:
            if acao == "fill":
                valor = kwargs.get("valor", "")
                timeout = kwargs.get("timeout", 5000)
                page.locator(sel).fill(valor, timeout=timeout)
                if i > 0:
                    report_log(f"[SELETOR] '{chave}' usou fallback #{i}: {sel}", "info")
                return None

            elif acao == "click":
                timeout = kwargs.get("timeout", 5000)
                page.locator(sel).click(timeout=timeout)
                if i > 0:
                    report_log(f"[SELETOR] '{chave}' usou fallback #{i}: {sel}", "info")
                return None

            elif acao == "wait":
                timeout = kwargs.get("timeout", 10000)
                page.wait_for_selector(sel, timeout=timeout)
                if i > 0:
                    report_log(f"[SELETOR] '{chave}' usou fallback #{i}: {sel}", "info")
                return None

            elif acao == "locator":
                loc = page.locator(sel)
                # Validate it exists with a short timeout
                loc.wait_for(state="attached", timeout=kwargs.get("timeout", 5000))
                if i > 0:
                    report_log(f"[SELETOR] '{chave}' usou fallback #{i}: {sel}", "info")
                return loc

        except (PlaywrightTimeoutError, PlaywrightError) as e:
            erros.append(f"  [{i}] '{sel}': {e.message[:80]}")
            continue  # try next selector

    # All selectors failed
    msg = (
        f"Nenhum seletor funcionou para '{chave}' (etapa: {step}).\n"
        + "\n".join(erros)
    )
    raise PlaywrightError(msg)
```

**Usage example (replacing existing direct locator calls):**

```python
# Before:
page.locator("#USUARIO").fill(login_funcionario)
page.locator("#SENHA").fill(senha_funcionario)

# After:
tentar_seletores(page, "zanthus_usuario", "fill", step="login_zanthus", valor=login_funcionario)
tentar_seletores(page, "zanthus_senha",   "fill", step="login_zanthus", valor=senha_funcionario)
```

---

## Thread-safe Tkinter Pattern (ROB-01 + UI button)

### How the existing pattern works (already correct)

The app already uses the correct pattern in `adicionar_log()`:

```python
def adicionar_log(self, mensagem, tipo="info"):
    def _add():
        # ... modify Text widget ...
    self.root.after(0, _add)   # schedules _add on the main thread's event loop
```

`root.after(0, fn)` is the canonical thread-safe way to execute Tkinter code from a
background thread. [ASSUMED — standard Tkinter threading documentation pattern]

### Adding a "Abrir pasta de screenshots" button after an error

The button must be created on the main thread. The pattern is the same — schedule creation
via `root.after(0, ...)` from the background thread callback:

```python
# In AlterarDadosClientesApp:

def mostrar_btn_screenshots(self):
    """Chamado via root.after() quando uma screenshot foi salva."""
    import subprocess
    screenshots_dir = os.path.join(
        os.environ.get('LOCALAPPDATA', os.path.expanduser('~\\AppData\\Local')),
        'ClubeAlteraDados', 'screenshots'
    )
    # Only show the button once — check if it already exists
    if hasattr(self, '_btn_screenshots') and self._btn_screenshots.winfo_exists():
        return  # already visible

    self._btn_screenshots = ttk.Button(
        self.root,  # or a specific frame in the layout
        text="Abrir pasta de screenshots",
        bootstyle="warning-outline",
        command=lambda: subprocess.Popen(f'explorer "{screenshots_dir}"')
    )
    self._btn_screenshots.pack(pady=(2, 5), padx=20, fill="x")
```

From the background thread (or from `adicionar_log` when `tipo == "erro"` and a screenshot
path is known):

```python
# In the error handling path inside run_in_thread or via a special callback:
self.root.after(0, self.mostrar_btn_screenshots)
```

### Extended callback signature for passing screenshot path

The current `log_callback = self.adicionar_log` signature is `(msg, tipo)`. To pass a
screenshot path without changing all call sites, add an optional third parameter:

```python
def adicionar_log(self, mensagem, tipo="info", screenshot_path: str = None):
    def _add():
        # ... existing log code ...
        if screenshot_path and tipo == "erro":
            self.mostrar_btn_screenshots()  # safe: already on main thread inside _add
    self.root.after(0, _add)
```

And update the global `report_log`:

```python
def report_log(msg, tipo="info", screenshot_path=None):
    if log_callback:
        log_callback(msg, tipo, screenshot_path)
    else:
        print(f"[{tipo}] {msg}")
```

---

## Common Pitfalls

### Pitfall 1: Catching `PlaywrightError` before `PlaywrightTimeoutError`
**What goes wrong:** `TimeoutError` is a subclass of `Error`. If `except Error` appears
first, timeout errors are classified as generic errors and retried with wrong logic.
**How to avoid:** Always write `except PlaywrightTimeoutError` before `except PlaywrightError`.

### Pitfall 2: Taking screenshot AFTER `finalizar_playwright()`
**What goes wrong:** `browser.close()` invalidates all `Page` objects. `page.screenshot()`
then raises `PlaywrightError: Target page, context or browser has been closed`.
**How to avoid:** Screenshot call must come before `finalizar_playwright()` in every
`except` block. The pattern: screenshot → report → finalizar → raise.

### Pitfall 3: `page` global is `None` when screenshot is attempted
**What goes wrong:** If `funcionais()` failed (browser didn't launch), `page` is `None` and
`page.screenshot()` raises `AttributeError`.
**How to avoid:** `tirar_screenshot_erro()` should guard: `if page is None: return None`.

### Pitfall 4: `wait_for_selector` timeout for "CPF not found" looks like a transient timeout
**What goes wrong:** When the CRM can't find a CPF, it simply never shows `#btnEditar`.
`wait_for_selector("#btnEditar", timeout=30000)` raises `PlaywrightTimeoutError` — same
exception class as a slow network timeout. If you retry, you waste 3 attempts on a
permanent condition.
**How to avoid:** In `classificar_erro`, detect CPF-not-found by checking if the failing
step is `"busca_cpf"` AND the selector is `"#btnEditar"` (or `crm_btn_editar`). Mark as
permanent. This is why the `step` parameter in `classificar_erro` is important.

### Pitfall 5: `selectors` dict key for XPath vs CSS
**What goes wrong:** Playwright accepts both CSS selectors and XPath (prefix `//`).
`page.wait_for_selector('//input[@type="submit"]')` works, but
`page.locator('//input[@type="submit"]').fill(...)` also works. The risk is mixing
`wait_for_selector` (which takes a string) with `page.locator` (which also takes a string).
They are compatible — no pitfall here — but document it so the team doesn't add an `xpath=`
prefix unnecessarily.
**How to avoid:** Plain `//` prefix is sufficient for XPath in all Playwright selectors.

### Pitfall 6: Tkinter widget creation from background thread (without `root.after`)
**What goes wrong:** Calling `ttk.Button(...).pack()` directly from a background thread
causes random crashes or UI corruption because Tkinter is not thread-safe.
**How to avoid:** ALL widget creation and modification must go through `root.after(0, fn)`.
The `adicionar_log` method already does this correctly — extend the same pattern for the
screenshots button.

---

## Architecture Patterns

### Recommended call flow for each automation step

```
run_in_thread()
  └─ executar_com_retry(main_function, ...)
       └─ main_function()
            ├─ loguin_function_Zanthus()     # attempt 1
            │    ├─ funcionais()
            │    ├─ tentar_seletores(...)     # ROB-04
            │    ├─ [on except] tirar_screenshot_erro()   # ROB-01
            │    ├─ [on except] finalizar_playwright()
            │    └─ [on except] raise        # triggers retry in executar_com_retry
            └─ clientes_page()
                 ├─ tentar_seletores(...)
                 ├─ [on except] tirar_screenshot_erro()
                 ├─ [on except] finalizar_playwright()
                 └─ [on except] raise
```

The retry wrapper restarts from `main_function()` — so `funcionais()` (browser launch) is
re-executed on each retry. This is correct and was already decided.

### Recommended file structure change

No new files are needed. All new code goes into `CLUBE_modif.py`:
- `SELECTORS` dict: top-level constant, before `loguin_function_Zanthus()`
- `tirar_screenshot_erro()`: module-level function
- `classificar_erro()`: module-level function
- `tentar_seletores()`: module-level function
- `executar_com_retry()`: module-level function
- `mostrar_btn_screenshots()`: new method on `AlterarDadosClientesApp`

---

## Package Legitimacy Audit

No new packages are required for this phase. All requirements are implementable with:
- `playwright.sync_api` — already installed [VERIFIED: runtime]
- `os`, `time`, `logging`, `traceback`, `datetime`, `subprocess` — Python stdlib
- `tkinter`, `ttkbootstrap` — already installed [VERIFIED: present in codebase imports]

**Packages removed due to slopcheck:** none (no new packages)

---

## Environment Availability

| Dependency | Required By | Available | Notes |
|------------|-------------|-----------|-------|
| playwright (sync_api) | ROB-01, 02, 03, 04 | YES | Verified by runtime introspection |
| ttkbootstrap | Screenshots button UI | YES | Already in use |
| %LOCALAPPDATA% env var | ROB-01 screenshot path | YES | Windows — already used in app_data_dir |

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `root.after(0, fn)` is the canonical thread-safe pattern for Tkinter widget access | Thread-safe UI section | Low — this is universally documented; alternative is a Queue + polling loop, equally valid |
| A2 | `subprocess.Popen(f'explorer "{dir}"')` opens Windows Explorer to the folder | Screenshots button | Low — standard Windows shell invocation |

All exception class names, `page.screenshot()` signature, and `parse_error` mapping were
verified by runtime introspection of the installed package — not training data.

---

## Sources

### PRIMARY (HIGH confidence — runtime verified)
- `playwright._impl._errors` — source-inspected at runtime; confirms `Error`, `TimeoutError`, `TargetClosedError` class hierarchy
- `playwright._impl._helper.parse_error` — source-inspected at runtime; confirms how JS error names map to Python exception types (`"TimeoutError"` -> `TimeoutError`, everything else -> `Error`)
- `playwright.sync_api.Page.screenshot` — signature inspected at runtime; confirms `full_page`, `path`, `type` keyword arguments
- `CLUBE_modif.py` lines 96-100, 702-727, 734-746 — existing `report_log`, `adicionar_log`, `start_thread` / `run_in_thread` patterns read directly

### SECONDARY (MEDIUM confidence)
- Tkinter `after(0, fn)` thread-safety: standard pattern per Python docs; confirmed consistent with existing usage in `adicionar_log` [ASSUMED — standard Tkinter pattern]
