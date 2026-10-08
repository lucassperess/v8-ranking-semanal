# Validação integrada de contexto e volume — 08/10/2026

## Base e alcance do teste

Validação local, com 20 empresas diferentes das do ranking de referência:
PETR4, VALE3, ITUB4, BBDC4, ABEV3, WEGE3, BBAS3, RENT3, SUZB3, PRIO3,
GGBR4, CSNA3, BRAP4, LREN3, RADL3, VIVT3, TIMS3, EQTL3, CMIG4 e SBSP3.

Os preços, volumes e arquivos usados para testar a classificação são artificiais.
As identidades empresariais e as fontes de contexto foram consultadas externamente.
O resultado exibe um aviso de validação local. Não deve ser publicado como
análise de preços reais nem tomado como teste de obtenção online da classificação B3.

Referência: 07/10/2026. Semana: 28/09 a 04/10/2026. Janela principal:
25/09 → 02/10; alternativa: 28/09 → 02/10.

O cenário `volume` de `scripts.validate_context_replication` mantém o cenário
anterior disponível e acrescenta quedas, preços estáveis, um volume zero,
um volume ausente, um negativo e um fechamento diário ausente.
Usa os módulos de cálculo, apresentação, volume e contexto da aplicação.
Nesta rodada, o formulário público e o worker não foram executados novamente;
o resultado concluído foi registrado na fila local para verificar sua apresentação.

## Cálculos e volumes

Uma conferência independente, lendo o CSV artificial diretamente, verificou:

- 40 retornos e a ordenação das duas janelas; médias de 1,31% e 1,03%.
- 100 valores diários de volume e 40 médias de volume nas linhas do ranking.
- Zero explícito preservado; ausências e negativos excluídos da média.
- ITUB4 e VALE3 com cobertura de quatro dos cinco dias, identificada na interface.
- WEGE3 com volume disponível mesmo no dia sem fechamento; as duas comparações
  diárias afetadas pelo preço ausente permanecem vazias.

`scripts.audit_run_context` também conferiu 40 retornos semanais, 180 comparações
diárias, 57 valores financeiros contra os arquivos CVM salvos e oito comparações
de mercado. Não encontrou divergências nesses cálculos.

## Cobertura das fontes

As 20 empresas receberam contexto com acontecimentos datados, totalizando 45
acontecimentos aceitos. Onze empresas têm acontecimentos da própria semana até
o fechamento; nove têm apenas acontecimentos anteriores. Quinze têm antecedentes
datados, contando também seis das onze com acontecimentos na semana.
Nenhum acontecimento empresarial aceito foi publicado depois do fechamento final.

Isso não equivale a explicar a causa dos 20 retornos: os preços são fictícios e
a validação de trechos, datas e identidade foi automática, com revisão por IA.
Não houve revisão editorial humana individual de todas as notícias.

Ibovespa, S&P 500, Nasdaq e dólar PTAX têm as duas comparações disponíveis.
Foi aceito um texto de contexto político. Não foram confirmados acontecimentos
para os temas Banco Central e Federal Reserve. A interface informa essa ausência;
a camada de notícias macroeconômicas ainda não cobre todos os temas.

## Tempo e consumo informado

- Pipeline financeiro com classificação artificial: 1,63 segundo.
- Coleta e geração de contexto: 323,11 segundos, ou 5 minutos e 23,11 segundos.
- Soma desses tempos de processamento: 324,74 segundos. Não é uma medição de
  upload, espera em fila ou classificação online completa pelo formulário.
- OpenAI: 49 chamadas, todas com uso informado; 356.629 tokens de entrada
  e 16.917 de saída.
- Tavily: 43 buscas e 23 extrações.
- Reserva conservadora de modelos utilizada: US$ 3,550144 de um teto de US$ 6.
  Essa reserva não é o valor faturado. O faturamento OpenAI e os créditos Tavily
  não foram informados por essas respostas.

Todas as empresas tiveram sua parcela protegida de US$ 0,24; cada um dos três
temas de mercado teve US$ 0,40. Nenhuma falha foi registrada nos diagnósticos.
Este resultado verifica uma execução completa; não garante os mesmos tempos
ou cobertura para qualquer outra extração.

## Reprodução e interface

Reprodução concluída em 31,84 segundos, sem credenciais e com as funções de
rede bloqueadas durante o teste. Houve zero tentativas de rede e zero chamadas
novas de API. Os conteúdos empresariais e de mercado coincidiram com os
originais. As assinaturas de todos os arquivos da coleta original permaneceram
iguais. O volume também foi recuperado do arquivo derivado, sem reler o CSV bruto.

Conferência visual no desktop e em viewport móvel de 390 px: tabela com médias
e cobertura, seleção de ticker, abas Gráfico/Contexto, alternativa sem retorno
no primeiro dia, lacunas e alternância Retornos/Volume. Nenhum erro ou aviso
foi capturado no console; a página móvel não apresentou excesso de largura.

Evidências privadas e capturas estão em
`runs/context-volume-validation-20261008/`, fora do Git. A prévia local usa
`/analise/c08c08c08c08c08c08c08c08c08c08c0` na porta 8883.

## Verificação e próximo passo

136 testes executados: nenhuma falha, um teste opcional ignorado. Ruff,
formatação, verificação do JavaScript/CSS e assinaturas da demonstração histórica
aprovados. A documentação técnica passou a informar o orçamento padrão atual
de US$ 6, corrigindo a menção antiga a US$ 3.

Próximo passo: revisão final da documentação de entrega para explicar contexto,
volume, reprodução e limitações; depois, preparação da publicação dentro do
escopo autorizado. Esta etapa não alterou a VPS, o site publicado ou o standby.
