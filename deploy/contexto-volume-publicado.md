# Contexto, volume e documentação publicados

Publicação realizada em 08/10/2026 em https://ranking.lucaspsm.com/.

## Versão ativa

- Imagem de app e worker: `v8-ranking:context-ef0731d`.
- Assinatura: `sha256:384fec441861e79472f3f6df77329d1bd355fa5c260e28ef9e5cbad63e008488`.
- App saudável e worker em execução; `/healthz` respondeu `{"ok":true}`.
- Volume original `v8-ranking_ranking_data` preservado.
- Standby `v8-ranking:standby-20261008` preservado com sua assinatura anterior.
- Release preparada e testada conforme [registro da preparação](preparacao-contexto-volume.md).

## Troca e restauração

A fila e as coletas de contexto estavam vazias. O app foi parado para impedir novos envios durante a troca; a fila foi conferida novamente antes de interromper o worker.

Duas tentativas foram interrompidas durante a exportação do backup: primeiro, a conexão SQLite ao volume somente para leitura; depois, o `docker cp` de um arquivo em `/tmp` do worker. Em ambas, o mecanismo de restauração voltou à imagem anterior e confirmou o app saudável. Nenhuma dessas tentativas substituiu os dados ou concluiu a ativação da candidata.

A tentativa concluída fez a cópia consistente por `sqlite3.Connection.backup` no worker e exportou seus bytes diretamente para um arquivo privado na VPS. `PRAGMA integrity_check` passou antes e depois da exportação. A configuração anterior e esse banco estão em:

`/home/lucas/backups/v8-ranking/20261008-published-ef0731d-final/`.

Após iniciar os novos serviços, houve uma resposta 404 transitória até o proxy registrar o app saudável. A verificação com tentativas limitadas terminou em 200. Não houve novas chamadas de IA ou Tavily nesta publicação, nem envio de outra base para processamento.

Para restaurar a versão imediatamente anterior, preservando os dados:

```bash
cp /home/lucas/backups/v8-ranking/20261008-published-ef0731d-final/rollback.yaml /opt/stacks/v8-ranking/compose.yaml
docker compose --env-file /opt/stacks/v8-ranking/context.env -f /opt/stacks/v8-ranking/compose.yaml up -d --no-build --wait --wait-timeout 90
curl -fsS https://ranking.lucaspsm.com/healthz
```

Para retornar ao standby original, consulte [o registro anterior de restauração](contexto-publicado.md). Não apague o volume. A cópia do banco não precisa ser restaurada numa troca normal de imagem.

## Conferência pública

- 27 verificações HTTP aprovadas.
- Oito guias acessíveis; cinco prints novos idênticos, byte por byte, aos arquivos revisados.
- Rankings principal e alternativo, relatório e volume do case idênticos aos arquivos versionados.
- A execução pública anterior `0d6dc1e1bad04e44a3c9daa5ed036a5b` conserva seu ranking e os quatro arquivos de contexto acessíveis. Não foi refeita sua coleta nem acrescentado volume retroativamente.
- Downloads do CSV original e de evidências privadas continuam bloqueados com 404.
- Navegador: coluna de volume e cobertura, seleção de ESTR4, aba Contexto, modo Volume e atualização das datas e retorno ao trocar a janela.
- Desktop: captura atual do dashboard público conferida.
- Celular: ranking e documentação não excederam a largura de 390 px. A ampliação do print de ESTR4 foi conferida visualmente: modal centralizado, imagem carregada, bordas arredondadas, zoom de 1,5×, ajuste e fechamento funcionando. A pendência visual registrada na preparação foi encerrada.
- As cinco imagens novas carregaram no guia; console sem erros ou avisos na conferência.

Capturas e resultados detalhados, fora do Git: `runs/release-review-20261008/`. A suíte completa de 136 testes e os controles estáticos foram aprovados na preparação; não houve alteração do código depois dela.
