# Consolidação do contexto empresarial

Etapa concluída em 07/10/2026 na branch `codex/contexto`, sem integração visual ou publicação.

## Conteúdo preparado

- 23 empresas e 24 tickers: união exata das duas listas, com contexto empresarial compartilhado por TASA3/TASA4 e leituras próprias dos preços.
- 20 demonstrativos oficiais: trimestre abril–junho de 2026, comparativo do mesmo trimestre de 2025, escopo consolidado quando disponível e individual para Westwing.
- Cinco antecedentes adicionais revisados: negociação da Ambipar por leilão, relatório de crédito da Armac e documentos oficiais de Economatica, Qualicorp e Westwing.
- Acontecimentos semanais selecionados da triagem anterior, agrupando documentos do mesmo fato e preservando informações posteriores ao último fechamento.
- 48 registros de fontes. Essa contagem não significa 48 acontecimentos independentes nem mede causalidade.

Os [textos revisados](contexto-textos-revisados.md) permitem conferir cada empresa. O arquivo para a futura integração é `context/case-2026-09-22/company_context_v2.json`. A primeira preparação foi preservada em `company_context_v1.json`; o registro editorial e a assinatura da versão revisada estão em `editorial_review.json`.

## Revisão realizada

Os textos foram preparados a partir das contas e fontes conferidas. A leitura dos preços foi calculada diretamente dos arquivos da execução. Uma revisão adicional pela Responses API usou GPT-6.1 Sol com esforço `low`, saída estruturada e `store=false`, abrangendo todos os códigos CVM e tickers.

A API recebeu 71.679 tokens de entrada e retornou 1.846 tokens de saída. Custo estimado dessa chamada: US$ 0,161818, pelos preços registrados em [contexto-modelos.md](contexto-modelos.md). Antes dela, duas solicitações retornaram HTTP 400 por incompatibilidade de `reasoning.effort=none`; o parâmetro foi corrigido. Essas respostas não informaram consumo de tokens. Não se afirma saldo de conta ou custo faturado.

A revisão adicional produziu nove apontamentos. Todos foram avaliados e resolvidos editorialmente: precisão sobre o período semestral da Bioma, lacunas de Mangels/Plascar, data do patrimônio da Renauxview, separação da informação dominical da IMC, datas de decisão/divulgação em Qualicorp/Economatica e cronologia dos preços de Fasa/Taurus. A revisão da IA não verificou os corpos originais das fontes nem aprovou causas; a conferência das fontes foi uma etapa distinta.

Para reproduzir a compilação, usar `python -m scripts.build_case_context --output <novo-arquivo.json>`. A saída continua marcada para revisão; uma nova compilação não herda automaticamente a aprovação editorial da versão anterior. A revisão por API é opcional e privada, via `scripts.review_compiled_context`, com limite local por chamada e sem aprovação automática.

## Verificações e limites

Os testes cobrem origem das fontes, datas posteriores, associação a outra empresa, duplicação ou ausência de ticker, interpretação das unidades, versões dos demonstrativos, exclusão do retorno de segunda na alternativa e preservação das lacunas. Os artefatos históricos permanecem sem alterações.

Todos os ativos têm leitura dos preços e contexto empresarial documentado. A causa da variação não está estabelecida para todos eles. Os textos registram essa diferença e as perguntas ainda sem resposta. A cobertura é do case; não foi implementada geração automática para novos envios.

## Etapas seguintes

Consolidar o contexto geral e os indicadores verificáveis da semana; depois integrar a apresentação no dashboard e revisar a prévia desktop/mobile. O conteúdo empresarial desta etapa está preparado para essa integração. Publicação permanece posterior à revisão da prévia.
