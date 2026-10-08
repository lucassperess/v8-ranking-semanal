# Contexto por execução — validação local de 08/10/2026

Novos envios recebem contexto construído com suas próprias datas e instrumentos. O ranking fica disponível antes da coleta; a interface atualiza o contexto sem recarregar a página. Uma falha dessa etapa não invalida o resultado financeiro. Produção e standby não foram alterados.

## Outra base e outra semana

A validação usou 20 empresas diferentes das do top original, referência 07/10/2026 e semana de 28/09 a 04/10. Preços e arquivos de classificação são artificiais; notícias, documentos financeiros e indicadores foram coletados das fontes externas. O dashboard avisa que os preços são fictícios.

| Conferência | Resultado |
| --- | --- |
| Empresas com contexto específico | 20 de 20 |
| Com acontecimentos datados aceitos | 12 |
| Apenas com antecedentes financeiros | 8 |
| Retornos semanais reconciliados | 40 |
| Comparações diárias reconciliadas | 180 |
| Contas financeiras reconciliadas com CVM | 57 |
| Comparações de indicadores nas duas janelas | 8 |
| Reprodução dos textos e indicadores salvos | Iguais, sem novas chamadas |
| Suíte Python | 95 testes, um ignorado, sem falhas |

Os acontecimentos podem incluir antecedentes; a contagem não representa causas de preço comprovadas. As oito empresas restantes têm resultados financeiros disponíveis antes do fechamento, identificados como antecedentes. Três contas comparativas ausentes permaneceram ausentes.

Ibovespa, S&P 500, Nasdaq Composite e PTAX foram calculados nas datas exatas das duas janelas. A busca macroeconômica aceitou um acontecimento político datado; não confirmou acontecimentos sobre Banco Central ou Federal Reserve nas fontes consultadas. Essa ausência é informada e não significa que nada aconteceu.

## Reprodução e limites

Respostas dos provedores e documentos permanecem privados em cada execução. Derivados públicos possuem assinaturas SHA-256 e vínculo ao resultado financeiro. O replay grava outra pasta, preserva a geração original e compara seu conteúdo. Uma busca posterior com fontes ou modelo atualizados poderá produzir outro texto.

O processo exige identidade compatível com a classificação datada, trechos encontrados nos documentos, datas verificáveis e segunda leitura por IA. Não equivale a revisão humana individual nem garante explicação causal dos retornos. A busca seleciona até seis textos por empresa e antecedentes de até 90 dias.

O limite conservador de reserva para o modelo é US$ 3 por geração. Não mede o custo faturado e exclui Tavily. A primeira coleta completa observada levou aproximadamente 4 minutos e 55 segundos; fontes, fila, tamanho da base e rede podem mudar esse tempo. O prazo total do worker é dez minutos.

Também foram conferidos falta de credenciais, identidade ou data incorreta, evidência alterada, resposta inválida da IA, falha na inicialização da coleta e seleção dos 20 ativos nas duas janelas. No mobile de 390 px, não houve transbordamento horizontal. O ranking permaneceu disponível durante a coleta e o contexto apareceu automaticamente depois.

Prévia local com preços fictícios: `http://127.0.0.1:8879/analise/397cb98702af4d349ef7301fea8843a1`. Evidências temporárias: `runs/context-replication-final-2026-10-08/analysis`, fora do Git. Consulte [os comandos técnicos](../docs/desenvolvimento.md) para gerar, conferir e reproduzir uma execução.
