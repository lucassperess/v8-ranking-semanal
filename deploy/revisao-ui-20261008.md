# Revisão visual publicada em 08/10/2026

Código publicado: `91bfa5e`. Imagem: `v8-ranking:context-91bfa5e`.
Identificação da imagem: `sha256:e1dcb489f7b95b90c38b52177b83d806f877dd02c2ce0ae79c4f9872f8483a5e`.

O contexto geral e os acontecimentos da semana passaram para antes do ranking. A explicação dos indicadores fica no botão de informação. Foram removidos o bloco “Contexto de negociação” e a frase adicional da PTAX. O link de volume usa azul; a tabela de volumes usa uma escala azul logarítmica comum às ações e datas exibidas, com zero neutro e ausência marcada por traço. Os guias e dois prints foram atualizados.

Verificação: 18 testes da aplicação passaram; frontend, formatação, Ruff e assinaturas dos resultados conferidos. A revisão foi inspecionada em desktop e em largura móvel de 390 pixels. Antes da troca, 17 rotas da imagem candidata foram verificadas sem rede externa. Após a publicação, 27 verificações públicas passaram: prints e quatro arquivos do case coincidem com o repositório, a execução anterior continua disponível e downloads privados permanecem bloqueados. Não houve novas chamadas às APIs de contexto.

O volume de dados foi preservado. O banco foi copiado com backup consistente do SQLite e verificação de integridade. O Compose anterior e o banco estão em `/home/lucas/backups/v8-ranking/20261008-ui-91bfa5e`. A imagem standby `v8-ranking:standby-20261008` mantém a identificação registrada na entrega anterior.

## Restaurar a versão anterior desta revisão

Na VPS, depois de conferir que não há processamento ativo:

```bash
cp /home/lucas/backups/v8-ranking/20261008-ui-91bfa5e/rollback.yaml /opt/stacks/v8-ranking/compose.yaml
docker compose --env-file /opt/stacks/v8-ranking/context.env -f /opt/stacks/v8-ranking/compose.yaml up -d --no-build --wait --wait-timeout 90
curl -fsS https://ranking.lucaspsm.com/healthz
```

Essa restauração retorna à imagem `context-ef0731d` e conserva os envios no volume. Para o standby anterior à camada de contexto, consulte os comandos da entrega original. Não restaure o banco sobre envios recentes nem remova o volume.
