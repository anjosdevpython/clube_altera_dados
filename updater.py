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
GITHUB_TOKEN = ""                    
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
        print(f"Erro ao checar atualizacao: {e}")
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
        print(f"Erro: aplicativo não encontrado em {APP_EXE_PATH}")
    sys.exit(0)

def main():
    current_version = get_current_version()
    print(f"Versao atual: {current_version}")
    
    release = get_latest_github_release()
    if not release:
        run_app()

    latest_version = release.get("tag_name") 
    if current_version == latest_version:
        run_app()
        
    print(f"Atualizacao encontrada. Saltando para {latest_version}...")
    
    zip_url, sha256_url = None, None
    for asset in release.get("assets", []):
        if asset["name"].startswith(ZIP_PREFIX) and asset["name"].endswith(".zip"):
            zip_url = asset["url"] if IS_PRIVATE else asset["browser_download_url"]
        elif asset["name"].endswith(".sha256"):
            sha256_url = asset["url"] if IS_PRIVATE else asset["browser_download_url"]
            
    if not zip_url or not sha256_url:
        run_app()

    temp_zip = os.path.join(BASE_DIR, "update.zip")
    temp_sha256 = os.path.join(BASE_DIR, "update.sha256")
    
    try:
        download_file(sha256_url, temp_sha256)
        download_file(zip_url, temp_zip)
        
        with open(temp_sha256, "r", encoding="utf-8") as f:
            expected_hash = f.read().strip().split()[0]
            
        print("Verificando SHA-256...")
        if not verify_sha256(temp_zip, expected_hash):
            run_app()

        os.system(f"taskkill /F /IM \"{APP_EXE_NAME}\" >nul 2>&1")
        time.sleep(1.5)
        
        print("Instalando nova versao...")
        if os.path.exists(APP_DIR):
            shutil.rmtree(APP_DIR, ignore_errors=True)
        os.makedirs(APP_DIR, exist_ok=True)
            
        with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
            zip_ref.extractall(APP_DIR)
            
        with open(VERSION_FILE, "w", encoding="utf-8") as f:
            f.write(latest_version)
            
    except Exception as e:
        print(f"Erro processando atualizacao: {e}")
    finally:
        if os.path.exists(temp_zip): os.remove(temp_zip)
        if os.path.exists(temp_sha256): os.remove(temp_sha256)
        
    run_app()

if __name__ == "__main__":
    main()
