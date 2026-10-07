# Versão preservada antes do contexto

Registro de 07/10/2026. Esta etapa preserva a entrega e prepara uma pasta separada; não implementa notícias, IA ou uma nova publicação.

## Identificação conferida

- Commit publicado: `82e05074c84e534e4da1850e71d645e7effbbe6e`.
- Tag local: `standby-pre-contexto-2026-10-07`, apontando para esse commit.
- Checkout original: `C:/Users/lucas/OneDrive/Desktop/Codex/Projetos/v8-ranking-semanal`, branch `main`, sem alterações locais versionáveis na conferência.
- GitHub `origin/main` e checkout da VPS: mesmo commit.
- Site: https://ranking.lucaspsm.com/; `/healthz` respondeu `{"ok":true}`.
- App e worker estavam ativos; app com estado `healthy`.
- Imagem existente na VPS: `v8-ranking:latest`, ID `sha256:5d547e66ac8a73ea8674a0f7cb0b7e9c8f9a3bfba97054a3223ff6b9c6b1ad95`.
- SHA-256 do compose ativo: `dc5876bb9b144173170c264ee079fe9b3610990eea2972bee2a8bdf925216bd5`.

## Desenvolvimento separado

Pasta: `C:/Users/lucas/OneDrive/Desktop/Codex/Projetos/v8-ranking-semanal-contexto`.
Branch: `codex/contexto`, criada a partir da versão preservada. O checkout original permanece em `main`.

O worktree compartilha o histórico Git, mas possui arquivos próprios. Os diretórios ignorados com dados, cache B3, ambientes e execuções continuam no checkout original; não foram movidos, removidos nem incorporados ao Git. A demonstração em `resultados/2026-09-22` já está versionada.

Para a futura prévia local, usar a porta `8001` e estado exclusivo no worktree:

```powershell
Set-Location "C:/Users/lucas/OneDrive/Desktop/Codex/Projetos/v8-ranking-semanal-contexto"
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements-web.txt
$env:RANKING_DATA_DIR = "$PWD/runtime-data-contexto"
.venv/Scripts/python -m uvicorn webapp.server:app --host 127.0.0.1 --port 8001
```

Para testar novos envios, abrir outro terminal nessa mesma pasta, definir a mesma variável e executar `.venv/Scripts/python -m webapp.worker`. Esses comandos são instruções; a prévia e o worker não foram iniciados nesta etapa. A demonstração pode ser vista sem worker.

## Cópia portátil

Bundle fora dos checkouts:
`C:/Users/lucas/OneDrive/Desktop/Codex/Projetos/v8-ranking-standby-2026-10-07/standby.bundle`.

O bundle contém a tag e o histórico necessário para recuperar o código e os resultados versionados, sem depender do GitHub. Não é backup de uploads, banco SQLite, dados brutos, cache ou credenciais. Sua integridade foi verificada com `git bundle verify`.

Exemplo de recuperação em uma pasta nova:

```powershell
git clone "C:/Users/lucas/OneDrive/Desktop/Codex/Projetos/v8-ranking-standby-2026-10-07/standby.bundle" "C:/Users/lucas/OneDrive/Desktop/Codex/Projetos/v8-ranking-recuperado"
git -C "C:/Users/lucas/OneDrive/Desktop/Codex/Projetos/v8-ranking-recuperado" switch --detach standby-pre-contexto-2026-10-07
```

## Configuração de produção e eventual retomada

- Checkout da VPS: `/home/lucas/projects/v8-ranking-semanal`.
- Stack ativa: `/opt/stacks/v8-ranking/compose.yaml`; configuração de referência no repositório: `deploy/compose.yaml`.
- Python da imagem: `3.12-slim`; dependências em `requirements-web.txt`.
- App: `uvicorn webapp.server:app`, porta interna `8000`; worker: `python -m webapp.worker`.
- Estado: `RANKING_DATA_DIR=/data`, volume persistente `ranking_data` da stack `v8-ranking`.
- Proxy: rede externa `proxy`, Traefik e resolvedor `letsencrypt`, domínio `ranking.lucaspsm.com`.
- Credenciais e chaves SSH permanecem fora do registro. Nenhum segredo foi copiado.

Se futuramente for necessário voltar à versão preservada, conferir primeiro o estado do checkout da VPS, preservar alterações e retornar ao commit acima. Depois conferir a configuração e reconstruir app e worker conforme `deploy/README.md`. Preservar a stack, o volume e o proxy existentes; não usar `down -v`.

O código preservado permite reconstrução com as dependências fixadas, mas a base Docker é uma tag mutável. O ID acima identifica a imagem ativa na conferência; nesta etapa não foi exportada uma cópia da imagem nem realizado backup do volume de produção.

A configuração e os serviços da VPS não foram alterados. O site atual continua sendo a entrega disponível.
