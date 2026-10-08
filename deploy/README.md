# Operação da interface na VPS

## Configuração da versão com contexto

Esta versão foi validada localmente; este registro não declara uma publicação na VPS. O Compose transmite `OPENAI_API_KEY`, `TAVILY_API_KEY` e `CONTEXT_ENABLED` somente ao worker. Configure as chaves no ambiente que inicia o Compose ou em um arquivo privado fornecido com `--env-file /caminho/arquivo.env`. Não inclua esse arquivo no checkout, na imagem ou em logs. Confira a configuração sem exibir os valores das chaves.

Com `CONTEXT_ENABLED=0`, ou sem as duas credenciais, o ranking continua funcionando. O worker libera o resultado financeiro antes de coletar o contexto, dentro do mesmo prazo total de dez minutos. A API oferece `GET /api/analyses/{id}/context`; quatro derivados públicos aparecem na auditoria. `context/private/` não é servido pelas rotas de download e acompanha a remoção da execução após sete dias.

Veja [o registro de validação](contexto-replicavel.md) e [os comandos de reprodução](../docs/desenvolvimento.md).

## Operação do ranking

O `compose.yaml` publica apenas o contêiner `app` na rede externa `proxy` do Traefik existente. Nenhuma porta nova é exposta no host. O contêiner `worker` compartilha o volume `ranking_data` com a aplicação e acessa a internet para obter referências datadas da B3. O resultado fixo está na imagem; envios e cache B3 ficam no volume, fora do Git.

Na VPS, mantenha o checkout em `/home/lucas/projects/v8-ranking-semanal` e a stack em `/opt/stacks/v8-ranking/compose.yaml`. Antes de subir, confira `docker compose -f /opt/stacks/v8-ranking/compose.yaml config`. Depois:

```bash
docker compose -f /opt/stacks/v8-ranking/compose.yaml up -d --build
docker compose -f /opt/stacks/v8-ranking/compose.yaml ps
curl -fsS https://ranking.lucaspsm.com/healthz
```

O Traefik usa o resolvedor Let's Encrypt já configurado na VPS para `ranking.lucaspsm.com`. O DNS deste subdomínio aponta para a VPS. A imagem instala as dependências Python fixadas em `requirements-web.txt`. `app` e `worker` têm limites de memória e logs limitados. O worker aceita um job por vez; a API recusa a quarta análise simultânea. O processo encerra uma análise após dez minutos.

O banco SQLite em `/data/jobs.sqlite3` guarda a fila. `/data/uploads` contém CSVs temporários, `/data/runs` as saídas isoladas, `/data/reference` o cache datado da B3 e `/data/logs` os registros de execução. O worker remove arquivos brutos após 24 horas, resultados após sete dias e metadados após 30 dias. Para atualizar, faça pull do commit revisado e execute `docker compose ... up -d --build`; o volume não é apagado. Para voltar à imagem anterior, use o commit anterior e repita o build. **Não use `down -v`**, pois isso apagaria o volume.

Endpoints: `GET /api/featured`, `POST /api/analyses` (multipart `file` + `reference_date`), `GET /api/analyses/{id}`, `GET /api/analyses/{id}/result` e rotas `files` com lista permitida de resultados derivados. O identificador da análise é aleatório; não existe endpoint para listar envios. Uma falha de esquema, data, fonte B3 ou classificação deixa a análise em `failed` com mensagem visível, sem resultado parcial anunciado como válido.
