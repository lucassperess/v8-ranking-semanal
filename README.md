# Ranking semanal de ações — etapa de tratamento

Pipeline em Python 3.11+ (biblioteca padrão) para preparar extrações diárias da Economatica. **Esta etapa não calcula retornos nem seleciona a semana ou o universo do ranking.** O arquivo recebido é copiado sem alteração para a pasta da execução; nenhuma linha é descartada e nenhum preço ausente é preenchido. O projeto pode ser executado novamente com outro arquivo e outra data de referência.

O enunciado do case exige que a **primeira linha do README final** apresente a média dos retornos do top 20. Este repositório contém apenas a etapa de tratamento; a primeira linha será atualizada na entrega final, depois que o ranking for calculado e validado. Este README ainda não é a entrega final.

## Executar

```powershell
python etl.py --input "CAMINHO\economatica.csv" --reference-date 2026-09-22 --output-dir "runs\extracao-2026-09-22"
```

Para outra semana, informe **novo CSV, nova data e nova pasta de saída**. A data é usada para identificar registros posteriores a ela; não recorta o arquivo. Use `--coverage-drop 0.25` para ajustar o limite de alerta de queda de cobertura (25% por padrão). Para comparar com uma execução anterior:

```powershell
python etl.py --input "CAMINHO\nova_extracao.csv" --reference-date 2026-09-29 --output-dir "runs\extracao-2026-09-29" --baseline-summary "runs\extracao-2026-09-22\quality_summary.json"
```

O programa espera **as nove colunas e sua ordem originais**. Detecta UTF-8 ou Windows-1252, usa vírgula como separador, ponto decimal e `-` como ausência. Uma alteração de esquema ou separador interrompe a execução com erro. Linhas malformadas, por sua vez, permanecem representadas na base normalizada, com os campos recuperáveis e um alerta `MALFORMED_ROW`.

### Classificação opcional pela B3

O [Cadastro de Instrumentos Listados da B3](https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/consultas/boletim-diario/dados-publicos-de-produtos-listados-e-de-balcao/glossario/) pode enriquecer a classificação. Baixe um **snapshot referente à data analisada ou anterior** e passe seu CSV com `--b3-registry`. O leitor reconhece `TckrSymb` e `SctyCtgyNm` (ou os nomes completos em inglês) e `RptDt`. Se este último faltar, informe `--b3-snapshot-date AAAA-MM-DD`. Um snapshot posterior à data de referência é rejeitado. Um cadastro com mais de sete dias gera alerta de desatualização. O arquivo de referência original fica fora do Git; seu hash e sua data ficam no manifesto.

```powershell
python etl.py --input "CAMINHO\economatica.csv" --reference-date 2026-09-22 --output-dir "runs\com-b3" --b3-registry "CAMINHO\cadastro_b3.csv" --overrides "overrides\approved.csv"
```

O cruzamento usa ticker normalizado, preserva todas as linhas e sinaliza códigos sem correspondência. A categoria B3 prevalece quando interpretável. Categoria oficial desconhecida ou conflitante fica sem resolução automática. Sem B3, regras de sufixo geram apenas rótulos **provisórios**: `3` a `8` como possível ação, `32`/`33` como possível BDR; sufixo `11` fica ambíguo. Essas regras não definem elegibilidade para o ranking. A [série histórica da B3](https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/historico/mercado-a-vista/cotacoes-historicas/) também pode auxiliar a verificar instrumentos negociados em uma data, mas seus preços não substituem os preços ajustados da Economatica.

Se uma classificação exigir revisão, registre a decisão em `overrides/approved.csv`, com ticker, categoria, URL da fonte, responsável, data da aprovação e justificativa. Esse arquivo é versionado. Uma categoria oficial já resolvida pela B3 não é alterada pelo mapeamento manual. Sugestões de IA nunca entram no ETL automaticamente.

## Saídas de cada execução

| Arquivo | Conteúdo |
| --- | --- |
| `economatica_original.csv` | Cópia bit a bit da entrada, conferida por SHA-256. |
| `normalized.csv` | Uma linha para cada linha de dados recebida, inclusive falhas de parsing. |
| `quality_issues.csv` | Uma ocorrência por verificação acionada; códigos, linhas, campos e motivos. Alertas por data/arquivo têm `record_id` vazio. |
| `quality_by_date.csv` | Linhas, tickers distintos, fechamentos positivos, fechamentos ausentes e variação de cobertura por data. |
| `quality_summary.json` | Contagens gerais, datas e frequência dos alertas. |
| `manifest.json` | Parâmetros, versões, hashes de entrada, código, referências e saídas. |

**Dicionário de `normalized.csv`:** `record_id` é a posição da linha de dados no arquivo; `source_line` é a linha física no CSV; `ativo_original` e `data_original` guardam o texto recebido; `ticker` e `exchange` separam, por exemplo, `ABCD3<XBSP>`; `trade_date` é a data ISO validada; `close`, `adjusted_quantity`, `open`, `high`, `low`, `average` e `raw_volume` são números decimais convertidos sem arredondamento, escritos com precisão da fonte; `instrument_type`, `classification_source` e `classification_detail` explicam a classificação; `raw_fields_json` guarda os nove campos recebidos (ou o texto da linha malformada); `parse_status` indica leitura válida ou inválida. Campos não interpretáveis ficam vazios na parte tipada, mas permanecem em `raw_fields_json` e em `quality_issues.csv`.

**Códigos de qualidade:** `MISSING_VALUE`, `INVALID_NUMBER`, `INVALID_DATE`, `FUTURE_DATE`, `INVALID_TICKER`, `MALFORMED_ROW`, `DUPLICATE_EXACT`, `DUPLICATE_CONFLICT`, `NONPOSITIVE_PRICE`, `NEGATIVE_AMOUNT`, `LOW_ABOVE_HIGH`, `OUTSIDE_DAILY_RANGE`, `VOLUME_PRICE_DIVERGENCE`, `DATE_WITHOUT_QUOTES`, `COVERAGE_DROP`, `EXTRACTION_COVERAGE_DROP`, `B3_TICKER_UNMATCHED`, `B3_CATEGORY_UNRESOLVED`, `B3_STALE_SNAPSHOT` e `INSTRUMENT_AMBIGUOUS`. `MISSING_VALUE` é informativo: um feriado ou um ativo suspenso pode ter valores ausentes sem representar erro. `VOLUME_PRICE_DIVERGENCE` também é informativo: volume bruto e quantidade/preço ajustados podem estar em bases diferentes, além de haver arredondamento.

## Achados da extração recebida

Na execução com referência em **22/09/2026**, sem cadastro B3: 4.828 linhas preservadas, 478 códigos, 1.278 fechamentos ausentes, 43 registros em 02/01/1920 sem preço, nove linhas históricas com quantidade e volume mas sem preço e nenhuma chave ticker–data duplicada. Há 11 ocorrências de valor fora do intervalo diário no arquivo inteiro, inclusive preços médios. A data 07/09/2026 contém linhas mas nenhum fechamento positivo; 21/09/2026 pertence à semana corrente em relação à data de referência. Esses fatos são diagnósticos, **não regras fixas para futuras extrações**. O ETL não presume causas de movimentos nem moeda adicional além do texto da fonte.

## Revisão opcional de exceções

`review_exceptions.py` lista códigos ambíguos ou não resolvidos, sem conexão de rede por padrão:

```powershell
python review_exceptions.py --input "runs\extracao-2026-09-22\normalized.csv" --output "runs\extracao-2026-09-22\exceptions_for_review.csv" --limit 25
```

Se desejar sugestões da Groq, informe um modelo compatível por `--model` e defina `GROQ_API_KEY` no ambiente. Opcionalmente forneça `--official-evidence` com colunas `ticker,official_reference_url,official_excerpt`. Sem evidência oficial, o script só aceita sugestão de próximo passo, não de categoria. O resultado permanece `pendente_validacao_humana`; para passar a valer, é preciso verificar a fonte e registrar uma aprovação em `overrides/approved.csv`. Indisponibilidade ou limite da Groq não impede o ETL principal.

## Testes e reprodução

```powershell
python -m unittest discover -s tests -v
```

Os testes sintéticos não exigem rede nem arquivos externos. Para incluir a verificação de regressão com a extração original, defina `ECONOMATICA_CASE_CSV` com seu caminho antes de rodá-los. Essa verificação exige 4.828 linhas rastreáveis e compara byte a byte as saídas de duas execuções. O arquivo bruto, o PDF e os resultados locais ficam fora do repositório público.
