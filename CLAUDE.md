# Instruções para Claude

<!-- portable-efficiency:start -->
## Eficiência persistente do agente

- Use o estilo Caveman: responda primeiro, de forma concisa e no idioma do usuário. Preserve fatos técnicos, negações, código, comandos, caminhos, números e erros. Use frases completas quando a clareza exigir. Pedidos de detalhes prevalecem; “stop caveman” desativa o estilo na sessão. Não comprima código nem documentação persistida.
- Se RTK estiver instalado neste executor, use seus comandos compatíveis para reduzir a saída destinada ao contexto, preservando a semântica e as permissões. Exemplo: `rtk git status`. Não duplique uma transformação já feita por hook. Ferramentas não suportadas continuam nativas; recupere a saída original quando o resumo não bastar. Não declare filtragem automática sem verificar o hook e a ferramenta realmente usados.
- Preserve o modelo escolhido no aplicativo, inclusive Auto quando já configurado. Preserve a integração existente de Headroom, Caveman e recuperação MCP. Estas instruções não instalam serviços nem ativam roteamento de modelos.
- Cada executor local, Cloud, SSH ou CI precisa de instalação e validação próprias. Nunca reutilize caminhos Windows ou o localhost de outro host. Não substitua o provedor nativo, exponha proxies loopback publicamente, copie credenciais para o repositório ou adicione hooks de ciclo de vida sem pedido explícito.
- Sem autorização para gasto adicional, valide com inspeção e testes locais/sintéticos; não faça chamadas reais de benchmark a modelos nem inicie tarefas de agentes remotos. Separe sempre: instrução versionada, ferramenta instalada, integração ativa e economia medida.
<!-- portable-efficiency:end -->
