# Instalação obrigatória por executor

Antes de trabalhar em cada sessão com shell, execute na raiz do checkout:

```sh
python3 tools/agent-efficiency/ensure.py
```

No Windows, use `python` no lugar de `python3`. O modo padrão instala ferramentas ausentes; `--check` é somente diagnóstico e não substitui a instalação. Instalações utilizáveis existentes são preservadas, sem atualização forçada. Executores diferentes têm instalações independentes.

O bootstrap instala RTK 0.49.0 a partir do release oficial, conferindo SHA256 fixado; Headroom `headroom-ai[proxy,mcp]==0.42.0` em venv privado; e `@caveman-ai/cli@4.0.1` em prefixo npm privado. Quando faltarem os binários auxiliares Caveman, usa `setup --install --json`, que verifica o bundle assinado. Não executa `enable` nem altera o provedor do aplicativo.

Requer Python 3.10+ com venv/pip e, quando for necessário instalar Caveman, Node.js 22.13+ e npm. A ausência de pré-requisito, permissão, rede ou arquitetura suportada deve ser corrigida no executor com as ferramentas oficiais disponíveis. Não trate bloqueio como instalação concluída. Não ignore políticas do host nem instale na planta industrial.

O relatório local fica em `~/.agent-efficiency/last-status.json`. Um lock impede instalações concorrentes. Se uma instalação for interrompida, confira se o PID do lock ainda está ativo antes de remover um lock órfão. Não apague o lock de outra sessão em execução.

Como o processo filho não altera o PATH da sessão pai, use o caminho absoluto retornado ou o comando abaixo. Ele encontra os executáveis gerenciados sem depender de reiniciar o shell:

```sh
python3 tools/agent-efficiency/ensure.py --exec rtk git status
```

Use RTK nos comandos compatíveis, preservando permissões e semântica; recupere a saída original quando necessária. Não aplique o filtro duas vezes se o hook nativo já o fizer. O wrapper também resolve `headroom` e `caveman`.

## Instalação não equivale a integração

Depois de instalar, configure e valide Headroom, Caveman Auto/compressão e MCP de recuperação no próprio executor, quando o host permitir controlar o transporte do cliente. Preserve integrações existentes, modelos escolhidos e autenticação nativa. Use loopback, cache sem perdas no Headroom e a recuperação correspondente à compressão. Não substitua o provedor `openai` por `caveman`. Não execute `caveman enable` ou `doctor --fix` sobre a integração compatível do desktop.

Este bootstrap instala e verifica os executáveis. Ele não declara que um proxy esteja na rota das chamadas, não inicia agentes/modelos, não configura hooks de ciclo de vida e não modifica credenciais. O campo `integration: not_verified` é deliberado: a integração exige validação específica do host, separada da instalação.

No Cloud gerenciado, a disponibilidade de binários dentro do container não garante acesso ao transporte de inferência do agente. Se o produto impedir a integração, registre o impedimento e mantenha as otimizações suportadas. Chats web/mobile sem shell não executam instaladores. A instalação do PC não é herdada por eles.

Para persistir em um ambiente Cloud reutilizável, adicione o comando de instalação ao setup permitido pelo produto e publique a configuração autenticada. As instruções AGENTS.md/CLAUDE.md mandam o agente executar o bootstrap a cada sessão; não são um hook executado pelo sistema operacional. Sessões existentes precisam atualizar o checkout e reler as instruções.

## Validação sem inferência

```sh
python3 -m unittest discover -s tools/agent-efficiency -p test_ensure.py
python3 tools/agent-efficiency/ensure.py --check
```

Testes simulam ferramentas ausentes, reexecução, falhas, integridade do download, extração segura, instalação de companions e concorrência. Não fazem downloads nem chamadas a modelos. O código não mede economia de tokens. Nenhuma validação automatizada implica aceite industrial.
