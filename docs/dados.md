# Dados e tratamento

O tratamento interpreta a extração, padroniza campos e registra problemas. Ele mantém todas as linhas rastreáveis; a decisão sobre quais ações entram no ranking ocorre depois.

## Formato aceito

CSV separado por vírgula, ponto decimal, ausência indicada por `-` e codificação UTF-8 ou Windows-1252. O cabeçalho deve conter estas nove colunas, nesta ordem:

```text
Ativo
Data
Fechamento|ajust p/ prov|Em moeda orig
Q Títs|ajust p/ prov
Abertura|ajust p/ prov|Em moeda orig
Máximo|ajust p/ prov|Em moeda orig
Mínimo|ajust p/ prov|Em moeda orig
Médio|ajust p/ prov|Em moeda orig
Volume$|Em moeda orig
```

Uma coluna renomeada, separador diferente ou estrutura incompatível gera erro explícito. O programa não tenta adivinhar equivalências.

## O que é padronizado

| Campo normalizado | Significado |
| --- | --- |
| `record_id`, `source_line` | Identificação do registro e linha física do CSV |
| `ativo_original`, `data_original` | Conteúdo original preservado |
| `ticker`, `exchange` | Código normalizado e bolsa indicada no ativo |
| `trade_date` | Data interpretada em formato ISO |
| `close`, `open`, `high`, `low`, `average` | Valores numéricos dos preços fornecidos |
| `adjusted_quantity`, `raw_volume` | Quantidade ajustada e volume financeiro da fonte |
| `instrument_type`, `classification_source` | Tipo e origem da classificação inicial; veja o dicionário completo no README |
| `raw_fields_json`, `parse_status` | Conteúdo bruto e situação da leitura |

A precisão recebida é preservada. Não há arredondamento prévio dos preços, preenchimento por zero ou carregamento do último preço conhecido. A classificação inicial pode ser provisória; veja a [confirmação dos instrumentos](classificacao.md).

## Controles de qualidade

São registrados datas inválidas ou posteriores à referência, números inválidos, ausências, preços não positivos, quantidades e volumes negativos, duplicatas, mínimo maior que máximo e preços fora do intervalo diário.

A granularidade esperada é **ativo × data**. Duplicatas exatas ou conflitantes são sinalizadas, sem remoção automática. Uma linha malformada permanece registrada com seu conteúdo e motivo.

Cobertura significa quantos ativos possuem dados numa data. Quedas acentuadas geram alertas e controles adicionais na seleção das pontas. Divergências entre quantidade, volume e preço médio não autorizam correção: quantidade ajustada e volume bruto podem estar em bases diferentes.

## Arquivos do tratamento

O comando Python produz `normalized.csv`, `quality_issues.csv`, `quality_by_date.csv`, `quality_summary.json` e `manifest.json`, além da cópia original. As ocorrências registram código, campo, linha e motivo. Esses arquivos completos não são todos disponibilizados pelo site público.

```powershell
python etl.py --input "CAMINHO\economatica.csv" --reference-date 2026-09-22 --output-dir "runs\tratamento"
```

Troque a referência e o caminho conforme a extração. O tratamento sozinho não calcula retornos nem seleciona o top 20.

Uma nova extração gera uma nova versão. Preços ajustados podem ser revistos pela fonte; não anexamos as linhas cegamente à execução anterior.
