import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from playwright.sync_api import sync_playwright
import os   
import random
import sys
import json
import hashlib
import base64
from datetime import datetime
import shutil
import logging
from time import sleep

# Configurar logging para erros
caminho_pasta = os.path.join(os.path.expanduser('~'), "pydata")
os.makedirs(caminho_pasta, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(caminho_pasta, "pyerrors.log"),
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

sys.path.append(caminho_pasta)  

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
        
        # Preencher login e senha
        page.locator("#USUARIO").fill(login_funcionario)
        page.locator("#SENHA").fill(senha_funcionario)
        
        # Clicar no botão entrar
        # O Selenium usava Keys.F12 no campo de senha mas clicava depois
        # Aqui vamos clicar diretamente no botão de submit
        page.locator('//input[@type="submit" and @value=" Entrar "]').click()
        
        # Aguarda pela presença do Menu para confirmar login
        try:
            # Espera até 10 segundos
            page.wait_for_selector("#Menu", timeout=10000)
            zanthus_confirmação = ['yes']
        except:
            zanthus_confirmação = []
            
        finalizar_playwright()
    except Exception as e:
        finalizar_playwright()
        import traceback
        raise Exception(f"ERRO na função loguin_function_Zanthus(): {str(e)}\n{traceback.format_exc()}")

def funcionais():
    global playwright_instance, browser, context, page
    playwright_instance = sync_playwright().start()
    browser = playwright_instance.chromium.launch(headless=False)
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
        nome_pasta = "pydata"
        caminho_pasta = os.path.join(os.path.expanduser('~'), nome_pasta)
        os.makedirs(caminho_pasta, exist_ok=True)
        caminho_arquivo = os.path.join(caminho_pasta, "pyhistloc.txt")
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
        nome_pasta = "pydata"
        caminho_pasta = os.path.join(os.path.expanduser('~'), nome_pasta)
        os.makedirs(caminho_pasta, exist_ok=True)
        caminho_arquivo = os.path.join(caminho_pasta, "pyhiscred.json")
        caminho_backup = os.path.join(caminho_pasta, "pyhiscred.json.backup")
        
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
        nome_pasta = "pydata"
        caminho_pasta = os.path.join(os.path.expanduser('~'), nome_pasta)
        caminho_arquivo = os.path.join(caminho_pasta, "pyhiscred.json")
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
        nome_pasta = "pydata"
        caminho_pasta = os.path.join(os.path.expanduser('~'), nome_pasta)
        caminho_arquivo = os.path.join(caminho_pasta, "pyhiscred.json")
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

def loguin_function():
    import traceback
    try:
        funcionais()
        page.goto('https://crm.grupominipreco.com.br')
        page.wait_for_selector("#Usuario", timeout=15000)
        page.locator("#Usuario").fill('GUSTAVO.ALVES')
        page.locator("#Senha").fill('Cwb123@')
        page.locator("#btnEntrar").click()
        
        # Espera carregar a página inicial
        page.wait_for_load_state("networkidle")
        
        # Vai para a página de clientes
        page.goto('https://crm.grupominipreco.com.br/Cliente/')
        page.wait_for_selector("#cpfcliente", timeout=15000)
    except Exception as e:
        finalizar_playwright()
        raise Exception(f"ERRO no login do CRM: {str(e)}\n{traceback.format_exc()}")

def clientes_page():
    global cpf, email, senha
    import traceback
    try:
        # Preenche o CPF e aperta Enter
        page.locator("#cpfcliente").fill(cpf)
        page.keyboard.press("Enter")
        
        # Espera o botão editar aparecer
        page.wait_for_selector("#btnEditar", timeout=15000)
        page.locator("#btnEditar").click()
        
        # Espera carregar os campos de edição
        page.wait_for_selector("#Nome", timeout=15000)
        
        # Realiza a alteração de dados
        alterar_dados()
        
        # Clica em Salvar
        page.locator("#btnSalvar").click()
        
        # Espera a mensagem de OK e clica
        page.wait_for_selector("#lnkMensagemOK", timeout=15000)
        page.locator("#lnkMensagemOK").click()
        
        finalizar_playwright()
    except Exception as e:
        finalizar_playwright()
        raise Exception(f"ERRO ao processar página de cliente: {str(e)}\n{traceback.format_exc()}")

def alterar_dados():
    import traceback
    try:
        if change_email:
            page.locator("#Email").fill(email)
            page.locator("#ConfirmarEmail").fill(email)
        
        if change_password:
            page.locator("#Senha").fill(senha)
            page.locator("#ConfirmarSenha").fill(senha)
    except Exception as e:
        raise Exception(f"ERRO ao preencher dados: {str(e)}\n{traceback.format_exc()}")

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
        self.root.geometry("500x600")
        
        self.style = ttk.Style("flatly")
        self.style.configure("TFrame", background="white")
        self.style.configure("TLabel", background="white")
        self.style.configure("black.TButton", background="black", foreground="white", font=("Inter", 10, "bold"))
        
        self.var_senha = tk.BooleanVar()
        self.var_email = tk.BooleanVar()
        self.var_senha_email = tk.BooleanVar()
        
        self.build_ui()
    
    def build_ui(self):
        title = ttk.Label(self.root, text="VALIDAÇÃO DO FUNCIONÁRIO", font=("Inter", 16, "bold"), foreground="#DD1426")
        title.pack(pady=(20, 10))
        
        login_frame = ttk.Frame(self.root)
        login_frame.pack(pady=10, fill="x", padx=20)
        
        ttk.Label(login_frame, text="CÓDIGO ZANTHUS", font=("Inter", 10, "bold")).grid(row=0, column=0, sticky='w', pady=(5, 0), columnspan=2)
        self.login_funcionario_entry = ttk.Entry(login_frame, width=72, bootstyle="dark")
        self.login_funcionario_entry.grid(row=1, column=0, sticky='w', pady=(0, 10), columnspan=2)
        
        ttk.Label(login_frame, text="SENHA ZANTHUS", font=("Inter", 10, "bold")).grid(row=2, column=0, sticky='w', pady=(5, 0), columnspan=2)
        self.senha_funcionario_entry = ttk.Entry(login_frame, width=72, show="*", bootstyle="dark")
        self.senha_funcionario_entry.grid(row=3, column=0, sticky='w', pady=(0, 15), columnspan=2)
        
        title = ttk.Label(self.root, text="ALTERAR DADOS DOS CLIENTES", font=("Inter", 16, "bold"), foreground="#DD1426")
        title.pack(pady=(20, 10))

        checkbox_frame = ttk.Frame(self.root)
        checkbox_frame.pack(pady=10, fill="x", padx=40)
        
        self.senha_check = ttk.Checkbutton(checkbox_frame, text="SENHA", variable=self.var_senha, bootstyle="danger", command=lambda: self.update_checkbox("senha"))
        self.senha_check.grid(row=0, column=0, padx=35)
        
        self.email_check = ttk.Checkbutton(checkbox_frame, text="EMAIL", variable=self.var_email, bootstyle="danger", command=lambda: self.update_checkbox("email"))
        self.email_check.grid(row=0, column=1, padx=35)
        
        self.senha_email_check = ttk.Checkbutton(checkbox_frame, text="SENHA E EMAIL", variable=self.var_senha_email, bootstyle="danger", command=lambda: self.update_checkbox("senha_email"))
        self.senha_email_check.grid(row=0, column=2, padx=35)
        
        inputs_frame = ttk.Frame(self.root)
        inputs_frame.pack(pady=10, fill="x", padx=20)
        
        ttk.Label(inputs_frame, text="DIGITE O CPF DO CLIENTE", font=("Inter", 10, "bold")).grid(row=0, column=0, sticky='w', pady=(5, 0), columnspan=2)
        self.cpf_entry = ttk.Entry(inputs_frame, width=72, bootstyle="dark")
        self.cpf_entry.grid(row=1, column=0, sticky='w', pady=(0, 10), columnspan=2)
        
        ttk.Label(inputs_frame, text="DIGITE O NOVO EMAIL", font=("Inter", 10, "bold")).grid(row=2, column=0, sticky='w', pady=(5, 0), columnspan=2)
        self.email_entry = ttk.Entry(inputs_frame, width=72, bootstyle="dark")
        self.email_entry.grid(row=3, column=0, sticky='w', pady=(0, 10), columnspan=2)
        
        ttk.Label(inputs_frame, text="DIGITE SUA NOVA SENHA   (Somente números)", font=("Inter", 10, "bold")).grid(row=4, column=0, sticky='w', pady=(5, 0), columnspan=2)
        self.senha_entry = ttk.Entry(inputs_frame, width=72, show="*", bootstyle="dark")
        self.senha_entry.grid(row=5, column=0, sticky='w', pady=(0, 10), columnspan=2)
        
        iniciar_btn = ttk.Button(self.root, text="INICIAR", style="black.TButton", command=self.iniciar)
        iniciar_btn.pack(pady=20, fill="x", padx=20)

    def update_checkbox(self, selected):
        global change_password, change_email, change_all
        change_password = False
        change_email = False
        change_all = False
        self.var_senha.set(False)
        self.var_email.set(False)
        self.var_senha_email.set(False)
        if selected == "senha":
            self.var_senha.set(True)
            change_password = True
        elif selected == "email":
            self.var_email.set(True)
            change_email = True
        elif selected == "senha_email":
            self.var_senha_email.set(True)
            change_all = True
    
    def reset_values(self):
        global change_password, change_email, change_all, zanthus_confirmação
        self.cpf_entry.delete(0, tk.END)
        self.email_entry.delete(0, tk.END)
        self.senha_entry.delete(0, tk.END)
        self.login_funcionario_entry.delete(0, tk.END)
        self.senha_funcionario_entry.delete(0, tk.END)
        self.var_senha.set(False)
        self.var_email.set(False)
        self.var_senha_email.set(False)
        change_password = False
        change_email = False
        change_all = False
        zanthus_confirmação = []

    def iniciar(self):
        global change_password, change_email, change_all, cpf, email, senha, login_funcionario, senha_funcionario, zanthus_confirmação
        
        cpf = self.cpf_entry.get()
        email = self.email_entry.get()
        senha = self.senha_entry.get()
        login_funcionario = self.login_funcionario_entry.get()
        senha_funcionario = self.senha_funcionario_entry.get()

        filtrar_cpf()
        
        senha_salva = buscar_credencial_json(login_funcionario)
        
        if senha_salva and senha_salva == senha_funcionario:
            zanthus_confirmação = ['yes']
        else:
            try:
                loguin_function_Zanthus()
                if len(zanthus_confirmação) > 0:
                    salvar_credenciais_json(login_funcionario, senha_funcionario)
            except Exception as err_zanthus: 
                zanthus_confirmação = []
                remover_credencial_json(login_funcionario)
                messagebox.showinfo("ERRO NO LOGIN ZANTHUS", f"FALHA NO LOGUIN ZANTHUS\n\n{str(err_zanthus)}")
        
        if len(zanthus_confirmação)>0:
            match len(cpf):
                case 11:
                    if change_password:
                        if len(senha)>=4 and senha.isdigit():
                            try: main_function()
                            except Exception as err: messagebox.showinfo("ERRO", f"OPERACAO FALHOU\n{err}")
                            else:
                                messagebox.showinfo("CONCLUÍDO", f"CPF: {cpf}\nNova Senha: {senha}")
                                self.reset_values()
                        else: messagebox.showinfo("Atenção", "Senha deve ter 4 dígitos numéricos.")
                    elif change_email:
                        if len(email)>5 and "@" in email and "." in email:
                            try: main_function()
                            except Exception as err: messagebox.showinfo("ERRO", f"OPERACAO FALHOU\n{err}")
                            else:
                                messagebox.showinfo("CONCLUÍDO", f"CPF: {cpf}\nNovo Email: {email}")
                                self.reset_values()
                        else: messagebox.showinfo("Atenção", "Email inválido.")
                    elif change_all:
                        if len(senha)>=4 and senha.isdigit() and len(email)>5 and "@" in email and "." in email:
                            try: main_function()
                            except Exception as err: messagebox.showinfo("ERRO", f"OPERACAO FALHOU\n{err}")
                            else:
                                messagebox.showinfo("CONCLUÍDO", f"CPF: {cpf}\nAlterados Senha e Email")
                                self.reset_values()
                        else: messagebox.showinfo("Atenção", "Verifique os dados digitados.")
                    else:
                        messagebox.showinfo("Atenção", "Selecione o que deseja alterar.")
                case _:
                    messagebox.showinfo("CPF INVÁLIDO", "O CPF DEVE CONTER 11 DIGITOS")

if __name__ == "__main__":
    root = ttk.Window(themename="flatly")
    app = AlterarDadosClientesApp(root)
    root.mainloop()