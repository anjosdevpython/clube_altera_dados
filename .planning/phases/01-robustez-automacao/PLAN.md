# Phase 1: Robustez da Automação — Execution Plan

**File:** `CLUBE_modif.py` (single-file modification, all changes go here)
**Goal:** O operador nunca recebe "deu erro" sem saber o que aconteceu — falhas têm diagnóstico, screenshots e retries automáticos.
**Requirements:** ROB-01, ROB-02, ROB-03, ROB-04

---

## Execution Order

Tasks must be executed in order. Each task builds on the previous.

| Task | Title | Depends On | Requirement |
|------|-------|------------|-------------|
| T-01 | Imports e constantes base | — | ROB-01, ROB-04 |
| T-02 | `tirar_screenshot_erro()` + `report_log` com screenshot_path | T-01 | ROB-01 |
| T-03 | `mostrar_btn_screenshots()` na classe UI | T-02 | ROB-01 |
| T-04 | `SELECTORS` dict + `tentar_seletores()` | T-01 | ROB-04 |
| T-05 | `classificar_erro()` | T-01 | ROB-02 |
| T-06 | `executar_com_retry()` | T-05 | ROB-03 |
| T-07 | Refatorar `loguin_function_Zanthus()` | T-02, T-04 | ROB-01, ROB-04 |
| T-08 | Refatorar `loguin_function()` | T-02, T-04 | ROB-01, ROB-04 |
| T-09 | Refatorar `clientes_page()` e `alterar_dados()` | T-02, T-04, T-05 | ROB-01, ROB-02, ROB-04 |
| T-10 | Integrar retry em `iniciar()` + mensagens de sucesso | T-06 | ROB-02, ROB-03 |
| T-11 | `adicionar_log` recebe `screenshot_path` opcional | T-02, T-03 | ROB-01 |

---

## T-01 — Imports e constantes base

**File:** `CLUBE_modif.py`, bloco de imports no topo (após linha 17, antes de `import urllib`)

**Mudanças:**

1. Adicionar import das classes de exceção do Playwright logo após a linha `from playwright.sync_api import sync_playwright`:

```
from playwright.sync_api import (
    sync_playwright,
    Error as PlaywrightError,
    TimeoutError as PlaywrightTimeoutError,
)
```

Remover o `from playwright.sync_api import sync_playwright` existente (linha 5) e substituir por esse bloco.

2. Adicionar após a linha `caminho_logs = ...` (linha 61) e `caminho_dados = ...` (linha 62), antes do `os.makedirs(caminho_logs, ...)`:

```python
caminho_screenshots = os.path.join(app_data_dir, "screenshots")
os.makedirs(caminho_screenshots, exist_ok=True)
```

**Verificacao:**
- `python -c "from playwright.sync_api import Error as PlaywrightError, TimeoutError as PlaywrightTimeoutError; print('OK')"` deve imprimir `OK` sem erro.
- Variavel `caminho_screenshots` deve estar definida no escopo do modulo quando o arquivo for importado.

**Criterio de aceite:** Nenhum `NameError` ou `ImportError` ao iniciar o programa.

---

## T-02 — Funcao `tirar_screenshot_erro()`

**File:** `CLUBE_modif.py`, inserir como funcao de modulo apos `def report_log(...)` (apos linha 100)

**Mudanças:**

Adicionar a funcao a seguir imediatamente apos o bloco `def report_log(msg, tipo="info"):`:

```python
def tirar_screenshot_erro(prefixo: str = "erro") -> str | None:
    """
    Captura screenshot da pagina atual e salva em caminho_screenshots.
    Deve ser chamada ANTES de finalizar_playwright().
    Retorna o caminho do arquivo salvo, ou None se falhar.
    """
    global page
    if page is None:
        return None
    try:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{prefixo}_{ts}.png"
        filepath = os.path.join(caminho_screenshots, filename)
        page.screenshot(path=filepath, full_page=True)
        return filepath
    except Exception as exc_screenshot:
        logging.warning(f"Screenshot falhou (nao critica): {exc_screenshot}")
        return None
```

Notas de implementacao:
- A funcao acessa `page` via global — consistente com o padrao existente no modulo.
- O guard `if page is None` previne `AttributeError` se `funcionais()` nao foi chamada ainda.
- O `try/except Exception` interno impede que falha de screenshot mascare o erro original.
- Nao recebe `page` como argumento — usa o global, igual a `finalizar_playwright()`.

**Verificacao:**
- Inspecionar visualmente que a funcao esta presente e recua com 4 espacos.
- Garantir que `caminho_screenshots` (definido em T-01) e `datetime` estao acessiveis no escopo.

**Criterio de aceite:** Funcao definida; chamar `tirar_screenshot_erro("teste")` com `page is None` retorna `None` sem excecao.

---

## T-03 — Metodo `mostrar_btn_screenshots()` na classe `AlterarDadosClientesApp`

**File:** `CLUBE_modif.py`, dentro da classe `AlterarDadosClientesApp`, inserir apos o metodo `fechar_progressbar` (apos linha 732)

**Mudanças:**

Adicionar o metodo abaixo, identado como metodo da classe:

```python
def mostrar_btn_screenshots(self):
    """
    Exibe botao 'Abrir pasta de screenshots' abaixo do log.
    Thread-safe: deve ser chamado via root.after(0, ...).
    Nao duplica o botao se ja estiver visivel.
    """
    if hasattr(self, '_btn_screenshots') and self._btn_screenshots.winfo_exists():
        return
    self._btn_screenshots = ttk.Button(
        self.root,
        text="Abrir pasta de screenshots",
        bootstyle="warning-outline",
        command=lambda: subprocess.Popen(
            f'explorer "{caminho_screenshots}"',
            shell=True
        )
    )
    self._btn_screenshots.pack(pady=(2, 5), padx=20, fill="x")
```

Notas:
- `shell=True` e necessario para `subprocess.Popen` com string no Windows quando se usa `explorer`.
- `winfo_exists()` retorna 0 (falsy) para widgets destruidos — o guard impede duplicacao.
- `caminho_screenshots` e o global definido em T-01.

**Verificacao:**
- Inspecionar que o metodo esta identado corretamente como metodo da classe.
- Chamar `app.root.after(0, app.mostrar_btn_screenshots)` no console nao deve gerar erro.

**Criterio de aceite:** Metodo existe; chamar duas vezes nao cria dois botoes.

---

## T-04 — Dict `SELECTORS` e funcao `tentar_seletores()`

**File:** `CLUBE_modif.py`, inserir como constante e funcao de modulo apos `def tirar_screenshot_erro(...)` (apos T-02)

**Mudanças:**

Adicionar o bloco a seguir (constante + funcao) apos `tirar_screenshot_erro`:

```python
# ============================================================================
# SELECTORS — Seletores com fallback para resistir a mudancas no HTML do CRM
# Estrutura: { "chave": ["seletor_primario", "fallback_1", "fallback_2"] }
# ============================================================================
SELECTORS = {
    # Zanthus
    "zanthus_usuario":      ["#USUARIO",         "input[name='USUARIO']",         "input[name='usuario']"],
    "zanthus_senha":        ["#SENHA",            "input[name='SENHA']",           "input[name='senha']"],
    "zanthus_submit":       ['//input[@type="submit" and @value=" Entrar "]', 'input[type="submit"]', 'button[type="submit"]'],
    "zanthus_menu":         ["#Menu",             ".menu-principal",               "[id*='Menu']"],
    # CRM (Bnex)
    "crm_usuario":          ["#Usuario",          "input[name='Usuario']",         "input[name='usuario']"],
    "crm_senha_login":      ["#Senha",            "input[name='Senha']",           "input[name='senha']"],
    "crm_btn_entrar":       ["#btnEntrar",        "button[type='submit']",         "input[type='submit']"],
    "crm_cpf_campo":        ["#cpfcliente",       "input[name='cpfcliente']",      "input[placeholder*='CPF']"],
    "crm_btn_editar":       ["#btnEditar",        ".btn-editar",                   "button:has-text('Editar')"],
    "crm_nome":             ["#Nome",             "input[name='Nome']",            "input[id*='Nome']"],
    "crm_email":            ["#Email",            "input[name='Email']",           "input[type='email']"],
    "crm_confirmar_email":  ["#ConfirmarEmail",   "input[name='ConfirmarEmail']",  "input[placeholder*='onfirm']"],
    "crm_nova_senha":       ["#Senha",            "input[name='Senha']",           "input[type='password']"],
    "crm_confirmar_senha":  ["#ConfirmarSenha",   "input[name='ConfirmarSenha']",  "input[placeholder*='onfirm']"],
    "crm_btn_salvar":       ["#btnSalvar",        "button:has-text('Salvar')",     "input[value='Salvar']"],
    "crm_msg_ok":           ["#lnkMensagemOK",    ".mensagem-ok",                  "[id*='MensagemOK']"],
}


def tentar_seletores(page_obj, chave: str, acao: str, step: str = "", **kwargs):
    """
    Tenta cada seletor em SELECTORS[chave] em ordem sequencial.

    Parametros:
        page_obj: instancia de Page do Playwright (passa page global ou parametro).
        chave: chave em SELECTORS (ex: "crm_cpf_campo").
        acao: 'fill' | 'click' | 'wait' | 'locator'.
        step: nome da etapa para mensagens de erro (ex: "busca_cpf").
        kwargs:
            valor (str)    — para acao='fill'
            timeout (int)  — milissegundos, default 10000 para 'wait', 5000 para outros

    Retorna:
        None para 'fill', 'click', 'wait'.
        Locator para 'locator'.

    Levanta:
        PlaywrightError com mensagem descritiva se todos os seletores falharem.
    """
    seletores = SELECTORS.get(chave, [])
    if not seletores:
        raise ValueError(f"Chave '{chave}' nao encontrada em SELECTORS")

    erros = []
    for i, sel in enumerate(seletores):
        try:
            if acao == "fill":
                valor = kwargs.get("valor", "")
                timeout = kwargs.get("timeout", 5000)
                page_obj.locator(sel).fill(valor, timeout=timeout)
                if i > 0:
                    report_log(f"[SELETOR] '{chave}' usou fallback #{i}: {sel}", "info")
                return None

            elif acao == "click":
                timeout = kwargs.get("timeout", 5000)
                page_obj.locator(sel).click(timeout=timeout)
                if i > 0:
                    report_log(f"[SELETOR] '{chave}' usou fallback #{i}: {sel}", "info")
                return None

            elif acao == "wait":
                timeout = kwargs.get("timeout", 10000)
                page_obj.wait_for_selector(sel, timeout=timeout)
                if i > 0:
                    report_log(f"[SELETOR] '{chave}' usou fallback #{i}: {sel}", "info")
                return None

            elif acao == "locator":
                loc = page_obj.locator(sel)
                loc.wait_for(state="attached", timeout=kwargs.get("timeout", 5000))
                if i > 0:
                    report_log(f"[SELETOR] '{chave}' usou fallback #{i}: {sel}", "info")
                return loc

        except (PlaywrightTimeoutError, PlaywrightError) as exc_sel:
            erros.append(f"  [{i}] '{sel}': {exc_sel.message[:100]}")
            continue

    msg = (
        f"Nenhum seletor funcionou para '{chave}' (etapa: {step}).\n"
        + "\n".join(erros)
    )
    raise PlaywrightError(msg)
```

**Verificacao:**
- `python -c "import CLUBE_modif; print(list(CLUBE_modif.SELECTORS.keys()))"` deve listar as 16 chaves sem erro (ajustar nome do modulo se necessario).
- SELECTORS deve ter exatamente 16 chaves: `zanthus_usuario`, `zanthus_senha`, `zanthus_submit`, `zanthus_menu`, `crm_usuario`, `crm_senha_login`, `crm_btn_entrar`, `crm_cpf_campo`, `crm_btn_editar`, `crm_nome`, `crm_email`, `crm_confirmar_email`, `crm_nova_senha`, `crm_confirmar_senha`, `crm_btn_salvar`, `crm_msg_ok`.

**Criterio de aceite:** `SELECTORS` existe como dict de modulo com 16 chaves; `tentar_seletores` aceita os 4 valores de `acao` sem `NameError`.

---

## T-05 — Funcao `classificar_erro()`

**File:** `CLUBE_modif.py`, inserir apos `tentar_seletores` (apos T-04)

**Mudanças:**

Adicionar a funcao a seguir:

```python
def classificar_erro(e: Exception, step: str = "") -> tuple:
    """
    Recebe uma excecao e o nome da etapa onde ocorreu.
    Retorna (mensagem_para_operador: str, eh_permanente: bool).

    mensagem_para_operador: texto sem traceback, destinado ao log da UI.
    eh_permanente: True = nao tentar retry; False = erro transiente, retry valido.

    REGRA CRITICA: checar PlaywrightTimeoutError ANTES de PlaywrightError,
    pois TimeoutError e subclasse de Error.
    """
    # CPF nao encontrado: wait_for_selector("#btnEditar") atinge timeout na etapa de busca.
    # Distinguido pela etapa, nao pelo tipo de excecao.
    if step == "busca_cpf" and isinstance(e, PlaywrightTimeoutError):
        return (
            "CPF nao encontrado no sistema CRM. Verifique se o numero esta correto e cadastrado no Clube.",
            True,  # permanente — sem retry
        )

    # Todos os seletores falharam apos tentar_seletores() — mensagem ja vem descritiva
    if isinstance(e, PlaywrightError) and "Nenhum seletor funcionou" in str(e):
        return (
            f"Elemento da pagina nao encontrado (etapa: {step}). "
            "O layout do CRM pode ter mudado. Informe o TI.",
            True,  # permanente — retry nao resolve mudanca de layout
        )

    if isinstance(e, PlaywrightTimeoutError):
        msgs = {
            "login_zanthus": "Timeout ao carregar o portal Zanthus. O site pode estar lento ou fora do ar.",
            "login_crm":     "Timeout ao carregar o CRM. O site pode estar lento ou fora do ar.",
            "busca_cpf":     "Timeout aguardando resultado da busca de CPF no CRM.",
            "salvar":        "Timeout aguardando confirmacao do CRM apos salvar os dados.",
            "confirmar_ok":  "Timeout aguardando mensagem de confirmacao do CRM.",
        }
        msg = msgs.get(step, f"Operacao excedeu o tempo limite na etapa '{step}'. Tente novamente.")
        return (msg, False)  # transiente

    if isinstance(e, PlaywrightError):
        raw = e.message
        if "net::" in raw or "ERR_" in raw:
            primeira_linha = raw.split("\n")[0]
            return (
                f"Falha de conexao com o sistema ({primeira_linha}). Verifique sua internet.",
                False,  # transiente
            )
        if "closed" in raw.lower():
            return (
                "O navegador foi fechado inesperadamente. Tente novamente.",
                False,  # transiente
            )
        return (
            f"Erro inesperado do Playwright na etapa '{step}': {raw[:150]}",
            False,
        )

    # Erro Python puro (FileNotFoundError, ValueError, FileNotFoundError do crm_config, etc.)
    return (
        f"Erro interno do programa ({type(e).__name__}): {str(e)[:150]}",
        True,  # tratado como permanente — nao ha garantia de que retry resolve
    )
```

**Verificacao:**
- `classificar_erro(PlaywrightTimeoutError("x"), step="busca_cpf")` deve retornar `(msg_cpf, True)`.
- `classificar_erro(PlaywrightTimeoutError("x"), step="login_crm")` deve retornar `(msg_timeout, False)`.
- `classificar_erro(ValueError("config faltando"))` deve retornar `(msg_interno, True)`.

**Criterio de aceite:** Funcao retorna tupla `(str, bool)` em todos os ramos sem `NameError`.

---

## T-06 — Funcao `executar_com_retry()`

**File:** `CLUBE_modif.py`, inserir apos `classificar_erro` (apos T-05)

**Mudanças:**

Adicionar a funcao:

```python
def executar_com_retry(funcao_automacao, max_tentativas: int = 3, backoff_s: float = 2.0):
    """
    Executa funcao_automacao() com retry automatico para erros transientes.

    funcao_automacao: callable sem argumentos. Use lambda se precisar passar args.
    max_tentativas: numero maximo de tentativas (default 3, conforme D-09).
    backoff_s: segundos de espera entre tentativas (default 2, conforme D-09).

    Em caso de erro permanente (classificar_erro retorna eh_permanente=True),
    reporta e relanca imediatamente sem tentar novamente.

    Em caso de erro transiente, aguarda backoff_s e tenta novamente.
    Apos max_tentativas falhas, reporta e relanca o ultimo erro.
    """
    import time
    import traceback

    ultimo_erro = None
    for tentativa in range(1, max_tentativas + 1):
        try:
            funcao_automacao()
            return  # sucesso — encerra o loop
        except Exception as e:
            ultimo_erro = e
            logging.error(
                f"Tentativa {tentativa}/{max_tentativas} falhou:\n{traceback.format_exc()}"
            )
            # Determinar step a partir da mensagem de excecao (melhor esforco)
            step = _extrair_step_da_excecao(e)
            msg_ui, eh_permanente = classificar_erro(e, step=step)

            if eh_permanente:
                report_log(f"Erro permanente: {msg_ui}", "erro")
                raise

            if tentativa < max_tentativas:
                report_log(
                    f"Tentativa {tentativa}/{max_tentativas} falhou: {msg_ui} "
                    f"Aguardando {int(backoff_s)}s antes de tentar novamente...",
                    "erro",
                )
                time.sleep(backoff_s)
            else:
                report_log(
                    f"Todas as {max_tentativas} tentativas falharam. Ultimo erro: {msg_ui}",
                    "erro",
                )

    raise ultimo_erro


def _extrair_step_da_excecao(e: Exception) -> str:
    """
    Extrai o nome da etapa a partir da mensagem da excecao (convencao interna).
    As funcoes de automacao incluem o step no texto da excecao quando re-raise.
    Retorna string vazia se nao conseguir extrair.
    """
    msg = str(e)
    # Convencao: excecoes re-lançadas incluem "[step=<nome>]" no inicio
    import re
    match = re.search(r'\[step=([^\]]+)\]', msg)
    return match.group(1) if match else ""
```

**Verificacao:**
- Funcao `executar_com_retry` existe no modulo.
- Funcao auxiliar `_extrair_step_da_excecao` existe no modulo.

**Criterio de aceite:** `executar_com_retry(lambda: None)` executa sem erro; `executar_com_retry(lambda: 1/0, max_tentativas=2)` executa 2 tentativas e relanca `ZeroDivisionError`.

---

## T-07 — Refatorar `loguin_function_Zanthus()`

**File:** `CLUBE_modif.py`, substituir funcao existente `loguin_function_Zanthus()` (linhas 114-140)

**Mudanças:**

Substituir o corpo inteiro da funcao por:

```python
def loguin_function_Zanthus():
    global zanthus_confirmação
    try:
        funcionais()
        page.goto('https://minipreco.zanthus.bluesoft.com.br')

        report_log(f"Portal Zanthus carregado. Logando como {login_funcionario}...")
        tentar_seletores(page, "zanthus_usuario", "fill", step="login_zanthus", valor=login_funcionario)
        tentar_seletores(page, "zanthus_senha",   "fill", step="login_zanthus", valor=senha_funcionario)

        report_log("Enviando formulario de login Zanthus...")
        tentar_seletores(page, "zanthus_submit", "click", step="login_zanthus")

        try:
            tentar_seletores(page, "zanthus_menu", "wait", step="login_zanthus", timeout=10000)
            zanthus_confirmação = ['yes']
        except (PlaywrightTimeoutError, PlaywrightError):
            zanthus_confirmação = []

        finalizar_playwright()
    except Exception as e:
        caminho = tirar_screenshot_erro(prefixo=f"[step=login_zanthus]_erro")
        if caminho:
            report_log(f"Screenshot salvo: {caminho}", "info")
        finalizar_playwright()
        import traceback as _tb
        raise Exception(f"[step=login_zanthus] ERRO na funcao loguin_function_Zanthus(): {str(e)}\n{_tb.format_exc()}")
```

Notas criticas:
- O prefixo `[step=login_zanthus]` no nome do arquivo de screenshot e na mensagem de excecao permite que `_extrair_step_da_excecao` recupere o step.
- `tirar_screenshot_erro` e chamada ANTES de `finalizar_playwright()` — ordem obrigatoria (D-05, Pitfall 2).
- `tentar_seletores` substitui todos os `page.locator(...)` e `page.wait_for_selector(...)` diretos.
- O `except` final captura qualquer excecao incluindo as de `tentar_seletores`.

**Verificacao:**
- Inspecionar que nenhum `page.locator(...)` ou `page.wait_for_selector(...)` direto permanece na funcao.
- Inspecionar que `tirar_screenshot_erro` aparece antes de `finalizar_playwright()` no bloco except.

**Criterio de aceite:** Funcao nao contem `page.locator(` ou `page.wait_for_selector(` diretos; contem `tentar_seletores` e `tirar_screenshot_erro`.

---

## T-08 — Refatorar `loguin_function()`

**File:** `CLUBE_modif.py`, substituir funcao existente `loguin_function()` (linhas 306-328)

**Mudanças:**

Substituir o corpo inteiro da funcao por:

```python
def loguin_function():
    import traceback as _tb
    try:
        crm_usuario, crm_senha = _carregar_crm_config()
        funcionais()
        report_log("Acessando CRM Mini Preco (Bnex)...")
        page.goto('https://crm.grupominipreco.com.br')

        tentar_seletores(page, "crm_usuario",     "wait", step="login_crm", timeout=15000)
        report_log("Realizando login no CRM...")
        tentar_seletores(page, "crm_usuario",     "fill", step="login_crm", valor=crm_usuario)
        tentar_seletores(page, "crm_senha_login", "fill", step="login_crm", valor=crm_senha)
        tentar_seletores(page, "crm_btn_entrar",  "click", step="login_crm")

        page.wait_for_load_state("networkidle")

        report_log("Navegando para pagina de Clientes...")
        page.goto('https://crm.grupominipreco.com.br/Cliente/')
        tentar_seletores(page, "crm_cpf_campo", "wait", step="login_crm", timeout=30000)
    except Exception as e:
        caminho = tirar_screenshot_erro(prefixo="[step=login_crm]_erro")
        if caminho:
            report_log(f"Screenshot salvo: {caminho}", "info")
        finalizar_playwright()
        raise Exception(f"[step=login_crm] ERRO no login do CRM: {str(e)}\n{_tb.format_exc()}")
```

Notas:
- `page.wait_for_load_state("networkidle")` e mantido pois nao tem equivalente em SELECTORS — e uma espera de estado, nao de seletor.
- `page.goto(...)` e mantido direto — falhas de navegacao sao capturadas como `PlaywrightError` pelo `except Exception`.
- `tentar_seletores(... "wait" ...)` para `crm_usuario` substitui `page.wait_for_selector("#Usuario", timeout=15000)`.

**Verificacao:**
- Nenhum `page.locator(` ou `page.wait_for_selector(` direto na funcao.
- `tirar_screenshot_erro` antes de `finalizar_playwright()` no except.

**Criterio de aceite:** Funcao nao contem chamadas diretas ao Playwright exceto `page.goto` e `page.wait_for_load_state`; contem `tentar_seletores` e `tirar_screenshot_erro`.

---

## T-09 — Refatorar `clientes_page()` e `alterar_dados()`

**File:** `CLUBE_modif.py`, substituir as funcoes `clientes_page()` (linhas 330-362) e `alterar_dados()` (linhas 364-377)

**Mudanças:**

Substituir `clientes_page()` por:

```python
def clientes_page():
    global cpf, email, senha
    import traceback as _tb
    try:
        report_log(f"Buscando CPF: {cpf}")
        tentar_seletores(page, "crm_cpf_campo", "fill", step="busca_cpf", valor=cpf)
        page.keyboard.press("Enter")

        # CRITICO: timeout aqui = CPF nao encontrado (permanente).
        # classificar_erro detecta step="busca_cpf" + PlaywrightTimeoutError como permanente.
        tentar_seletores(page, "crm_btn_editar", "wait", step="busca_cpf", timeout=30000)
        report_log("Cliente encontrado. Abrindo edicao...")
        tentar_seletores(page, "crm_btn_editar", "click", step="busca_cpf")

        tentar_seletores(page, "crm_nome", "wait", step="edicao_dados", timeout=30000)

        alterar_dados()

        report_log("Enviando alteracoes no CRM...")
        tentar_seletores(page, "crm_btn_salvar", "click", step="salvar")

        report_log("Aguardando confirmacao de sucesso...")
        # lnkMensagemOK pode ter multiplas instancias — filtra o visivel
        seletores_ok = SELECTORS.get("crm_msg_ok", [])
        clicou_ok = False
        for sel in seletores_ok:
            try:
                page.locator(sel).filter(visible=True).first.click(timeout=15000)
                clicou_ok = True
                break
            except (PlaywrightTimeoutError, PlaywrightError):
                continue
        if not clicou_ok:
            raise PlaywrightError("[step=confirmar_ok] Mensagem de confirmacao nao encontrada apos salvar.")

        report_log("Confirmando mensagem de sucesso...", "sucesso")
        finalizar_playwright()
    except Exception as e:
        # Determinar step a partir da excecao para screenshot descritivo
        step_exc = _extrair_step_da_excecao(e) or "clientes_page"
        caminho = tirar_screenshot_erro(prefixo=f"[step={step_exc}]_erro")
        if caminho:
            report_log(f"Screenshot salvo: {caminho}", "info")
        finalizar_playwright()
        raise Exception(f"[step={step_exc}] ERRO ao processar pagina de cliente: {str(e)}\n{_tb.format_exc()}")
```

Substituir `alterar_dados()` por:

```python
def alterar_dados():
    import traceback as _tb
    try:
        if change_email:
            report_log(f"Alterando email para: {email}")
            tentar_seletores(page, "crm_email",           "fill", step="edicao_dados", valor=email)
            tentar_seletores(page, "crm_confirmar_email", "fill", step="edicao_dados", valor=email)

        if change_password:
            report_log("Alterando senha...")
            tentar_seletores(page, "crm_nova_senha",      "fill", step="edicao_dados", valor=senha)
            tentar_seletores(page, "crm_confirmar_senha", "fill", step="edicao_dados", valor=senha)
    except Exception as e:
        raise Exception(f"[step=edicao_dados] ERRO ao preencher dados: {str(e)}\n{_tb.format_exc()}")
```

Notas criticas:
- `crm_msg_ok` nao usa `tentar_seletores` para "click" porque o comportamento especial `.filter(visible=True).first` nao e suportado pelo helper. O loop manual mantem a logica de fallback.
- O prefixo `[step=busca_cpf]` na excecao de `tentar_seletores("crm_btn_editar", "wait")` garante que `_extrair_step_da_excecao` retorne `"busca_cpf"`, ativando o ramo permanente em `classificar_erro`.

**Verificacao:**
- Nenhum `page.locator(` direto em `alterar_dados()`.
- Em `clientes_page()`, os unicos `page.locator(` diretos sao para `crm_msg_ok` (logica especial de `.filter(visible=True)`).
- `tirar_screenshot_erro` aparece antes de `finalizar_playwright()`.

**Criterio de aceite:** `alterar_dados()` nao contem `page.locator(` direto; `clientes_page()` contem `tentar_seletores` para todas as operacoes exceto o loop de `crm_msg_ok`.

---

## T-10 — Integrar retry em `iniciar()` e mensagem de sucesso

**File:** `CLUBE_modif.py`, metodo `AlterarDadosClientesApp.iniciar()` (linhas 748-853)

**Mudanças:**

Localizar as tres ocorrencias de `main_function()` no metodo `iniciar()` (uma para cada modo: senha, email, ambos) e substituir cada uma por `executar_com_retry(main_function)`.

As tres ocorrencias estao nos blocos `try:` dentro dos `if change_password:`, `elif change_email:` e `elif change_all:`.

Antes:
```python
main_function()
```

Depois (em cada uma das tres ocorrencias):
```python
executar_com_retry(main_function)
```

Tambem atualizar as mensagens de sucesso (blocos `else:` apos cada `try/except`) para usar o formato do D-13:

Para `change_password` (linha ~803):
```python
tipo_alterado = "SENHA"
self.adicionar_log(f"✅ {tipo_alterado} alterado com sucesso para CPF {cpf}.", "sucesso")
messagebox.showinfo("Sucesso", f"Senha alterada com sucesso!\n\nCPF: {cpf}\nNova Senha: {senha}")
self.reset_values()
```

Para `change_email` (linha ~823):
```python
tipo_alterado = "EMAIL"
self.adicionar_log(f"✅ {tipo_alterado} alterado com sucesso para CPF {cpf}.", "sucesso")
messagebox.showinfo("Sucesso", f"Email alterado com sucesso!\n\nCPF: {cpf}\nNovo Email: {email}")
self.reset_values()
```

Para `change_all` (linha ~843):
```python
tipo_alterado = "SENHA E EMAIL"
self.adicionar_log(f"✅ {tipo_alterado} alterados com sucesso para CPF {cpf}.", "sucesso")
messagebox.showinfo("Sucesso", f"Senha e Email alterados!\n\nCPF: {cpf}")
self.reset_values()
```

Nota: os blocos `except Exception as err:` existentes e as chamadas `self.adicionar_log(f"Erro no CRM: {err}", "erro")` podem ser mantidos — `executar_com_retry` ja loga internamente, mas o `except` do `iniciar()` atua como safety net final para a UI.

**Verificacao:**
- Buscar `main_function()` no arquivo — deve aparecer exatamente 1 vez (dentro de `main_function` em si, linha 383) e 0 vezes dentro de `iniciar()`.
- Buscar `executar_com_retry(main_function)` — deve aparecer 3 vezes.
- As tres mensagens de sucesso devem conter `"✅"` e `"alterado com sucesso para CPF"`.

**Criterio de aceite:** `executar_com_retry(main_function)` aparece 3 vezes em `iniciar()`; mensagens de sucesso seguem o formato D-13.

---

## T-11 — Atualizar `adicionar_log()` e `report_log()` para `screenshot_path` opcional

**File:** `CLUBE_modif.py`, funcao global `report_log` (linhas 96-100) e metodo `AlterarDadosClientesApp.adicionar_log()` (linhas 702-727)

**Mudanças:**

Substituir `report_log` global por:

```python
def report_log(msg, tipo="info", screenshot_path=None):
    if log_callback:
        log_callback(msg, tipo, screenshot_path)
    else:
        print(f"[{tipo}] {msg}")
```

Substituir o metodo `adicionar_log` por:

```python
def adicionar_log(self, mensagem, tipo="info", screenshot_path=None):
    """Adiciona mensagem formatada ao log e salva no arquivo persistente."""
    def _add():
        self.log_text.config(state="normal")
        agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        try:
            cpf_txt = self.cpf_entry.get().strip() or "N/A"
        except:
            cpf_txt = "N/A"

        linha = f"{agora} - {mensagem} - {cpf_txt}"
        prefixo_icone = "✅" if tipo == "sucesso" else "❌" if tipo == "erro" else "🔹"

        self.log_text.insert(tk.END, f"{prefixo_icone} {linha}\n", tipo)

        try:
            log_file = os.path.join(caminho_logs, "automacoes.log")
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"{linha}\n")
        except:
            pass

        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")
        self.root.update_idletasks()

        # Mostrar botao de screenshots se houve screenshot nesta mensagem de erro
        if screenshot_path and tipo == "erro":
            self.mostrar_btn_screenshots()

    self.root.after(0, _add)
```

Notas:
- O parametro `screenshot_path` e opcional — todas as chamadas existentes a `report_log(msg, tipo)` continuam funcionando sem mudanca.
- `self.mostrar_btn_screenshots()` e chamado dentro de `_add`, que ja roda no main thread via `root.after(0, _add)` — thread-safe, sem necessidade de `root.after` adicional.
- O `log_text` ja tem o tag `"erro"` configurado (linha 612) — nao precisa adicionar.

**Verificacao:**
- `report_log("teste", "info")` sem `screenshot_path` funciona.
- `report_log("teste erro", "erro", screenshot_path="/tmp/x.png")` nao gera `TypeError`.
- `adicionar_log` aceita 2 ou 3 argumentos alem de `self`.

**Criterio de aceite:** Assinatura de `report_log` tem 3 parametros com defaults; `adicionar_log` tem 4 parametros com defaults; nenhuma chamada existente no codigo quebra.

---

## Verificacao Final do Conjunto

Apos completar T-01 a T-11, verificar:

1. **Screenshot salvo em falha real:**
   - Forcar erro digitando CPF invalido (ex: 12345678901 inexistente no CRM).
   - Verificar que `%LOCALAPPDATA%\ClubeAlteraDados\screenshots\` contem um arquivo `.png` apos o erro.
   - Verificar que o botao "Abrir pasta de screenshots" aparece na UI.

2. **Mensagem descritiva na UI:**
   - CPF inexistente deve mostrar mensagem sobre CPF nao encontrado (sem traceback).
   - Erro de rede (desligar VPN/internet antes de rodar) deve mostrar mensagem de conexao.

3. **Retry em acao:**
   - Simular timeout (throttling via DevTools ou rede lenta) — observar no log mensagens "Tentativa 1/3 falhou... Aguardando 2s".

4. **Selectors com fallback (inspecao de codigo):**
   - `grep -n "page.locator\|page.wait_for_selector" CLUBE_modif.py` deve retornar apenas:
     - Linhas dentro de `tentar_seletores()` (o helper em si)
     - Linha do loop `crm_msg_ok` em `clientes_page()`
     - Linhas dentro de `loguin_function_Zanthus()` somente se `page.wait_for_selector` for usado para verificar `#Menu` (aceitavel; alternativa e usar `tentar_seletores`)

5. **Smoke test de execucao normal:**
   - Operacao bem-sucedida deve mostrar `"✅ [TIPO] alterado com sucesso para CPF [numero]."` no log.
   - Nenhum traceback deve aparecer na UI (apenas no `pyerrors.log`).

---

## Mapa de Decisoes Implementadas

| Decisao | Task | Implementacao |
|---------|------|---------------|
| D-01: screenshots em %LOCALAPPDATA%\ClubeAlteraDados\screenshots\ | T-01 | `caminho_screenshots = os.path.join(app_data_dir, "screenshots")` |
| D-02: full_page=True | T-02 | `page.screenshot(path=filepath, full_page=True)` |
| D-03: nunca limpar screenshots | T-02 | Sem logica de limpeza na funcao |
| D-04: botao "Abrir pasta" na UI | T-03, T-11 | `mostrar_btn_screenshots()` via `adicionar_log` |
| D-05: screenshot ANTES de finalizar_playwright | T-07, T-08, T-09 | Ordem no except: screenshot → finalizar → raise |
| D-06: retry recomeça do inicio | T-06, T-10 | `executar_com_retry(main_function)` chama tudo do zero |
| D-07: retry em TimeoutError e erro de rede | T-05, T-06 | `classificar_erro` retorna `eh_permanente=False` |
| D-08: CPF nao encontrado = permanente | T-05 | `step == "busca_cpf"` + `PlaywrightTimeoutError` → `eh_permanente=True` |
| D-09: 2s backoff, 3 tentativas | T-06, T-10 | `executar_com_retry(..., max_tentativas=3, backoff_s=2.0)` |
| D-10: linguagem simples, acao clara | T-05 | Mensagens em `classificar_erro` sem jargao tecnico |
| D-11: traceback apenas no log de arquivo | T-06 | `logging.error(traceback.format_exc())` sem exibir na UI |
| D-12: classificacao por tipo de excecao | T-05 | `classificar_erro()` com ramos por tipo e step |
| D-13: mensagem de sucesso padronizada | T-10 | `"✅ [tipo] alterado com sucesso para CPF [cpf]."` |
| D-14: SELECTORS dict hard-coded | T-04 | `SELECTORS = { ... }` no modulo |
| D-15: 2 fallbacks por seletor | T-04 | Cada chave tem lista de 3 seletores |
| D-16: falha total = screenshot + erro descritivo | T-04 | `tentar_seletores` levanta `PlaywrightError` descritivo |
| D-17: atualizacoes via nova versao | — | Fora de escopo desta fase (GitHub Releases existente) |
