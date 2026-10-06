# Auditoria e reprodução

Auditar significa conseguir ligar o resultado à entrada, às regras, às fontes e às decisões que o produziram. As datas e contagens da auditoria pertencem à execução consultada.

## Abra a auditoria da execução

No dashboard, use o acesso à auditoria para consultar datas, universo, alertas e downloads. A referência tem uma auditoria fixa; uma análise enviada tem seu próprio endereço.

Esta documentação apresenta regras gerais. Use os arquivos da execução para conferir seus números, evitando aplicar as contagens do case a outra extração.

## Qual arquivo consultar

| Pergunta | Arquivo |
| --- | --- |
| Como chegou às posições? | `top20.csv` e `all_returns.csv` |
| O que muda na outra janela? | `top20_alternativo.csv` e `all_returns_alternativo.csv` |
| Quais códigos ficaram sem duas pontas? | `candidate_exclusions.csv` |
| Há alertas nos dados usados? | `quality_context.json` |
| Quais datas, médias e versões foram utilizadas? | `ranking_report.json` |
| Como interpretar a execução? | `README.md` da execução |

Downloads públicos são limitados a uma lista de derivados permitidos. Na pasta completa do comando Python, existem também os arquivos normalizados, ocorrências por linha, evidências da B3 e decisões de universo. O arquivo de exclusões por ausência de preços não substitui o registro de instrumentos excluídos pelo tipo.

## O que significa hash

Hash SHA-256 é uma assinatura calculada a partir do conteúdo de um arquivo. Se o conteúdo mudar, sua assinatura também muda. Isso permite conferir integridade e identificar qual entrada foi usada. Não demonstra que os dados estejam corretos.

Os manifestos registram parâmetros, arquivos, versões e assinaturas. Para repetir uma execução, preserve a entrada, a configuração, o código e as fontes B3 utilizadas. Uma nova versão de dados ou código pode produzir outro resultado.

## Reproduza pelo Python

Com Python 3.11+ disponível, na raiz do repositório:

```powershell
python weekly_ranking.py --input "CAMINHO\economatica.csv" --reference-date 2026-09-22 --output-dir "runs\reproducao"
```

Substitua os caminhos e a referência pelos da análise. O pipeline busca fontes necessárias que ainda não estejam disponíveis. Adicione `--offline` somente quando todas as fontes necessárias já estiverem guardadas no cache.

Confira datas, elegibilidade e arquivos de retorno antes de comparar duas execuções. Mesmos preços com regras ou datas diferentes não são a mesma análise.

## Versão da documentação

Os artigos são mantidos em Markdown no Git e publicados pelo site. A documentação atual descreve o código revisado; o relatório histórico conserva a identificação do código que executou o case.

Ainda não há associação automática entre cada execução e uma revisão arquivada destes artigos. Para conferir comportamento histórico após uma alteração, consulte a versão correspondente no Git e os manifestos. Veja [metodologia](metodologia.md) e [README do projeto](../README.md).
