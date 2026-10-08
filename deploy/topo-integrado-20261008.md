# Topo integrado publicado em 08/10/2026

Código publicado: `32c5b1c`. Imagem: `v8-ranking:context-32c5b1c`.
Identificação: `sha256:780bf4e916551ef7d8f400bc57d1889b7d938e9a3c79da50b54fbfcaa4e2826b`.

O seletor da janela passou para antes do resumo. Os três indicadores usam colunas iguais e fonte de 32 pixels no desktop e 28 pixels no celular; a média mantém a cor de seu sinal. A comparação das médias ocupa uma linha secundária. Referências de mercado usam uma faixa compacta, com datas visíveis e valores e fontes em expansão. Até três acontecimentos aparecem com títulos, datas e fontes; a expansão conserva todos os textos. Nenhum dado do ranking, volume ou contexto histórico foi recalculado.

Verificações: 18 testes da aplicação, frontend, formatação, Ruff e assinaturas do case passaram. A troca global foi conferida no preview e no endereço público: alternativa com média de 15,93% e datas de 14/09 a 18/09. Em largura móvel de 390 pixels, não houve transbordamento da página; tooltips e troca da janela foram conferidos. A imagem candidata passou por 20 rotas sem rede externa. Depois da publicação, 29 verificações públicas passaram, incluindo os dois prints novos, arquivos do case sem mudança e preservação da execução anterior. Não foram feitas novas chamadas às APIs de contexto.

O Compose anterior e o backup consistente do SQLite estão em `/home/lucas/backups/v8-ranking/20261008-top-32c5b1c`. Os serviços usam o mesmo volume de dados. A imagem standby mantém sua identificação anterior.

## Restaurar a revisão anterior

Na VPS, depois de conferir que não há processamento ativo:

```bash
cp /home/lucas/backups/v8-ranking/20261008-top-32c5b1c/rollback.yaml /opt/stacks/v8-ranking/compose.yaml
docker compose --env-file /opt/stacks/v8-ranking/context.env -f /opt/stacks/v8-ranking/compose.yaml up -d --no-build --wait --wait-timeout 90
curl -fsS https://ranking.lucaspsm.com/healthz
```

Isso retorna à imagem `context-91bfa5e`, preservando os envios no volume. Não remova o volume nem substitua o banco sobre novos envios.
