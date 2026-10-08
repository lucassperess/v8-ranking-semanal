# Desenvolvimento e roteiro de leitura

Este guia permite localizar o cálculo, preparar um ambiente e verificar mudanças sem depender do histórico da conversa. A [documentação de uso](como-usar.md) atende quem explora a interface; este artigo atende quem mantém o código.

## Roteiro recomendado

1. [README principal](../README.md): objetivo, resultado de referência e comandos de reprodução.
2. [Decisões](decisoes.md) e [metodologia](metodologia.md): definições e limites que governam o cálculo.
3. [Arquitetura](sistema.md): caminho do envio ao resultado.
4. [weekly_ranking.py](../weekly_ranking.py): siga `run`, `choose_week`, `rank_pair` e a geração do relatório.
5. Módulos abaixo: acompanhe as entradas e saídas de cada etapa.
6. [Testes](../tests): exemplos dos contratos e comportamentos esperados.
7. [Resultado do case](../resultados/2026-09-22/README.md): exemplo histórico, com arquivos derivados versionados.

## Mapa técnico

| Arquivo ou pasta | Responsabilidade | Teste principal |
| --- | --- | --- |
| `etl.py` | Ler esquema, normalizar campos, preservar linhas, registrar qualidade e manifesto | `test_etl.py` |
| `b3_registry.py` | Interpretar cadastro B3 e calcular identificações de conteúdo | `test_b3_registry.py` |
| `resolve_period.py` | Obter e reaproveitar fontes datadas para as pontas | Casos de resolução em `test_classify_period.py` |
| `classify_period.py` | Reunir evidências oficiais e classificação por instrumento/data | `test_classify_period.py` |
| `ranking_universe.py` | Decidir incluir, excluir ou revisar para ON/PN | `test_ranking_universe.py` |
| `weekly_ranking.py` | Escolher janela, ordenar retornos e produzir média/relatórios | `test_weekly_ranking.py` |
| `verify_b3.py` | Conferência adicional de classificação com COTAHIST | `test_verify_b3.py` |
| `review_exceptions.py` | Revisão opcional de exceções, separada da rotina principal | `test_review_exceptions.py` |
| `webapp/server.py`, `store.py`, `worker.py` | API, persistência/fila, processamento e limpeza | `test_webapp.py` cobre API, fila e apresentação; não é teste integral da operação na VPS |
| `webapp/presentation.py` | Adaptar derivados e calcular contexto visual em Python | `test_webapp.py` |
| `webapp/documentation.py`, `docs/` | Renderizar artigos Markdown versionados e índice de busca | `test_webapp.py` |
| `webapp/static/` | Interface HTML/CSS/JavaScript | Conferência no navegador das páginas afetadas |
| `scripts/create_featured_daily.py` | Preparar séries visuais da demonstração a partir do bruto | Conferir saídas e lacunas ao atualizar a demonstração |
| `scripts/export_audit.py` | Exportar evidências derivadas de uma execução para a demonstração correspondente | Confere assinaturas e recusa versões conflitantes antes da cópia |
| `deploy/` | Docker, Traefik e operação da aplicação | Verificação de saúde e HTTPS após publicação autorizada |

Nem toda linha do projeto possui teste automático específico. Use a tabela para localizar verificações existentes, sem pressupor cobertura integral.

## Preparar o ambiente

O núcleo de tratamento/classificação/ranking usa Python 3.11+ e a biblioteca padrão. Para trabalhar na interface e executar todos os testes, instale as dependências de desenvolvimento, que incluem as da aplicação.

### Windows / PowerShell

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements-dev.txt
.venv\Scripts\python -m unittest discover -s tests -v
```

### Linux / macOS

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m unittest discover -s tests -v
```

`requirements-web.txt` instala o necessário para servir o site. `requirements-dev.txt` inclui também `httpx`, utilizado nos testes da API. Os comandos acima usam o executável da pasta virtual explicitamente, sem exigir ativação do ambiente.

## Executar a interface local

No Windows, a partir da raiz, em um terminal:

```powershell
.venv\Scripts\python -m uvicorn webapp.server:app --host 127.0.0.1 --port 8000
```

Em outro terminal:

```powershell
.venv\Scripts\python -m webapp.worker
```

Abra `http://127.0.0.1:8000`. No Linux/macOS, use `.venv/bin/python` nos mesmos comandos. A demonstração pode ser consultada sem worker; novos envios precisam dele.

O diretório padrão de estado local é `runtime-data/`. A variável `RANKING_DATA_DIR` permite outro diretório. A operação da VPS e suas configurações ficam em [deploy/README.md](../deploy/README.md).

## Reproduzir o pipeline

### Contexto opcional de cada envio

O worker libera o ranking antes de chamar `context_pipeline.generate`. A coleta utiliza as empresas do top das duas janelas e tem prazo próprio de até quinze minutos após o cálculo do ranking. Uma falha do contexto não invalida o resultado financeiro. Após verificar cada empresa, o coletor publica um snapshot atômico em `context/progress.json`, vinculado à assinatura da apresentação. A API pode retornar `partial`, com `processing`, `completed_companies` e `total_companies`; o navegador consulta o andamento e atualiza o ticker selecionado quando ele fica pronto. O snapshot contém apenas os resultados concluídos e fontes públicas, sem corpos integrais ou credenciais. Se a coleta for interrompida, os textos concluídos permanecem consultáveis. Referências de mercado e os quatro derivados auditáveis completos são publicados ao final do lote; o snapshot não substitui o manifesto final. O replay não regrava o progresso da execução original.

Configure `OPENAI_API_KEY` e `TAVILY_API_KEY` no ambiente do worker ou no `.env` local, fora do Git. `CONTEXT_ENABLED=0` desativa a coleta. O modelo desta versão é `gpt-6-luna`. Chaves e respostas privadas não chegam ao navegador.

Para uma execução que já contém `presentation.json`, classificações e rankings:

```powershell
.venv/Scripts/python -m context_pipeline.generate --run-dir "runs/minha-analise"
.venv/Scripts/python -m scripts.audit_run_context --run-dir "runs/minha-analise"
.venv/Scripts/python -m context_pipeline.generate --run-dir "runs/minha-analise" --replay
```

O primeiro comando consulta fontes externas e pode consumir créditos; recusa sobrescrever um contexto concluído. O segundo reconcilia os números com suas entradas salvas. O terceiro usa exclusivamente respostas e evidências guardadas em `context/private/`, grava uma pasta `context/replay-*` e compara os textos e indicadores com a geração original. Uma busca futura não garante as mesmas notícias ou palavras.

A identificação exige correspondência entre ticker, ISIN da classificação datada e empresa no cadastro B3. A busca considera a semana e até 90 dias anteriores. Para leitura pela IA, seleciona até seis textos de 3.000 caracteres por empresa, priorizando documentos oficiais. Isso não constitui um catálogo completo das notícias de todos os dias.

Trechos, datas e identidade recebem conferência automática; acontecimentos válidos passam por segunda leitura por IA. Sem acontecimentos válidos, o resumo financeiro pode ser produzido pelas regras Python, sem a segunda chamada ao modelo. Resultados financeiros anteriores ao fechamento servem como antecedentes, sem comprovar a causa da oscilação. A reserva conservadora padrão para chamadas ao modelo é US$ 6 por geração, configurável por execução; não corresponde ao valor faturado e não inclui Tavily. A divisão entre empresas e temas de mercado está descrita na seção de orçamento protegido abaixo.

Os arquivos `context/{company,market,audit,manifest}.json` são derivados públicos. As respostas completas e documentos ficam privados. O manifesto vincula o contexto ao `presentation.json`; datas e ativos são conferidos na API. O teste `python -m scripts.validate_context_replication --output runs/teste-contexto` usa preços e classificações artificiais, que não devem ser publicados como dados reais.

Exemplo da referência, com o CSV original disponível fora do Git:

```powershell
.venv\Scripts\python weekly_ranking.py --input "CAMINHO\economatica.csv" --reference-date 2026-09-22 --output-dir "runs\reproducao-2026-09-22"
```

Para uma nova extração, substitua arquivo, referência e diretório. Fontes oficiais ausentes podem ser baixadas. `--reference-dir` escolhe a pasta de fontes; `--offline` impede novas buscas e só permite concluir se as evidências guardadas forem suficientes.

Não é possível reproduzir integralmente o case apenas com os derivados do Git: o CSV bruto e as fontes necessárias também são entradas. Veja [auditoria](auditoria.md) para o que está disponível publicamente.

Para complementar uma demonstração com evidências da **mesma execução**, use:

```powershell
.venv\Scripts\python -m scripts.export_audit --run-dir "runs\reproducao-2026-09-22" --destination "resultados\2026-09-22"
```

O destino deve existir e conter o mesmo `ranking_report.json`. O exportador confere as evidências e recusa arquivos existentes com conteúdo diferente antes de copiar. Ele não publica bruto nem altera retornos, README editorial ou séries diárias. Uma reprodução com outra versão de código pode gerar outro relatório: nesse caso, use outro destino para a nova demonstração, sem substituir o histórico.

## Testes e limites da verificação

A suíte padrão utiliza casos sintéticos e fontes locais artificiais. Não depende de Groq, credenciais ou rede. Testes que precisam da extração original são opcionais e podem aparecer como ignorados quando ela não estiver configurada.

Para habilitar a regressão do tratamento com o CSV original no PowerShell:

```powershell
$env:ECONOMATICA_CASE_CSV = "CAMINHO\economatica.csv"
.venv\Scripts\python -m unittest discover -s tests -v
```

No Linux/macOS:

```bash
ECONOMATICA_CASE_CSV="/caminho/economatica.csv" .venv/bin/python -m unittest discover -s tests -v
```

Essa regressão confere o tratamento e sua repetição; não equivale a testar downloads reais da B3 ou executar uma análise pública completa.

Para conferir a área web isoladamente:

```powershell
.venv\Scripts\python -m unittest discover -s tests -p "test_webapp.py" -v
```

Após editar, rode também `git diff --check`. Mudanças em dados ou regras precisam de testes com casos relevantes; mudanças de layout precisam de inspeção no navegador. Conferir a média histórica não prova, sozinho, que novas extrações funcionem.

## Manutenção da documentação

As oito páginas de uso são publicadas a partir de uma lista explícita em `webapp/documentation.py`. Este roteiro e o registro de decisões são documentação técnica no GitHub; não foram adicionados ao menu público nesta etapa.

Ao mudar uma regra, atualize a decisão, o artigo aplicável e o teste correspondente. Ao mudar uma saída, atualize seus consumidores e o dicionário de campos. Ao documentar limitações, diferencie funcionamento atual e melhorias planejadas.

## Organização da interface e verificações automáticas

O cabeçalho tem uma única fonte em `webapp/templates/header.html`. `webapp/pages.py` compõe as páginas no servidor e marca a navegação ativa. Preserve os identificadores usados pelo JavaScript ao editar esse template.

- `styles.css`: estilos compartilhados, ranking e formulário de nova análise.
- `mobile.css`: navegação móvel, ranking compacto, controles por toque, índices persistentes e tabelas com rótulos por campo. Confira a ordem dos estilos na página ao editar regras.
- `summary.css`: seletor global, resumo integrado e comparação das médias, incluindo a composição móvel.
- `context.css` e `context.js`: apresentação do contexto empresarial, referências de mercado e acontecimentos.
- `mobile-dashboard.js`: aviso inicial, dispensa no navegador e interação móvel com o dashboard.
- `documentation.css`: navegação e artigos da documentação.
- `audit.css`: apresentação da auditoria de uma execução.

Edite a regra existente antes de acrescentar outra para o mesmo seletor e propriedade no mesmo contexto. HTML, CSS e JavaScript são formatados com Prettier; Node.js 22 é uma ferramenta de desenvolvimento, sem necessidade no servidor de produção.

```powershell
npm ci --ignore-scripts
npm run format
npm run format:check
npm run check:frontend
.venv\Scripts\python -m ruff check .
.venv\Scripts\python -m scripts.verify_artifacts
```

No Linux/macOS, use `.venv/bin/python`. O verificador da interface confere sintaxe JavaScript, interpretação do CSS e declarações sobrescritas no mesmo contexto. Ruff verifica erros essenciais de Python. A conferência dos derivados verifica assinaturas, retornos a partir das pontas, ordenação, top 20 e médias das duas janelas; ela não substitui uma reprodução a partir do CSV bruto.

O workflow `.github/workflows/checks.yml` executa essas verificações em cada envio de código e pull request. Os testes Python rodam em Linux (3.11 e 3.12) e Windows (3.11); a formatação e a sintaxe da interface rodam em Linux com Node 22. A regressão com o bruto original permanece opcional e é ignorada no CI quando a entrada não está disponível.

Uma execução aprovada no CI não verifica downloads reais da B3, o comportamento visual no navegador nem a operação da VPS. Essas conferências continuam necessárias quando a mudança afeta essas áreas. O workflow não publica automaticamente o site.

## Revisão e teste de novas extrações

`webapp/review.py` reaproveita `etl.transform` em lotes e `weekly_ranking.select_week` para conferir datas e cobertura antes da fila. `POST /api/analyses` responde 409 com `short_week_review` quando é necessária revisão, sem manter upload ou criar job. O cliente apresenta datas e exige checkbox; no segundo envio, `allow_nonfriday_end`, `reviewed_sha256` e `reviewed_reference_date` vinculam a aceitação à entrada. A API reconfere o arquivo.

A fila migra bancos existentes acrescentando opções com padrão vazio. O worker passa `--allow-nonfriday-end` somente quando autorizado e grava `analysis_request.json`. Ele executa novamente todos os controles. `submission_details` confere a compatibilidade do registro com o relatório. Mensagens de falha recebem orientação por categoria; a mensagem original permanece visível.

`tests/test_replication.py` executa o worker em subprocesso real com extrações e fontes B3 **artificiais e locais**, sem rede. Os fixtures não devem ser publicados como evidência oficial. A API também é conferida com duas entradas distintas, migração de banco antigo, confirmação invalidada e bloqueios. Uma extração real diferente deve ser conferida em desenvolvimento para verificar aquisição das fontes e apresentação por HTTPS.

### Motivos de perdas na coleta de contexto

Novas gerações registram etapas e resultados em `context/diagnostics/{codigo}.json`,
inclusive para os temas macroeconômicos. O arquivo é atualizado durante a coleta:
se o processo for encerrado, a última etapa iniciada continua registrada.
Na conclusão, `context_audit.json` inclui esses registros em `processing_diagnostics`.
O registro geral `run.json` identifica falhas de identidade, catálogo CVM,
leitura financeira e indicadores de mercado.

Os registros distinguem busca vazia, falha HTTP (com o status, sem o corpo ou
endereço da resposta), ausência de texto legível, limites de seleção/leitura,
ausência de propostas da IA, rejeição pela verificação e rejeição na segunda
leitura. `event_index` identifica a posição na proposta original da IA.

| Motivo | O que aconteceu |
| --- | --- |
| `local_budget_exhausted` | O limite interno impediu a chamada; não significa saldo da API esgotado. A reserva necessária e a restante são estimativas, não gastos faturados. |
| `quote_not_found` | A citação proposta não corresponde literalmente ao texto lido. |
| `financial_source_used_as_event` | A IA citou o antecedente financeiro no campo destinado a acontecimentos. |
| `unknown_source_id` | A proposta citou uma fonte que não foi fornecida para verificar acontecimentos. |
| `publication_date_not_verified` | O trecho não confirma a data de publicação exigida para aquela fonte. |
| `model_review_rejected` | A segunda leitura recusou o acontecimento já verificado pela rotina Python. |
| `model_proposed_no_events` | A IA respondeu, mas não propôs acontecimentos; não é prova de que eles não existem. |
| `no_selected_sources` | Não havia textos selecionados para iniciar a geração. Consulte as etapas anteriores para distinguir busca vazia de falha de consulta. |

O estado de execução também distingue serviço desativado, credenciais ausentes,
prazo excedido, encerramento do servidor e falha do processo de contexto.
Mensagens brutas de exceções, credenciais e corpos de documentos não são copiados
para os diagnósticos públicos. Propostas e respostas já arquivadas continuam na
coleta privada para conferência mais detalhada.

O replay grava diagnósticos no seu próprio diretório, preservando os da geração
original. Ele registra o que ocorreu durante a reprodução; não reconstrói
automaticamente o orçamento ou uma falha de rede de uma execução antiga.
Os registros são acrescentados à auditoria, sem mudar preços, regras de aceitação,
textos empresariais ou indicadores. Esta etapa, isoladamente, não aumenta a cobertura.

### Leitura de acontecimentos e correção limitada da proposta

O contrato `run-context-1.1` exige citações contínuas e literais. A IA não deve
inserir `[...]` para unir trechos separados. Os identificadores permitidos para
acontecimentos são enviados em `event_source_ids`; resultados trimestrais
continuam no campo de antecedentes financeiros, sem serem tratados como fatos
ocorridos na semana.

Para documentos oficiais da CVM, a data de entrega confirmada pelos metadados
é a referência de publicação. Não é necessário encontrar essa data no corpo do
PDF. Isso não muda a data do acontecimento: uma decisão anterior pode ser
divulgada durante a semana. Para notícias web, permanece necessária a data
literal no texto, com dia, mês e ano.

Uma proposta inválida pode receber uma única tentativa de correção sem novas
buscas, usando os mesmos textos e os motivos da rejeição. Uma proposta vazia
também pode ser revista quando há documentos oficiais selecionados como
acontecimentos datados. Eventos inicialmente válidos são preservados. A saída
corrigida passa novamente pela verificação Python e pela segunda leitura da IA;
não há flexibilização das regras de aceitação. A tentativa usa o limite interno
existente e pode ser impedida por orçamento ou prazo.

`decision-{codigo}.json` guarda a proposta inicial e `repair_feedback`, além da
proposta final. Os diagnósticos distinguem rejeições iniciais, tentativa de
correção e resultado final. O contrato de prompt faz parte da identidade da
reprodução: respostas de versões diferentes não são misturadas. Para reproduzir
uma geração antiga, use a versão de código e prompt registrada naquela geração.

Em 08/10/2026, uma conferência local com chamadas novas à OpenAI e os mesmos
textos arquivados recuperou acontecimentos nos quatro casos escolhidos:

| Ação | Informação recuperada |
| --- | --- |
| RCSL3 | Convocação de assembleia para votar um grupamento; não equivale a grupamento aprovado. |
| CASH3 | Divulgação de aumento de capital relacionado ao exercício de opções; a reunião ocorreu em 08/09, antes da semana analisada. |
| WDCN3 | Proposta vinculante para aquisição da Teki, ainda sujeita às condições descritas no documento. |
| MEAL3 | Assembleia de debenturistas e esclarecimento de 18/09 sobre ausência de acordo firmado. O documento divulgado em 20/09 permanece marcado como posterior ao último fechamento e fora da interpretação do retorno semanal. |

Não houve novas consultas de notícias, Tavily ou CVM nesse teste. Os quatro casos
passaram pela verificação e revisão, mas não medem a cobertura de todo o ranking
nem comprovam a causa das variações. A soma das reservas locais estimadas foi
US$ 0,614656; não é uma medição da cobrança efetiva da OpenAI. Os insumos privados
e respostas ficaram em `runs/context-step2-2026-10-08/`, fora do Git. A conferência
automatizada resultou em 109 testes: 108 aprovados e um ignorado. Esta etapa foi
validada localmente; sua conclusão não declara publicação na produção.

### Seleção das fontes de contexto

O contrato `run-context-1.2` separa coleta, seleção e geração em
`collect_issuer_sources` e `prepare_issuer`. `context_pipeline/selection.py`
filtra páginas sociais, cotações, calendários genéricos, URLs inválidas,
duplicatas e resultados sem identificação explícita da empresa. O texto
extraído também precisa identificar a empresa antes de ocupar uma vaga. Isso
é um filtro de relevância, não uma confirmação da veracidade do conteúdo;
as verificações de identidade, data e citação e a segunda leitura continuam
obrigatórias.

As duas buscas existentes procuram acontecimentos da semana e antecedentes
anteriores, respectivamente. A segunda termina na véspera da semana, sem
exigir um ticker na notícia nem restringir a consulta a resultados trimestrais.
A abreviação final `PART` do nome de negociação B3 é retirada da consulta e
reconhecida no filtro; a identidade oficial original é preservada para verificar
as evidências. Uma falha na busca de antecedentes não apaga os resultados da
busca semanal.

Os catálogos IPE da CVM abrangem os 90 dias anteriores e a semana, inclusive
quando esse intervalo cruza o ano. Entre até cinco documentos por empresa,
a seleção reserva até três vagas para a semana e duas para antecedentes;
vagas restantes podem ser preenchidas pelo outro grupo. Comunicados sobre
negócios e decisões precedem documentos institucionais. A quantidade de
fontes enviadas à IA continua limitada a seis.

O limite de leitura continua em 3.000 caracteres por fonte. Em vez de assumir
que os primeiros caracteres sempre contêm a notícia, o seletor escolhe um
trecho contínuo do texto original, considerando identificação, assuntos
empresariais e presença de menus. Ele não une partes distantes nem altera as
palavras. `body_excerpt_offset` registra onde o trecho começa. Um trecho pode
deixar de fora informação necessária; a verificação continua recusando
afirmações sem apoio no texto efetivamente lido.

O arquivo privado `source-selection-{codigo}.json` guarda os trechos, o período
e os problemas da coleta. As respostas originais e os PDFs continuam salvos
separadamente. O replay consulta as evidências arquivadas e não sobrescreve
esse registro. Documentos anteriores recebem `before_week=true` e título
identificado como antecedente. Documentos posteriores ao fechamento ficam
fora da interpretação e da contagem de cobertura aproveitável.

A auditoria separa empresas com acontecimentos divulgados durante a semana
até o fechamento (`companies_with_preclose_weekly_events`) e empresas com
acontecimentos anteriores (`companies_with_prior_events`). Uma empresa pode
estar nos dois grupos. Resultados trimestrais continuam como antecedentes
financeiros próprios, não como prova da causa do retorno. Encontrar documentos
ou cobrir todas as empresas não equivale a explicar causalmente todas as altas.

Relatórios trimestrais identificados pelo título recebem o papel
`financial_antecedent`; formulários rotineiros de posições/negociação e convites
institucionais não são contados como mudanças empresariais. Essa classificação
é conservadora e baseada no título; não constitui avaliação humana de
materialidade. Ela evita contar um relatório de posições sem operações como
um acontecimento que explique uma variação de preço.

### Reserva distribuída do contexto — contrato `run-context-1.3`

A reserva padrão para chamadas de modelos é US$ 6 por execução, configurável
por `CONTEXT_BUDGET_USD` ou `--budget-usd`. É um limite baseado em estimativas
conservadoras, não o valor faturado pelo provedor. Não inclui créditos da Tavily.

Quando há empresas e temas de mercado, 80% da reserva é dividido igualmente
entre as empresas confirmadas e 20% entre os três temas de mercado. Dois tickers
da mesma empresa compartilham a parcela. Na primeira rodada, uma empresa não
pode consumir a parcela de outra. Os temas de mercado são agendados primeiro.
Depois que todos terminam essa rodada, participantes bloqueados pela reserva
recebem uma tentativa de recuperação usando o saldo global, as fontes salvas
e as respostas já recebidas. Isso não garante aprovação nem cobertura completa.

Após a recuperação, até quatro empresas que ainda têm apenas antecedentes
financeiros recebem uma busca adicional, com leitura de até três novos textos.
Essas chamadas de modelo também respeitam o saldo global. Um resultado adicional
sem acontecimento empresarial confirmado não substitui o conteúdo anterior.
Perfis de ações, agendas, tabelas de resultados e boletins de preços são filtrados.
Nomes anteriores só ampliam a identidade quando o documento financeiro confirma
o mesmo código CVM e CNPJ. Sem acontecimentos válidos, a segunda revisão pela IA
não é chamada; o resumo financeiro continua sendo produzido pelas regras Python.

A auditoria registra parcelas, reservas utilizadas, tentativas novas de API e
tokens informados pela OpenAI. Respostas reaproveitadas não contam como chamadas
novas. O custo faturado permanece desconhecido (`billing_cost_usd=null`); os
retornos da Tavily usados nesta etapa não informam consumo de créditos.
O contrato novo exige uma execução própria: não misture seus arquivos com os
de uma geração anterior. A reprodução usa evidências e respostas arquivadas.

### Volume e reprodução do derivado

O worker arquiva `volume_context.json` a partir da base normalizada conferida.
Para associar esse novo derivado a um resultado anterior, sem sobrescrever
arquivos históricos, use `python -m scripts.build_volume_context --run-dir
CAMINHO --normalized CAMINHO_NORMALIZED` (adicione `--featured` para o case).
O comando recusa arquivo já existente e valida as assinaturas da base e da entrada.
Na reprodução, a apresentação usa o JSON salvo sem consultar APIs nem exigir o bruto.

O volume usa as datas observadas dentro da semana nas duas janelas. A média
divide a soma dos volumes válidos pela quantidade desses valores, incluindo
zeros explícitos e excluindo ausências, negativos e duplicatas. A apresentação
informa cobertura; esse campo não altera a elegibilidade nem os rankings.
Os JSONs públicos de contexto não contêm a coleta privada necessária ao replay.
Preserve a pasta completa da execução e sua versão de código antes da expiração.

### Validação integrada de contexto e volume

Em 08/10/2026, o cenário `volume` de `scripts.validate_context_replication`
verificou uma nova semana com 20 empresas diferentes das do case, preços e
classificações artificiais e fontes externas de contexto. Conferiu cálculos,
zeros e lacunas de volume, cobertura e reprodução sem rede. A coleta levou
323,11 segundos: onze empresas tiveram acontecimentos da semana e nove
apenas acontecimentos anteriores. As notícias macroeconômicas tiveram
cobertura parcial. O teste não comprova classificação B3 online nem garante
prazo e cobertura para qualquer arquivo. Veja o [registro completo](../deploy/contexto-volume-validacao.md).

### Conferência visual mobile

Confira 320, 390 e 430 px e o desktop antes de publicar alterações de layout. Verifique navegação completa, ausência de sobreposição na introdução, retorno visível no ranking, seleção e volta do gráfico, abertura/fechamento de informações, matriz com datas e ticker fixos, menus e tabelas da documentação, seletor da auditoria e referência brasileira no formulário. Conferência de viewport no navegador não substitui teste em Android e iOS físicos, especialmente para seleção de arquivos e teclado.


## Arquivar a documentação aplicável

Novas análises da interface recebem `documentation_snapshot.json` na conclusão, antes da preparação do resultado. `webapp/doc_revision.py` guarda README e arquivos Markdown de `docs/`, identifica a revisão pelo conteúdo e vincula a cópia à entrada e à assinatura do código do relatório. A API verifica essa correspondência e a integridade dos textos ao ler os guias.

Uma execução pelo comando, ou anterior a esse registro, exige conferência das regras antes da associação:

```powershell
.venv/Scripts/python -m scripts.archive_documentation --run-dir "runs/reproducao-2026-09-22" --reviewed
```

O parâmetro declara que a compatibilidade foi revisada; não faz essa revisão automaticamente. O registro usa `reviewed_after_execution`, informa quando a associação ocorreu e não sobrescreve cópias existentes. A demonstração histórica usa esse modo. Não mude o relatório ou os CSVs para acrescentar documentação.

A auditoria abre `/documentacao/referencia/{assunto}` para os guias associados à referência e `/analise/{id}/documentacao/{assunto}` para uma análise. A busca permanece nos artigos atuais; cópias arquivadas usam o menu de assuntos. `documentation_snapshot.json` é um derivado público permitido, sem dados brutos, endereços IP ou credenciais. O prazo da cópia acompanha o resultado de teste.

Imagens dos guias ficam em `docs/assets/`, com nomes que identificam a versão. Preserve arquivos já referenciados por cópias arquivadas; adicione uma imagem com outro nome quando atualizar exemplos. O site serve as capturas em `/documentation-assets/`. A referência técnica concentra comandos avançados e o dicionário antes presentes no README principal.

### Conferência das mudanças de apresentação

Ao revisar o dashboard, confira as duas janelas, as datas e os valores do resumo. No celular, verifique a comparação inicialmente recolhida, a abertura e o fechamento, o aviso de primeira visita e a dispensa em uma visita posterior no mesmo navegador. O ranking móvel deve ocultar a média de volume sem impedir a consulta diária. Confira também a rolagem da tabela de fontes e os grupos de auditoria disponíveis. Uma simulação de viewport não equivale a um teste em aparelho físico.

As imagens atuais dos guias preservam os PNGs originais fornecidos pelo usuário. Substitua os links nos artigos atuais, sem sobrescrever imagens utilizadas por cópias arquivadas.
