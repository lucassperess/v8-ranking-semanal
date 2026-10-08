# Publicação da documentação revisada — 08/10/2026

## Versão publicada

- Código da imagem: `34e64da`.
- Imagem: `v8-ranking:context-34e64da`.
- Identidade Docker: `sha256:6c4c0951a4d962f514c87649e934d1b4f908751217c1e19b8af3e8fc9a958afb`.
- SHA-256 da release: `d938e3ba424baab635bdeb90f218c981891b38f7f776388147886724d72f41fd`.
- Backup: `/home/lucas/backups/v8-ranking/20261008-documentation-34e64da`.
- Aplicação saudável e worker ativo em https://ranking.lucaspsm.com/.

A release publica a revisão dos guias e os PNGs originais fornecidos pelo usuário, incluindo gráfico e contexto de ECOM3. O código de aplicação é o mesmo da versão anteriormente publicada; as diferenças são documentação, imagens e registros de operação.

## Conferência da publicação

- 53 verificações públicas aprovadas: oito artigos, imagens referenciadas, assets da interface, auditoria, derivados selecionados e bloqueios de arquivos privados.
- HTML dos oito artigos e bytes das imagens conferidos contra a release local.
- Sete respostas e derivados comparados antes e depois: apresentação do case, contexto, dois rankings, relatório, documentação histórica e volume. Nenhuma diferença.
- Universos de retornos principal e alternativo conferidos contra os arquivos versionados.
- Os 16 prints do guia de uso carregaram no navegador. O novo contexto de ECOM3 abriu na ampliação interna, com a imagem original e controle de fechamento funcional.
- Em viewport de 390 pixels, os três prints móveis carregaram e a página não apresentou transbordamento horizontal. Essa conferência de largura e carregamento não equivale a um teste em aparelho físico.
- CI da release `34e64da` aprovado antes da publicação: interface e Python em Linux e Windows.

Não havia análises aguardando, em execução ou contexto em processamento antes da troca. A cópia consistente do SQLite passou na conferência de integridade. O volume, os guias históricos e os demais serviços da VPS foram preservados. Não houve nova coleta ou geração nas APIs externas.

## Restauração

```bash
cp /home/lucas/backups/v8-ranking/20261008-documentation-34e64da/rollback.yaml /opt/stacks/v8-ranking/compose.yaml
docker compose --env-file /opt/stacks/v8-ranking/context.env -f /opt/stacks/v8-ranking/compose.yaml up -d --no-build --wait --wait-timeout 90
curl -fsS https://ranking.lucaspsm.com/healthz
```

O comando restaura `v8-ranking:context-8336f7f` com o volume atual. A imagem anterior permanece disponível. A identidade do standby original continua `sha256:5d547e66ac8a73ea8674a0f7cb0b7e9c8f9a3bfba97054a3223ff6b9c6b1ad95`.

O [registro da revisão local](documentacao-dashboard-20261008.md) descreve a preparação anterior à publicação. As verificações daquela etapa e desta publicação têm escopos distintos.
