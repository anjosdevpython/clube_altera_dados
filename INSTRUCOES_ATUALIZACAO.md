# 🚀 Guia de Atualização - Clube Altera Dados

Siga este passo a passo sempre que realizar uma melhoria no código e desejar que todos os usuários recebam a nova versão automaticamente.

---

## 1. Preparar a Nova Versão no Código

Antes de compilar, você precisa "subir" o número da versão para que o atualizador saiba que há algo novo.

1.  **No arquivo `CLUBE_modif.py`**: Localize a variável `CURRENT_VERSION` no topo do arquivo e altere (Ex: de `"1.0.1"` para `"1.0.2"`).
2.  **No arquivo `version.txt`**: Altere o texto para a mesma versão (Ex: `1.0.2`).
3.  **Salve os arquivos.**

---

## 2. Compilar o Executável

Abra o Terminal (PowerShell) na pasta do projeto e execute o comando abaixo para gerar a nova pasta `dist`:

```powershell
C:\Python312\python.exe -m PyInstaller --noconfirm --onedir -w --add-data "pw-browsers;pw-browsers" --name "CLUBE_modif" "CLUBE_modif.py"
```

> [!TIP]
> Se você alterou o código do **atualizador** (`updater.py`), também deve recompilá-lo:
> `C:\Python312\python.exe -m PyInstaller --noconfirm --onefile --name "clube_updater" "updater.py"`

---

## 3. Criar o Pacote de Download (ZIP e SHA256)

O sistema de atualização baixa um arquivo `.zip`. Você precisa gerar esse pacote e a "assinatura digital" (SHA256) dele.

No PowerShell, execute estes comandos (ajuste `1.0.2` para a sua versão atual):

```powershell
# 1. Criar o arquivo ZIP (compactando o conteúdo de dist/CLUBE_modif)
Compress-Archive -Path dist\CLUBE_modif\* -DestinationPath CLUBE_modif-1.0.2.zip -Force

# 2. Gerar o arquivo SHA256 (para segurança do download)
$hash = (Get-FileHash CLUBE_modif-1.0.2.zip -Algorithm SHA256).Hash.ToLower()
$hash | Out-File -FilePath CLUBE_modif-1.0.2.zip.sha256 -NoNewline -Encoding utf8

echo "Pronto! Arquivos CLUBE_modif-1.0.2.zip e .sha256 criados."
```

---

## 4. Publicar no GitHub (Lançamento Oficial)

Para que os usuários recebam o aviso de atualização ao abrir o programa:

1.  Acesse o seu repositório no GitHub.
2.  No menu à direita, clique em **Releases** -> **Draft a new release**.
3.  **Choose a tag**: Digite `v1.0.2` (deve começar com 'v').
4.  **Release title**: Digite `v1.0.2 - Melhorias e Correções`.
5.  **Assets**: Arraste os dois arquivos criados no Passo 3 (`.zip` e `.zip.sha256`) para a área de upload.
6.  Clique em **Publish release**.

---

## 5. Gerar Novo Instalador (Opcional)

Se você quiser enviar o arquivo de instalação (`.exe`) para **novos usuários**, gere o instalador atualizado:

1.  Clique com o botão direito no arquivo `installer.iss`.
2.  Selecione **Compile**.
3.  O novo instalador aparecerá na pasta `Output/`.

---

### ⚠️ Lembretes Importantes:
*   **Repositório Público**: Como o repositório agora é público, você não precisa se preocupar com tokens de acesso no código.
*   **Nomes de Arquivo**: Nunca mude o padrão de nomes (`CLUBE_modif-X.X.X.zip`), pois o atualizador foi programado para buscar esse padrão exato.
