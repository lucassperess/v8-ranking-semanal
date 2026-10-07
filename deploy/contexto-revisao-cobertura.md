# Revisão da estratégia de contexto

07/10/2026. Trabalho na branch de contexto; sem publicação. A versão de reserva continua preservada.

## Diagnóstico

O indicador anterior, 12 de 23 empresas com fontes datadas na semana, mediu disponibilidade de notícias selecionadas. Não mediu quanto da valorização ou desvalorização foi explicado. Usá-lo como taxa de sucesso da proposta foi inadequado.

A pesquisa estava excessivamente restrita à semana. Empresas menores, em dificuldade ou sem notícia recente ficaram com um painel vazio, embora existam demonstrativos e antecedentes relevantes. Trocar o modelo que resume os textos não resolve a ausência de evidências. Repetir a mesma notícia em vários sites também não aumenta o poder explicativo.

## Correção aplicada à preparação das evidências

- Foram coletados demonstrativos oficiais da CVM, com identificação por código CVM, para ampliar o contexto empresarial.
- Para 20 das 23 empresas, foram selecionadas contas de abril a junho de 2026, com comparativos do mesmo trimestre de 2025. Foram excluídas versões entregues depois de 18/09. Valores em milhares de reais foram convertidos explicitamente para reais.
- Para os 24 tickers da união das duas listas, foram preparados padrões de preços: comparação principal e alternativa, maior alta diária, pior dia e comparações ausentes. As duas espécies da Taurus compartilham notícias, mas mantêm seus próprios preços.
- Ambipar, Estrela e Fasa não têm demonstrativo elegível nesse catálogo consultado. Isso não comprova ausência de qualquer demonstração. Estrela e Fasa possuem documentos oficiais na triagem anterior; a situação de negociação da Ambipar ainda exige consolidação das novas fontes.

Os dados ampliados estão em `context/case-2026-09-22/expanded_evidence.json`. Sua condição continua sendo evidência para revisão, sem publicação e sem causalidade inferida. A triagem anterior foi preservada para rastrear a mudança de método.

## Exemplos que demonstram a utilidade da mudança

### PLAS3: a janela muda a interpretação

O papel caiu 5,88% na semana completa e subiu 13,55% na alternativa. Na segunda-feira, caiu 17,11% em relação ao fechamento anterior. A alternativa começa depois dessa queda, no fechamento de segunda. Por isso, os dois resultados têm sinais diferentes.

O demonstrativo disponível antes da semana registra prejuízo de R$ 47,64 milhões no segundo trimestre e patrimônio líquido negativo de R$ 825,28 milhões em junho. Isso descreve a situação financeira conhecida, mas não prova o motivo de cada negociação. Falta preço na quinta-feira: não há base para afirmar uma sequência diária completa de recuperação.

### TXRX4: a alta se concentrou em um dia

O papel subiu 22,29% na semana completa. A quinta-feira registrou alta de 20,90%; a segunda havia caído 2,86%. No trimestre anterior, a empresa registrou prejuízo de R$ 22,84 milhões, contra R$ 13,56 milhões um ano antes. A alta da ação não demonstra, por si só, melhora dos resultados da empresa. Falta evidência específica para atribuir o salto de quinta-feira a um acontecimento.

### LUXM4: parte do salto foi devolvida

A alta semanal foi de 9,93%. Na quarta-feira, o preço subiu 15,44%; na quinta, caiu 12,79%. A alternativa retorna 3,46%, pois exclui a alta de 6,25% da segunda-feira. A Trevisa registrou lucro de R$ 3,18 milhões no segundo trimestre, contra R$ 3,31 milhões no mesmo trimestre de 2025. Trata-se de lucro trimestral, não do acumulado do semestre.

### BIED3: os cinco dias tiveram alta

O papel subiu 14,77% na semana completa, com retornos diários positivos nos cinco dias. O resultado alternativo foi de 11,75%, excluindo o movimento de segunda. A Bioma registrou prejuízo trimestral de R$ 4,84 milhões, menor que o prejuízo de R$ 10,62 milhões um ano antes. O lucro acumulado no semestre não deve ser apresentado como lucro desse trimestre.

Esses exemplos derivam dos preços da execução e dos documentos CVM associados no arquivo de evidências. São protótipos de leitura factual, não textos causais aprovados para o dashboard.

## Próxima sequência de entrega

1. Consolidar, para cada empresa, demonstrativos, antecedentes e acontecimentos semanais. Validar as novas fontes de Ambipar e os antecedentes estratégicos encontrados para as demais empresas.
2. Produzir uma explicação individual que conecte a leitura do gráfico à situação documentada. A IA recebe somente fatos e referências conferidos; não preenche causas ausentes.
3. Revisar todos os ativos, incluindo os exclusivos da alternativa. Avaliar utilidade do texto, relação temporal, contas comparáveis e afirmações sustentadas. Uma notícia de baixo interesse não resolve uma lacuna.
4. Consolidar o contexto geral uma vez: juros, câmbio, índices e acontecimentos políticos. Fontes numéricas conflitantes precisam de confirmação antes de virar indicador. Não repetir o contexto macro como causa específica de todos os papéis.
5. Integrar os textos aprovados abaixo do gráfico e conferir a prévia em desktop e mobile. Publicação permanece uma decisão posterior.

## Como avaliar o resultado

Separar quatro perguntas: o ativo tem leitura dos preços? Tem contexto empresarial verificado? Tem acontecimento relevante no período? Há evidência de relação com o movimento? Não somar essas dimensões em uma falsa porcentagem de causalidade.

A meta é entregar contexto útil para todos os ativos. Não é possível prometer uma causa documentada para cada oscilação. Quando a relação não estiver demonstrada, o texto ainda precisa explicar concretamente o comportamento do preço e a situação conhecida da empresa, indicando a pergunta que permaneceu sem resposta.
