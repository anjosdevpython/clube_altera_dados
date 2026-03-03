import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from time import sleep
import os   
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import random
import sys
import json
import hashlib
import base64
from datetime import datetime
import shutil
import logging

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

# os.chdir(os.path.dirname(os.path.abspath(__file__)))
# os.chdir(os.path.dirname(os.path.abspath(caminho_pasta)))



# Variáveis globais para controle das opções selecionadas
zanthus_confirmação=[]
change_password = None
change_email=None
change_all=None

def change():
    global change_all, change_email, change_password
    if change_all == True:
        change_password=True
        change_email=True

#  limitar imput para somente senha numérica 



def filtrar_cpf():
    global cpf
    try:
        cpf=cpf.replace('.','').replace('-','').replace(',','').strip()
    except:pass


    # função loguin 
def loguin_function_Zanthus():
    global zanthus_confirmação
    try:
        funcionais()
        driver.get('https://minipreco.zanthus.bluesoft.com.br')
        sleep(1)
        usuario = wait.until(EC.presence_of_element_located((By.ID, "USUARIO")))
        usuario.click()
        usuario.send_keys(login_funcionario)
        password = wait.until(EC.presence_of_element_located((By.ID, "SENHA")))
        password.click()
        password.send_keys(senha_funcionario,Keys.F12)
        login = wait.until(EC.element_to_be_clickable((By.XPATH, '//input[@type="submit" and @value=" Entrar "]'))).click()
        # driver.maximize_window()

        zanthus_confirmação= waiting.until(EC.presence_of_all_elements_located((By.ID, "Menu")))
        driver.quit()
    except Exception as e:
        driver.quit()
        import traceback
        raise Exception(f"ERRO na função loguin_function_Zanthus(): {str(e)}\\n{traceback.format_exc()}")
    
    

def funcionais():
    global service,driver, wait, waiting
    
    from selenium.webdriver.chrome.options import Options
    chrome_options = Options()
    # Configurações para resolver problemas de resolução e zoom
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--force-device-scale-factor=1")
    chrome_options.add_argument("--high-dpi-support=1")
    chrome_options.add_argument("--disable-gpu")  # Opcional, ajuda em alguns casos
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    wait = WebDriverWait(driver, 15)  
    waiting = WebDriverWait(driver, 7)  


# def funcionais():
#     global service,driver, wait, waiting
    
#     chrome_options = Options()
#     # Configurações para resolver problemas de resolução e zoom
#     chrome_options.add_argument("--window-size=1920,1080")
#     chrome_options.add_argument("--force-device-scale-factor=1")
#     chrome_options.add_argument("--high-dpi-support=1")
#     chrome_options.add_argument("--disable-gpu") # Opcional, ajuda em alguns casos
    
#     service = Service(ChromeDriverManager().install())
#     driver = webdriver.Chrome(service=service, options=chrome_options)
#     wait = WebDriverWait(driver, 15)  
#     waiting = WebDriverWait(driver, 7)  

def escrever_arquivo_txt():
    try:
        # Pasta que será criada no diretório local (onde o script está rodando)
        nome_pasta = "pydata"

        # Pega o diretório base do usuário (home) e cria a pasta lá
        caminho_pasta = os.path.join(os.path.expanduser('~'), nome_pasta)
        os.makedirs(caminho_pasta, exist_ok=True)

        # Caminho completo do arquivo
        caminho_arquivo = os.path.join(caminho_pasta, "pyhistloc.txt")
        with open(caminho_arquivo, "a+", encoding="utf-8") as arquivo:
            conteudo_antigo = arquivo.read()  # Lê tudo
            arquivo.seek(0)  # Volta ao início do arquivo
            try:
                arquivo.write(f'Código do funcionário: {login_funcionario}   cpf do cliente: {cpf}  email: {email}, senha: {senha}\\n')
            except:
                try:
                    arquivo.write(f'Código do funcionário: {login_funcionario}   cpf do cliente: {cpf}   senha: {senha}\\n')
                except:
                        arquivo.write(f'Código do funcionário: {login_funcionario}   cpf do cliente: {cpf}  email: {email}\\n')
    except Exception as e:
        logging.error(f'Erro no escritor de arquivos de histórico: {e}')
        print(f'Erro no escritor de arquivos: {e}')

# ============================================================================
# NOVO SISTEMA DE CREDENCIAIS COM CRIPTOGRAFIA E MÚLTIPLOS USUÁRIOS
# ============================================================================

def get_cipher():
    """
    Gera uma chave de criptografia baseada em identificador único da máquina.
    Retorna objeto Fernet para criptografar/descriptografar dados.
    """
    try:
        # Usa nome do computador como base para gerar chave consistente
        machine_id = os.environ.get('COMPUTERNAME', 'DEFAULT_KEY')
        key_material = f"CLUBE_MODIF_{machine_id}_2025".encode()
        
        # Gera chave de 32 bytes usando SHA256
        key_hash = hashlib.sha256(key_material).digest()
        key_encoded = base64.urlsafe_b64encode(key_hash)
        
        return Fernet(key_encoded)
    except Exception as e:
        logging.error(f"Erro ao criar cipher de criptografia: {e}")
        raise

def salvar_credenciais_json(login, senha):
    """
    Salva ou atualiza credenciais de um funcionário no arquivo JSON criptografado.
    Suporta múltiplos usuários.
    
    Args:
        login (str): Código Zanthus do funcionário
        senha (str): Senha Zanthus do funcionário
    
    Returns:
        bool: True se salvou com sucesso, False caso contrário
    """
    try:
        nome_pasta = "pydata"
        caminho_pasta = os.path.join(os.path.expanduser('~'), nome_pasta)
        os.makedirs(caminho_pasta, exist_ok=True)
        
        caminho_arquivo = os.path.join(caminho_pasta, "pyhiscred.json")
        caminho_backup = os.path.join(caminho_pasta, "pyhiscred.json.backup")
        
        # Verificar permissões de escrita
        if os.path.exists(caminho_arquivo) and not os.access(caminho_arquivo, os.W_OK):
            logging.error(f"Sem permissão de escrita em {caminho_arquivo}")
            return False
        
        # Criar backup do arquivo existente
        if os.path.exists(caminho_arquivo):
            try:
                shutil.copy2(caminho_arquivo, caminho_backup)
            except Exception as e:
                logging.error(f"Erro ao criar backup: {e}")
        
        # Carregar dados existentes ou criar nova estrutura
        dados = {"version": "1.0", "funcionarios": []}
        
        if os.path.exists(caminho_arquivo):
            try:
                with open(caminho_arquivo, "rb") as f:
                    dados_encrypted = f.read()
                    if dados_encrypted:
                        cipher = get_cipher()
                        dados_json = cipher.decrypt(dados_encrypted).decode('utf-8')
                        dados = json.loads(dados_json)
            except Exception as e:
                logging.error(f"Erro ao carregar credenciais existentes (arquivo pode estar corrompido): {e}")
                # Tenta recuperar do backup
                if os.path.exists(caminho_backup):
                    try:
                        with open(caminho_backup, "rb") as f:
                            dados_encrypted = f.read()
                            if dados_encrypted:
                                cipher = get_cipher()
                                dados_json = cipher.decrypt(dados_encrypted).decode('utf-8')
                                dados = json.loads(dados_json)
                        logging.info("Recuperado com sucesso do backup")
                    except Exception as e2:
                        logging.error(f"Backup também corrompido: {e2}")
                        dados = {"version": "1.0", "funcionarios": []}
        
        # Criptografar senha
        cipher = get_cipher()
        senha_encrypted = cipher.encrypt(senha.encode()).decode('utf-8')
        
        # Buscar se login já existe e atualizar, ou adicionar novo
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
        
        # Salvar dados criptografados
        try:
            dados_json = json.dumps(dados, indent=2)
            dados_encrypted = cipher.encrypt(dados_json.encode())
            
            with open(caminho_arquivo, "wb") as f:
                f.write(dados_encrypted)
            
            # Validar que arquivo foi escrito corretamente
            with open(caminho_arquivo, "rb") as f:
                test_read = f.read()
                if not test_read:
                    raise Exception("Arquivo salvo está vazio")
            
            return True
            
        except Exception as e:
            logging.error(f"Erro ao salvar credenciais: {e}")
            # Restaurar backup se falhou
            if os.path.exists(caminho_backup):
                try:
                    shutil.copy2(caminho_backup, caminho_arquivo)
                    logging.info("Backup restaurado após falha na escrita")
                except Exception as e2:
                    logging.error(f"Erro ao restaurar backup: {e2}")
            return False
            
    except Exception as e:
        logging.error(f'Erro geral ao salvar credenciais JSON: {e}')
        return False

def buscar_credencial_json(login):
    """
    Busca e retorna a senha descriptografada de um funcionário.
    
    Args:
        login (str): Código Zanthus do funcionário
    
    Returns:
        str or None: Senha descriptografada se encontrada, None caso contrário
    """
    try:
        nome_pasta = "pydata"
        caminho_pasta = os.path.join(os.path.expanduser('~'), nome_pasta)
        caminho_arquivo = os.path.join(caminho_pasta, "pyhiscred.json")
        
        if not os.path.exists(caminho_arquivo):
            return None
        
        # Validar permissões de leitura
        if not os.access(caminho_arquivo, os.R_OK):
            logging.error(f"Sem permissão de leitura em {caminho_arquivo}")
            return None
        
        # Carregar e descriptografar arquivo
        with open(caminho_arquivo, "rb") as f:
            dados_encrypted = f.read()
            if not dados_encrypted:
                logging.warning("Arquivo de credenciais está vazio")
                return None
        
        cipher = get_cipher()
        dados_json = cipher.decrypt(dados_encrypted).decode('utf-8')
        dados = json.loads(dados_json)
        
        # Validar estrutura JSON
        if "funcionarios" not in dados or not isinstance(dados["funcionarios"], list):
            logging.error("Estrutura JSON inválida em arquivo de credenciais")
            return None
        
        # Buscar login específico
        for func in dados["funcionarios"]:
            if func.get("login") == login and "senha_encrypted" in func:
                senha_encrypted = func["senha_encrypted"].encode()
                senha = cipher.decrypt(senha_encrypted).decode('utf-8')
                return senha
        
        return None
        
    except Exception as e:
        logging.error(f"Erro ao buscar credencial JSON: {e}")
        return None

def remover_credencial_json(login):
    """
    Remove credencial específica do JSON sem deletar o arquivo inteiro.
    
    Args:
        login (str): Código Zanthus do funcionário a ser removido
    
    Returns:
        bool: True se removeu com sucesso, False caso contrário
    """
    try:
        nome_pasta = "pydata"
        caminho_pasta = os.path.join(os.path.expanduser('~'), nome_pasta)
        caminho_arquivo = os.path.join(caminho_pasta, "pyhiscred.json")
        
        if not os.path.exists(caminho_arquivo):
            return True  # Já não existe, missão cumprida
        
        # Carregar dados
        with open(caminho_arquivo, "rb") as f:
            dados_encrypted = f.read()
        
        cipher = get_cipher()
        dados_json = cipher.decrypt(dados_encrypted).decode('utf-8')
        dados = json.loads(dados_json)
        
        # Remover funcionário específico
        dados["funcionarios"] = [f for f in dados["funcionarios"] if f.get("login") != login]
        
        # Salvar de volta
        dados_json = json.dumps(dados, indent=2)
        dados_encrypted = cipher.encrypt(dados_json.encode())
        
        with open(caminho_arquivo, "wb") as f:
            f.write(dados_encrypted)
        
        logging.info(f"Credencial removida para login: {login}")
        return True
        
    except Exception as e:
        logging.error(f"Erro ao remover credencial JSON: {e}")
        return False

# ============================================================================
# FUNÇÕES ANTIGAS MANTIDAS PARA RETROCOMPATIBILIDADE (NÃO MAIS USADAS)
# ============================================================================

def escrever_arquivo_python(): 
    """DEPRECATED: Mantida apenas para retrocompatibilidade"""
    try:
        # Pasta que será criada no diretório local (onde o script está rodando)
        nome_pasta = "pydata"

        # Pega o diretório base do usuário (home) e cria a pasta lá
        caminho_pasta = os.path.join(os.path.expanduser('~'), nome_pasta)
        os.makedirs(caminho_pasta, exist_ok=True)

        # Caminho completo do arquivo
        caminho_arquivo = os.path.join(caminho_pasta, "pyhisarm.py")
        with open(caminho_arquivo, "w", encoding="utf-8") as arquivo:
            arquivo.write(f'\\nlz="{login_funcionario}"')
            arquivo.write(f'\\npz="{random.randint(0000,9999)}{senha_funcionario[0]}{random.randint(0000,9999)}{senha_funcionario[1]}{random.randint(0000,9999)}{senha_funcionario[2]}{random.randint(0000,9999)}{senha_funcionario[3:]}"')

    except Exception as e:
        logging.error(f'Erro no escritor de arquivos Python (deprecated): {e}')

def excluir_arquivo_senha():
    """DEPRECATED: Mantida apenas para retrocompatibilidade"""
    try:
        nome_pasta = "pydata"
        caminho_pasta = os.path.join(os.path.expanduser('~'), nome_pasta)
        caminho_arquivo = os.path.join(caminho_pasta, "pyhisarm.py")
        
        if os.path.exists(caminho_arquivo):
            os.remove(caminho_arquivo)
            logging.info(f"Arquivo de senhas antigo excluído: {caminho_arquivo}")
    except Exception as e:
        logging.error(f'Erro ao excluir arquivo de senhas antigo: {e}')


def loguin_function():
    import traceback
    
    try:
        funcionais()
    except Exception as e:
        raise Exception(f"ERRO ao inicializar driver (função funcionais, linha ~137): {str(e)}\\n{traceback.format_exc()}")
    
    try:
        driver.get('https://crm.grupominipreco.com.br')
        sleep(1)
        while len(driver.find_elements(By.ID, "Usuario")) < 1:
            sleep(0.5)
        usuario = wait.until(EC.presence_of_element_located((By.ID, "Usuario")))
        usuario.click()
        usuario.send_keys('GUSTAVO.ALVES')
    except Exception as e:
        raise Exception(f"ERRO ao preencher campo de usuário (linha ~138-144): {str(e)}\\n{traceback.format_exc()}")
    
    try:
        password = wait.until(EC.presence_of_element_located((By.ID, "Senha")))
        password.click()
        password.send_keys('Cwb123@')
    except Exception as e:
        raise Exception(f"ERRO ao preencher campo de senha (linha ~145-147): {str(e)}\\n{traceback.format_exc()}")
    
    try:
        sleep(1)
        login = wait.until(EC.element_to_be_clickable((By.ID, "btnEntrar"))).click()
        # driver.maximize_window()
        sleep(3)
        driver.get('https://crm.grupominipreco.com.br/Cliente/')
        sleep(2)
    except Exception as e:
        raise Exception(f"ERRO ao fazer login ou navegar para página de clientes (linha ~148-153): {str(e)}\\n{traceback.format_exc()}")


def clientes_page():
    global cpf, email,senha
    import traceback
    
    try:
        while len(driver.find_elements(By.ID, "cpfcliente")) < 1:
            sleep(0.5)
        wait.until(EC.presence_of_all_elements_located((By.ID, 'cpfcliente')))
        input_cpf= driver.find_element(By.ID, 'cpfcliente')
        input_cpf.clear()
        input_cpf.send_keys(cpf,Keys.ENTER)
    except Exception as e:
        raise Exception(f"ERRO ao buscar CPF na página de clientes (linha ~159-164): {str(e)}\\n{traceback.format_exc()}")
    
    try:
        wait.until(EC.presence_of_element_located((By.ID, "btnEditar"))).click()
    except Exception as e:
        raise Exception(f"ERRO ao clicar no botão Editar (linha ~165): {str(e)}\\n{traceback.format_exc()}")
    
    try:
        driver.execute_script("document.body.style.zoom='40%'") 
        wait.until(EC.presence_of_element_located((By.ID, 'Nome')))
        try:
            alterar_dados()
        except Exception as e:
            try:
                driver.execute_script("document.body.style.zoom='15%'") 
                alterar_dados()
            except Exception as e2:
                raise Exception(f"ERRO ao alterar dados do cliente (linha ~167-174): Primeira tentativa: {str(e)}, Segunda tentativa: {str(e2)}\\n{traceback.format_exc()}")
    except Exception as e:
        if "ERRO ao alterar dados" not in str(e):
            raise Exception(f"ERRO ao preparar página para alteração (linha ~168-174): {str(e)}\\n{traceback.format_exc()}")
        else:
            raise
    
    try:
        sleep(0.5)
        try:
            driver.find_element(By.ID, 'btnSalvar').click()
        except:
            driver.find_element(By.XPATH, "//body").send_keys(Keys.PAGE_DOWN)
            driver.find_element(By.XPATH, "//body").send_keys(Keys.PAGE_DOWN)
            driver.find_element(By.XPATH, "//body").send_keys(Keys.PAGE_DOWN)
            sleep(0.5)
            try:
                driver.find_element(By.ID, 'btnSalvar').click()
            except Exception as e:
                try:
                    driver.execute_script("document.body.style.zoom='15%'") 
                    driver.find_element(By.ID, 'btnSalvar').click()
                except Exception as e2:
                    raise Exception(f"ERRO ao clicar no botão Salvar (linha ~178-188): {str(e2)}\\n{traceback.format_exc()}")
    except Exception as e:
        if "ERRO ao clicar no botão Salvar" not in str(e):
            raise Exception(f"ERRO ao salvar dados (linha ~176-188): {str(e)}\\n{traceback.format_exc()}")
        else:
            raise

    try:
        sleep(1.5)
        wait.until(EC.visibility_of_element_located((By.ID, 'lnkMensagemOK'))).click()
    except Exception as e:
        raise Exception(f"ERRO ao clicar no botão OK da mensagem de confirmação (linha ~191): {str(e)}\\n{traceback.format_exc()}")
    
    driver.quit()

def alterar_dados():
    import traceback
    
    if change_email==True:
        try:
            input_email = driver.find_element(By.ID, "Email")
            input_email.clear()
            sleep(0.1)
            input_email.send_keys(email)
            sleep(0.1)
            input_confirmar_email = driver.find_element(By.ID, "ConfirmarEmail")
            input_confirmar_email.clear()
            sleep(0.1)
            input_confirmar_email.send_keys(email)
        except Exception as e:
            raise Exception(f"ERRO ao alterar EMAIL (linha ~196-204): {str(e)}\\n{traceback.format_exc()}")
    
    if change_password==True:
        try:
            input_senha=driver.find_element(By.ID, "Senha")
            input_senha.clear()
            sleep(0.1)
            input_senha.send_keys(senha)
            input_confirmar_senha =driver.find_element(By.ID, "ConfirmarSenha")
            input_confirmar_senha.clear()
            sleep(0.1)
            input_confirmar_senha.send_keys(senha)
            sleep(0.1)
        except Exception as e:
            raise Exception(f"ERRO ao alterar SENHA (linha ~206-214): {str(e)}\\n{traceback.format_exc()}")
    

def main_function():
    import traceback
    
    try:
        change()   
    except Exception as e:
        raise Exception(f"ERRO na função change() (linha ~219): {str(e)}\\n{traceback.format_exc()}")
    
    try:
        loguin_function()
    except Exception as e:
        raise Exception(f"ERRO na função loguin_function() (linha ~220): {str(e)}\\n{traceback.format_exc()}")
    
    try:
        clientes_page()
    except Exception as e:
        raise Exception(f"ERRO na função clientes_page() (linha ~221): {str(e)}\\n{traceback.format_exc()}")
    
    try:
        escrever_arquivo_txt()
    except Exception as e:
        raise Exception(f"ERRO na função escrever_arquivo_txt() (linha ~222): {str(e)}\n{traceback.format_exc()}")
    
    # Usar novo sistema de credenciais JSON ao invés do antigo
    try:
        salvar_credenciais_json(login_funcionario, senha_funcionario)
    except Exception as e:
        logging.error(f"ERRO ao salvar credenciais no JSON: {str(e)}\n{traceback.format_exc()}")
        # Não é crítico, continua mesmo se falhar em salvar
    
    zanthus_confirmação=[]

# ---------------------------------------------------------------------------------------------------------
# ----------INTERFACE GRÁFICA-----------------------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------------------------------

class AlterarDadosClientesApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ALTERAR DADOS CLIENTES")
        self.root.geometry("500x600")  # Aumentei a altura para acomodar os novos campos
        
        # Configuração do tema ttkbootstrap
        self.style = ttk.Style("flatly")
        self.style.configure("TFrame", background="white")
        self.style.configure("TLabel", background="white")
        # Configuração específica para o botão preto
        self.style.configure("black.TButton", 
                      background="black", 
                      foreground="white",
                      font=("Inter", 10, "bold"))
        
        # Variáveis para os checkboxes
        self.var_senha = tk.BooleanVar()
        self.var_email = tk.BooleanVar()
        self.var_senha_email = tk.BooleanVar()
        
        self.build_ui()
    
    def build_ui(self):
        # Título principal
        title = ttk.Label(self.root, text="VALIDAÇÃO DO FUNCIONÁRIO", font=("Inter", 16, "bold"), foreground="#DD1426")
        title.pack(pady=(20, 10))
        
        # Frame para campos de login do funcionário
        login_frame = ttk.Frame(self.root)
        login_frame.pack(pady=10, fill="x", padx=20)
        
        # Campo LOGIN DO FUNCIONÁRIO
        ttk.Label(login_frame, text="CÓDIGO ZANTHUS", font=("Inter", 10, "bold")).grid(row=0, column=0, sticky='w', pady=(5, 0), columnspan=2)
        self.login_funcionario_entry = ttk.Entry(login_frame, width=72, bootstyle="dark")
        self.login_funcionario_entry.grid(row=1, column=0, sticky='w', pady=(0, 10), columnspan=2)
        
        # Campo SENHA DO FUNCIONÁRIO
        ttk.Label(login_frame, text="SENHA ZANTHUS", font=("Inter", 10, "bold")).grid(row=2, column=0, sticky='w', pady=(5, 0), columnspan=2)
        self.senha_funcionario_entry = ttk.Entry(login_frame, width=72, show="*", bootstyle="dark")
        self.senha_funcionario_entry.grid(row=3, column=0, sticky='w', pady=(0, 15), columnspan=2)
        
        # Título principal
        title = ttk.Label(self.root, text="ALTERAR DADOS DOS CLIENTES", font=("Inter", 16, "bold"), foreground="#DD1426")
        title.pack(pady=(20, 10))

        # Frame para as checkboxes
        checkbox_frame = ttk.Frame(self.root)
        checkbox_frame.pack(pady=10, fill="x", padx=40)
        
        # Cria as checkboxes com estilo "danger"
        self.senha_check = ttk.Checkbutton(checkbox_frame, text="SENHA", variable=self.var_senha, 
                                  bootstyle="danger", 
                                  command=lambda: self.update_checkbox("senha"))
        self.senha_check.grid(row=0, column=0, padx=35)
        
        self.email_check = ttk.Checkbutton(checkbox_frame, text="EMAIL", variable=self.var_email, 
                                  bootstyle="danger", 
                                  command=lambda: self.update_checkbox("email"))
        self.email_check.grid(row=0, column=1, padx=35)
        
        self.senha_email_check = ttk.Checkbutton(checkbox_frame, text="SENHA E EMAIL", variable=self.var_senha_email, 
                                        bootstyle="danger", 
                                        command=lambda: self.update_checkbox("senha_email"))
        self.senha_email_check.grid(row=0, column=2, padx=35)
        
        # Frame para campos de entrada
        inputs_frame = ttk.Frame(self.root)
        inputs_frame.pack(pady=10, fill="x", padx=20)
        
        # Campo CPF
        ttk.Label(inputs_frame, text="DIGITE O CPF DO CLIENTE", font=("Inter", 10, "bold")).grid(row=0, column=0, sticky='w', pady=(5, 0), columnspan=2)
        self.cpf_entry = ttk.Entry(inputs_frame, width=72, bootstyle="dark")
        self.cpf_entry.grid(row=1, column=0, sticky='w', pady=(0, 10), columnspan=2)
        
        # Campo EMAIL
        ttk.Label(inputs_frame, text="DIGITE O NOVO EMAIL", font=("Inter", 10, "bold")).grid(row=2, column=0, sticky='w', pady=(5, 0), columnspan=2)
        self.email_entry = ttk.Entry(inputs_frame, width=72, bootstyle="dark")
        self.email_entry.grid(row=3, column=0, sticky='w', pady=(0, 10), columnspan=2)
        
        # Campo SENHA
        ttk.Label(inputs_frame, text="DIGITE SUA NOVA SENHA   (Somente números)", font=("Inter", 10, "bold")).grid(row=4, column=0, sticky='w', pady=(5, 0), columnspan=2)
        self.senha_entry = ttk.Entry(inputs_frame, width=72, show="*", bootstyle="dark")
        self.senha_entry.grid(row=5, column=0, sticky='w', pady=(0, 10), columnspan=2)
        # self.senha_entry.grid( columnspan=2, row=5, column=0, sticky="w", padx=90, pady=20)
        
        # BOTÃO INICIAR
        iniciar_btn = ttk.Button(self.root, text="INICIAR", 
                  style="black.TButton", command=self.iniciar)
        iniciar_btn.pack(pady=20, fill="x", padx=20)

    
    def update_checkbox(self, selected):
        # Função para garantir que apenas uma checkbox esteja selecionada por vez
        global change_password, change_email, change_all
        
        # Reseta todas as variáveis globais
        change_password = False
        change_email = False
        change_all = False
        
        # Desmarca todas as checkboxes
        self.var_senha.set(False)
        self.var_email.set(False)
        self.var_senha_email.set(False)
        
        # Marca apenas a checkbox selecionada e atualiza a variável global correspondente
        if selected == "senha":
            self.var_senha.set(True)
            change_password = True
        elif selected == "email":
            self.var_email.set(True)
            change_email = True
        elif selected == "senha_email":
            self.var_senha_email.set(True)
            change_all = True
 # ADICIONE ESTE MÉTODO À SUA CLASSE, FORA DA FUNÇÃO iniciar()

    
    def reset_values(self):
        """Limpa todos os campos e reseta as variáveis"""
        global change_password, change_email, change_all, zanthus_confirmação
        
        # Limpa os campos após exibir a mensagem
        self.cpf_entry.delete(0, tk.END)
        self.email_entry.delete(0, tk.END)
        self.senha_entry.delete(0, tk.END)
        self.login_funcionario_entry.delete(0, tk.END)
        self.senha_funcionario_entry.delete(0, tk.END)
        
        # Opcional: resetar a seleção das checkboxes
        self.var_senha.set(False)
        self.var_email.set(False)
        self.var_senha_email.set(False)
        
        # Resetar as variáveis globais
        change_password = False
        change_email = False
        change_all = False
        zanthus_confirmação = []

    def iniciar(self):
        global change_password, change_email, change_all, cpf, email, senha, login_funcionario, senha_funcionario, zanthus_confirmação
        
        # Obtém os valores dos campos
        cpf = self.cpf_entry.get()
        email = self.email_entry.get()
        senha = self.senha_entry.get()
        login_funcionario = self.login_funcionario_entry.get()
        senha_funcionario = self.senha_funcionario_entry.get()

        filtrar_cpf()

        # ========================================================================
        # NOVO SISTEMA: Validar credenciais usando JSON criptografado
        # ========================================================================
        
        # Buscar senha salva no JSON para este login
        senha_salva = buscar_credencial_json(login_funcionario)
        
        # Se encontrou credencial salva e senha bate, pular validação Zanthus
        if senha_salva and senha_salva == senha_funcionario:
            zanthus_confirmação = ['yes']
            logging.info(f"Login validado via cache JSON: {login_funcionario}")
        else:
            # Credencial não encontrada ou senha diferente - validar no Zanthus
            try:
                loguin_function_Zanthus()
                # Se login Zanthus funcionou, salvar credenciais no JSON
                if len(zanthus_confirmação) > 0:
                    salvar_credenciais_json(login_funcionario, senha_funcionario)
                    logging.info(f"Credencial salva no JSON após validação Zanthus: {login_funcionario}")
            except Exception as err_zanthus: 
                zanthus_confirmação = []
                # Remover credencial do JSON se login Zanthus falhou
                remover_credencial_json(login_funcionario)
                logging.error(f"Falha no login Zanthus, credencial removida: {login_funcionario}")
                messagebox.showinfo("ERRO NO LOGIN ZANTHUS", f"FALHA NO LOGUIN ZANTHUS\n\n{str(err_zanthus)}")
        
        if len(zanthus_confirmação)>0:
            match len(cpf):
                case 11:
                    # VALIDAÇÕES
                    opcao = ""
                    if change_password:
                        opcao = "Alterar SENHA"
                        if len(senha)>=4 and senha.isdigit():
                            try:
                                main_function()
                            except Exception as err:
                                driver.quit()
                                messagebox.showinfo("ERRO", f"OCORREU UM ERRO E A OPERAÇÃO NÃO FOI CONCLUÍDA \\n {err}")
                            else:
                                messagebox.showinfo("OPERAÇÃO CONLUÍDA", f"CPF: {cpf} \\nSenha: {senha}")
                                self.reset_values()  # CHAMANDO COMO MÉTODO DA CLASSE

                        else:
                            messagebox.showinfo("Atenção", "A SENHA DEVE CONTER NO MÍNIMO 4 CARACTERES")
                    elif change_email:
                        opcao = "Alterar EMAIL"
                        if len(email)>5 and   "@" in email and '.' in email:
                            try:
                                main_function()
                            except Exception as err:
                                driver.quit()
                                messagebox.showinfo("ERRO", f"OCORREU UM ERRO E A OPERAÇÃO NÃO FOI CONCLUÍDA \\n {err}")
                            else:
                                messagebox.showinfo("OPERAÇÃO CONLUÍDA", f"CPF: {cpf} \\nEmail: {email}")
                                self.reset_values()  # CHAMANDO COMO MÉTODO DA CLASSE
                        else:
                            messagebox.showinfo("EMAIL INVÁLIDO", "FORMATO DE EMAIL INVÁLIDO, DIGITE NOVAMENTE")

                    elif change_all:
                        opcao = "Alterar SENHA E EMAIL"
                        
                        if len(senha)>=4 and senha.isdigit():
                            if len(email)>5 and  "@" in email and '.' in email:
                                try:
                                    main_function()
                                except Exception as err:
                                    driver.quit()
                                    messagebox.showinfo("ERRO", f"OCORREU UM ERRO E A OPERAÇÃO NÃO FOI CONCLUÍDA \\n {err}")
                                else:
                                    messagebox.showinfo("OPERAÇÃO CONLUÍDA", f"CPF: {cpf} \\nEmail: {email} \\nSenha: {senha}")
                                    self.reset_values()  # CHAMANDO COMO MÉTODO DA CLASSE
                            else:
                                messagebox.showinfo("EMAIL INVÁLIDO", "FORMATO DE EMAIL INVÁLIDO")
                                
                        else:
                            messagebox.showinfo("Atenção", "A SENHA DEVE CONTER NO MÍNIMO 4 CARACTERES APENAS NUMÉRICOS")
                    else:
                        messagebox.showinfo("Atenção", "Selecione uma opção (SENHA, EMAIL ou SENHA E EMAIL)")
                        
                case _:
                    messagebox.showinfo("CPF INVÁLIDO", "O CPF DEVE CONTER 11 DIGITOS, \\n DIGITE NOVAMENTE")


if __name__ == "__main__":
    root = ttk.Window(themename="flatly")  # Usando a janela do ttkbootstrap
    app = AlterarDadosClientesApp(root)
    root.mainloop()