# Etapa 4 — coleta e organização das evidências

Concluída em 07/10/2026 na branch `codex/contexto`. A coleta é exclusiva do case preservado; não modifica o processamento de novas análises nem os arquivos históricos assinados.

## Resultado

- União dos dois rankings: 24 tickers, associados a 23 companhias; Taurus ON e PN compartilham a pesquisa.
- Identidades associadas às descrições B3 da execução e ao cadastro oficial CVM, com código CVM, CNPJ e nome legal.
- 26 consultas Tavily e 26 consultas Exa: 23 empresas e três temas gerais (Brasil, Estados Unidos e tema fiscal).
- 85 resultados retornados pela Tavily e 130 pela Exa. São resultados de busca, não 215 notícias aprovadas.
- 185 URLs candidatas corporativas após deduplicação por empresa; duplicatas entre emissores ainda podem existir e precisam ser avaliadas na revisão.
- 23 documentos oficiais entregues na semana por nove companhias. Todos os 23 PDFs foram baixados e tiveram texto extraído com `pypdf` do runtime disponível, preservando arquivos e assinaturas.
- Seis registros de PTAX: 11/09 e os cinco dias úteis de 14 a 18/09.
- Quatro fontes iniciais tiveram metadados de publicação e conteúdo conferidos: sindicato da Taurus, comunicado do Copom, comunicado do Fed e notícia fiscal da Agência Senado.

As 26 buscas avançadas Tavily equivalem nominalmente a 52 créditos segundo a regra documentada; não foi consultada a fatura. O acesso Exa usado foi o MCP/CLI disponível no ambiente, não uma credencial Exa instalada no aplicativo.

## Arquivos

Versionados fora da demonstração histórica:

- `context/case-2026-09-22/issuers.json`: universo e identificação usada na pesquisa.
- `context/case-2026-09-22/source_index.json`: índice sem textos integrais, com empresas, links, datas informadas pelos provedores e documentos CVM. Os candidatos estão marcados como pendentes de revisão.
- `context/case-2026-09-22/verified_sources.json`: fontes iniciais com datas e condições conferidas. Não são textos finais para o dashboard.

Snapshot privado local, ignorado pelo Git:

- `runs/context-case-2026-09-22-v1/collection.json`: dossiê com identidade, documentos, buscas e PTAX.
- `runs/context-case-2026-09-22-v1/tavily-searches.json` e `exa-searches.json`: resultados por empresa/tema.
- `runs/context-case-2026-09-22-v1/exa/`: respostas indexadas da Exa por código CVM/tema.
- `runs/context-case-2026-09-22-v1/documents/`: PDFs oficiais, textos extraídos e índice IPE recebido.
- `runs/context-case-2026-09-22-v1/official-document-texts.json`: metadata e texto de cada PDF, para revisão.

O índice versionado registra assinaturas do dossiê e da extração. Os arquivos integrais locais não são publicados e precisam ser preservados se a pasta de trabalho for movida. As chaves permanecem somente no `.env` local ignorado.

## Cuidados confirmados na coleta

- Resultados relacionados a outra empresa, astrologia, assuntos policiais e barras laterais não devem ser aceitos por conterem o nome ou ticker.
- Datas devolvidas pela busca podem estar ausentes ou divergir da página; a leitura da fonte decide a aprovação.
- `Data_Referencia` CVM não é automaticamente a data da notícia. Há documentos entregues na semana que convocam reuniões futuras e outros sobre acontecimentos anteriores.
- Foram preservadas todas as versões de documentos da semana; a revisão escolherá e identificará a versão apropriada, sem contar versões como acontecimentos independentes.
- IMC tem documentos com versões e datas de entrega diferentes; um documento de domingo não será tratado como informação já disponível na sexta.
- A página do comunicado do Copom indica publicação em 16/09 às 18h32 e atualização em 23/09. A leitura atual confirma conteúdo retrospectivo, não constitui captura da página no momento do pregão.
- Nenhum texto coletado foi convertido automaticamente em motivo para a alta ou queda. Nenhuma mensagem "sem notícias" foi atribuída somente porque uma consulta voltou vazia.

## Reprodução da coleta

Na raiz do worktree, com `TAVILY_API_KEY` no `.env` e `mcporter` disponível:

```powershell
../v8-ranking-semanal/.venv/Scripts/python -m scripts.collect_case_context --exa --output runs/context-case-2026-09-22-v2
```

O comando gera um novo snapshot e recusa sobrescrever uma pasta não vazia. Tem um bloqueio explícito para não usar suas datas de case em outra referência. Não chama a OpenAI nem produz resumos.

Extração dos documentos com Python que tenha `pypdf`:

```powershell
& 'C:/Users/lucas/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -m scripts.extract_context_documents --collection runs/context-case-2026-09-22-v2/collection.json --output runs/context-case-2026-09-22-v2/pdf-extraction
```

A extração desta primeira coleta foi executada diretamente com o runtime, e os caminhos acima descrevem a forma versionada de repetir a operação. A cópia do índice de metadata para `context/` foi preparada depois da coleta; não é atualização automática do case público.

## Verificações

- Cinco testes locais: cobertura dos dois rankings e agrupamento ON/PN, leitura das chaves, estado de revisão dos resultados indexados, ausência de credencial e falha HTTP sem expor chave.
- Ruff e `git diff --check`.
- Verificação das assinaturas, retornos, ordenação e médias dos arquivos históricos: preservados.
- OpenAI: Luna e Sol responderam aos testes. Escolha e custos registrados em `contexto-modelos.md`.

## Próxima etapa

A seleção inicial de evidências e a conferência das fontes aprovadas foram registradas em [contexto-triagem.md](contexto-triagem.md). O índice original continua preservado como matéria-prima; as decisões ficam em `triage.json`. A próxima etapa é preparar e revisar os rascunhos com as fontes aprovadas e as lacunas explícitas. A camada visual e a publicação ainda não foram executadas; a produção continua na revisão standby.
