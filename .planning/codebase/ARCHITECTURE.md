# Codebase Architecture — Clube Altera Dados

## Overview

Ferramenta desktop interna para operadores da Mini Preço automatizarem troca de senha e email de clientes no CRM (Bnex/Grupo Mini Preço). Interface Tkinter, automação via Playwright headless.

## Componentes

```
CLUBE_modif.py          # App principal — GUI + lógica de automação
updater.py              # Módulo de auto-atualização (GitHub Releases)
gerar_versao.py         # Script de build/release (gera version.txt + .spec)
replace_script.py       # Substituição de arquivos no update (helper do updater)
convert_ico.py          # Converte PNG → ICO para o ícone da janela
preparar_icones.py      # Prepara assets de ícone para build
instalador de bibliotecas.py  # Script auxiliar de instalação de deps
test_fix_direct.py      # Testes manuais pontuais
```

## Fluxo de dados (operação principal)

```
Operador (GUI)
  → preenche: login Zanthus, CPF cliente, nova senha/email
  → clica INICIAR
      → Thread background:
          1. loguin_function_Zanthus() — valida login no portal Zanthus
          2. loguin_function()         — loga no CRM Bnex com conta de serviço
          3. clientes_page()           — busca CPF e clica em editar
          4. alterar_dados()           — preenche novos valores
          5. salva + confirma popup
          6. escrever_arquivo_txt()    — appenda log local (pyhistloc.txt)
          7. salvar_credenciais_json() — persiste senha Zanthus criptografada
```

## Sistemas externos

| Sistema | URL | Uso |
|---------|-----|-----|
| Zanthus | minipreco.zanthus.bluesoft.com.br | Validação de login do operador |
| CRM Bnex | crm.grupominipreco.com.br | Alteração de dados do cliente |
| GitHub API | api.github.com/repos/anjosdevpython/clube_altera_dados | Verificação de updates |

## Stack

| Camada | Tecnologia |
|--------|-----------|
| GUI | Tkinter + ttkbootstrap (tema flatly/darkly) |
| Automação web | Playwright (Chromium headless) |
| Criptografia | Fernet (cryptography) |
| Distribuição | PyInstaller → .exe |
| Auto-update | GitHub Releases + updater.exe separado |

## Segurança

- Credenciais do operador (Zanthus): salvas em `pyhiscred.json` criptografado com Fernet (chave derivada do `COMPUTERNAME`)
- Credenciais da conta de serviço CRM: lidas de `crm_config.json` (externo, gitignored)
- GitHub PAT: lido de `github_token.txt` (externo, gitignored)
- Logs de operações: `pyhistloc.txt` em AppData local

## Estrutura de arquivos em runtime

```
[BASE_DIR]/
  app/
    CLUBE_modif.exe      # Executável principal
    _internal/
      pw-browsers/       # Chromium bundlado pelo Playwright
  updater/
    clube_updater.exe    # Executável do updater
  version.txt            # Versão atual (ex: v1.0.12)
  crm_config.json        # Credenciais CRM (NÃO no git)
  github_token.txt       # PAT GitHub (NÃO no git)

[LOCALAPPDATA]/ClubeAlteraDados/
  logs/pyerrors.log      # Log de erros Python
  data/
    pyhiscred.json       # Senhas Zanthus criptografadas
    pyhistloc.txt        # Histórico de operações
```
