# ⚡ Clube Altera Dados - WebApp para Servidor AD / Rede Local

Esta pasta (`webapp_servidor/`) contém o pacote **WebApp de Produção** para rodar diretamente no **Servidor da Empresa (Servidor AD / Windows Server)**.

---

## 🌟 Vantagens de Rodar no Servidor AD / Rede Interna:
1. **Zero Bloqueios de IP:** O Servidor AD está na rede interna da loja/empresa e tem acesso direto ao Zanthus e ao CRM Bnex sem nenhuma restrição de nuvem ou firewall externo.
2. **Acesso por Qualquer Computador na Rede:** Os operadores acessam pelo navegador digitando o IP ou nome do Servidor (ex: `http://192.168.1.10:5000` ou `http://servidor-ad:5000`).
3. **Servidor HTTP de Alta Performance (`Waitress`):** Suporta múltiplas requisições simultâneas de vários operadores.
4. **Sem Instalação no PC do Operador:** Nenhuma dependência nos computadores dos funcionários.

---

## 🚀 Como Instalar e Rodar no Servidor AD (Passo a Passo):

### Passo 1: Copiar a pasta `webapp_servidor` para o Servidor AD
Copie esta pasta para qualquer local no Servidor Windows (exemplo: `C:\Servicos\webapp_servidor`).

### Passo 2: Liberar a Porta 5000 no Firewall
Clique com o botão direito no arquivo `configurar_firewall.bat` ➔ **Executar como Administrador**.

### Passo 3: Iniciar o Servidor WebApp
Clique duas vezes no arquivo `iniciar_servidor.bat`.
Ele instalará as dependências (`flask`, `requests`, `waitress`) e iniciará o servidor na porta 5000!

---

## 🌐 Como os Operadores Acessam:

Em qualquer computador da rede interna ou loja, basta abrir o navegador (Chrome/Edge) e digitar:

`http://<IP_DO_SERVIDOR_AD>:5000`

*(Exemplo: `http://192.168.1.100:5000` ou `http://servidor-ad:5000`)*
