# Operação da interface na VPS

A revisão visual mais recente está registrada em [Revisão de UI de 08/10/2026](revisao-ui-20261008.md), incluindo a imagem publicada, as verificações e a restauração da versão anterior.

## Configuração da versão com contexto

O Compose transmite `OPENAI_API_KEY`, `TAVILY_API_KEY` e `CONTEXT_ENABLED` somente ao worker. Na VPS, o arquivo privado fica em `/opt/stacks/v8-ranking/context.env`, com permissão 600. Forneça `--env-file` em toda chamada que recrie os serviços. Não inclua esse arquivo no checkout, na imagem ou em logs. Confira a configuração com `config --quiet`, sem exibir os valores das chaves. Consulte o [registro da publicação](contexto-publicado.md) para a versão e a validação observadas.

Com `CONTEXT_ENABLED=0`, ou sem as duas credenciais, o ranking continua funcionando. O worker libera o resultado financeiro antes de coletar o contexto, dentro do mesmo prazo total de dez minutos. A API oferece `GET /api/analyses/{id}/context`; quatro derivados públicos aparecem na auditoria. `context/private/` não é servido pelas rotas de download e acompanha a remoção da execução após sete dias.

Veja [o registro de validação](contexto-replicavel.md) e [os comandos de reprodução](../docs/desenvolvimento.md).

## Operação do ranking

O `compose.yaml` publica apenas o contêiner `app` na rede externa `proxy` do Traefik existente. Nenhuma porta nova é exposta no host. O contêiner `worker` compartilha o volume `ranking_data` com a aplicação e acessa a internet para obter referências datadas da B3. O resultado fixo está na imagem; envios e cache B3 ficam no volume, fora do Git.

Na VPS, a stack fica em `/opt/stacks/v8-ranking/compose.yaml`. O código revisado é extraído em um diretório próprio de release, e a imagem recebe uma tag com o commit. Antes de construir a imagem, normalize as permissões do diretório da release para leitura pelo usuário da aplicação; um `git archive` extraído sob `umask 077` impede essa leitura. Não aplique essa normalização ao arquivo de chaves ou aos backups. Confira os imports com a própria imagem antes de substituir os serviços. Depois:

```bash
docker compose --env-file /opt/stacks/v8-ranking/context.env -f /opt/stacks/v8-ranking/compose.yaml config --quiet
docker compose --env-file /opt/stacks/v8-ranking/context.env -f /opt/stacks/v8-ranking/compose.yaml up -d --no-build --wait --wait-timeout 90
docker compose -f /opt/stacks/v8-ranking/compose.yaml ps
curl -fsS https://ranking.lucaspsm.com/healthz
```

O Traefik usa o resolvedor Let's Encrypt já configurado na VPS para `ranking.lucaspsm.com`. O DNS deste subdomínio aponta para a VPS. A imagem instala as dependências Python fixadas em `requirements-web.txt`. `app` e `worker` têm limites de memória e logs limitados. O worker aceita um job por vez; a API recusa a quarta análise simultânea. O processo encerra uma análise após dez minutos.

O banco SQLite em `/data/jobs.sqlite3` guarda a fila. `/data/uploads` contém CSVs temporários, `/data/runs` as saídas isoladas, `/data/reference` o cache datado da B3 e `/data/logs` os registros de execução. O worker remove arquivos brutos após 24 horas, resultados após sete dias e metadados após 30 dias. Para atualizar, construa e confira uma nova imagem, preserve a imagem anterior e substitua a tag na stack; o volume não é apagado. A restauração usa a imagem e o Compose preservados, conforme o registro da publicação. **Não use `down -v`**, pois isso apagaria o volume.

Endpoints: `GET /api/featured`, `POST /api/analyses` (multipart `file` + `reference_date`), `GET /api/analyses/{id}`, `GET /api/analyses/{id}/result` e rotas `files` com lista permitida de resultados derivados. O identificador da análise é aleatório; não existe endpoint para listar envios. Uma falha de esquema, data, fonte B3 ou classificação deixa a análise em `failed` com mensagem visível, sem resultado parcial anunciado como válido.
