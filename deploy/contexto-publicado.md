# Publicação da versão com contexto

## Versão e operação

Publicação realizada em 08/10/2026 em `https://ranking.lucaspsm.com/`.
Código da imagem: `796c948`, tag `v8-ranking:context-796c948`, assinatura
`sha256:42a6864f767bd051264b99cd8b99398879003718592e16b282cdcc03a62ac1f4`.
O código está em `/home/lucas/projects/v8-ranking-releases/796c948` na VPS.
Os serviços continuam usando o volume `v8-ranking_ranking_data` e o Traefik existente.

O arquivo privado `/opt/stacks/v8-ranking/context.env`, com permissão 600,
transmite as credenciais OpenAI e Tavily somente ao worker. A presença das
credenciais foi conferida no worker e sua ausência no app, sem imprimir valores.

## Ocorrências e correções

A primeira imagem não iniciou porque a extração do pacote sob `umask 077`
deixou arquivos inacessíveis ao usuário da aplicação. A versão anterior foi
restaurada; as permissões do diretório da release foram normalizadas e os
imports da aplicação e do worker passaram antes da nova substituição.

O primeiro envio público, `bf3aa71aa7754edba26a81f68d3d2c37`, reproduziu
o ranking do case, mas a coleta de contexto atingiu o prazo total de dez minutos.
A leitura financeira carregava BPP, que não era utilizado, e mantinha registros
de todas as empresas em memória. O commit `796c948` lê DRE em fluxo e mantém
somente os registros das empresas consultadas. As regras de escolha de período,
versão, moeda, escala e contas foram preservadas.

Verificação da correção: 97 testes, um ignorado, sem falhas; Ruff e `git diff --check`
passaram. Na base local de validação, a leitura financeira levou 2,84 segundos e
reproduziu as contas das 19 empresas com antecedentes financeiros salvos, sem
consultar APIs novamente.

## Preservação e restauração

Imagem anterior preservada: `v8-ranking:standby-20261008`.
Backup privado: `/home/lucas/backups/v8-ranking/20261008-contexto`.
Contém o Compose anterior, uma cópia consistente de SQLite e `ranking-data.tar.gz`.
O arquivo compactado foi conferido com `gzip -t`. A cópia dos arquivos exclui os
arquivos transitórios `jobs.sqlite3*`; o banco consistente está em `jobs.sqlite3`.

Para restaurar apenas o código e a configuração anteriores, preservando os dados:

```bash
cp /home/lucas/backups/v8-ranking/20261008-contexto/rollback.yaml /opt/stacks/v8-ranking/compose.yaml
docker compose -f /opt/stacks/v8-ranking/compose.yaml up -d --no-build --wait --wait-timeout 90
curl -fsS https://ranking.lucaspsm.com/healthz
```

Não apague o volume. A restauração dos dados por backup só é necessária em caso
de perda ou corrupção deles; não faz parte da troca normal de versão.

## Verificação pública

Os arquivos fixos `top20.csv` e `ranking_report.json` permaneceram idênticos aos
versionados. O primeiro envio produziu janelas e datas idênticas ao case:
17,78% de média principal, 15,93% na alternativa e 308 ações elegíveis.

O navegador confirmou gráfico/contexto, seleção de ações e atualização das datas
e retornos ao trocar a janela. Não houve erros no console. Em largura de 390 px,
a página não apresentou transbordamento horizontal. O CSV do ranking respondeu
200; tentativas de baixar o CSV original e arquivos privados responderam 404.

Evidências temporárias e capturas: `runs/deployment-2026-10-08`, fora do Git.

### Segundo envio, com a correção

Execução: `0d6dc1e1bad04e44a3c9daa5ed036a5b`, realizada pelo formulário público
com o CSV original e referência 22/09/2026. Entrada SHA-256:
`dbce30af2c26e14d8e3f3c675741c95aedd101dfc1a90bad62ae81e72a0def4a`.
O resultado está em `https://ranking.lucaspsm.com/analise/0d6dc1e1bad04e44a3c9daa5ed036a5b`
e segue a retenção normal de sete dias.

- Ranking e datas iguais ao case nas duas janelas.
- Contexto disponível após 519 segundos desde o envio, dentro do limite total.
- 24 tickers, 23 empresas e nenhuma identidade não confirmada.
- Quatro empresas com acontecimentos datados; 19 com antecedentes financeiros.
- Nenhuma empresa marcada como evidência insuficiente nesta coleta.
- Quatro indicadores de mercado nas datas exatas das duas janelas.
- Nenhum acontecimento macroeconômico confirmado nesta coleta; os tópicos ausentes
  permanecem identificados. Isso não comprova que não houve acontecimentos.
- Conferência independente: 47 retornos semanais, 212 comparações diárias,
  69 contas CVM e oito comparações de mercado, sem divergências.
- Manifesto, contexto empresarial, mercado e auditoria responderam 200; assinaturas
  SHA-256 dos três conteúdos coincidiram com o manifesto.
- O navegador mostrou o contexto automaticamente, a distinção entre antecedentes
  e acontecimentos e a fonte CVM do resultado financeiro. Console sem erros.
- O replay na VPS reproduziu `company.json` e `market.json` pelas respostas salvas,
  sem novas consultas às APIs. A geração original foi preservada.

O uso de memória observado durante a coleta corrigida foi de aproximadamente
163 MB, frente a 1,8 GB observado na tentativa anterior. Isso é uma observação
deste teste, não uma garantia de consumo máximo ou tempo para qualquer arquivo.
A coleta automática trouxe menos acontecimentos que a revisão editorial do case:
as versões permanecem separadas. Contexto disponível para todas as empresas não
significa causa do retorno confirmada para todas elas. O custo faturado pelas APIs
não foi medido; a reserva do modelo registrada na auditoria não é uma fatura.
