# Revisão do conteúdo da prévia

Concluída em 07/10/2026, no ramo `codex/contexto`, sem publicação.

## Escopo e resultado

Foram revisadas as interpretações das 23 empresas, os 24 tickers presentes na união das duas janelas e o contexto geral. As interpretações e os acontecimentos da versão 2 foram preservados após a conferência. A versão 3 melhora a apresentação dos números e das lacunas.

Correções aplicadas:

- Documentos oficiais mostram **Entrega à CVM**, sem confundir registro com primeira divulgação pública. Quando um acontecimento reúne dois documentos, aparecem as duas datas de entrega.
- Uma comparação diária fica vazia quando **pelo menos um** dos dois preços está ausente ou conflitante. A explicação anterior podia sugerir que ambos precisavam faltar.
- Valores financeiros acima de mil recebem separador de milhares, por exemplo `R$ 3.055,50 milhões`. Os valores de origem permanecem os mesmos.
- O manifesto da prévia identifica a versão do conteúdo e sua revisão por assinatura, preservando as versões anteriores.

## Conferência independente

O comando `python -m scripts.audit_case_context` reconcilia os valores com os dados brutos salvos e recalcula as comparações. Resultado: nenhuma divergência nas 140 contas financeiras, 47 retornos semanais, 212 comparações diárias das duas janelas e oito comparações de mercado. As comparações diárias incluem pares repetidos nas duas janelas, não 212 pares distintos.

As contas financeiras foram comparadas diretamente aos CSVs do arquivo ITR da CVM. Os indicadores de mercado foram comparados às respostas históricas salvas do Yahoo Finance e à PTAX do Banco Central. Os corpos das notícias e documentos reutilizam a coleta e a revisão editorial anteriores; esta etapa não realizou uma nova busca exaustiva.

Também passaram:

- Suíte completa: 84 testes, um ignorado, sem falhas.
- Ruff, formatação e verificação de frontend com Node 22.
- Verificação das assinaturas, retornos e médias dos artefatos históricos.
- Inspeção no navegador de datas da IMC, aviso sobre informação posterior ao fechamento, data da publicação sindical da Mangels e explicação das lacunas.
- Leitura em desktop e mobile de 390 px, sem transbordamento horizontal.

## Limites e próxima etapa

O conteúdo está conferido para a prévia do case de 22/09/2026. Há contexto específico para todos os tickers das duas janelas; isso não significa que uma causa tenha sido comprovada para cada oscilação. Onde a evidência não permite concluir, a pergunta permanece aberta no painel.

Novos envios ainda não geram notícias automaticamente. Essa capacidade exige uma etapa própria e não deve ser prometida na entrega desta prévia.

O próximo passo é a revisão final da navegação e da documentação da camada de contexto antes da publicação. Produção e standby permanecem preservados. Não foram feitas novas chamadas pagas a modelos nesta revisão.
