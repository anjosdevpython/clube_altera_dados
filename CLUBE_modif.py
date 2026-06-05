import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from playwright.sync_api import (
    sync_playwright,
    Error as PlaywrightError,
    TimeoutError as PlaywrightTimeoutError,
)
import os   
import random
import sys
import json
import hashlib
import base64
from datetime import datetime
import shutil
import subprocess
import logging
from time import sleep
import threading

import urllib.request
import urllib.error

# ============================================================================
# CONFIGURAÇÕES DE ATUALIZAÇÃO
# ============================================================================
CURRENT_VERSION = "1.0.12"
GITHUB_REPO = "anjosdevpython/clube_altera_dados"

if getattr(sys, 'frozen', False):
    # No PyInstaller 6+, arquivos extras podem estar em MEIPASS ou no _internal
    bundle_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(sys.executable)))
    # Pasta base onde fica o updater, version.txt e a pasta app
    base_proj_dir = os.path.dirname(os.path.dirname(os.path.abspath(sys.executable)))
    posssiveis_caminhos = [
        os.path.join(bundle_dir, "pw-browsers"),
        os.path.join(bundle_dir, "_internal", "pw-browsers")
    ]
    for caminho in posssiveis_caminhos:
        if os.path.exists(caminho):
            os.environ['PLAYWRIGHT_BROWSERS_PATH'] = caminho
            break
else:
    # Em desenvolvimento, usa o caminho relativo local
    base_proj_dir = os.path.dirname(os.path.abspath(__file__))
    os.environ['PLAYWRIGHT_BROWSERS_PATH'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pw-browsers")

# Tentar ler versão real do version.txt se existir
try:
    v_path = os.path.join(base_proj_dir, "version.txt")
    if os.path.exists(v_path):
        with open(v_path, "r") as vf:
            CURRENT_VERSION = vf.read().strip()
except: pass

# Definir pasta de dados do usuário para evitar PermissionError
if sys.platform == "win32":
    app_data_dir = os.path.join(os.environ.get('LOCALAPPDATA', os.path.expanduser('~\\AppData\\Local')), 'ClubeAlteraDados')
else:
    app_data_dir = os.path.join(os.path.expanduser('~'), '.clubealteradados')

# Configurar logging para erros
caminho_logs = os.path.join(app_data_dir, "logs")
caminho_dados = os.path.join(app_data_dir, "data")
caminho_screenshots = os.path.join(app_data_dir, "screenshots")
os.makedirs(caminho_screenshots, exist_ok=True)
os.makedirs(caminho_logs, exist_ok=True)
os.makedirs(caminho_dados, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(caminho_logs, "pyerrors.log"),
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

try:
    from cryptography.fernet import Fernet
except ImportError:
    logging.error("Biblioteca cryptography não instalada. Execute: pip install cryptography")
    print("ERRO: Biblioteca 'cryptography' não encontrada.")
    print("Por favor, execute: pip install cryptography")
    sys.exit(1)

sys.path.append(caminho_dados)  

# Variáveis globais para controle das opções selecionadas
zanthus_confirmação=[]
change_password = None
change_email=None
change_all=None

# Playwright globals
playwright_instance = None
browser = None
context = None
page = None

# Callback para atualização da UI em tempo real
log_callback = None

def report_log(msg, tipo="info", screenshot_path=None):
    if log_callback:
        log_callback(msg, tipo, screenshot_path)
    else:
        print(f"[{tipo}] {msg}")

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


def change():
    global change_all, change_email, change_password
    if change_all == True:
        change_password=True
        change_email=True

def filtrar_cpf():
    global cpf
    try:
        cpf=cpf.replace('.','').replace('-','').replace(',','').strip()
    except:pass

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
            report_log(f"Screenshot salvo: {caminho}", "erro", screenshot_path=caminho)
        finalizar_playwright()
        import traceback as _tb
        raise Exception(f"[step=login_zanthus] ERRO na funcao loguin_function_Zanthus(): {str(e)}\n{_tb.format_exc()}")

def funcionais():
    global playwright_instance, browser, context, page
    playwright_instance = sync_playwright().start()
    browser = playwright_instance.chromium.launch(headless=True)
    context = browser.new_context(viewport={'width': 1920, 'height': 1080})
    page = context.new_page()

def finalizar_playwright():
    global playwright_instance, browser, context, page
    try:
        if browser: browser.close()
        if playwright_instance: playwright_instance.stop()
    except: pass
    browser = None
    playwright_instance = None
    context = None
    page = None

def escrever_arquivo_txt():
    try:
        caminho_arquivo = os.path.join(caminho_dados, "pyhistloc.txt")
        with open(caminho_arquivo, "a+", encoding="utf-8") as arquivo:
            try:
                arquivo.write(f'Código do funcionário: {login_funcionario}   cpf do cliente: {cpf}  email: {email}, senha: {senha}\n')
            except:
                try:
                    arquivo.write(f'Código do funcionário: {login_funcionario}   cpf do cliente: {cpf}   senha: {senha}\n')
                except:
                        arquivo.write(f'Código do funcionário: {login_funcionario}   cpf do cliente: {cpf}  email: {email}\n')
    except Exception as e:
        logging.error(f'Erro no escritor de arquivos de histórico: {e}')
        print(f'Erro no escritor de arquivos: {e}')

def get_cipher():
    try:
        machine_id = os.environ.get('COMPUTERNAME', 'DEFAULT_KEY')
        key_material = f"CLUBE_MODIF_{machine_id}_2025".encode()
        key_hash = hashlib.sha256(key_material).digest()
        key_encoded = base64.urlsafe_b64encode(key_hash)
        return Fernet(key_encoded)
    except Exception as e:
        logging.error(f"Erro ao criar cipher de criptografia: {e}")
        raise

def salvar_credenciais_json(login, senha):
    try:
        # Agora usa a pasta local 'data' na raiz da instalação
        caminho_arquivo = os.path.join(caminho_dados, "pyhiscred.json")
        caminho_backup = os.path.join(caminho_dados, "pyhiscred.json.backup")
        
        if os.path.exists(caminho_arquivo) and not os.access(caminho_arquivo, os.W_OK):
            return False
        
        if os.path.exists(caminho_arquivo):
            try: shutil.copy2(caminho_arquivo, caminho_backup)
            except: pass
        
        dados = {"version": "1.0", "funcionarios": []}
        
        if os.path.exists(caminho_arquivo):
            try:
                with open(caminho_arquivo, "rb") as f:
                    dados_encrypted = f.read()
                    if dados_encrypted:
                        cipher = get_cipher()
                        dados_json = cipher.decrypt(dados_encrypted).decode('utf-8')
                        dados = json.loads(dados_json)
            except:
                if os.path.exists(caminho_backup):
                    try:
                        with open(caminho_backup, "rb") as f:
                            dados_encrypted = f.read()
                            if dados_encrypted:
                                cipher = get_cipher()
                                dados_json = cipher.decrypt(dados_encrypted).decode('utf-8')
                                dados = json.loads(dados_json)
                    except: pass
        
        cipher = get_cipher()
        senha_encrypted = cipher.encrypt(senha.encode()).decode('utf-8')
        
        funcionario_encontrado = False
        for func in dados["funcionarios"]:
            if func["login"] == login:
                func["senha_encrypted"] = senha_encrypted
                func["ultimo_uso"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                funcionario_encontrado = True
                break
        
        if not funcionario_encontrado:
            dados["funcionarios"].append({
                "login": login,
                "senha_encrypted": senha_encrypted,
                "ultimo_uso": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "criado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
        
        dados_json = json.dumps(dados, indent=2)
        dados_encrypted = cipher.encrypt(dados_json.encode())
        with open(caminho_arquivo, "wb") as f:
            f.write(dados_encrypted)
        return True
    except Exception as e:
        logging.error(f'Erro geral ao salvar credenciais JSON: {e}')
        return False

def buscar_credencial_json(login):
    try:
        # Agora usa a pasta local 'data'
        caminho_arquivo = os.path.join(caminho_dados, "pyhiscred.json")
        if not os.path.exists(caminho_arquivo): return None
        with open(caminho_arquivo, "rb") as f:
            dados_encrypted = f.read()
        cipher = get_cipher()
        dados_json = cipher.decrypt(dados_encrypted).decode('utf-8')
        dados = json.loads(dados_json)
        for func in dados["funcionarios"]:
            if func.get("login") == login and "senha_encrypted" in func:
                senha_encrypted = func["senha_encrypted"].encode()
                senha = cipher.decrypt(senha_encrypted).decode('utf-8')
                return senha
        return None
    except: return None

def remover_credencial_json(login):
    try:
        # Agora usa a pasta local 'data'
        caminho_arquivo = os.path.join(caminho_dados, "pyhiscred.json")
        if not os.path.exists(caminho_arquivo): return True
        with open(caminho_arquivo, "rb") as f:
            dados_encrypted = f.read()
        cipher = get_cipher()
        dados_json = cipher.decrypt(dados_encrypted).decode('utf-8')
        dados = json.loads(dados_json)
        dados["funcionarios"] = [f for f in dados["funcionarios"] if f.get("login") != login]
        dados_json = json.dumps(dados, indent=2)
        dados_encrypted = cipher.encrypt(dados_json.encode())
        with open(caminho_arquivo, "wb") as f:
            f.write(dados_encrypted)
        return True
    except: return False

def _carregar_crm_config():
    """Carrega credenciais do CRM de crm_config.json (nunca hardcoded no código)."""
    candidatos = [
        os.path.join(base_proj_dir, "crm_config.json"),
        os.path.join(os.path.dirname(os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__)), "crm_config.json"),
        os.path.join(caminho_dados, "crm_config.json"),
    ]
    for caminho in candidatos:
        if os.path.exists(caminho):
            try:
                with open(caminho, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    return cfg.get("usuario", ""), cfg.get("senha", "")
            except Exception as e:
                logging.error(f"Erro ao ler crm_config.json em {caminho}: {e}")
    logging.error("crm_config.json não encontrado. Crie o arquivo com {\"usuario\": \"...\", \"senha\": \"...\"}")
    raise FileNotFoundError(
        "Arquivo crm_config.json não encontrado.\n"
        f"Crie-o em: {candidatos[0]}\n"
        "Conteúdo esperado: {\"usuario\": \"LOGIN\", \"senha\": \"SENHA\"}"
    )

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
        report_log("✓ Login CRM realizado", "sucesso")

        report_log("Navegando para pagina de Clientes...")
        page.goto('https://crm.grupominipreco.com.br/Cliente/')
        tentar_seletores(page, "crm_cpf_campo", "wait", step="login_crm", timeout=30000)
    except Exception as e:
        caminho = tirar_screenshot_erro(prefixo="[step=login_crm]_erro")
        if caminho:
            report_log(f"Screenshot salvo: {caminho}", "erro", screenshot_path=caminho)
        finalizar_playwright()
        raise Exception(f"[step=login_crm] ERRO no login do CRM: {str(e)}\n{_tb.format_exc()}")

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
        report_log(f"✓ CPF {cpf} encontrado", "sucesso")
        report_log("Cliente encontrado. Abrindo edicao...")
        tentar_seletores(page, "crm_btn_editar", "click", step="busca_cpf")

        tentar_seletores(page, "crm_nome", "wait", step="edicao_dados", timeout=30000)

        alterar_dados()

        report_log("Enviando alteracoes no CRM...")
        tentar_seletores(page, "crm_btn_salvar", "click", step="salvar")
        report_log("✓ Dados salvos", "sucesso")

        report_log("Aguardando confirmacao de sucesso...")
        # lnkMensagemOK pode ter multiplas instancias — filtra o visivel
        seletores_ok = SELECTORS.get("crm_msg_ok", [])
        clicou_ok = False
        for sel in seletores_ok:
            try:
                page.locator(sel).filter(visible=True).first.click(timeout=15000)
                clicou_ok = True
                report_log("✓ Operação confirmada pelo CRM", "sucesso")
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
            report_log(f"Screenshot salvo: {caminho}", "erro", screenshot_path=caminho)
        finalizar_playwright()
        raise Exception(f"[step={step_exc}] ERRO ao processar pagina de cliente: {str(e)}\n{_tb.format_exc()}")

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

def main_function():
    import traceback
    try:
        change()   
        loguin_function()
        clientes_page()
        escrever_arquivo_txt()
        salvar_credenciais_json(login_funcionario, senha_funcionario)
    except Exception as e:
        finalizar_playwright()
        raise Exception(f"ERRO na operação principal: {str(e)}\n{traceback.format_exc()}")
    finally:
        zanthus_confirmação=[]

# ---------------------------------------------------------------------------------------------------------
# ----------INTERFACE GRÁFICA-----------------------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------------------------------

class AlterarDadosClientesApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ALTERAR DADOS CLIENTES - PLAYWRIGHT ENGINE")
        self.root.geometry("550x700")
        
        # Carregar ícone se existir
        # No executável, ele fica no bundle_dir (MEIPASS)
        if getattr(sys, 'frozen', False):
            icon_path = os.path.join(getattr(sys, '_MEIPASS', os.getcwd()), "clube_icon.ico")
        else:
            icon_path = "clube_icon.ico"
            
        if os.path.exists(icon_path):
            try: self.root.iconbitmap(icon_path)
            except: pass
        
        self.tema_atual = "flatly"
        self.style = ttk.Style(self.tema_atual)
        self.style.configure("TFrame", background="#f0f2f5")
        self.style.configure("TLabel", background="#f0f2f5", font=("Inter", 10))
        self.style.configure("Header.TLabel", font=("Inter", 14, "bold"), foreground="#DD1426")
        self.style.configure("Sub.TLabel", font=("Inter", 9, "bold"), foreground="#555")
        
        self.style.configure("Action.TButton", 
                      font=("Inter", 11, "bold"),
                      padding=10)
        
        self.style.configure("TLabelframe", background="#f0f2f5", borderwidth=1)
        self.style.configure("TLabelframe.Label", background="#f0f2f5", font=("Inter", 10, "bold"), foreground="#DD1426")
        
        self.var_opcao = tk.StringVar(value="")
        
        # Lista para armazenar o histórico de resultados na memória
        self.historico_resultados = []
        
        # Configura o callback global para as funções de automação
        global log_callback
        log_callback = self.adicionar_log
        
        self.build_ui()
    
    def check_updates(self, manual=True):
        """Verifica atualizações no GitHub"""
        try:
            url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
            with urllib.request.urlopen(url, timeout=5) as response:
                release = json.loads(response.read().decode())
                latest_version = release.get("tag_name", "").replace("v", "")
                
                if latest_version and latest_version != CURRENT_VERSION.replace("v", ""):
                    atualizar = True if not manual else messagebox.askyesno(
                        "Atualização Disponível",
                        f"Uma nova versão ({latest_version}) foi encontrada!\nDeseja atualizar agora?\n\n"
                        "O programa será fechado para concluir a instalação."
                    )
                    if atualizar:
                        # Tenta localizar o updater em diferentes layouts de instalação
                        candidatos = [
                            os.path.normpath(os.path.join(base_proj_dir, "updater", "clube_updater.exe")),
                            os.path.normpath(os.path.join(os.path.dirname(sys.executable), "updater", "clube_updater.exe")),
                            os.path.normpath(os.path.join(base_proj_dir, "clube_updater.exe"))
                        ]
                        updater_exe = next((p for p in candidatos if os.path.exists(p)), None)
                        
                        if updater_exe:
                            try:
                                subprocess.Popen(
                                    [updater_exe],
                                    cwd=os.path.dirname(updater_exe),
                                    creationflags=subprocess.CREATE_NEW_CONSOLE
                                )
                                self.root.destroy()
                                sys.exit(0)
                            except Exception as e:
                                logging.error(f"Erro ao executar updater: {e}")
                                messagebox.showerror("Erro de Execução", f"Não foi possível iniciar o atualizador.\n\nDetalhe: {e}")
                        else:
                            logging.error(f"Updater não encontrado. Caminhos testados: {candidatos}")
                            messagebox.showerror(
                                "Componente Ausente",
                                "O arquivo de atualização não foi encontrado.\n\n"
                                f"Caminhos testados:\n- " + "\n- ".join(candidatos) + "\n\n"
                                "💡 SOLUÇÃO: Reinstale o programa para restaurar os componentes do sistema."
                            )
                elif manual:
                    # Silenciado conforme pedido do usuário
                    pass
        except Exception as e:
            if manual:
                messagebox.showerror("Falha na Rede", 
                    f"Não foi possível verificar atualizações.\n\n"
                    f"🔍 Detalhe: {e}\n\n"
                    "💡 SOLUÇÃO: Verifique sua conexão com a internet e se o GitHub não está bloqueado na sua rede.")

    def alternar_tema(self):
        if self.tema_atual == "flatly":
            self.tema_atual = "darkly"
            self.btn_tema.config(text="☀️ Claro")
        else:
            self.tema_atual = "flatly"
            self.btn_tema.config(text="🌙 Escuro")
            
        self.style.theme_use(self.tema_atual)
        
        # Se for darkly, ajustamos alguns text/border ou deixamos o ttkbootstrap se virar
        if self.tema_atual == "darkly":
            self.style.configure("TFrame", background="#222")
            self.style.configure("TLabel", background="#222", foreground="#eee")
            self.style.configure("TLabelframe", background="#222")
            self.style.configure("TLabelframe.Label", background="#222", foreground="#ff6b6b")
            self.style.configure("Sub.TLabel", background="#222", foreground="#bbb")
        else:
            self.style.configure("TFrame", background="#f0f2f5")
            self.style.configure("TLabel", background="#f0f2f5", foreground="#000")
            self.style.configure("TLabelframe", background="#f0f2f5")
            self.style.configure("TLabelframe.Label", background="#f0f2f5", foreground="#DD1426")
            self.style.configure("Sub.TLabel", background="#f0f2f5", foreground="#555")

    def build_ui(self):
        # Container principal com fundo cinza claro para contraste
        main_container = ttk.Frame(self.root, style="TFrame")
        main_container.pack(fill="both", expand=True)

        # Header / Banner
        header_frame = ttk.Frame(main_container, bootstyle="danger")
        header_frame.pack(fill="x", pady=(0, 20))
        
        ttk.Label(header_frame, text="🛡️ CLUBE ALTERA DADOS", 
                  font=("Inter", 16, "bold"), foreground="white", 
                  bootstyle="inverse-danger", padding=15).pack(side="left")
                  
        self.btn_tema = ttk.Button(header_frame, text="🌙 Escuro", bootstyle="light", command=self.alternar_tema)
        self.btn_tema.pack(side="right", padx=15)

        # --- SEÇÃO 1: ACESSO ZANTHUS ---
        zanthus_card = ttk.Labelframe(main_container, text=" 🔑 VALIDAÇÃO ZANTHUS ", padding=15)
        zanthus_card.pack(fill="x", padx=20, pady=10)
        
        zan_inner = ttk.Frame(zanthus_card)
        zan_inner.pack(fill="x")
        
        zan_left = ttk.Frame(zan_inner)
        zan_left.pack(side="left", fill="x", expand=True, padx=(0, 5))
        ttk.Label(zan_left, text="CÓDIGO FUNCIONÁRIO:", style="Sub.TLabel").pack(anchor="w")
        self.login_funcionario_entry = ttk.Entry(zan_left, bootstyle="dark")
        self.login_funcionario_entry.pack(fill="x", pady=(0, 5))
        
        zan_right = ttk.Frame(zan_inner)
        zan_right.pack(side="right", fill="x", expand=True, padx=(5, 0))
        ttk.Label(zan_right, text="SENHA DE ACESSO:", style="Sub.TLabel").pack(anchor="w")
        self.senha_funcionario_entry = ttk.Entry(zan_right, show="*", bootstyle="dark")
        self.senha_funcionario_entry.pack(fill="x", pady=(0, 5))
        
        # --- SEÇÃO 2: AÇÃO E CLIENTE ---
        cliente_card = ttk.Labelframe(main_container, text=" 👤 DADOS DO CLIENTE ", padding=15)
        cliente_card.pack(fill="x", padx=20, pady=10)
        
        # Seleção de Ocupação (Checkboxes em destaque)
        check_frame = ttk.Frame(cliente_card)
        check_frame.pack(fill="x", pady=(0, 15))
        
        self.senha_check = ttk.Radiobutton(check_frame, text="SENHA", variable=self.var_opcao, value="senha",
                                        bootstyle="danger-toolbutton", command=self.update_checkbox)
        self.senha_check.pack(side="left", expand=True, padx=2, fill="x")
        
        self.email_check = ttk.Radiobutton(check_frame, text="EMAIL", variable=self.var_opcao, value="email",
                                        bootstyle="danger-toolbutton", command=self.update_checkbox)
        self.email_check.pack(side="left", expand=True, padx=2, fill="x")
        
        self.senha_email_check = ttk.Radiobutton(check_frame, text="AMBOS", variable=self.var_opcao, value="senha_email",
                                               bootstyle="danger-toolbutton", command=self.update_checkbox)
        self.senha_email_check.pack(side="left", expand=True, padx=2, fill="x")

        cli_inner = ttk.Frame(cliente_card)
        cli_inner.pack(fill="x", pady=(0, 10))
        
        cli_left = ttk.Frame(cli_inner)
        cli_left.pack(side="left", fill="x", expand=True, padx=(0, 5))
        ttk.Label(cli_left, text="CPF DO CLIENTE (11 dígitos, só números):", style="Sub.TLabel").pack(anchor="w")
        self.cpf_entry = ttk.Entry(cli_left, bootstyle="dark")
        self.cpf_entry.pack(fill="x", pady=(0, 5))
        
        cli_right = ttk.Frame(cli_inner)
        cli_right.pack(side="right", fill="x", expand=True, padx=(5, 0))
        ttk.Label(cli_right, text="NOVA SENHA (SÓ NÚMEROS, MIN 4):", style="Sub.TLabel").pack(anchor="w")
        self.senha_entry = ttk.Entry(cli_right, show="*", bootstyle="dark")
        self.senha_entry.pack(fill="x", pady=(0, 5))
        
        ttk.Label(cliente_card, text="NOVO EMAIL:", style="Sub.TLabel").pack(anchor="w")
        self.email_entry = ttk.Entry(cliente_card, bootstyle="dark")
        self.email_entry.pack(fill="x")

        # --- BOTÃO PRINCIPAL E PROGRESSBAR ---
        self.iniciar_btn = ttk.Button(main_container, text="🚀 INICIAR AUTOMAÇÃO", 
                                     style="Action.TButton", bootstyle="danger",
                                     command=self.start_thread)
        self.iniciar_btn.pack(pady=(15, 5), fill="x", padx=20)
        
        self.progressbar = ttk.Progressbar(main_container, mode="indeterminate", bootstyle="danger")
        # escondido inicialmente, será ativado no start_thread

        # --- SEÇÃO 3: LOGS ---
        log_card = ttk.Frame(main_container, padding=1)
        log_card.pack(fill="both", expand=True, padx=20, pady=(0, 5))
        
        ttk.Label(log_card, text="📋 STATUS DO PROCESSO", style="Sub.TLabel").pack(anchor="w")
        
        result_inner = ttk.Frame(log_card)
        result_inner.pack(fill="both", expand=True)
        
        self.log_text = tk.Text(result_inner, height=6, font=("Consolas", 9), 
                               borderwidth=1, relief="solid", padx=10, pady=10)
        self.log_text.tag_configure("info", foreground="#007bff")
        self.log_text.tag_configure("sucesso", foreground="#28a745")
        self.log_text.tag_configure("erro", foreground="#dc3545")
        self.log_text.pack(side="left", fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(result_inner, orient="vertical", command=self.log_text.yview)
        scrollbar.pack(side="right", fill="y")
        self.log_text.configure(yscrollcommand=scrollbar.set)
        self.log_text.config(state="disabled")
        
        # Botões do Log
        btns_log = ttk.Frame(log_card)
        btns_log.pack(fill="x", pady=5)
        
        ttk.Button(btns_log, text="🗑️ Limpar", bootstyle="link-secondary", 
                   command=lambda: [self.log_text.config(state="normal"), self.log_text.delete("1.0", tk.END), self.log_text.config(state="disabled")]).pack(side="left")
        
        self.export_btn = ttk.Button(btns_log, text="💾 Exportar Relatório", 
                                    bootstyle="outline-secondary", command=self.exportar_log)
        self.export_btn.pack(side="right")

        # Footer
        footer = ttk.Frame(self.root, bootstyle="secondary")
        footer.pack(side="bottom", fill="x")
        
        version_label = ttk.Label(footer, text=f"Build: {CURRENT_VERSION} | Playwright Engine", 
                                 font=("Inter", 7), bootstyle="inverse-secondary", padding=5)
        version_label.pack(side="left")
        
        credits_label = ttk.Label(footer, text="Desenvolvido por Allan Anjos & Victor Lameiro", 
                                 font=("Inter", 7), bootstyle="inverse-secondary", padding=5)
        credits_label.pack(side="right")
        
        # Bind do ENTER para facilitar
        self.root.bind('<Return>', lambda e: self.start_thread())
        
        # Verificar atualização automaticamente
        self.root.after(1500, lambda: self.check_updates(manual=False))

    def update_checkbox(self, selected=None):
        global change_password, change_email, change_all
        change_password = False
        change_email = False
        change_all = False
        
        selected = self.var_opcao.get()
        if selected == "senha":
            change_password = True
        elif selected == "email":
            change_email = True
        elif selected == "senha_email":
            change_all = True
    
    def reset_values(self):
        global change_password, change_email, change_all, zanthus_confirmação
        self.cpf_entry.delete(0, tk.END)
        self.email_entry.delete(0, tk.END)
        self.senha_entry.delete(0, tk.END)
        self.login_funcionario_entry.delete(0, tk.END)
        self.senha_funcionario_entry.delete(0, tk.END)
        self.var_opcao.set("")
        change_password = False
        change_email = False
        change_all = False
        zanthus_confirmação = []
        if hasattr(self, '_btn_tentar_novamente') and self._btn_tentar_novamente.winfo_exists():
            self._btn_tentar_novamente.pack_forget()

    def exportar_log(self):
        """Salva o conteúdo do log em um arquivo TXT"""
        try:
            from tkinter import filedialog
            conteudo = self.log_text.get("1.0", tk.END).strip()
            if not conteudo:
                messagebox.showwarning("Aviso", "O log está vazio.")
                return
            
            # Sugere nome de arquivo com data
            nome_sugerido = f"Relatorio_Alteracao_{datetime.now().strftime('%d_%m_%Y_%H%M')}.txt"
            caminho = filedialog.asksaveasfilename(defaultextension=".txt", 
                                                 initialfile=nome_sugerido,
                                                 title="Salvar Log de Exportação",
                                                 filetypes=[("Arquivo de Texto", "*.txt")])
            if caminho:
                with open(caminho, "w", encoding="utf-8") as f:
                    f.write("RELATÓRIO DE ALTERAÇÃO DE DADOS - CLUBE MINI PREÇO\n")
                    f.write("="*50 + "\n")
                    f.write(conteudo)
                    f.write("\n" + "="*50 + "\n")
                    f.write(f"Exportado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
                messagebox.showinfo("Sucesso", f"Log exportado com sucesso!\n\n{caminho}")
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível exportar o log:\n{e}")

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

    def mostrar_btn_tentar_novamente(self):
        def _show():
            if hasattr(self, '_btn_tentar_novamente') and self._btn_tentar_novamente.winfo_exists():
                return
            self._btn_tentar_novamente = ttk.Button(
                self.root,
                text="🔄 Tentar novamente",
                bootstyle="warning",
                command=self._tentar_novamente_click
            )
            self._btn_tentar_novamente.pack(pady=(2, 5), padx=20, fill="x")
        self.root.after(0, _show)

    def _tentar_novamente_click(self):
        if hasattr(self, '_btn_tentar_novamente') and self._btn_tentar_novamente.winfo_exists():
            self._btn_tentar_novamente.pack_forget()
        self.start_thread()

    def fechar_progressbar(self):
        self.progressbar.stop()
        self.progressbar.pack_forget()
        self.iniciar_btn.config(state="normal")

    def start_thread(self):
        self.iniciar_btn.config(state="disabled")
        self.progressbar.pack(fill="x", padx=20, pady=(0, 10))
        self.progressbar.start(10)
        if self.log_text.get("1.0", "end-1c").strip():
            agora = datetime.now().strftime("%H:%M:%S")
            self.adicionar_log(f"────────────────── Nova tentativa — {agora} ──────────────────")
        self.adicionar_log("Iniciando processo em segundo plano...")
        thread = threading.Thread(target=self.run_in_thread, daemon=True)
        thread.start()

    def run_in_thread(self):
        try:
            self.iniciar()
        finally:
            self.root.after(0, self.fechar_progressbar)

    def iniciar(self):
        global change_password, change_email, change_all, cpf, email, senha, login_funcionario, senha_funcionario, zanthus_confirmação
        
        cpf = self.cpf_entry.get()
        email = self.email_entry.get()
        senha = self.senha_entry.get()
        login_funcionario = self.login_funcionario_entry.get()
        senha_funcionario = self.senha_funcionario_entry.get()
        zanthus_confirmação = [] # Limpa status anterior
        
        filtrar_cpf()
        
        senha_salva = buscar_credencial_json(login_funcionario)
        
        if senha_salva and senha_salva == senha_funcionario:
            zanthus_confirmação = ['yes']
            self.adicionar_log("Login Zanthus carregado (Cache).")
            self.adicionar_log("✓ Zanthus validado", "sucesso")
        else:
            try:
                self.adicionar_log("Validando credentials no Zanthus...")
                loguin_function_Zanthus()
                if len(zanthus_confirmação) > 0:
                    salvar_credenciais_json(login_funcionario, senha_funcionario)
                    self.adicionar_log("Login Zanthus realizado com sucesso!", "sucesso")
                    self.adicionar_log("✓ Zanthus validado", "sucesso")
                else:
                    self.adicionar_log("Falha no Login Zanthus: Usuário ou Senha incorretos.", "erro")
                    messagebox.showerror("Erro de Login", "Código ou Senha Zanthus estão incorretos.\n\n💡 SOLUÇÃO: Verifique os dados digitados.")
                    self.mostrar_btn_tentar_novamente()
                    return
            except Exception as err_zanthus: 
                zanthus_confirmação = []
                remover_credencial_json(login_funcionario)
                self.adicionar_log(f"Erro técnico Zanthus: {str(err_zanthus)}", "erro")
                messagebox.showerror("Erro de Login Zanthus", 
                    f"Falha ao validar credenciais no Zanthus.\n\n"
                    f"🔍 Erro: {str(err_zanthus)}\n\n"
                    "💡 SOLUÇÃO:\n"
                    "1. Verifique se seu Código e Senha Zanthus estão corretos.\n"
                    "2. Verifique se o site do Bluesoft/Zanthus está fora do ar no navegador.")
                self.mostrar_btn_tentar_novamente()
                return

        if len(zanthus_confirmação)>0:
            match len(cpf):
                case 11:
                    if change_password:
                        if len(senha)>=4 and senha.isdigit():
                            try:
                                self.adicionar_log(f"Iniciando alteração de SENHA para CPF {cpf}...")
                                executar_com_retry(main_function)
                            except Exception as err:
                                self.adicionar_log(f"Erro no CRM: {err}", "erro")
                                messagebox.showerror("Operação Falhou",
                                    f"Não foi possível alterar a senha.\n\n"
                                    f"🔍 Detalhe: {err}\n\n"
                                    "💡 SOLUÇÃO: Verifique se o CPF do cliente existe no CRM e se você tem permissão para editar.")
                                self.mostrar_btn_tentar_novamente()
                            else:
                                tipo_alterado = "SENHA"
                                self.adicionar_log(f"✅ {tipo_alterado} alterado com sucesso para CPF {cpf}.", "sucesso")
                                messagebox.showinfo("Sucesso", f"Senha alterada com sucesso!\n\nCPF: {cpf}\nNova Senha: {senha}")
                                self.reset_values()
                        else: 
                            messagebox.showwarning("Dados Inválidos", 
                                "A senha deve conter pelo menos 4 dígitos numéricos.\n\n"
                                "💡 SOLUÇÃO: Digite apenas números no campo de senha.")
                    elif change_email:
                        if len(email)>5 and "@" in email and "." in email:
                            try:
                                self.adicionar_log(f"Iniciando alteração de EMAIL para CPF {cpf}...")
                                executar_com_retry(main_function)
                            except Exception as err:
                                self.adicionar_log(f"Erro no CRM: {err}", "erro")
                                messagebox.showerror("Operação Falhou",
                                    f"Não foi possível alterar o email.\n\n"
                                    f"🔍 Detalhe: {err}\n\n"
                                    "💡 SOLUÇÃO: Verifique sua conexão e se o CPF está correto no CRM.")
                                self.mostrar_btn_tentar_novamente()
                            else:
                                tipo_alterado = "EMAIL"
                                self.adicionar_log(f"✅ {tipo_alterado} alterado com sucesso para CPF {cpf}.", "sucesso")
                                messagebox.showinfo("Sucesso", f"Email alterado com sucesso!\n\nCPF: {cpf}\nNovo Email: {email}")
                                self.reset_values()
                        else: 
                            messagebox.showwarning("Email Inválido", 
                                "O formato do email digitado é inválido.\n\n"
                                "💡 SOLUÇÃO: Use o formato: nome@dominio.com")
                    elif change_all:
                        if len(senha)>=4 and senha.isdigit() and len(email)>5 and "@" in email and "." in email:
                            try:
                                self.adicionar_log(f"Iniciando alteração de SENHA E EMAIL para CPF {cpf}...")
                                executar_com_retry(main_function)
                            except Exception as err:
                                self.adicionar_log(f"Erro no CRM: {err}", "erro")
                                messagebox.showerror("Operação Falhou",
                                    f"Não foi possível alterar os dados.\n\n"
                                    f"🔍 Detalhe: {err}\n\n"
                                    "💡 SOLUÇÃO: Reinicie o programa e tente novamente.")
                                self.mostrar_btn_tentar_novamente()
                            else:
                                tipo_alterado = "SENHA E EMAIL"
                                self.adicionar_log(f"✅ {tipo_alterado} alterados com sucesso para CPF {cpf}.", "sucesso")
                                messagebox.showinfo("Sucesso", f"Senha e Email alterados!\n\nCPF: {cpf}")
                                self.reset_values()
                        else: 
                            messagebox.showwarning("Verifique os Dados", 
                                "A senha deve ter 4+ números e o email deve ser válido.\n\n"
                                "💡 SOLUÇÃO: Preencha todos os campos corretamente.")
                    else:
                        messagebox.showinfo("Atenção", "Selecione o que deseja alterar.")
                case _:
                    messagebox.showwarning("CPF Inválido", 
                        f"O CPF digitado contém {len(cpf)} dígitos.\n\n"
                        "💡 SOLUÇÃO: O CPF deve conter exatamente 11 números.")

if __name__ == "__main__":
    root = ttk.Window(themename="flatly")
    app = AlterarDadosClientesApp(root)
    root.mainloop()
