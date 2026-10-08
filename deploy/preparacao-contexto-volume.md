# Preparação da publicação de contexto e volume

Conferência realizada em 08/10/2026. Esta etapa prepara a release sem substituir os serviços ativos.

## Release pronta

- Código: `ef0731d`, branch `codex/contexto`.
- Imagem candidata: `v8-ranking:context-ef0731d`.
- Assinatura da imagem: `sha256:384fec441861e79472f3f6df77329d1bd355fa5c260e28ef9e5cbad63e008488`.
- Diretório da release na VPS: `/home/lucas/projects/v8-ranking-releases/ef0731d`.
- Pacote `ef0731d.tar`: SHA-256 `69cc11d337d3fc2dc0864abd124769a85d7082599f8e44021c74027aeefc62d2`, igual no computador e na VPS.
- Compose candidato e cópia do Compose ativo: `/home/lucas/backups/v8-ranking/20261008-prepared-ef0731d/`, em diretório privado.

O Compose candidato troca somente as duas referências de imagem. Preserva o volume, o proxy e a configuração do worker. As credenciais permanecem no arquivo privado existente; não foram copiadas para o pacote ou a imagem.

## Conferências realizadas

- Suíte completa: 136 testes, nenhuma falha e um teste opcional ignorado. Os testes cobrem envio, fila, worker, falhas, arquivos, isolamento entre execuções, contexto e volume.
- Ruff, assinaturas dos artefatos históricos, formatação, checagem do frontend e diferenças Git aprovados.
- Navegador local: formulário de envio, resultado independente, troca de janela, seleção de WEGE3, gráfico/contexto, lacunas diárias, volume, auditoria e navegação móvel. Resultado e auditoria não excederam a largura móvel; console sem avisos ou erros.
- O resultado usado nesta conferência é o cenário artificial previamente concluído, identificado como validação local. Não foi criado outro envio real nem repetida a coleta de contexto.
- Oito derivados da execução responderam 200, incluindo os dois rankings, volume e os quatro arquivos de contexto. Os JSONs foram lidos. Tentativas de baixar o original ou uma evidência privada responderam 404.
- Os arquivos públicos do case `top20.csv` e `ranking_report.json` permaneceram idênticos aos versionados.
- Imagem candidata: imports da aplicação e worker, artefatos históricos e 17 rotas HTTP aprovados, incluindo os oito guias e os cinco prints novos. O teste usou contêiner temporário sem rede externa, sem volumes de produção e sem credenciais.

A primeira espera de cinco segundos pelo servidor temporário foi insuficiente. Com espera limitada a vinte segundos e logs de inicialização, o servidor iniciou e todas as rotas passaram. Não foi necessário alterar o código da aplicação.

## Limite visual ainda registrado

A ampliação abre dentro da plataforma, a imagem carrega, cabe na largura móvel, amplia para 1,5×, ajusta à tela e fecha retornando à leitura. Esses estados foram conferidos pelos controles e pelas dimensões do DOM.

A captura do navegador da página longa permanece defeituosa: retorna preto ou duplica partes do conteúdo. Não foi possível encerrar a inspeção visual do modal no celular. Essa limitação não foi tratada como uma captura válida nem usada para substituir os prints legíveis do case. Uma conferência humana do modal no celular continua recomendada antes da entrega.

## Preservação

Os serviços ativos continuam em `v8-ranking:context-796c948`: app saudável e worker em execução. A imagem standby `v8-ranking:standby-20261008` conserva a assinatura `sha256:5d547e66ac8a73ea8674a0f7cb0b7e9c8f9a3bfba97054a3223ff6b9c6b1ad95`. O arquivo de restauração anterior também foi conferido.

O `rollback.yaml` da preparação restaura a versão atualmente publicada com contexto. O retorno à versão original standby usa o arquivo descrito em [Publicação do contexto](contexto-publicado.md). São duas opções distintas de restauração.

## Próxima etapa: substituir a imagem e conferir o site

Os comandos abaixo estão preparados, mas **não foram executados nesta etapa**. Antes de substituir, confira a fila e espere uma execução ativa terminar. Preserve uma cópia atualizada do Compose se ele tiver mudado após esta preparação.

```bash
cp /home/lucas/backups/v8-ranking/20261008-prepared-ef0731d/candidate.yaml /opt/stacks/v8-ranking/compose.yaml
docker compose --env-file /opt/stacks/v8-ranking/context.env -f /opt/stacks/v8-ranking/compose.yaml config --quiet
docker compose --env-file /opt/stacks/v8-ranking/context.env -f /opt/stacks/v8-ranking/compose.yaml up -d --no-build --wait --wait-timeout 90
curl -fsS https://ranking.lucaspsm.com/healthz
```

Depois, confira no endereço público os guias, imagens, ranking, volume, contexto e downloads. A conferência HTTP da candidata não substitui essa conferência visual pública.

Para restaurar a versão que estava ativa durante esta preparação:

```bash
cp /home/lucas/backups/v8-ranking/20261008-prepared-ef0731d/rollback.yaml /opt/stacks/v8-ranking/compose.yaml
docker compose --env-file /opt/stacks/v8-ranking/context.env -f /opt/stacks/v8-ranking/compose.yaml up -d --no-build --wait --wait-timeout 90
curl -fsS https://ranking.lucaspsm.com/healthz
```

Nenhum volume deve ser apagado. Não houve novas chamadas de IA ou Tavily, push ou troca da versão pública nesta etapa.
