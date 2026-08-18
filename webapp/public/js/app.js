/* ==========================================================================
   CLUBE ALTERA DADOS - WEBAPP FRONTEND ENGINE (VANILLA JS)
   ========================================================================== */

function formatCPF(input) {
    let v = input.value.replace(/\D/g, '');
    if (v.length > 11) v = v.substring(0, 11);
    
    if (v.length <= 11) {
        v = v.replace(/(\d{3})(\d)/, '$1.$2');
        v = v.replace(/(\d{3})(\d)/, '$1.$2');
        v = v.replace(/(\d{3})(\d{1,2})$/, '$1-$2');
    }
    input.value = v;
}

function togglePassword(inputId, btn) {
    const input = document.getElementById(inputId);
    if (!input) return;
    
    if (input.type === "password") {
        input.type = "text";
        btn.textContent = "🙈";
    } else {
        input.type = "password";
        btn.textContent = "👁️";
    }
}

function toggleInputState(inputId, isChecked) {
    const input = document.getElementById(inputId);
    if (input) {
        input.disabled = !isChecked;
        if (!isChecked) input.value = "";
    }
}

function appendLog(message, level = "INFO", timestamp = null) {
    const terminal = document.getElementById("terminalLogs");
    if (!terminal) return;

    const timeStr = timestamp || new Date().toLocaleTimeString('pt-BR');
    const logLine = document.createElement("div");
    
    let cssClass = "log-info";
    if (level === "SUCCESS") cssClass = "log-success";
    if (level === "ERROR") cssClass = "log-error";

    logLine.className = `log-line ${cssClass}`;
    logLine.innerHTML = `<span class="log-time">[${timeStr}]</span> ${escapeHtml(message)}`;
    
    terminal.appendChild(logLine);
    terminal.scrollTop = terminal.scrollHeight;
}

function clearLogs() {
    const terminal = document.getElementById("terminalLogs");
    if (terminal) {
        terminal.innerHTML = "";
        appendLog("Logs limpos pelo operador.", "INFO");
    }
}

function copyLogs() {
    const terminal = document.getElementById("terminalLogs");
    if (!terminal) return;

    const text = terminal.innerText;
    navigator.clipboard.writeText(text).then(() => {
        showToast("Logs copiados para a área de transferência!", "success");
    }).catch(err => {
        showToast("Erro ao copiar logs.", "error");
    });
}

function showToast(message, type = "success") {
    const container = document.getElementById("toastContainer");
    if (!container) return;

    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `<span>${type === 'success' ? '✅' : '❌'}</span> <span>${escapeHtml(message)}</span>`;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = "0";
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.innerText = text;
    return div.innerHTML;
}

async function handleFormSubmit(event) {
    event.preventDefault();

    const usr_z = document.getElementById("usuario_zanthus").value.trim();
    const pass_z = document.getElementById("senha_zanthus").value.trim();
    const cpf = document.getElementById("cpf").value.trim();
    
    const chk_email = document.getElementById("chk_alterar_email").checked;
    const chk_senha = document.getElementById("chk_alterar_senha").checked;
    
    const novo_email = document.getElementById("novo_email").value.trim();
    const nova_senha = document.getElementById("nova_senha").value.trim();

    if (!usr_z || !pass_z) {
        showToast("Por favor, preencha o Usuário e Senha do Zanthus.", "error");
        return;
    }

    if (!cpf) {
        showToast("Por favor, informe o CPF do cliente.", "error");
        return;
    }

    if (!chk_email && !chk_senha) {
        showToast("Selecione pelo menos uma opção: Alterar E-mail ou Alterar Senha.", "error");
        return;
    }

    // UI Elements
    const btnSubmit = document.getElementById("btnSubmit");
    const progressContainer = document.getElementById("progressContainer");
    const progressBar = document.getElementById("progressBar");
    const statusBadge = document.getElementById("statusBadge");
    const timerBadge = document.getElementById("timerBadge");

    // Lock UI
    btnSubmit.disabled = true;
    btnSubmit.querySelector(".btn-text").textContent = "PROCESSANDO ALTERAÇÃO...";
    progressContainer.style.display = "block";
    progressBar.style.width = "15%";

    statusBadge.textContent = "⏳ Executando automação...";
    statusBadge.style.color = "var(--warning)";
    statusBadge.style.backgroundColor = "rgba(245, 158, 11, 0.15)";
    
    timerBadge.style.display = "inline-block";
    timerBadge.textContent = "⏱️ Processando...";

    clearLogs();
    appendLog(`🚀 Enviando requisição HTTP para a API Vercel...`, "INFO");

    const payload = {
        usuario_zanthus: usr_z,
        senha_zanthus: pass_z,
        cpf: cpf,
        alterar_email: chk_email,
        alterar_senha: chk_senha,
        novo_email: chk_email ? novo_email : "",
        nova_senha: chk_senha ? nova_senha : ""
    };

    progressBar.style.width = "40%";

    try {
        const response = await fetch("/api/alterar_cliente", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        });

        progressBar.style.width = "85%";
        const result = await response.json();

        // Render returned server logs
        if (result.logs && Array.isArray(result.logs)) {
            result.logs.forEach(l => appendLog(l.message, l.level, l.time));
        }

        progressBar.style.width = "100%";

        if (response.ok && result.success) {
            statusBadge.textContent = "✅ Operação Concluída!";
            statusBadge.style.color = "var(--success)";
            statusBadge.style.backgroundColor = "rgba(16, 185, 129, 0.15)";

            timerBadge.textContent = `⏱️ ${result.elapsed_seconds || 0}s`;
            showToast(result.message || "Alteração realizada com sucesso!", "success");
        } else {
            statusBadge.textContent = "❌ Falha na Operação";
            statusBadge.style.color = "var(--error)";
            statusBadge.style.backgroundColor = "rgba(244, 63, 94, 0.15)";

            timerBadge.textContent = `⏱️ ${result.elapsed_seconds || 0}s`;
            showToast(result.message || "Não foi possível concluir a alteração.", "error");
        }

    } catch (error) {
        progressBar.style.width = "100%";
        statusBadge.textContent = "❌ Erro de Conexão";
        statusBadge.style.color = "var(--error)";

        appendLog(`❌ Erro na requisição AJAX: ${error.message}`, "ERROR");
        showToast("Erro ao conectar com o servidor da API.", "error");
    } finally {
        setTimeout(() => {
            progressContainer.style.display = "none";
            progressBar.style.width = "0%";
        }, 1000);

        btnSubmit.disabled = false;
        btnSubmit.querySelector(".btn-text").textContent = "EXECUTAR ALTERAÇÃO DIRETA (API)";
    }
}
