# Volume do top 20 — conferência local de 08/10/2026

Implementado: coluna de volume médio diário e cobertura; seletor entre retornos
e volume financeiro diário; escala azul linear comum; resumo de maiores e
menores médias, lacunas e volume na maior variação diária em valor absoluto.

Os cálculos usam Decimal no Python, somente nos dias dentro da semana.
Zero explícito é válido; ausências, números inválidos e duplicatas não viram
zero. A cobertura considera as datas da semana com fechamentos positivos
observados na extração. Uma média parcial é identificada.

`volume_context.json` é salvo para novas análises e oferecido na auditoria.
O case recebeu um derivado adicional a partir da base normalizada cuja
assinatura foi conferida. Rankings, retornos, médias e arquivos históricos
anteriores continuam com as mesmas assinaturas. A reprodução usa o derivado
salvo, sem APIs. Nenhuma chamada a modelos ou fontes foi necessária nesta etapa.

Conferência do case principal: ESTR4 tem média de R$ 1.191,20 nos cinco dias;
TASA4, R$ 8.789.228,00. MGEL4 possui quatro de cinco dias válidos. Na alternativa,
PLAS3 tem média de R$ 12.261,00 em quatro de cinco dias válidos.

Verificação: 136 testes, um ignorado, nenhuma falha. Ruff, assinaturas dos
artefatos históricos, formatação, JavaScript/CSS e diff aprovados. Prévia
conferida no desktop e em 320, 390 e 430 px, incluindo alternância de medida,
janela alternativa, cobertura incompleta e explicação por toque. Nenhum erro
JavaScript na prévia. Não foi realizado teste em telefone físico.

Captura local: `runs/volume-ui-20261008/volume-desktop.png` (não versionada).
Nenhuma publicação ou alteração da VPS/standby foi realizada.
