# Manual do Usuário: Clube Altera Dados

Bem-vindo(a) ao **Clube Altera Dados**! Este manual foi criado para ajudar você a utilizar a ferramenta de form rápida, prática e sem erros.

A interface do nosso sistema foi totalmente renovada para ser mais simples e os processos para alterar os dados dos clientes agora funcionam nos bastidores, sem travar o seu computador, enquanto você acompanha o que está acontecendo!

---

## 1. Conhecendo a Interface

O programa é dividido em três áreas principais:
1. **Validação Zanthus:** Onde você identifica quem está realizando a operação.
2. **Dados do Cliente:** Onde você informa de quem são os dados que irão mudar e qual será o novo valor.
3. **Status do Processo:** Um pequeno painel ("Log") onde o robô te avisa se a tarefa deu certo ou se teve algum problema, em tempo real.

\* *No topo, do lado direito, você encontrará o botão "🌙 Escuro" / "☀️ Claro" para alternar as cores da tela conforme achar mais confortável para seus olhos.*

---

## 2. Como Alterar a Senha ou Email de um Cliente

Siga os passos abaixo, na ordem em que aparecem na tela:

### Passo 1: Acesse com suas Credenciais
Na área **🔑 VALIDAÇÃO ZANTHUS**:
* **Código Funcionário:** Digite seu código de operador/funcionário usado no sistema Zanthus.
* **Senha de Acesso:** Informe sua senha do Zanthus. *(O sistema lembrará sua senha se for o mesmo que usou da última vez na máquina, agilizando o processo).*

### Passo 2: O que você quer alterar?
Na área **👤 DADOS DO CLIENTE**, o primeiro passo é **clicar** em um dos 3 grandes botões vermelhos:
* `SENHA`: O robô mudará apenas a senha do cliente.
* `EMAIL`: O robô mudará apenas o email do cliente.
* `AMBOS`: O robô mudará os dois dados ao mesmo tempo.

### Passo 3: Preencha os Dados do Cliente
Após selecionar e confirmar o que será editado, os campos abrirão para preenchimento:
* **CPF DO CLIENTE:** Digite **apenas números** (sem pontos ou traços). O sistema exige exatamente 11 dígitos.
* **NOVA SENHA:** Preencha aqui a nova senha, que deverá conter **apenas números** e ter **no mínimo 4 dígitos**. (Deixe em branco se selecionou editar apenas o `EMAIL`).
* **NOVO EMAIL:** Preencha o novo email do cliente (precisa conter o `@` e um domínio válido, como `.com` ou `.com.br`). (Deixe em branco se selecionou editar apenas a `SENHA`).

### Passo 4: Deixe o Robô Trabalhar!
* Confirme se todos os dados acima foram digitados corretamente.
* Clique no botão **🚀 INICIAR AUTOMAÇÃO**.
* **Pronto!** Uma barra de carregamento vermelha surgirá animada e você não precisará fazer mais nada. O robô vai abrir o navegador por trás das cortinas, acessar o CRM e modificar os dados do cliente por você.

---

## 3. Acompanhando o Status e Relatórios

Na parte de baixo do aplicativo (**📋 STATUS DO PROCESSO**), você acompanha literalmente tudo que está acontecendo durante as etapas.

Lá aparecerão mensagens guiadas:
* 🔹 **Azul:** O robô está carregando sites ou conectando-se ao sistema.
* ✅ **Verde:** Sucesso! O cliente teve sua edição cadastrada e salva na nuvem.
* ❌ **Vermelho:** Erro. Algo aconteceu (CPF não existe, senha inválida, ou você não tem permissão para editar aquele cliente).

### Exportando Relatórios
Se você precisa enviar um comprovante ou histórico para sua supervisão sobre quantas alterações você realizou no dia:
1. Clique no botão cinza **💾 Exportar Relatório**.
2. O próprio sistema vai gerar e salvar um arquivo Bloco de Notas (TXT) bonito na sua máquina, com o histórico listado com data, hora, CPF processado e o seu login, perfeito para auditoria.

### Fim de Expediente
Você pode clicar em **🗑️ Limpar** para apagar o histórico de status da sua tela atual, zerando o painel para iniciar um novo dia ou atendimento. 

---

> **Dicas Importantes:**
> * Nunca feche a janela preta que acompanha o programa no fundo (ela é o cérebro que comanda o Robô Playwright).
> * Se ao tentar abrir o programa você recebia mensagens estranhas antes de erros, pode esquecer! Nesta versão 1.0.11 o aplicativo criará as pastas corretas independente de você ser Administrador ou não no Windows.
