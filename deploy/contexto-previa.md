# Contexto integrado à prévia local

Revisão em 07/10/2026. Ramo `codex/contexto`. Esta etapa não publica a aplicação.

## Conteúdo disponível

- Contexto das 23 empresas que correspondem aos 24 tickers presentes na união dos dois rankings do case de 22/09/2026.
- Leitura dos preços da janela selecionada, antecedentes empresariais, acontecimentos datados e fontes consultáveis no painel da ação.
- Quatro indicadores: Ibovespa, S&P 500, Nasdaq Composite e dólar PTAX de venda. As comparações usam 11→18/09 na janela principal e 14→18/09 na alternativa.
- Quatro acontecimentos gerais: juros do Fed, meta Selic, avaliação fiscal da IFI e pesquisa Datafolha. Acontecimentos e indicadores têm fontes identificadas.
- “Além do top 20” continua como última seção do dashboard.

Os textos oferecem contexto documentado, não uma estimativa da parcela do retorno causada por cada notícia. Antecedentes de agosto não são apresentados como anúncios novos da semana. Informações publicadas depois de 18/09 recebem aviso explícito. Uma pesquisa eleitoral representa as intenções de voto observadas naquele levantamento; não é previsão de resultado.

## Fontes e precisão

Os índices usam a série histórica diária do Yahoo Finance, identificada pelo símbolo retornado pelo provedor. Não são apresentados como preços oficiais da B3. PTAX e meta Selic vêm do Banco Central. O comunicado do Fed, a publicação da Agência Senado e a matéria original da Folha foram conferidos na coleta desta etapa. A ata do Copom divulgada depois da semana não entrou como informação conhecida nos pregões.

O indicador de dólar é PTAX de venda, referência diária, não fechamento de mercado. Variações são calculadas em Python com a precisão recebida; valores exibidos usam duas casas decimais. Uma reportagem com valores conflitantes do Ibovespa foi descartada para a comparação quantitativa.

`market_context.json` guarda indicadores, datas, fontes, notas de revisão e assinaturas das séries recebidas. O script `build_market_context.py` usa respostas salvas em `runs/context-market-v1`, preservando a saída anterior.

## Integração e independência do ranking

O navegador busca `/api/featured/context`, separado de `/api/featured`. Não chama serviços de busca nem modelos e não recebe credenciais. A seleção de ação ou janela apresenta os valores e textos previamente preparados.

`preview_manifest.json` vincula os textos e a revisão editorial por SHA256 com finais de linha LF. Também vincula os três arquivos históricos usados para preparar a leitura dos preços. Uma base diferente, um arquivo ausente ou um texto modificado sem revisão deixa o contexto indisponível. O ranking permanece acessível.

O conteúdo desta prévia foi preparado para o case. Novos envios ainda não geram contexto de notícias automaticamente e não recebem os textos do case. Essa expansão exige uma etapa própria de coleta, revisão, custo e tratamento de falhas.

## Verificação

- Suíte completa: 84 testes, com um ignorado.
- Ruff, verificação de artefatos históricos e `git diff --check` aprovados.
- Node 22: dependências instaladas com `npm ci --ignore-scripts`; formatação e verificação de JavaScript/CSS aprovadas.
- Navegador real: seleção dos 20 ativos de cada janela, total de 40 seleções, todas com contexto correspondente.
- Janela alternativa: indicadores mudam para 14→18/09; gráfico diário mantém o primeiro dia como ponto de partida, sem retorno inventado.
- Desktop e mobile de 390 e 320 px: inspeção visual e conferência da largura do documento, sem transbordamento horizontal dos novos blocos.
- Fontes e antecedentes são recolhíveis; seções abertas permanecem abertas ao alternar preços/retornos ou redimensionar a tela.
- IMC: conferido o aviso sobre informação de domingo, posterior ao fechamento de sexta-feira.
- Nenhum aviso ou erro de console foi observado nas interações conferidas.

Prévia: `http://127.0.0.1:8879/`. Para iniciar novamente:

```powershell
../v8-ranking-semanal/.venv/Scripts/python -m uvicorn webapp.server:app --host 127.0.0.1 --port 8879
```

A produção e o ponto de recuperação `standby-pre-contexto-2026-10-07` permanecem preservados. Não houve novas chamadas pagas a modelos nesta etapa.

## Ajuste de apresentação: gráfico e contexto em abas

O painel começa em “Gráfico”. A aba “Contexto” substitui a área do gráfico; ticker, retorno, preços e seletor de ação ficam disponíveis nas duas visualizações. A aba escolhida permanece ao mudar ação ou janela. As setas do teclado, Home e End alternam as abas. Ao voltar ao gráfico, ele é redesenhado com a largura disponível.

No desktop, o contexto tem uma área de leitura de 430 px com rolagem própria. No mobile, a altura acompanha o texto e a rolagem é da página. Fontes e detalhes permanecem recolhíveis. Os acontecimentos gerais da semana também começam recolhidos, em seção própria; os quatro indicadores continuam visíveis.

Conferidos no navegador: alternância das abas, atualização de ação e janela sem perda da aba escolhida, navegação por teclado, retorno ao gráfico sem perda de largura e telas de 1366, 390 e 320 px. Nenhum erro de console foi observado.

## Topo e espaço útil do gráfico

O ticker é o seletor no topo, com ON/PN ao lado e o retorno semanal à direita. O rótulo redundante “Ativo selecionado” foi removido. Inicial, final e variação formam uma faixa alinhada; os dois grupos de controles permanecem separados por função.

As explicações de preços, retornos diários, lacunas e datas da janela ficam no “i” do gráfico. A variação em reais tem explicação própria. Os botões usam o comportamento comum da plataforma: hover e foco no desktop; toque, clique fora e Escape no mobile. Em telas estreitas, a explicação aberta aparece dentro da largura da tela, acima da borda inferior. Alertas específicos continuam visíveis.

Conferidos o encaixe a 320 e 390 px, a atualização ON/PN, o texto sobre o primeiro dia da alternativa, a permanência da aba ao trocar o ticker e os alertas de BIED3. Os preços, cálculos e fontes não foram alterados.

Refinamento visual: o seletor usa fonte regular de 14 px no desktop e 16 px no mobile. ON/PN aparece como texto simples, sem pílula nem botão de informação. O gráfico de barras não repete o título “Retorno diário”. O “i” do gráfico fica no canto inferior direito, depois dos eixos, e a explicação abre acima dele no desktop. Conferidos os dois modos do gráfico e a abertura da explicação em tela de 320 px, sem transbordamento horizontal.
