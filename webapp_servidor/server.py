import os
import sys
import time
from flask import Flask, request, jsonify, send_from_directory

# Ajustar caminho base
base_dir = os.path.dirname(os.path.abspath(__file__))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from crm_api_engine import CrmApiEngine

# Inicializar Flask com a pasta public para arquivos estáticos
public_dir = os.path.join(base_dir, "public")
app = Flask(__name__, static_folder=public_dir, static_url_path="")

@app.route('/')
def index():
    return send_from_directory(public_dir, 'index.html')

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        "status": "online",
        "service": "Clube Altera Dados - Servidor AD WebApp Engine",
        "timestamp": int(time.time())
    })

@app.route('/api/alterar_cliente', methods=['POST'])
def alterar_cliente():
    t_start = time.time()
    logs = []
    
    def add_log(msg, level="INFO"):
        logs.append({
            "time": time.strftime("%H:%M:%S"),
            "level": level,
            "message": msg
        })

    try:
        data = request.get_json(force=True) or {}
        
        usr_z = str(data.get("usuario_zanthus", "")).strip()
        pass_z = str(data.get("senha_zanthus", "")).strip()
        cpf = str(data.get("cpf", "")).strip()
        novo_email = str(data.get("novo_email", "")).strip() if data.get("alterar_email", True) else None
        nova_senha = str(data.get("nova_senha", "")).strip() if data.get("alterar_senha", True) else None

        if not usr_z or not pass_z:
            return jsonify({
                "success": False,
                "message": "Credenciais do Zanthus (Usuário e Senha) são obrigatórias.",
                "logs": [{"time": time.strftime("%H:%M:%S"), "level": "ERROR", "message": "Credenciais Zanthus ausentes."}]
            }), 400

        if not cpf:
            return jsonify({
                "success": False,
                "message": "CPF do cliente é obrigatório.",
                "logs": [{"time": time.strftime("%H:%M:%S"), "level": "ERROR", "message": "CPF do cliente não informado."}]
            }), 400

        add_log("🚀 Iniciando automação HTTP em alta velocidade (Servidor AD)...", "INFO")
        engine = CrmApiEngine()

        # Step 1: Login Zanthus
        add_log("1. Autenticando operador no Zanthus via HTTP POST...", "INFO")
        ok_z, ms_z, msg_z = engine.login_zanthus_api(usr_z, pass_z)
        if not ok_z:
            add_log(f"❌ Falha no Zanthus: {msg_z} ({ms_z}ms)", "ERROR")
            return jsonify({
                "success": False,
                "message": f"Falha na autenticação do Zanthus: {msg_z}",
                "elapsed_seconds": round(time.time() - t_start, 2),
                "logs": logs
            }), 401

        add_log(f"➜ Zanthus: {msg_z} ({ms_z}ms)", "SUCCESS")

        # Step 2: Login CRM Bnex
        add_log("2. Autenticando no CRM Bnex via HTTP POST...", "INFO")
        crm_u = os.environ.get("CRM_USUARIO", "GUSTAVO.ALVES")
        crm_p = os.environ.get("CRM_SENHA", "Cwb123@")
        
        ok_c, ms_c, data_c = engine.login_crm_api(crm_u, crm_p)
        if not ok_c:
            add_log(f"❌ Falha no CRM Bnex: Autenticação recusada em {ms_c}ms", "ERROR")
            return jsonify({
                "success": False,
                "message": "Falha na autenticação do CRM Bnex.",
                "elapsed_seconds": round(time.time() - t_start, 2),
                "logs": logs
            }), 401

        add_log(f"➜ CRM Bnex: Autenticado com sucesso em {ms_c}ms", "SUCCESS")

        # Step 3: Alteração do Cliente
        add_log(f"3. Enviando alteração para o CPF {cpf}...", "INFO")
        ok_a, ms_a, msg_a = engine.alterar_cliente_api(cpf, novo_email, nova_senha)
        
        t_total = round(time.time() - t_start, 2)

        if ok_a:
            add_log(f"➜ Alteração: {msg_a} ({ms_a}ms)", "SUCCESS")
            add_log(f"✅ OPERAÇÃO CONCLUÍDA COM SUCESSO EM {t_total}s!", "SUCCESS")
            return jsonify({
                "success": True,
                "message": msg_a,
                "elapsed_seconds": t_total,
                "logs": logs
            }), 200
        else:
            add_log(f"❌ Alteração Falhou: {msg_a} ({ms_a}ms)", "ERROR")
            return jsonify({
                "success": False,
                "message": msg_a,
                "elapsed_seconds": t_total,
                "logs": logs
            }), 400

    except Exception as e:
        t_total = round(time.time() - t_start, 2)
        add_log(f"❌ ERRO INESPERADO: {str(e)}", "ERROR")
        return jsonify({
            "success": False,
            "message": f"Erro interno no servidor: {str(e)}",
            "elapsed_seconds": t_total,
            "logs": logs
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    print(f"==================================================")
    print(f"⚡ CLUBE ALTERA DADOS - SERVIDOR AD WEBAPP INICIADO")
    print(f"➜ Porta: {port}")
    print(f"➜ Acesse no Servidor AD ou na Rede Local:")
    print(f"   http://localhost:{port}")
    print(f"   http://<IP_DO_SERVIDOR_AD>:{port}")
    print(f"==================================================")

    # Tenta usar o Waitress (Servidor HTTP Profissional para Windows Server)
    try:
        from waitress import serve
        serve(app, host='0.0.0.0', port=port, threads=8)
    except ImportError:
        print("[AVISO] Waitress não instalado. Rodando com servidor padrao Flask...")
        app.run(host='0.0.0.0', port=port, debug=False)
