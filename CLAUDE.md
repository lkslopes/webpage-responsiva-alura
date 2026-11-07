# Instruções para Claude

<!-- portable-efficiency:start -->
## Eficiência obrigatória em cada sessão

- Antes de trabalhar, execute `python3 tools/agent-efficiency/ensure.py` na raiz do checkout (`python` no Windows). O modo padrão instala RTK, Headroom e Caveman quando ausentes e verifica os executáveis. Não substitua por “usar se instalado” nem por `--check`. Corrija pré-requisitos ausentes com instaladores oficiais permitidos pelo executor. Em caso de bloqueio real de acesso, rede ou plataforma, registre o erro e o que falta; não declare o ambiente padronizado.
- Use RTK nos comandos suportados, preservando semântica e permissões. Quando o PATH ainda não reconhecer a instalação, use `python3 tools/agent-efficiency/ensure.py --exec rtk <comando>` ou o caminho retornado. Não duplique o filtro de um hook ativo; recupere a saída original quando necessário.
- Após instalar, configure e valide Headroom e Caveman Auto/compressão com recuperação MCP no próprio executor, quando o host permitir integração ao transporte. Preserve integrações existentes, autenticação e modelo escolhido, inclusive Auto. Instalação, integração ativa e economia medida são estados diferentes; não conclua a configuração só porque o binário existe. Procedimento e limitações: `tools/agent-efficiency/README.md`.
- Use o estilo Caveman: responda primeiro, de forma concisa e no idioma do usuário. Preserve fatos técnicos, negações, código, comandos, caminhos, números e erros. Pedidos de detalhes prevalecem; “stop caveman” desativa o estilo. Não comprima código nem documentação persistida.
- Cada executor local, Cloud, SSH ou CI precisa da própria instalação. Nunca reutilize o localhost de outro host, exponha proxies publicamente ou copie credenciais para Git. Preserve o provedor nativo; não execute `caveman enable` nem `doctor --fix` sobre a integração compatível do desktop. Não adicione hooks de ciclo de vida sem pedido explícito.
- Sem autorização para gasto adicional, use inspeção e testes sintéticos; não inicie benchmarks de modelos ou agentes remotos. Chats sem shell e hosts que bloqueiam o transporte não se tornam compatíveis por estas instruções. Sessões existentes precisam atualizar o checkout e recarregar as instruções.
<!-- portable-efficiency:end -->
