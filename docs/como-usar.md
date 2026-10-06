# Como usar o dashboard

O dashboard apresenta os resultados calculados pelo Python. Os controles mudam a visualização; não alteram os preços recebidos ou recalculam o ranking no navegador.

## Leia os indicadores

| Indicador | Interpretação |
| --- | --- |
| Média do top 20 | Média aritmética dos 20 retornos selecionados na janela principal |
| Ações elegíveis | ON/PN com duas pontas utilizáveis e confirmação oficial |
| Ações em alta | Proporção com retorno positivo entre as elegíveis |
| Janela alternativa | Média do top 20 usando primeiro e último fechamento dentro da semana |

Os ícones de informação exibem explicações curtas ao passar o mouse ou receber foco pelo teclado. Para aprofundar os critérios, consulte a [metodologia](metodologia.md).

## Explore uma ação

Selecione uma linha do ranking ou escolha o ticker no controle junto ao gráfico. O painel mostra o ativo selecionado e o retorno da janela exibida.

- **Preços (R$):** fechamentos observados em reais por ação.
- **Retornos diários (%):** variações entre datas consecutivas da extração.
- **Hover ou foco nos pontos:** detalhes do valor e da data. No dispositivo móvel, toque no ponto.
- **Valores nas extremidades:** preços inicial e final da série exibida no modo de preços.

Uma lacuna não é uma variação de zero. Veja [por que podem faltar dados](duvidas.md).

## Compare o contexto

A distribuição agrupa os retornos das ações elegíveis. A proporção de altas e baixas descreve essa amostra, não todo o mercado.

A matriz do top 20 apresenta movimentos diários com cores e valores. Uma célula vazia significa que faltam preços utilizáveis para aquela comparação. A fórmula semanal usa suas próprias duas pontas; não soma os percentuais da matriz.

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
