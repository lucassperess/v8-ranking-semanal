# Etapa 3 — teste e escolha das fontes

Conferência em 07/10/2026, na branch `codex/contexto`. Foram realizadas consultas reais às fontes públicas e buscas pelo backend Exa disponível no ambiente. Nenhuma conta ou assinatura foi criada e nenhuma integração foi publicada. Este teste é uma amostra, não a coleta completa do case.

## Credenciais

Não foram encontradas as variáveis de acesso dos provedores avaliados no processo atual nem arquivos `.env` na raiz dos dois checkouts. O usuário informou que ainda não tem conta em Marketaux ou Tavily. Nenhuma chave foi solicitada no chat ou registrada aqui.

Marketaux respondeu HTTP 401 à consulta sem chave de `ECOM3.SA` no período do case. Isso confirma a necessidade de autenticação, não a cobertura do ticker. Marketaux e Tavily permanecem sem validação autenticada; seus planos/documentação não são evidência de cobertura desta semana.

## Amostra de empresas

O cadastro oficial CVM foi baixado e lido. Identidades verificadas:

| Tickers | Companhia | Código CVM | CNPJ |
| --- | --- | --- | --- |
| ECOM3 | ECONOMATICA S.A. | 26077 | 26.345.998/0001-50 |
| TASA3 e TASA4 | TAURUS ARMAS S.A. | 6173 | 92.781.335/0001-02 |
| AMBP3 | AMBIPAR PARTICIPAÇÕES E EMPREENDIMENTOS S.A. | 24961 | 12.648.266/0001-24 |

Fonte: https://dados.cvm.gov.br/dados/CIA_ABERTA/CAD/DADOS/cad_cia_aberta.csv

ECOM3 exige especial atenção: os resultados de busca também mencionam a antiga denominação TC e o ticker TRAD3. Essas referências são pistas a verificar nos documentos oficiais antes de ampliar a pesquisa. O nome da emissora coincide com o da plataforma fornecedora de preços; uma notícia sobre a plataforma não deve ser associada à ação sem conferir a identidade.

## CVM IPE — download e filtro reais

Arquivo: https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/IPE/DADOS/ipe_cia_aberta_2026.zip

- Download final: HTTP 200, 1.689.970 bytes; CSV com 36.032 registros.
- Última data de entrega observada no arquivo: 03/10/2026.
- Foram encontrados 427 registros de todas as empresas com `Data_Entrega` entre 14 e 20/09/2026, inclusive.
- Para os três emissores da amostra: 103 registros de ECOM, 53 de Taurus e 68 de Ambipar no ano; nenhum entregue entre 14 e 20/09.
- O resultado vazio para a amostra não decorre de um arquivo sem a semana pesquisada. Significa somente ausência de entregas nesse filtro e nessa versão do conjunto; não comprova ausência de acontecimentos ou notícias.
- O cadastro apresentou registros repetidos para alguns emissores: deduplicar por identidade oficial e não tratar cada registro cadastral como uma empresa diferente.

Problemas técnicos resolvidos no teste: a primeira requisição padrão retornou 403; a repetição com cabeçalho `User-Agent: Mozilla/5.0` retornou 200. O CSV do IPE não é UTF-8 e foi lido com Windows-1252. Essas diferenças precisam ser tratadas na coleta futura. O sucesso de uma requisição não garante disponibilidade permanente.

Decisão: usar CVM para identidade e documentos oficiais, complementando com RI e busca. A CVM sozinha não oferece contexto diário suficiente para esta amostra.

## Busca Exa e leitura das páginas

Foram realizadas cinco buscas: ECOM, Taurus, Ambipar, Copom e tema fiscal no Senado. Elas produziram resultados não vazios. A busca por palavras e datas também retornou páginas fora do período; selecionar os primeiros resultados sem conferir as datas é inadequado.

| Amostra | Evidência encontrada | Avaliação |
| --- | --- | --- |
| ECOM3 | Cadastro B3 e referências a documentos anteriores/posteriores à semana | Identificação possível; nenhum acontecimento da semana foi validado nesta busca limitada. Não declarar pesquisa exaustiva nem atribuir a alta ao material encontrado. |
| Taurus | Publicação do sindicato em 18/09 sobre assembleia de 17/09 | Página primária acessível com data da publicação e do acontecimento. É relato do sindicato e deve ser atribuído a ele. Não prova a causa da valorização. |
| Ambipar | Fato relevante de 28/09, disponível no RI/CDN e indexado pela busca | Documento primário legível, mas posterior ao período: rejeitado como acontecimento da semana do case. O acesso demonstra capacidade de obter o documento, não cobertura dentro da semana. |

Fontes abertas e conferidas:

- Taurus: https://metalsaoleo.org.br/2026/09/18/trabalhadores-da-taurus-rejeitam-proposta-e-aprovam-estado-de-greve/
- Ambipar, documento rejeitado por data: https://filemanager-cdn.mziq.com/published/765f69d9-d6b2-42fc-b305-639ec9488ac1/03ab0277-d3e2-4589-93a9-5d5e919a6870
- Cadastro B3 de ECOM: https://sistemaswebb3-listados.b3.com.br/listedCompaniesPage/main/26077/ECOM/overview?language=pt-br

O catálogo de fatos relevantes do RI Ambipar abriu, mas o conteúdo textual retornou sem lista utilizável para o ano selecionado. O catálogo B3 também não devolveu conteúdo textual no leitor utilizado. Resultado de busca indexado e página recuperada são evidências diferentes: obter o documento direto ou outra fonte verificável antes de finalizar o contexto.

Decisão: Exa é o complemento de busca efetivamente testado para preparar o case neste ambiente. O acesso disponível via ferramenta/CLI não equivale a credenciais para integrar automaticamente Exa à aplicação. Não colocar essa ferramenta no caminho de uma requisição do dashboard; o conteúdo será preparado previamente.

## Contexto geral — fontes oficiais

- Banco Central: ata referente à reunião de 15 e 16/09/2026, PDF oficial acessível e legível: https://www.bcb.gov.br/content/copom/atascopom/Copom281-not20260916281.pdf
- Federal Reserve: comunicado publicado em 16/09/2026 às 14h EDT, página oficial acessível: https://www.federalreserve.gov/newsevents/pressreleases/monetary20260916a.htm
- Agência Senado: notícia fiscal publicada em 17/09/2026 às 17h27: https://www12.senado.leg.br/noticias/materias/2026/09/17/governo-tera-que-cortar-despesas-para-fechar-as-contas-em-2027-diz-ifi

A ata do Copom descreve uma reunião dentro da semana, mas sua data de publicação não foi estabelecida neste teste. Para explicar o que já era conhecido durante os pregões, localizar o comunicado da decisão publicado naquela data; uma ata posterior pode confirmar o fato retrospectivamente, com essa condição explícita.

A notícia fiscal traz projeções da IFI, que devem ser atribuídas à instituição, sem transformar projeções em resultados realizados. Nesta etapa não foi preparado o resumo macro, nem medida a cobertura de toda a política da semana.

## Banco Central PTAX — API consultada com sucesso

Consulta final HTTP 200, sem chave, com seis registros: 11, 14, 15, 16, 17 e 18/09/2026.

Endpoint consultado:

```text
https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/CotacaoDolarPeriodo(dataInicial=@dataInicial,dataFinalCotacao=@dataFinalCotacao)?@dataInicial='09-11-2026'&@dataFinalCotacao='09-18-2026'&$format=json
```

| Data | Compra (R$/US$) | Venda (R$/US$) |
| --- | --- | --- |
| 11/09/2026 | 5,0912 | 5,0918 |
| 14/09/2026 | 5,1690 | 5,1696 |
| 15/09/2026 | 5,1484 | 5,1490 |
| 16/09/2026 | 5,1520 | 5,1527 |
| 17/09/2026 | 5,1515 | 5,1521 |
| 18/09/2026 | 5,1569 | 5,1575 |

A primeira consulta selecionava um campo `tipoBoletim` inexistente nesse resultado e retornou 400; remover essa seleção resolveu o problema. Para a integração futura, validar o contrato da resposta e não confundir erro de consulta com falta de cotação. PTAX é taxa de referência, sem substituir preços Economatica nem ser chamada de fechamento de bolsa.

Decisão: BCB PTAX aprovado para a coleta do indicador cambial do case. Ibovespa e índices americanos ainda não tiveram série/endpoint validado e continuam condicionados a teste próprio.

## Combinação escolhida e pendências

Base disponível para continuar a preparação do case:

1. Cadastro e documentos CVM para identificação e evidência oficial.
2. Documentos diretos de RI quando necessários e acessíveis.
3. Exa para localizar notícias e documentos complementares, com leitura e conferência das fontes.
4. BCB/Fed/Agência Senado para acontecimentos gerais selecionados.
5. API BCB PTAX para câmbio.

Marketaux permanece candidato adicional, sem evidência suficiente para ser escolhido como provedor principal. Seu teste autenticado depende de conta/chave. Tavily não precisa ser integrado junto com Exa nesta primeira preparação.

Também falta escolher e testar a síntese por uma API de IA com credencial disponível; nenhuma síntese via API de modelo foi executada. Isso pertence à etapa 5. A coleta completa por empresa pertence à etapa 4.

Resultado: fontes públicas e busca disponível têm evidência suficiente para iniciar a coleta do case. Não foi comprovada cobertura de todos os ativos, todos os dias, nem de Marketaux/Tavily. O dashboard e a produção permanecem inalterados.

## Complemento — testes autenticados após configuração das chaves

Ainda em 07/10/2026, o usuário configurou as chaves gratuitas no `.env` local. O arquivo foi conferido como ignorado pelo Git; nenhuma chave foi exibida ou versionada. O comando PowerShell fornecido anteriormente concatenou as duas variáveis quando já havia uma única linha no arquivo. Essa separação foi corrigida antes das consultas. Ambas ficaram em linhas próprias, com valores não vazios.

Este complemento substitui a pendência de autenticação acima. Ele não transforma os resultados de busca em contexto aprovado.

### Marketaux

- Três consultas autenticadas por símbolos `ECOM3.SA`, `TASA3.SA,TASA4.SA` e `AMBP3.SA`, no período de 14/09 a antes de 21/09: HTTP 200, `found=0` em todas.
- Complemento por termos: `ECOM3` e `Ambipar`, também HTTP 200, sem resultados.
- `Taurus`: nove resultados declarados, três devolvidos na primeira página. Os três eram sobre astrologia ou fundos homônimos e não foram aceitos como notícias da companhia. Os demais resultados não foram paginados; não afirmar ausência absoluta com base apenas nessa página.
- Controle com `AAPL`, no mesmo período: HTTP 200, 108 resultados declarados e três retornados. Esse controle comprova funcionamento da credencial e recuperação histórica para outro símbolo; não comprova cobertura da B3.
- As quatro consultas complementares inicialmente sem `User-Agent` retornaram 403; com o mesmo cabeçalho do primeiro teste, retornaram 200. Registrar a diferença técnica sem atribuí-la a limite de plano não demonstrado.
- Total: sete consultas com HTTP 200 e quatro tentativas com HTTP 403. O débito efetivo da franquia não foi consultado no painel.

Decisão: Marketaux não será o provedor principal desta primeira versão com a evidência disponível. A cobertura efetiva da amostra por ticker não foi demonstrada; também pode depender de convenções de símbolo ainda não verificadas. Credencial válida não equivale a fonte adequada para o case.

### Tavily

Seis consultas autenticadas, todas com HTTP 200: três em `topic=news` para a amostra de empresas e três em `topic=general`, com fontes selecionadas para Taurus, Ambipar e Copom. Todas usaram busca avançada, limitada ao período do case. Pela regra documentada, correspondem nominalmente a 12 créditos de busca; o consumo no painel não foi conferido.

- ECOM: os cinco resultados de notícias retornados não tratavam do emissor. Rejeitados para contexto corporativo.
- Taurus: notícias policiais mencionavam armas da marca, além de uma notícia de produto candidata a conferência. A pesquisa geral restrita à fonte sindical/companhia retornou vazia e não recuperou a publicação já encontrada pela Exa. Não tratar nome da marca em ocorrência policial como acontecimento financeiro da empresa.
- Ambipar: retornaram páginas de outros assuntos com referências à companhia em seções de notícias relacionadas, e itens sem data. Rejeitados para contexto corporativo nesta avaliação. O conteúdo da barra lateral pode conter acontecimentos posteriores à data da matéria.
- Copom: a consulta geral restrita ao BCB recuperou o comunicado `https://www.bcb.gov.br/detalhenoticia/21261/nota`, com trecho indicando publicação em 16/09/2026 às 18h32, além da ata e outros resultados. O leitor web não conseguiu abrir diretamente essa página; o trecho é uma pista útil, mas a leitura integral do comunicado permanece pendente antes de aprovar seu texto.

Decisão: Tavily poderá complementar buscas de contexto geral e fontes selecionadas. Nesta amostra não demonstrou vantagem suficiente para substituir Exa na localização de notícias corporativas. Data retornada pelo provedor, menção em trecho e título não bastam para aprovar uma notícia.

### Escolha atualizada

Manter CVM/RI e fontes oficiais como evidência, Exa como busca principal já disponível para preparar o case e BCB PTAX para câmbio. Tavily fica como complemento selecionado, com credencial testada. Marketaux fica fora do fluxo principal por ora, sem necessidade de assinatura paga para continuar.

Os testes autenticados da amostra estão concluídos. Permanecem para as próximas etapas a coleta de todos os emissores, revisão dos documentos e integração visual. A produção e a versão standby não foram alteradas.
