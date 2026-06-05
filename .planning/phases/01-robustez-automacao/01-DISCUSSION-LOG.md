# Phase 1: Robustez da Automação - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2025-06-05
**Phase:** 1-Robustez-Automação
**Areas discussed:** Screenshot de falha, Retry: escopo e lógica, Linguagem das mensagens, Seletores com fallback

---

## Screenshot de Falha

### Onde salvar

| Option | Description | Selected |
|--------|-------------|----------|
| AppData local | %LOCALAPPDATA%\ClubeAlteraDados\screenshots\ — sem admin | ✓ |
| Pasta do exe | Ao lado do .exe — mais fácil de achar, mas permissões | |

**Escolha:** AppData local

---

### Como o operador acessa

| Option | Description | Selected |
|--------|-------------|----------|
| Botão na UI de erro | "Abrir pasta de screenshots" junto com a mensagem | ✓ |
| Caminho na mensagem | Caminho completo do arquivo na mensagem de erro | |
| Claude decide | | |

**Escolha:** Botão na UI

---

### Limpeza

| Option | Description | Selected |
|--------|-------------|----------|
| Manter sempre | Nunca apaga — supervisor pode precisar | ✓ |
| N dias automático | Purge automático | |
| Junto com botão Limpar | Apaga com o log da UI | |

**Escolha:** Manter sempre

---

### Captura

| Option | Description | Selected |
|--------|-------------|----------|
| Página toda | full_page=True — captura tudo | ✓ |
| Apenas visível | Padrão Playwright — mais leve | |

**Escolha:** Página toda (full_page=True)

---

## Retry: Escopo e Lógica

### Comportamento do retry

| Option | Description | Selected |
|--------|-------------|----------|
| Recomeçar do início | Zanthus → CRM → CPF — mais simples | ✓ |
| Retomar de onde parou | Mais complexo, risco de duplicar ação | |

**Escolha:** Recomeçar do início

---

### Tipos de erro para retry

| Option | Description | Selected |
|--------|-------------|----------|
| Timeout de elemento | wait_for_selector excedeu — lentidão | ✓ |
| Erro de rede / navegação | page.goto falhou — conexão instável | ✓ |
| CPF não encontrado | #btnEditar nunca apareceu | Selecionado mas revertido |

**Escolha:** Timeout e erros de rede; CPF não encontrado = permanente (veja próxima questão)

---

### CPF não encontrado

| Option | Description | Selected |
|--------|-------------|----------|
| Permanente, sem retry | Provavelmente CPF errado | ✓ |
| Retry 1x | Pode ser lentidão do CRM | |

**Escolha:** Permanente — operador precisa corrigir o CPF
**Nota:** Conflito resolvido: usuário marcou CPF como retry e depois como permanente; escolha mais recente prevalece.

---

### Backoff

| Option | Description | Selected |
|--------|-------------|----------|
| 2s fixo | Simples: 2s entre tentativas | ✓ |
| Exponencial | 2s → 4s → 8s — mais respeitoso | |

**Escolha:** 2 segundos fixos, até 3 tentativas

---

## Linguagem das Mensagens

### Destinatário

| Option | Description | Selected |
|--------|-------------|----------|
| Operador de atendimento | Linguagem simples, ação clara | ✓ |
| Supervisor / TI | Linguagem técnica | |
| Ambos separados | UI simples + log técnico | |

**Escolha:** Operador — linguagem simples

---

### Traceback na UI

| Option | Description | Selected |
|--------|-------------|----------|
| Não — apenas no log | UI humanizada; pyerrors.log guarda stack trace | ✓ |
| Sim, colapsável | Mensagem + botão "Ver detalhes técnicos" | |

**Escolha:** Traceback só no log

---

### Classificação por tipo

| Option | Description | Selected |
|--------|-------------|----------|
| Tipo de exceção Playwright | TimeoutError / NavigationError / LocatorError | ✓ |
| Etapa onde falhou | loguin_function → "Falha no login" | |
| Combinar etapa + tipo | "Timeout na busca do CPF" | |

**Escolha:** Tipo de exceção Playwright

---

### Mensagem de sucesso

| Option | Description | Selected |
|--------|-------------|----------|
| Resumo simples | "Senha alterada com sucesso para CPF X" | ✓ |
| Apenas ✅ Sucesso | Minimalista | |
| Claude decide | | |

**Escolha:** Resumo com CPF — confirma o que foi feito

---

## Seletores com Fallback

### Como definir

| Option | Description | Selected |
|--------|-------------|----------|
| Hard-coded no código | Dicionário Python SELECTORS | ✓ |
| JSON de config | selectors.json ao lado do exe | |
| Defaults + override JSON | Código + override externo | |

**Escolha:** Hard-coded — fácil de ver e manter

---

### Quando todos falham

| Option | Description | Selected |
|--------|-------------|----------|
| Screenshot + erro descritivo | "Informe o TI" | ✓ |
| Screenshot + XPath genérico | Tentar //button[contains()] como último recurso | |

**Escolha:** Screenshot + erro descritivo, sem XPath genérico

---

### Manutenção

| Option | Description | Selected |
|--------|-------------|----------|
| Desenvolvedor via nova versão | GitHub Releases | ✓ |
| TI via JSON | TI edita sem recompilação | |

**Escolha:** Desenvolvedor — fluxo de release já existe

---

### Quantidade de alternativos

| Option | Description | Selected |
|--------|-------------|----------|
| 2 alternativos | Principal + 2 fallbacks | ✓ |
| 1 alternativo | Principal + 1 | |
| Todos os tipos | ID → name → text → role | |

**Escolha:** 2 alternativos por elemento

---

## Claude's Discretion

- Estratégia de tentativa dos seletores: try/except sequencial (primário → fallback 1 → fallback 2), não `page.locator().or_()` — facilita diagnóstico de qual funcionou

## Deferred Ideas

- UX progresso por etapa → Fase 2
- Botão "Tentar novamente" → Fase 2
- Log centralizado → Fase 3
- Operação em lote CSV → v2
- Seletores em JSON externo → v2
