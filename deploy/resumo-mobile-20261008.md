# Resumo móvel e aviso de uso — 08/10/2026

## Publicação

- Código da imagem: `8336f7f`.
- Imagem: `v8-ranking:context-8336f7f`.
- Identidade Docker: `sha256:663ee9a08a8b7665beeb7dfa8d7c51d4a3125f7f6bca97a0769d2242dcd98793`.
- SHA-256 da release: `b9173425039d320f9e1d2834ad2a43cf3a829c726005be006ab58eaa5097ad26`.
- Backup: `/home/lucas/backups/v8-ranking/20261008-mobile-summary-8336f7f`.
- Aplicação saudável e worker ativo em https://ranking.lucaspsm.com/.

No celular, o resumo apresenta três linhas com rótulos à esquerda e valores de 24 px alinhados à direita. A contagem de ações em alta fica abaixo do percentual; a janela não é repetida no bloco. “Comparar janelas” começa recolhido. A apresentação desktop continua com valores de 32 px e comparação visível.

Um diálogo inferior recomenda o computador na primeira visita em largura móvel, com texto sobre colunas ocultas e rolagem das tabelas. Continuar, fechar, Escape ou tocar fora dispensam o aviso. O fechamento fica salvo no navegador quando o armazenamento local está disponível. O diálogo usa foco modal nativo; não redireciona o usuário.

## Verificação

- 18 testes da interface, Ruff, formatação, verificação do frontend e `git diff --check` aprovados.
- Assinaturas, cálculos, ordenação e médias do case preservados.
- Candidato isolado: 25 rotas aprovadas, incluindo o novo JavaScript.
- Endereço público: 36 verificações HTTP, com correspondência dos assets, quatro derivados do case idênticos, execução anterior acessível e arquivos privados bloqueados.
- Revisão móvel em 320 e 390 pixels sem rolagem horizontal da página. Os três valores têm tamanho igual e a mesma coordenada direita.
- Fechamento pelo botão Continuar verificado na prévia; Escape verificado na página pública. O aviso não reapareceu após atualizar em nenhum dos dois casos.
- Comparação recolhida inicialmente, expansão funcional e atualização para 15,93% na janela alternativa verificadas na página pública.
- Desktop sem aviso e com a comparação visível conferido.

Não houve nova coleta ou geração de contexto nas APIs externas. O volume de dados foi preservado; o backup consistente do SQLite passou na verificação de integridade. A imagem anterior e a versão original standby permanecem disponíveis.

## Restauração

```bash
cp /home/lucas/backups/v8-ranking/20261008-mobile-summary-8336f7f/rollback.yaml /opt/stacks/v8-ranking/compose.yaml
docker compose --env-file /opt/stacks/v8-ranking/context.env -f /opt/stacks/v8-ranking/compose.yaml up -d --no-build --wait --wait-timeout 90
curl -fsS https://ranking.lucaspsm.com/healthz
```

Esse comando restaura `v8-ranking:context-48ca0e1` com o volume atual. A identidade de `v8-ranking:standby-20261008` permaneceu `sha256:5d547e66ac8a73ea8674a0f7cb0b7e9c8f9a3bfba97054a3223ff6b9c6b1ad95`.
