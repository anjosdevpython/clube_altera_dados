import os
import sys
import time
import json
import re
import urllib.parse
from typing import Tuple, Dict, Any, Optional

try:
    import requests
except ImportError:
    requests = None

class CrmApiEngine:
    """
    Engine de Alta Velocidade para automação de alteração de dados do Clube de Vantagens.
    Executa chamadas HTTP diretas sem necessidade de navegadores gráficos ou seletores da UI.
    Otimizado para execução Serverless (Vercel / AWS Lambda / Flask).
    """

    def __init__(self, crm_base_url: str = "https://painel-minipreco.bnex.com.br:5510"):
        self.crm_base_url = crm_base_url
        self.session = requests.Session() if requests else None
        self.session_authenticated = False
        
        # Headers padrão que mimetizam um navegador real
        if self.session:
            self.session.headers.update({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive"
            })

    def login_zanthus_api(self, usuario_zan: str, senha_zan: str) -> Tuple[bool, int, str]:
        """
        Valida operador no Zanthus através de requisição HTTP POST.
        Endpoint: https://minipreco.zanthus.bluesoft.com.br/manager/login.php5
        """
        t0 = time.time()
        url_zanthus = "https://minipreco.zanthus.bluesoft.com.br/manager/login.php5"
        payload = {
            "USUARIO": usuario_zan,
            "SENHA": senha_zan,
            "submit": " Entrar "
        }
        
        if not self.session:
            return False, 0, "Biblioteca requests não instalada"

        try:
            resp = self.session.post(url_zanthus, data=payload, timeout=8, allow_redirects=True)
            elapsed_ms = int((time.time() - t0) * 1000)

            # Validação: Se redirecionar para index/home ou contiver indícios de login concluído
            if "login.php5" not in resp.url or "Sair" in resp.text or "Logout" in resp.text or "Usuário ativo" in resp.text or resp.status_code == 200:
                if "Senha incorreta" in resp.text or "Usuário inválido" in resp.text or "incorretos" in resp.text:
                    return False, elapsed_ms, "Usuário ou senha Zanthus incorretos"
                return True, elapsed_ms, f"Operador '{usuario_zan}' autenticado com sucesso"
            else:
                return False, elapsed_ms, "Falha na autenticação do operador no Zanthus"

        except Exception as e:
            elapsed_ms = int((time.time() - t0) * 1000)
            return False, elapsed_ms, f"Erro de conexão com Zanthus: {str(e)}"

    def login_crm_api(self, crm_usuario: str = "GUSTAVO.ALVES", crm_senha: str = "Cwb123@") -> Tuple[bool, int, Dict[str, Any]]:
        """
        Realiza login completo no CRM Bnex via HTTP POST.
        Extrai o token CSRF (__RequestVerificationToken) e estabelece a sessão ASP.NET.
        """
        t0 = time.time()
        if not self.session:
            return False, 0, {"error": "Session uninitialized"}

        try:
            # Step 1: Obter token CSRF
            url_login_page = f"{self.crm_base_url}/Login?ReturnUrl=%2F"
            resp_page = self.session.get(url_login_page, timeout=8)
            
            # Extrair token CSRF
            match = re.search(r'name="__RequestVerificationToken"\s+type="hidden"\s+value="([^"]+)"', resp_page.text)
            if not match:
                match = re.search(r'value="([^"]+)"\s+name="__RequestVerificationToken"', resp_page.text)
            
            csrf_token = match.group(1) if match else ""

            # Step 2: POST de autenticação
            url_auth = f"{self.crm_base_url}/Login/Autenticar"
            headers_auth = {
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "X-Requested-With": "XMLHttpRequest",
                "Referer": url_login_page
            }
            
            payload_auth = {
                "usuario": crm_usuario,
                "senha": crm_senha,
                "ReturnUrl": "/",
                "__RequestVerificationToken": csrf_token
            }

            resp_auth = self.session.post(url_auth, data=payload_auth, headers=headers_auth, timeout=8)
            
            # Step 3: Handshake de sessão no root e /Cliente
            self.session.get(f"{self.crm_base_url}/", timeout=8)
            self.session.get(f"{self.crm_base_url}/Cliente", timeout=8)

            elapsed_ms = int((time.time() - t0) * 1000)
            
            if resp_auth.status_code == 200:
                self.session_authenticated = True
                return True, elapsed_ms, {"status": "Authenticated", "usuario": crm_usuario}
            else:
                return False, elapsed_ms, {"status": "Failed", "status_code": resp_auth.status_code}

        except Exception as e:
            elapsed_ms = int((time.time() - t0) * 1000)
            return False, elapsed_ms, {"error": str(e)}

    def alterar_cliente_api(self, cpf: str, novo_email: Optional[str] = None, nova_senha: Optional[str] = None) -> Tuple[bool, int, str]:
        """
        Busca e altera os dados do cliente (Email/Senha) no CRM Bnex via requisição HTTP direta.
        """
        t0 = time.time()
        if not self.session:
            return False, 0, "Sessão não iniciada"

        cpf_limpo = re.sub(r'\D', '', cpf)
        if not cpf_limpo:
            return False, 0, "CPF inválido ou não informado"

        try:
            # 1. Buscar cliente por CPF
            url_busca = f"{self.crm_base_url}/Cliente/ConsultarClientesGrid"
            payload_busca = {
                "sEcho": "1",
                "iColumns": "9",
                "sColumns": "",
                "iDisplayStart": "0",
                "iDisplayLength": "10",
                "mDataProp_0": "Codigo",
                "mDataProp_1": "Nome",
                "mDataProp_2": "Cpf",
                "mDataProp_3": "Email",
                "mDataProp_4": "DataNascimento",
                "mDataProp_5": "Situacao",
                "mDataProp_6": "TelefoneFormatado",
                "mDataProp_7": "CelularFormatado",
                "mDataProp_8": "Acoes",
                "sSearch": cpf_limpo,
                "bRegex": "false"
            }

            resp_busca = self.session.post(url_busca, data=payload_busca, timeout=8)
            if resp_busca.status_code != 200:
                return False, int((time.time() - t0) * 1000), f"Erro ao buscar cliente (HTTP {resp_busca.status_code})"

            data_json = resp_busca.json()
            aaData = data_json.get("aaData", [])
            if not aaData:
                return False, int((time.time() - t0) * 1000), f"Cliente com CPF {cpf_limpo} não foi encontrado no CRM"

            cliente = aaData[0]
            id_cliente = cliente.get("Codigo")

            # 2. Carregar formulário do cliente para obter campos obrigatórios
            url_edit_page = f"{self.crm_base_url}/Cliente/Editar/{id_cliente}"
            resp_edit_page = self.session.get(url_edit_page, timeout=8)

            # Extrair campos chave do HTML do cliente
            def _get_val(name):
                m = re.search(r'name="' + name + r'"[^>]*value="([^"]*)"', resp_edit_page.text)
                if not m:
                    m = re.search(r'value="([^"]*)"[^>]*name="' + name + r'"', resp_edit_page.text)
                return m.group(1) if m else ""

            nome_cli = _get_val("Nome") or cliente.get("Nome", "")
            data_nasc = _get_val("DataNascimento") or cliente.get("DataNascimento", "")
            sexo_cli = _get_val("Sexo") or "M"
            
            email_final = novo_email if (novo_email and novo_email.strip()) else (_get_val("Email") or cliente.get("Email", ""))
            
            # Extract CSRF token from edit page
            match_csrf = re.search(r'name="__RequestVerificationToken"\s+type="hidden"\s+value="([^"]+)"', resp_edit_page.text)
            csrf_token_edit = match_csrf.group(1) if match_csrf else ""

            # 3. Executar o POST de atualização de dados
            url_salvar = f"{self.crm_base_url}/Cliente/Salvar"
            payload_salvar = {
                "Codigo": id_cliente,
                "Nome": nome_cli,
                "Cpf": cpf_limpo,
                "Email": email_final,
                "DataNascimento": data_nasc,
                "Sexo": sexo_cli,
                "__RequestVerificationToken": csrf_token_edit
            }

            if nova_senha and nova_senha.strip():
                payload_salvar["Senha"] = nova_senha.strip()
                payload_salvar["ConfirmarSenha"] = nova_senha.strip()

            resp_salvar = self.session.post(url_salvar, data=payload_salvar, timeout=8)
            elapsed_ms = int((time.time() - t0) * 1000)

            if resp_salvar.status_code == 200 or "sucesso" in resp_salvar.text.lower():
                msg_ret = f"Dados do cliente {nome_cli} (CPF {cpf_limpo}) alterados com sucesso!"
                return True, elapsed_ms, msg_ret
            else:
                return False, elapsed_ms, f"Falha ao salvar dados no CRM Bnex (HTTP {resp_salvar.status_code})"

        except Exception as e:
            elapsed_ms = int((time.time() - t0) * 1000)
            return False, elapsed_ms, f"Erro no processamento da alteração: {str(e)}"
