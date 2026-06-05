import os
import sys
import json
import urllib.request
import urllib.error
import zipfile
import hashlib
import subprocess
import shutil
import time

# ==========================================
# CONFIGURAÇÕES DA APLICAÇÃO
# ==========================================
GITHUB_REPO = "anjosdevpython/clube_altera_dados"
IS_PRIVATE = False
# Token lido de arquivo externo (nunca hardcoded no código)
_token_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "github_token.txt")
GITHUB_TOKEN = open(_token_file).read().strip() if os.path.exists(_token_file) else ""
APP_EXE_NAME = "CLUBE_modif.exe"          
ZIP_PREFIX = "CLUBE_modif-"               

if getattr(sys, 'frozen', False):
    UPDATER_DIR = os.path.dirname(os.path.abspath(sys.executable))
    BASE_DIR = os.path.dirname(UPDATER_DIR)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

APP_DIR = os.path.join(BASE_DIR, "app")
VERSION_FILE = os.path.join(BASE_DIR, "version.txt")
APP_EXE_PATH = os.path.join(APP_DIR, APP_EXE_NAME)

# ==========================================
# MENSAGENS DE ERRO E SOLUÇÕES
# ==========================================
ERRORS = {
    "CHECK_UPDATE": {
        "msg": "Erro ao verificar atualizações no GitHub.",
        "sol": "Verifique sua conexão com a internet e tente novamente."
    },
    "ASSETS_NOT_FOUND": {
        "msg": "Arquivos de atualização não encontrados no servidor.",
        "sol": "Aguarde alguns minutos ou entre em contato com o desenvolvedor."
    },
    "DOWNLOAD_FAILED": {
        "msg": "Falha ao baixar os arquivos de atualização.",
        "sol": "Verifique sua conexão com a internet ou se um antivírus está bloqueando o download."
    },
    "HASH_MISMATCH": {
        "msg": "Integridade do arquivo falhou (SHA256 incorreto).",
        "sol": "O download pode ter sido corrompido. O atualizador tentará novamente na próxima execução."
    },
    "CLOSE_APP_FAILED": {
        "msg": f"Não foi possível fechar o {APP_EXE_NAME} automaticamente.",
        "sol": f"Por favor, feche o {APP_EXE_NAME} manualmente pelo Gerenciador de Tarefas."
    },
    "REPLACE_FILES_FAILED": {
        "msg": "Erro ao substituir os arquivos da nova versão.",
        "sol": "Certifique-se de que não há arquivos abertos e que você tem permissão de administrador."
    },
    "EXTRACT_FAILED": {
        "msg": "Erro ao extrair o pacote de atualização.",
        "sol": "O arquivo ZIP pode estar corrompido. Reinicie o atualizador para tentar novamente."
    },
    "EXE_NOT_FOUND": {
        "msg": "O aplicativo principal não foi encontrado após a atualização.",
        "sol": "A instalação pode ter falhado. Tente reinstalar o programa completamente."
    }
}

def show_error(error_key, detail=""):
    error = ERRORS.get(error_key, {"msg": "Erro desconhecido.", "sol": "Tente reiniciar o programa."})
    print("\n" + "="*50)
    print(f"❌ ERRO: {error['msg']}")
    if detail:
        print(f"🔍 DETALHE: {detail}")
    print(f"💡 SOLUÇÃO: {error['sol']}")
    print("="*50 + "\n")

def get_current_version():
    if os.path.exists(VERSION_FILE):
        with open(VERSION_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    return "0.0.0"

def get_latest_github_release():
    url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
    req = urllib.request.Request(url)
    if IS_PRIVATE and GITHUB_TOKEN:
        req.add_header("Authorization", f"token {GITHUB_TOKEN}")
    try:
        with urllib.request.urlopen(req, timeout=8) as response:
            return json.loads(response.read().decode())
    except urllib.error.URLError as e:
        show_error("CHECK_UPDATE", str(e))
        return None

def download_file(url, dest):
    print(f"Baixando: {url}")
    req = urllib.request.Request(url)
    if IS_PRIVATE and GITHUB_TOKEN:
        req.add_header("Accept", "application/octet-stream") 
        req.add_header("Authorization", f"token {GITHUB_TOKEN}")
        
    with urllib.request.urlopen(req, timeout=15) as response, open(dest, 'wb') as out_file:
        shutil.copyfileobj(response, out_file)

def verify_sha256(filepath, expected_hash):
    sha = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha.update(chunk)
    return sha.hexdigest().lower() == expected_hash.lower()

def run_app():
    if os.path.exists(APP_EXE_PATH):
        print("Iniciando aplicativo principal...")
        subprocess.Popen([APP_EXE_PATH], cwd=APP_DIR)
    else:
        show_error("EXE_NOT_FOUND", f"Caminho não existe: {APP_EXE_PATH}")
    sys.exit(0)

def main():
    current_version = get_current_version()
    print(f"Versao atual: {current_version}")
    
    release = get_latest_github_release()
    if not release:
        print("Nenhuma release encontrada.")
        time.sleep(2)
        return

    latest_version = release.get("tag_name") 
    if current_version == latest_version:
        print("Voce ja esta na versao mais recente.")
        time.sleep(2)
        return
        
    print(f"Atualizacao encontrada. Iniciando processo para {latest_version}...")
    
    zip_url, sha256_url = None, None
    for asset in release.get("assets", []):
        if asset["name"].startswith(ZIP_PREFIX) and asset["name"].endswith(".zip"):
            zip_url = asset["url"] if IS_PRIVATE else asset["browser_download_url"]
        elif asset["name"].endswith(".sha256"):
            sha256_url = asset["url"] if IS_PRIVATE else asset["browser_download_url"]
            
    if not zip_url or not sha256_url:
        show_error("ASSETS_NOT_FOUND")
        time.sleep(2)
        return

    temp_zip = os.path.join(BASE_DIR, "update.zip")
    temp_sha256 = os.path.join(BASE_DIR, "update.sha256")
    
    try:
        download_file(sha256_url, temp_sha256)
        download_file(zip_url, temp_zip)
    except Exception as e:
        show_error("DOWNLOAD_FAILED", str(e))
        time.sleep(5)
        return
        
    try:
        with open(temp_sha256, "r", encoding="utf-8") as f:
            expected_hash = f.read().strip().split()[0]
            
        print("Verificando integridade...")
        if not verify_sha256(temp_zip, expected_hash):
            show_error("HASH_MISMATCH")
            time.sleep(3)
            return

        print("Fechando aplicativo para atualizar...")
        # Tenta fechar o app com retries
        for _ in range(3):
            try:
                os.system(f"taskkill /F /IM \"{APP_EXE_NAME}\" >nul 2>&1")
                time.sleep(2)
            except: pass
            
        print("Substituindo arquivos...")
        # Tenta remover a pasta antiga várias vezes
        for _ in range(3):
            try:
                if os.path.exists(APP_DIR):
                    shutil.rmtree(APP_DIR)
                break
            except:
                time.sleep(2)
                
        try:
            os.makedirs(APP_DIR, exist_ok=True)
        except Exception as e:
            show_error("REPLACE_FILES_FAILED", str(e))
            time.sleep(5)
            return
            
        try:
            with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
                zip_ref.extractall(APP_DIR)
        except Exception as e:
            show_error("EXTRACT_FAILED", str(e))
            time.sleep(5)
            return
            
        with open(VERSION_FILE, "w", encoding="utf-8") as f:
            f.write(latest_version)
            
        print("Atualizacao concluida com sucesso!")
        time.sleep(1)
        run_app()
            
    except Exception as e:
        show_error("REPLACE_FILES_FAILED", str(e))
        time.sleep(5)
    finally:
        if os.path.exists(temp_zip): os.remove(temp_zip)
        if os.path.exists(temp_sha256): os.remove(temp_sha256)

if __name__ == "__main__":
    main()
