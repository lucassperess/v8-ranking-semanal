# Como usar o dashboard

O dashboard apresenta os resultados calculados pelo Python. Os controles mudam a visualização; não alteram os preços recebidos ou recalculam o ranking no navegador.

## Leia os indicadores

| Indicador | Interpretação |
| --- | --- |
| Média do top 20 | Média aritmética dos 20 retornos selecionados na janela principal |
| Ações elegíveis | ON/PN com duas pontas utilizáveis e confirmação oficial |
| Ações em alta | Proporção com retorno positivo entre as elegíveis |
| Janela alternativa | Média do top 20 usando primeiro e último fechamento dentro da semana |

Os ícones de informação exibem explicações curtas ao passar o mouse ou receber foco pelo teclado. No celular, toque para abrir ou fechar; tocar fora também fecha a explicação. Para aprofundar os critérios, consulte a [metodologia](metodologia.md).

## Explore uma ação

Selecione uma linha do ranking ou escolha o ticker no controle junto ao gráfico. O painel mostra o ativo selecionado e o retorno da janela exibida. No celular, o ranking prioriza posição, ticker e retorno; selecionar a linha abre o gráfico, onde é possível conferir os preços e a espécie. Use “Voltar ao ranking” para continuar a exploração.

- **Preços (R$):** fechamentos observados em reais por ação.
- **Retornos diários (%):** variações entre datas consecutivas da extração.
- **Hover ou foco nos pontos:** detalhes do valor e da data. No dispositivo móvel, toque na região da observação; o valor aparece abaixo do gráfico.
- **Valores nas extremidades:** preços inicial e final da série exibida no modo de preços.

Uma lacuna não é uma variação de zero. Veja [por que podem faltar dados](duvidas.md).

## Compare o contexto

A distribuição agrupa os retornos das ações elegíveis. A proporção de altas e baixas descreve essa amostra, não todo o mercado.

A matriz do top 20 apresenta movimentos diários com cores e valores. No celular, deslize dentro da matriz para consultar as datas e ações; ticker e cabeçalhos permanecem fixos. Tocar no ticker abre seu gráfico. Uma célula vazia significa que faltam preços utilizáveis para aquela comparação. A fórmula semanal usa suas próprias duas pontas; não soma os percentuais da matriz.

## Baixe e confira

O link ao lado de “Maiores altas da semana” baixa o ranking da janela exibida. A auditoria da execução reúne os demais arquivos permitidos, as datas e os alertas. Guarde o link da análise enviada enquanto ela estiver disponível.

## Envie outra extração

1. Abra [Nova análise](/nova-analise) e selecione um CSV de até 10 MB.
2. Confira a data de referência e a semana indicada. A referência define a semana-calendário anterior.
3. Envie e acompanhe a etapa do processamento.
4. Ao concluir, explore o resultado e abra sua auditoria. Se falhar, leia o motivo antes de tentar novamente.

O resultado de teste fica disponível por sete dias. O CSV bruto é removido após 24 horas e não é oferecido para download. Consulte [formato e tratamento](dados.md) antes de enviar outro esquema.

### Se a semana terminar antes de sexta-feira

O primeiro envio abrirá uma revisão no próprio formulário, sem criar análise nem guardar o CSV dessa tentativa. Confira as datas e a extração original. A ausência pode ser feriado ou arquivo incompleto; o site não decide a causa. Se você aceitar essas datas, marque a confirmação e execute novamente. A auditoria e o registro do envio mostrarão a decisão. Alterar arquivo ou referência exige nova revisão. Uma cobertura insuficiente impede continuar.

Se a análise falhar depois disso, a página apresenta o motivo e a orientação aplicável. A confirmação não substitui a classificação B3 nem corrige preços.

## Navegação no celular

Na documentação, “Assuntos” escolhe o artigo e “Nesta página” abre seu índice; as setas indicam abertura e fechamento. Os controles continuam acessíveis durante a leitura. Na auditoria, use o seletor de seção e consulte os arquivos agrupados em rankings, qualidade, classificação e reprodução. A tela cheia permanece disponível no desktop e é ocultada no mobile.

## Interprete os destaques e a variação em reais

O resumo acompanha a janela escolhida: informa o líder, a faixa de retornos do top, quantas ações começaram abaixo de R$ 1,00 e quais têm alertas nas duas pontas. São descrições dos dados, sem inferir causas das altas.

O painel da ação mostra os fechamentos inicial e final e a diferença **final − inicial**, em reais por ação ajustada, calculada em Python com precisão decimal. A diferença não é lucro de uma operação: não considera custos nem uma quantidade negociada. Valores pequenos podem aparecer com até seis casas na interface; os preços exatos permanecem nos CSVs auditados. A variação absoluta não muda a ordenação por retorno percentual.

A marca de informação no ticker indica um alerta da janela selecionada. Ao selecionar a ação, o painel mostra data, campo, motivo e se o campo entra na fórmula. Esses alertas consideram as duas pontas; não garantem ausência de problemas nos dias intermediários. A auditoria contém o contexto mais amplo.

“Contexto de negociação” explica a limitação da extração: volume bruto e quantidade ajustada podem usar bases diferentes. Sem confirmação de escala e comparabilidade, a interface não apresenta um indicador de liquidez ou inferências sobre facilidade de negociação. Nenhum filtro de liquidez foi aplicado.
