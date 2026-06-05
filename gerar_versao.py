import os
import sys
import json
import hashlib
import zipfile
import shutil
import subprocess
import tkinter as tk
from tkinter import messagebox, scrolledtext
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import threading
import requests

# ==========================================
# CONFIGURAÇÕES
# ==========================================
MAIN_FILE = "CLUBE_modif.py"
VERSION_FILE = "version.txt"
UPDATER_FILE = "updater.py"
INSTALLER_ISS = "installer.iss"
ZIP_PREFIX = "CLUBE_modif-"
GITHUB_REPO = "anjosdevpython/clube_altera_dados"
_token_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "github_token.txt")
GITHUB_TOKEN = open(_token_file).read().strip() if os.path.exists(_token_file) else ""

class AutoBuildApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AUTOMAÇÃO DE RELEASE - CLUBE")
        self.root.geometry("600x500")
        
        self.style = ttk.Style("darkly")
        
        self.setup_ui()
        self.load_current_version()

    def setup_ui(self):
        container = ttk.Frame(self.root, padding=20)
        container.pack(fill=BOTH, expand=YES)
        
        ttk.Label(container, text="GERADOR DE ATUALIZAÇÃO", font=("Inter", 16, "bold"), bootstyle="danger").pack(pady=10)
        
        # Versão
        v_frame = ttk.Frame(container)
        v_frame.pack(fill=X, pady=10)
        
        ttk.Label(v_frame, text="Versão Atual:", font=("Inter", 10)).pack(side=LEFT)
        self.lbl_current_v = ttk.Label(v_frame, text="0.0.0", font=("Inter", 10, "bold"), bootstyle="warning")
        self.lbl_current_v.pack(side=LEFT, padx=5)
        
        ttk.Label(v_frame, text="Nova Versão:", font=("Inter", 10)).pack(side=LEFT, padx=(20, 5))
        self.ent_new_v = ttk.Entry(v_frame, width=10)
        self.ent_new_v.pack(side=LEFT)
        
        # Opções
        self.check_installer = ttk.Checkbutton(container, text="Gerar Instalador Final (Inno Setup)", bootstyle="info", variable=tk.BooleanVar(value=True))
        self.check_installer.pack(pady=5, anchor=W)
        
        # Console de Log
        self.log_area = scrolledtext.ScrolledText(container, height=12, bg="#1a1a1a", fg="#00ff00", font=("Consolas", 9))
        self.log_area.pack(fill=BOTH, expand=YES, pady=10)
        
        # GitHub Config
        gh_frame = ttk.Frame(container)
        gh_frame.pack(fill=X, pady=5)
        
        self.check_github = ttk.Checkbutton(gh_frame, text="Fazer Release no GitHub", bootstyle="success", variable=tk.BooleanVar(value=False))
        self.check_github.pack(side=LEFT)
        
        ttk.Label(gh_frame, text="Token:", font=("Inter", 9)).pack(side=LEFT, padx=(10, 5))
        self.ent_token = ttk.Entry(gh_frame, width=30, show="*")
        self.ent_token.pack(side=LEFT)
        
        # Preencher se o token estiver no backend
        if GITHUB_TOKEN and GITHUB_TOKEN != "seu_token_aqui":
            self.ent_token.insert(0, GITHUB_TOKEN)
            self.check_github.state(['selected'])
        
        # Botas
        self.btn_iniciar = ttk.Button(container, text="🚀 INICIAR PROCESSO COMPLETO", bootstyle="danger", command=self.start_build_thread)
        self.btn_iniciar.pack(fill=X, pady=5)
        
        # Footer
        footer = ttk.Frame(container)
        footer.pack(fill=X, pady=5)
        
        credits_label = ttk.Label(footer, text="Desenvolvido por Allan Anjos & Victor Lameiro", font=("Inter", 8))
        credits_label.pack(side=RIGHT)

    def log(self, text):
        self.log_area.insert(tk.END, f"{text}\n")
        self.log_area.see(tk.END)

    def load_current_version(self):
        if os.path.exists(VERSION_FILE):
            with open(VERSION_FILE, "r") as f:
                v = f.read().strip()
                self.lbl_current_v.config(text=v)
                # Sugerir próxima versão
                parts = v.split('.')
                if len(parts) == 3:
                    parts[-1] = str(int(parts[-1]) + 1)
                    self.ent_new_v.insert(0, ".".join(parts))

    def start_build_thread(self):
        new_v = self.ent_new_v.get().strip()
        if not new_v:
            messagebox.showerror("Erro", "Digite a nova versão!")
            return
        
        self.btn_iniciar.state(['disabled'])
        self.log_area.delete(1.0, tk.END)
        threading.Thread(target=self.process_build, args=(new_v,), daemon=True).start()

    def process_build(self, version):
        try:
            # 1. Atualizar Arquivos
            self.log(f"--- FASE 1: ATUALIZANDO VERSÃO PARA {version} ---")
            
            # version.txt
            with open(VERSION_FILE, "w") as f:
                f.write(version)
            self.log("✅ version.txt atualizado.")
            
            # CLUBE_modif.py
            with open(MAIN_FILE, "r", encoding="utf-8") as f:
                lines = f.readlines()
            
            with open(MAIN_FILE, "w", encoding="utf-8") as f:
                for line in lines:
                    if line.startswith('CURRENT_VERSION ='):
                        f.write(f'CURRENT_VERSION = "{version}"\n')
                    else:
                        f.write(line)
            self.log(f"✅ {MAIN_FILE} atualizado.")

            # 2. PyInstaller App
            self.log("\n--- FASE 2: COMPILANDO APP PRINCIPAL (PyInstaller) ---")
            self.log("Isso pode demorar alguns minutos...")
            python_exe = sys.executable
            cmd_app = f'"{python_exe}" -m PyInstaller --noconfirm --onedir -w --icon="clube_icon.ico" --add-data "clube_icon.ico;." --add-data "pw-browsers;pw-browsers" --name "CLUBE_modif" "{MAIN_FILE}"'
            result = subprocess.run(cmd_app, shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                self.log(f"❌ Erro no PyInstaller App: {result.stderr}")
                return
            self.log("✅ Compilação do App concluída.")

            # 3. PyInstaller Updater
            self.log("\n--- FASE 3: COMPILANDO ATUALIZADOR ---")
            python_exe = sys.executable
            cmd_upd = f'"{python_exe}" -m PyInstaller --noconfirm --onefile --uac-admin --icon="clube_icon.ico" --name "clube_updater" "{UPDATER_FILE}"'
            subprocess.run(cmd_upd, shell=True)
            self.log("✅ Compilação do Atualizador concluída.")

            # 4. Criar ZIP e SHA256
            self.log("\n--- FASE 4: CRIANDO PACOTE DE DISTRIBUIÇÃO ---")
            zip_filename = f"{ZIP_PREFIX}{version}.zip"
            dist_path = os.path.join("dist", "CLUBE_modif")
            
            with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root_dir, dirs, files in os.walk(dist_path):
                    for file in files:
                        file_path = os.path.join(root_dir, file)
                        arcname = os.path.relpath(file_path, dist_path)
                        zipf.write(file_path, arcname)
            
            self.log(f"✅ ZIP criado: {zip_filename}")
            
            # SHA256
            sha = hashlib.sha256()
            with open(zip_filename, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha.update(chunk)
            
            hash_val = sha.hexdigest().lower()
            with open(f"{zip_filename}.sha256", "w") as f:
                f.write(hash_val)
            self.log(f"✅ Hash SHA256: {hash_val}")

            # 5. Installer
            if self.check_installer.instate(['selected']):
                self.log("\n--- FASE 5: GERANDO INSTALADOR (INNO SETUP) ---")
                
                # Atualiza versão no arquivo .iss antes de compilar
                if os.path.exists(INSTALLER_ISS):
                    with open(INSTALLER_ISS, "r", encoding="utf-8") as f:
                        iss_lines = f.readlines()
                    with open(INSTALLER_ISS, "w", encoding="utf-8") as f:
                        for line in iss_lines:
                            if line.startswith("AppVersion="):
                                f.write(f"AppVersion={version}\n")
                            else:
                                f.write(line)
                    self.log(f"✅ Versão atualizada no {INSTALLER_ISS}")

                iscc_path = r"C:\Program Files (x86)\Inno Setup 6\iscc.exe"
                if os.path.exists(iscc_path):
                    subprocess.run([iscc_path, INSTALLER_ISS], shell=True)
                    self.log("✅ Instalador gerado na pasta 'Output'.")
                else:
                    self.log("⚠️ Inno Setup não encontrado. Pulando instalador.")

            # 6. GitHub Release
            if self.check_github.instate(['selected']):
                self.log("\n--- FASE 6: REALIZANDO RELEASE NO GITHUB ---")
                token = self.ent_token.get().strip()
                if not token:
                    self.log("❌ Erro: Token do GitHub não fornecido!")
                else:
                    try:
                        files_to_upload = [
                            zip_filename,
                            f"{zip_filename}.sha256",
                            os.path.join("dist", "clube_updater.exe")
                        ]
                        installer_path = os.path.join("Output", "Instalador_Clube.exe")
                        if os.path.exists(installer_path):
                            files_to_upload.append(installer_path)

                        self.github_release(version, token, files_to_upload)
                        self.log("✅ Release no GitHub concluído com sucesso.")
                    except Exception as e:
                        self.log(f"❌ Erro no upload GitHub: {str(e)}")

            self.log("\n✨ PROCESSO CONCLUÍDO COM SUCESSO! ✨")
            self.log("Os arquivos para o GitHub estão na raiz da sua pasta.")
            
            msg = f"Versão {version} gerada com sucesso!"
            if self.check_github.instate(['selected']):
                msg += "\n\nRelease automatizado realizado no GitHub."
            else:
                msg += "\n\nAgora basta subir o ZIP e o .SHA256 para o GitHub Releases."
                
            messagebox.showinfo("Sucesso", msg)
            os.startfile(os.getcwd())

        except Exception as e:
            self.log(f"❌ ERRO CRÍTICO: {str(e)}")
            messagebox.showerror("Erro", str(e))
        finally:
            self.btn_iniciar.state(['!disabled'])

    def github_release(self, version, token, files):
        """Cria release e faz upload dos arquivos no GitHub"""
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        release_data = {
            "tag_name": f"v{version}",
            "name": f"Release v{version}",
            "body": f"Atualização automática: Versão {version} integrada com Playwright, Logs detalhados e exportação TXT.",
            "draft": False,
            "prerelease": False
        }
        
        self.log(f"Criando release v{version}...")
        url = f"https://api.github.com/repos/{GITHUB_REPO}/releases"
        response = requests.post(url, headers=headers, json=release_data)
        
        if response.status_code == 201:
            release_id = response.json()["id"]
            upload_url_template = response.json()["upload_url"].split("{")[0]
            self.log("Release criado com sucesso. Iniciando upload de assets...")
            
            for file_path in files:
                if os.path.exists(file_path):
                    file_name = os.path.basename(file_path)
                    self.log(f"Subindo {file_name}...")
                    
                    with open(file_path, "rb") as f:
                        upload_url = f"{upload_url_template}?name={file_name}"
                        headers_upload = headers.copy()
                        headers_upload["Content-Type"] = "application/octet-stream"
                        
                        resp_upload = requests.post(upload_url, headers=headers_upload, data=f)
                        if resp_upload.status_code == 201:
                            self.log(f"✅ {file_name} enviado.")
                        else:
                            self.log(f"⚠️ Falha ao subir {file_name}: {resp_upload.text}")
                else:
                    self.log(f"⚠️ Arquivo não encontrado para upload: {file_path}")
        else:
            raise Exception(f"Falha ao criar release: {response.text}")

if __name__ == "__main__":
    root = tk.Tk()
    app = AutoBuildApp(root)
    root.mainloop()
