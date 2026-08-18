# ⚡ Clube Altera Dados - WebApp Vercel Engine

Esta pasta (`webapp/`) contém a versão completa do **WebApp** para automação de alteração de dados do Clube de Vantagens em alta velocidade, pronta para deploy no **Vercel**.

---

## 🌟 Vantagens desta versão WebApp:
* **Zero Instalação nos PCs dos Operadores:** Basta acessar pelo navegador (Chrome, Edge, Safari, Mobile).
* **Vercel Serverless Architecture:** Executa as requisições em alta velocidade (~2 segundos por alteração).
* **Sem Erros de Permissão / UAC:** Não utiliza arquivos locais nem precisa de privilégios de Administrador.
* **Atualizações Instantâneas:** Qualquer alteração no repositório reflete automaticamente para todos os usuários ao dar F5.

---

## 🚀 Como fazer o Deploy no Vercel (Passo a Passo)

### Opção 1: Deploy via Interface Web da Vercel (Mais Fácil)

1. Acesse o painel da Vercel: [https://vercel.com/dashboard](https://vercel.com/dashboard)
2. Clique em **"Add New..."** ➔ **"Project"**.
3. Importe o seu repositório do GitHub (`anjosdevpython/clube_altera_dados`).
4. Em **Root Directory**, selecione a subpasta: `webapp`
5. *(Opcional)* Em **Environment Variables**, adicione as credenciais padrão se desejar:
   * `CRM_USUARIO`: `GUSTAVO.ALVES`
   * `CRM_SENHA`: `Cwb123@`
6. Clique em **Deploy**!
7. Em cerca de 30 segundos, a Vercel gerará o seu link oficial (ex: `https://clube-altera-dados.vercel.app`).

---

### Opção 2: Deploy via Terminal (Vercel CLI)

Se você utiliza o Vercel CLI instalado na sua máquina:

```bash
cd "c:\Users\allan.anjos\Downloads\CLUBECLUBE MUDA SENHA E EMAIL\webapp"
vercel --prod
```

---

## 💻 Teste Local (Sem Vercel)

Se você quiser testar o WebApp localmente no seu computador antes de enviar para a Vercel:

1. Abra o PowerShell na pasta `webapp`:
```powershell
cd "c:\Users\allan.anjos\Downloads\CLUBECLUBE MUDA SENHA E EMAIL\webapp"
```

2. Instale as dependências:
```powershell
pip install -r requirements.txt
```

3. Execute o servidor Flask:
```powershell
python api/index.py
```

4. Acesse no seu navegador: `http://localhost:5000`
