import os
import sys
import time
from flask import Flask, request, jsonify

# Adicionar pasta pai ao sys.path para importar crm_api_engine
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from crm_api_engine import CrmApiEngine

app = Flask(__name__)

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        "status": "online",
        "service": "Clube Altera Dados - Vercel API Direct Engine",
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

        add_log("🚀 Iniciando automação HTTP em alta velocidade (Vercel Engine)...", "INFO")
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

# Vercel necessita da variável app exportada
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
