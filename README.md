Média dos retornos do top 20: 17,78%

# Ranking semanal de ações

[![Verificações do projeto](https://github.com/lucassperess/v8-ranking-semanal/actions/workflows/checks.yml/badge.svg)](https://github.com/lucassperess/v8-ranking-semanal/actions/workflows/checks.yml)

Para manter ou revisar o projeto, siga o [roteiro técnico e preparação do ambiente](docs/desenvolvimento.md) e o [registro de decisões](docs/decisoes.md). As orientações para agentes ficam em [AGENTS.md](AGENTS.md), compartilhadas com Claude Code por [CLAUDE.md](CLAUDE.md).

Pipeline em Python 3.11+ (biblioteca padrão) para preparar extrações da Economatica, definir ações ON/PN, calcular retornos e gerar o top 20 da semana anterior. O arquivo recebido é copiado sem alteração para a pasta da execução; nenhuma linha é descartada e nenhum preço ausente é preenchido. O projeto pode ser executado novamente com outro arquivo e outra data de referência.

O [resultado do case](resultados/2026-09-22/README.md) apresenta as 20 ações, os retornos, a alternativa de janela e as premissas. O comando único abaixo gera automaticamente um novo README de resultado, com a média correta na primeira linha, para cada nova extração.

O [mapa da documentação](docs/README.md) define a organização proposta para os guias da ferramenta. O [artigo modelo de metodologia](docs/metodologia.md) explica as regras implementadas, com diagrama do processo, exemplo real, controles e instruções de conferência. A seção [Documentação](https://ranking.lucaspsm.com/documentacao) publica oito artigos a partir dos arquivos Markdown do repositório, com busca e navegação por assunto. A auditoria continua disponível por execução. Ela detalha as exclusões por tipo, o alcance dos alertas e oferece manifestos do tratamento, decisões e evidências B3 das duas janelas. Veja [como conferir os derivados](docs/auditoria.md).

## Interface para avaliar e reproduzir o case

O site [ranking.lucaspsm.com](https://ranking.lucaspsm.com) exibe o resultado de referência, os alertas e a metodologia. Na seção **Teste com uma nova extração**, qualquer avaliador pode enviar outro CSV da Economatica no mesmo esquema de nove colunas e informar uma data de referência. O site executa **este mesmo `weekly_ranking.py`**, gera um link separado para a nova análise e mostra a etapa em andamento. Uma semana terminada antes de sexta exige revisão das datas e confirmação explícita no formulário. Essa decisão fica na auditoria e no registro do envio; não dispensa os outros controles. O resultado de referência não muda quando alguém envia um arquivo. Os retornos e a média são calculados em Python; o navegador apenas apresenta os valores produzidos.

O arquivo enviado pode ter até **10 MB**. A fila aceita uma análise ativa e duas aguardando, com até três envios por hora por origem. Arquivos brutos são removidos após 24 horas e resultados de teste após sete dias. O CSV original e os arquivos brutos da B3 não ficam disponíveis para download público. O link da análise é aleatório e não há lista pública de envios: quem possui o link pode ver o resultado derivado enquanto ele existir. A aplicação não exige login, portanto não use o formulário para dados que não possam ser processados nessa demonstração pública.

Para executar a interface localmente:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements-web.txt
.venv\Scripts\python -m uvicorn webapp.server:app --host 127.0.0.1 --port 8000
```

Em outro terminal, inicie o worker (`.venv\Scripts\python -m webapp.worker`). Abra `http://127.0.0.1:8000`. No Linux, substitua `.venv\Scripts\python` por `.venv/bin/python`. A aplicação usa `runtime-data/` por padrão; `RANKING_DATA_DIR` escolhe outro diretório. Para recriar somente a série diária de apresentação do resultado fixo, sem incluir o CSV bruto no Git:

```powershell
python scripts/create_featured_daily.py --input "CAMINHO\economatica.csv"
```

As saídas `resultados/2026-09-22/daily_context.json` são apenas contexto visual. Suas lacunas permanecem vazias e não alteram o top 20. A implantação Docker com Traefik e as instruções de operação estão em [deploy/README.md](deploy/README.md).

### Páginas da interface

- `/`: ranking de referência, gráficos de preços/retornos diários e contexto da amostra.
- `/documentacao`: entrada dos guias, busca e navegação entre oito assuntos.
- `/documentacao/{assunto}`: artigo versionado, índice de seções e links relacionados.
- `/metodologia`: auditoria da referência, explicação do processo, comparação visual das janelas, universo, exclusões, exemplo de cálculo e arquivos da execução de referência.
- `/nova-analise`: envio de uma extração, conferência da semana e informações de formato, limites e retenção.
- `/analise/{id}`: acompanhamento de uma execução independente; ao terminar, mostra seu ranking e seus gráficos.
- `/analise/{id}/metodologia`: metodologia com datas, contagens, alertas e downloads específicos daquela execução. Não reutiliza as contagens do case.

O formulário sugere a referência a partir das datas presentes no CSV, incluindo datas no formato `DD/MM/AAAA`; o usuário deve conferir a semana indicada antes de enviar. A API continua sendo responsável pela validação do esquema e pela execução do pipeline. Uma falha fica explícita na página da análise, e os resultados enviados não aparecem em uma lista pública.

## Gerar um novo ranking

```powershell
python weekly_ranking.py --input "CAMINHO\economatica.csv" --reference-date 2026-09-22 --output-dir "runs\semana-2026-09-22"
```

O programa identifica a semana-calendário anterior, usa o último fechamento antes dela e o último fechamento da semana como pontas do retorno principal. Calcula também uma interpretação alternativa, do primeiro ao último fechamento dentro da semana. Obtém os arquivos oficiais da B3 se não estiverem em `data/reference/`; com eles já guardados, use `--offline`. Se o último dia com cotação for anterior à sexta-feira, para e exige revisão; `--allow-nonfriday-end` registra a aceitação expressa de uma semana encurtada. Uma queda acentuada de cobertura nas datas escolhidas também impede um resultado silencioso. As verificações de preços, duplicatas, classificação, ordenação e média são automáticas; a conferência manual foi feita apenas no desenvolvimento.

O retorno é `fechamento ajustado final / fechamento ajustado inicial - 1`, sempre com preços da Economatica. Não há filtro de liquidez. Os 20 maiores retornos são ordenados sem arredondamento, com ticker como desempate, e a média aritmética é arredondada só para exibição. O resultado da semana de 14 a 18/09/2026 foi **17,78%** na janela principal (11 a 18/09) e **15,93%** na alternativa (14 a 18/09). Os dois top 20 têm 16 ações em comum.

## Executar somente o tratamento

```powershell
python etl.py --input "CAMINHO\economatica.csv" --reference-date 2026-09-22 --output-dir "runs\extracao-2026-09-22"
```

Para outra semana, informe **novo CSV, nova data e nova pasta de saída**. A data é usada para identificar registros posteriores a ela; não recorta o arquivo. Use `--coverage-drop 0.25` para ajustar o limite de alerta de queda de cobertura (25% por padrão). Para comparar com uma execução anterior:

```powershell
python etl.py --input "CAMINHO\nova_extracao.csv" --reference-date 2026-09-29 --output-dir "runs\extracao-2026-09-29" --baseline-summary "runs\extracao-2026-09-22\quality_summary.json"
```

O programa espera **as nove colunas e sua ordem originais**. Detecta UTF-8 ou Windows-1252, usa vírgula como separador, ponto decimal e `-` como ausência. Uma alteração de esquema ou separador interrompe a execução com erro. Linhas malformadas, por sua vez, permanecem representadas na base normalizada, com os campos recuperáveis e um alerta `MALFORMED_ROW`.

### Cadastro oficial da B3: classificação por snapshot

O tratamento aceita o **ZIP diário original BVBG.028.02**, obtido na [Pesquisa por Pregão da B3](https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/historico/boletins-diarios/pesquisa-por-pregao/pesquisa-por-pregao/). Para a execução de exemplo, foi usado o cadastro do último pregão da semana anterior à referência: [IN260918.zip](https://www.b3.com.br/pesquisapregao/download?filelist=IN260918.zip,). O arquivo contém outro ZIP e dois XMLs; o leitor escolhe a última versão pelo nome temporal do XML e registra o membro escolhido. Faz leitura em fluxo, sem carregar os mais de 150 mil instrumentos na memória. Cada nova semana requer escolher explicitamente o snapshot apropriado, baixá-lo e fornecê-lo no comando. O programa não faz consulta ao cadastro vigente hoje para classificar retrospectivamente uma semana passada.

```powershell
python etl.py --input "CAMINHO\economatica.csv" --reference-date 2026-09-22 --output-dir "runs\com-b3" --b3-registry "data\reference\IN260918.zip" --overrides "overrides\approved.csv"
```

O cruzamento usa ticker normalizado no segmento de ações e mercado à vista (`Sgmt=1`, `Mkt=10`), preserva todas as linhas e sinaliza códigos sem correspondência. A combinação `SctyCtgy`, `Desc` e `CFICd` é usada para distinguir ação ON, ação PN, unit, BDR e ETF. Códigos de categoria novos, espécies contraditórias e múltiplos registros conflitantes ficam sem resolução automática. **Uma linha anterior ao snapshot não recebe sua classificação posterior**: fica com `classification_source=snapshot_posterior` até ser examinada com fontes da época. A B3 define [ações ON e PN](https://www.b3.com.br/pt_br/produtos-e-servicos/negociacao/renda-variavel/acoes.htm), [units](https://b3.com.br/pt_br/produtos-e-servicos/negociacao/renda-variavel/certificado-de-deposito-de-acoes-units.htm) e [BDRs](https://borainvestir.b3.com.br/tipos-de-investimentos/renda-variavel/acoes/qual-a-diferenca-entre-acoes-e-bdrs/). O mapeamento numérico das quatro categorias utilizadas foi validado nos registros e descrições do próprio snapshot; se o layout/domínio mudar, o código desconhecido não será forçado para uma categoria existente. O CSV tabular de cadastro ainda é aceito como entrada legada, com `TckrSymb`, `SctyCtgyNm` e `RptDt`, mas a execução documentada usa o ZIP oficial.

O programa valida a data `RptDt` contida no XML e rejeita snapshot posterior à referência. Mais de sete dias de diferença gera alerta. O manifesto registra URL da fonte, hash SHA-256 do ZIP, nome do XML, data, número de registros e tickers sem correspondência. O arquivo bruto B3 fica fora do Git. O rótulo identifica o instrumento **no snapshot escolhido**; não é prova de que sua classificação era a mesma em cada linha histórica da Economatica. Ausência de ticker no cadastro da data não prova inexistência ou falta de negociação. A [série histórica COTAHIST da B3](https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/historico/mercado-a-vista/cotacoes-historicas/) pode ser usada como checagem independente de negociação e espécie, mas seus preços brutos não substituem os preços ajustados da Economatica.

Sem B3, o **ETL geral** mantém seus rótulos de sufixo como provisórios. A decisão específica do universo semanal é feita depois, por `ranking_universe.py`, com confirmação datada para ações elegíveis.

### Resolver a classificação nas datas de preço

Após o ETL, informe explicitamente as duas datas de preço. A busca automática obtém o COTAHIST diário das duas datas e o cadastro B3 da data final; se ainda houver código sem tipo confirmado na data inicial, tenta também o cadastro inicial. Arquivos guardados em `data/reference/` não são sobrescritos. O manifesto registra URL, data e SHA-256 do arquivo baixado; para o cadastro aninhado, registra também o hash do ZIP interno. O cache do cadastro parseado usa o hash do conteúdo interno e do código. Isso evita reler um XML idêntico quando a B3 entrega um ZIP externo com metadados diferentes. O modo `--offline` reproduz a análise com os ZIPs já guardados.

```powershell
python resolve_period.py --normalized "runs\com-b3\normalized.csv" --start-date 2026-09-11 --end-date 2026-09-18 --output-dir "runs\classificacao-2026-09-18" --reference-dir "data\reference" --offline
```

Para fornecer os arquivos oficiais por conta própria, sem a etapa de busca:

```powershell
python classify_period.py --normalized "runs\com-b3\normalized.csv" --start-date 2026-09-11 --end-date 2026-09-18 --output-dir "runs\classificacao-manual" --b3-file "data\reference\IN260918.zip" --cotahist-file "data\reference\COTAHIST_D11092026.ZIP" --cotahist-file "data\reference\COTAHIST_D18092026.ZIP"
```

O classificador detalhado usa apenas evidência **da data exata do preço**: código, mercado, especificação e ISIN do COTAHIST; categoria, descrição, CFI e ISIN do cadastro. Ele mantém `classification_gate_passed` como medida de completude da **catalogação detalhada** dos candidatos. A etapa seguinte decide o universo do case com `ranking_gate_passed`. Uma execução com decisão de ranking pendente grava relatórios e termina com código `3`.

### Regra explícita do universo do case

O universo é **ação ordinária ou preferencial brasileira**, incluindo classes de preferenciais, com fechamento positivo nas duas datas informadas. Essa definição interpreta “ações” literalmente: [BDR é certificado depositário](https://www.b3.com.br/pt_br/produtos-e-servicos/negociacao/renda-variavel/brazilian-depositary-receipts-bdrs-nao-patrocinados-nivel-i.htm) e [unit é certificado que reúne valores mobiliários](https://b3.com.br/pt_br/produtos-e-servicos/negociacao/renda-variavel/certificado-de-deposito-de-acoes-units.htm); nenhum dos dois é uma ação individual ON/PN. O [manual de negociação da B3](https://sistemasweb.b3.com.br/normativos/MPODENEGOCIACAO20260525.pdf) define os códigos `3` (ON), `4` (PN), `5` a `8` (classes PN), `31` a `40` (BDR) e `11` a `30` (conjunto de outros produtos, incluindo units e fundos).

O programa lê **o código completo**, com prefixo alfanumérico de quatro caracteres: `B3SA3` é ON e `B1CS34` segue a faixa de BDR. Códigos `11` a `30` e formatos fora dessas faixas recebem `outro`, sem fingir distinguir unit, ETF e fundos somente pelo final. Um sufixo fracionário, como `F`, não é confundido com a ação de lote padrão. Para **incluir** uma ON/PN no ranking, a espécie precisa ser confirmada em fonte oficial nas **duas datas de preço**. BDR e `outro` são excluídos pela regra do código; a espécie detalhada pode ficar desconhecida. Qualquer conflito de preço duplicado, ISIN ou classificação oficial leva a `revisar` e impede o ranking. Uma fonte oficial que indique ação fora do padrão também leva a revisão, evitando exclusão silenciosa.

Essa é uma regra replicável para o **universo deste ranking**, não um cadastro histórico completo de cada instrumento da extração. Tickers sem os dois fechamentos positivos permanecem em `candidate_exclusions.csv`. Nenhuma linha da base normalizada é apagada e os preços da B3 não substituem os preços ajustados da Economatica.

As saídas são `period_classification.csv` (resultado detalhado por código e data), `b3_evidence.csv` (evidências oficiais), `candidate_exclusions.csv` (códigos sem os dois preços e motivo), `ranking_universe.csv` (decisão `incluir`, `excluir` ou `revisar`, com fundamento), `ranking_universe_summary.json`, `classification_summary.json` e `classification_manifest.json`. A busca automática acrescenta `source_acquisition.json`, inclusive falhas de acesso. Esta etapa não calcula retornos nem escolhe as datas do ranking.

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

**Códigos de qualidade:** `MISSING_VALUE`, `INVALID_NUMBER`, `INVALID_DATE`, `FUTURE_DATE`, `INVALID_TICKER`, `MALFORMED_ROW`, `DUPLICATE_EXACT`, `DUPLICATE_CONFLICT`, `NONPOSITIVE_PRICE`, `NEGATIVE_AMOUNT`, `LOW_ABOVE_HIGH`, `OUTSIDE_DAILY_RANGE`, `VOLUME_PRICE_DIVERGENCE`, `DATE_WITHOUT_QUOTES`, `COVERAGE_DROP`, `EXTRACTION_COVERAGE_DROP`, `B3_TICKER_UNMATCHED`, `B3_CATEGORY_UNRESOLVED`, `B3_STALE_SNAPSHOT`, `B3_SNAPSHOT_AFTER_TRADE_DATE` e `INSTRUMENT_AMBIGUOUS`. `MISSING_VALUE` é informativo: um feriado ou um ativo suspenso pode ter valores ausentes sem representar erro. `VOLUME_PRICE_DIVERGENCE` também é informativo: volume bruto e quantidade/preço ajustados podem estar em bases diferentes, além de haver arredondamento.

## Achados da extração recebida

Na execução com referência em **22/09/2026**, sem cadastro B3: 4.828 linhas preservadas, 478 códigos, 1.278 fechamentos ausentes, 43 registros em 02/01/1920 sem preço, nove linhas históricas com quantidade e volume mas sem preço e nenhuma chave ticker–data duplicada. Há 11 ocorrências de valor fora do intervalo diário no arquivo inteiro, inclusive preços médios. A data 07/09/2026 contém linhas mas nenhum fechamento positivo; 21/09/2026 pertence à semana corrente em relação à data de referência. Esses fatos são diagnósticos, **não regras fixas para futuras extrações**. O ETL não presume causas de movimentos nem moeda adicional além do texto da fonte.

Com o snapshot B3 de **18/09/2026**, o cruzamento localizou **473 dos 478** códigos da extração. `NEMO5`, `NEMO6`, `OIBR3`, `OIBR4` e `RNEW11` ficaram sem correspondência nesse snapshot; nenhum deles apresenta fechamento positivo na parte recente do arquivo. Eles permanecem na base e no manifesto para revisão. Essa cobertura não é uma regra para outras datas nem uma decisão de elegibilidade. Para nova extração, usar snapshot datado da própria análise e conferir as mesmas contagens antes de avançar ao ranking.

Na resolução específica de **11/09 e 18/09**, 320 códigos tinham fechamento positivo nas duas datas. Todos os **320 foram confirmados** por evidência datada: 238 ações ON, 70 PN, 9 units e 3 BDRs. Pela regra explícita do universo, **308 ações entram** e **12 instrumentos ficam fora** (9 units e 3 BDRs), sem pendências de revisão nessa execução. Os demais 158 aparecem em `candidate_exclusions.csv` com motivo. Isso valida a definição do universo para essas datas, **não** a seleção final dos 20 papéis.

### Conferência independente com o COTAHIST

Para verificar a espécie ON/PN/UNT dos papéis **que efetivamente negociaram** no dia do snapshot, use o [COTAHIST diário da B3](https://bvmf.bmfbovespa.com.br/InstDados/SerHist/COTAHIST_D18092026.ZIP). O programa lê `CODNEG`, `TPMERC` e `ESPECI` conforme o [layout oficial](https://www.b3.com.br/data/files/33/67/B9/50/D84057102C784E47AC094EA8/SeriesHistoricas_Layout.pdf), valida a data e grava contagens, hashes e eventuais divergências:

```powershell
python verify_b3.py --normalized "runs\com-b3\normalized.csv" --cotahist "data\reference\COTAHIST_D18092026.ZIP" --snapshot-date 2026-09-18 --output "runs\com-b3\cotahist_check.json"
```

Na execução do case, **326** códigos classificados como ON/PN/unit também constavam no COTAHIST de 18/09: 244 ON, 73 PN e 9 units; **nenhuma divergência**. Os demais não foram refutados: o COTAHIST só contém ativos negociados naquele pregão. O relatório é uma verificação adicional; não altera `normalized.csv` nem a classificação.

## Revisão opcional de exceções

`review_exceptions.py` lista códigos ambíguos ou não resolvidos, sem conexão de rede por padrão:

```powershell
python review_exceptions.py --input "runs\extracao-2026-09-22\normalized.csv" --output "runs\extracao-2026-09-22\exceptions_for_review.csv" --limit 25
```

Se desejar sugestões da Groq, informe um modelo compatível por `--model` e defina `GROQ_API_KEY` no ambiente. Opcionalmente forneça `--official-evidence` com colunas `ticker,official_reference_url,official_excerpt`. Sem evidência oficial, o script só aceita sugestão de próximo passo, não de categoria. O resultado permanece `pendente_validacao_humana`; para passar a valer, é preciso verificar a fonte e registrar uma aprovação em `overrides/approved.csv`. Indisponibilidade ou limite da Groq não impede o ETL principal.

## Testes e reprodução

Instale as dependências de desenvolvimento e execute a suíte no ambiente virtual, a partir da raiz:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements-dev.txt
.venv\Scripts\python -m unittest discover -s tests -v
```

No Linux/macOS, use `python3 -m venv .venv` e `.venv/bin/python` nos comandos seguintes. O [guia de desenvolvimento](docs/desenvolvimento.md) explica testes por área, regressão opcional e execução local de API/worker.

Os testes sintéticos não exigem rede nem arquivos externos. Para incluir a verificação de regressão com a extração original, defina `ECONOMATICA_CASE_CSV` com seu caminho antes de rodá-los. Essa verificação exige 4.828 linhas rastreáveis e compara byte a byte as saídas de duas execuções. O arquivo bruto, o PDF e os resultados locais ficam fora do repositório público.
