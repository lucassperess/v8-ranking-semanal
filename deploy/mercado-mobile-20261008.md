# Revisão das referências e da visualização móvel — 08/10/2026

## Versão publicada

- Código da imagem: `48ca0e1`.
- Imagem: `v8-ranking:context-48ca0e1`.
- Identidade Docker: `sha256:b311f73b028c377c4c7cfcebab753e9974eef7bd153c0b1841849a995e39f43c`.
- SHA-256 do arquivo da release: `4be782f60aa10bbec212ad1b06be4d38ebc8d5dc0a7cc3cd77c452ed76b0d35a`.
- Release: `/home/lucas/projects/v8-ranking-releases/48ca0e1`.
- Backup: `/home/lucas/backups/v8-ranking/20261008-refinement-48ca0e1`.
- Endereço: https://ranking.lucaspsm.com/.

## Alterações

Os quatro acontecimentos confirmados aparecem na lista e nos detalhes, na mesma ordem. Dados e fontes de mercado usam uma tabela com datas, valores, unidades e links. O período global fica junto ao seletor de semana; o cabeçalho de mercado não repete essas datas. Datas específicas de um indicador continuam identificadas quando diferem das globais.

O ranking usa o título “20 Maiores retornos da semana”. O subtítulo geral e os resumos narrativos de retornos e volumes foram removidos. A legenda de volume foi encurtada; a explicação da escala logarítmica ficou no ícone de informação e na documentação. Os volumes médios do desktop mostram o prefixo R$ e a cobertura.

No celular, a tabela prioriza posição, ativo e retorno, com o volume médio oculto. Os controles de semana, as datas, os acontecimentos e os espaçamentos receberam ajustes. O volume diário permanece disponível. A tabela de fontes tem rolagem horizontal dentro do próprio bloco.

## Conferências realizadas

- 18 testes de `tests.test_webapp`, sem falhas.
- Ruff, formatação, verificação do frontend e `git diff --check` aprovados.
- Assinaturas, retornos, ordenação e médias do case preservados.
- Candidato isolado de rede: 24 rotas responderam, incluindo oito guias e onze imagens.
- Publicação: 33 verificações HTTP; imagens corresponderam aos arquivos locais, quatro derivados do case permaneceram idênticos, uma execução anterior continuou acessível e os caminhos privados permaneceram bloqueados.
- Revisão visual em desktop e larguras móveis de 320 e 390 pixels. Na página pública de 390 pixels, a tabela apresentou somente posição, ativo e retorno, sem rolagem horizontal da página. Selecionar FASA3 atualizou o painel corretamente.
- A janela alternativa mostrou 15,93%, 302 elegíveis e datas de 14/09 a 18/09; os dados de mercado acompanharam a seleção.
- Quatro novos prints da documentação foram inspecionados. As imagens históricas permanecem disponíveis.

Os serviços estão ativos, a aplicação está saudável e o volume `v8-ranking_ranking_data` foi preservado. A publicação incluiu cópia consistente do SQLite com conferência de integridade. Não foram feitas novas chamadas de coleta ou geração de contexto nas APIs externas.

## Restauração

A versão anterior `v8-ranking:context-32c5b1c` permanece disponível. Para restaurar a apresentação anterior usando os dados atuais:

```bash
cp /home/lucas/backups/v8-ranking/20261008-refinement-48ca0e1/rollback.yaml /opt/stacks/v8-ranking/compose.yaml
docker compose --env-file /opt/stacks/v8-ranking/context.env -f /opt/stacks/v8-ranking/compose.yaml up -d --no-build --wait --wait-timeout 90
curl -fsS https://ranking.lucaspsm.com/healthz
```

A versão original `v8-ranking:standby-20261008` também foi preservada; identidade conferida: `sha256:5d547e66ac8a73ea8674a0f7cb0b7e9c8f9a3bfba97054a3223ff6b9c6b1ad95`. O arquivo de credenciais e os backups permanecem privados.
