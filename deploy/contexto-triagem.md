# Triagem das fontes do case

Primeira revisão concluída na branch `codex/contexto`, sem publicação. O resultado
está em `context/case-2026-09-22/triage.json`. A produção e a versão standby foram
preservadas. Esta etapa seleciona evidências; não escreve motivos para os retornos.

## O que os números significam

| Medida | Resultado | Limite da interpretação |
| --- | --- | --- |
| URLs distintas solicitadas para leitura | 179 | Os 185 candidatos por empresa continham seis repetições entre empresas |
| Páginas extraídas | 158/179 — 88,27% | Receber texto não confirma notícia pertinente ou data correta |
| Páginas com falha de extração | 21 | Algumas têm títulos irrelevantes; outras permanecem pendentes |
| Documentos oficiais examinados | 23 | Cinco são formulários rotineiros da Armac sobre períodos anteriores |
| Fontes aprovadas para apoiar rascunho | 23 | 18 documentos CVM, quatro artigos/avisos e o relato sindical da Taurus já conferido |
| Grupos de acontecimentos/divulgações | 16 | Documentos da mesma AGE ou eleição não viram vários acontecimentos |
| Empresas com algum contexto datado utilizável | 12/23 — 52,17% | Inclui opiniões, avisos e iniciativas operacionais; não mede explicação causal da alta |
| Candidatos retirados da seleção | 144 | Triagem combina leitura oficial, metadados e propostas da IA; datas sugeridas não são todas verificadas |
| Candidatos ainda pendentes | 42 | Não podem alimentar o rascunho como fatos confirmados |

São 209 registros de avaliação: 185 candidatos corporativos, 23 documentos CVM e
uma fonte sindical aprovada anteriormente. O mesmo documento pode também ter uma
republicação candidata na web. O agrupamento de eventos impede contá-los como fatos
independentes. Os três materiais macroeconômicos já conferidos continuam no arquivo
`verified_sources.json` e não entram na taxa de cobertura das empresas.

## Cobertura por empresa

| Situação | Ações |
| --- | --- |
| Algum contexto datado aprovado, com limites próprios | CASH3, DASA3, ESTR4, FASA3, ISAE3, MEAL3, MGEL4, ONCO3, RCSL3, TASA3/TASA4, WDCN3, YDUQ3 |
| Sem acontecimento específico entre os candidatos revisados | ARML3, BIED3, DOTZ3, LUXM4, QUAL3, WEST3 |
| Evidência insuficiente, com candidato relevante ou leitura não resolvida | AMBP3, AURE3, ECOM3, PLAS3, TXRX4 |

As empresas da primeira linha também podem ter candidatos pendentes. A terceira
linha não significa ausência de notícias. A segunda descreve apenas esta pesquisa,
que não é uma busca exaustiva de todas as publicações existentes.

Aviso de juros de debêntures da ISA, convocação de PLR da Mangels e biblioteca da
Dasa têm alcance limitado para contextualizar preços. Não inflar a qualidade da
cobertura contando esses materiais como causas de valorização.

## Correções efetivamente aplicadas à seleção

- **Armac:** o artigo sobre resultados de 2025 foi publicado em 01/04/2026. A data
  de setembro no cabeçalho era dinâmica. A fonte foi retirada do recorte semanal.
- **Bioma:** metadados da própria página datam o fechamento da operação em
  10/09/2025. A sugestão de candidato da IA foi descartada.
- **Westwing:** notícia da empresa alemã não foi associada à WEST3 brasileira.
- **Economatica/ECOM3:** o blog da plataforma tem uma publicação datada de 14/09.
  A associação societária dessa publicação à emissora ainda precisa de comprovação;
  o material permanece pendente, apesar da coincidência de marca.
- **WDC:** a fonte oficial descreve proposta vinculante, sujeita a condições.
  Matéria que afirma aquisição concluída não substitui essa informação.
- **Fasa e Recrusul:** propostas de grupamento continuam propostas. Datas das AGEs
  futuras ficam separadas das datas de protocolo/divulgação dos documentos.
- **Méliuz:** aumento de capital aprovado em 08/09, com documentos entregues em
  14/09. É divulgação de ato anterior; a primeira publicação não foi estabelecida.
- **Oncoclínicas:** notícia, fato relevante e ata da mesma eleição não são eventos
  independentes. A eleição ocorreu em 14/09; a ata foi entregue em 17/09.
- **IMC/Vinci:** esclarecimento de domingo, 20/09, traz informação adicional.
  Não pode aparecer como informação já conhecida no fechamento de sexta, 18/09.
- **IMC/dívida:** as atas de debenturistas de 15/09 e do conselho de 16/09 apresentam
  vencimentos/condições diferentes. A aprovação dos respectivos atos pode ser
  descrita, mas os parâmetros não serão fundidos ou apresentados como condições
  definitivas sem conciliação adicional.
- **Taurus e Mangels:** estado de greve não comprova paralisação; convocação de
  assembleia não comprova aprovação da PLR. Relatos do sindicato exigem atribuição.
- **XP e BBI:** análises são opiniões atribuídas aos bancos, não fatos que comprovem
  causalidade ou uma operação societária concluída.

## Papel e limites da IA

Luna sugeriu a triagem dos candidatos das 23 empresas. Todas as sugestões foram
mantidas no snapshot privado, separadas das decisões de aprovação. A revisão
editorial conferiu o conteúdo e as datas das fontes aprovadas e corrigiu as
ambiguidades acima. Os demais registros documentam a seleção e suas pendências;
não representam certificação integral de todos os textos retornados.

Dois retornos JSON não puderam ser lidos e foram repetidos. Também houve erros de
identidade, de recorte temporal e de interpretação de entrega CVM nas sugestões.
O pequeno teste sintético anterior não havia mostrado esses problemas. Por isso,
uma resposta da API ou uma recomendação do modelo não é aprovação de evidência.

`scripts/context_triage.py` exige identidade confirmada, leitura do corpo, data
rastreável dentro do recorte e grupo de evento para fontes aprovadas. Preserva as
divulgações de cada versão e impede declarar causalidade nessa etapa.

## Custos e preservação

- Tavily Extract informou **67 créditos** nas 18 respostas em lote. Não foi lida a
  fatura nem o saldo da conta.
- As 23 propostas salvas usaram 940.889 tokens de entrada e 23.722 de saída em Luna:
  **US$ 0,10595 estimados**, pelos preços já registrados em `contexto-modelos.md`.
- As duas primeiras respostas inválidas não tiveram uso preservado. O limite
  conservador delas é US$ 0,08. Assim, esta triagem fica estimada abaixo de
  **US$ 0,19**, excluindo os testes anteriores e os créditos da busca.
- Textos integrais, HTML, sugestões e consumo ficam em
  `runs/context-triage-2026-09-22-v1/`, ignorado pelo Git. Foram preservados os hashes
  dos textos recuperados e dos documentos aprovados. Nenhuma chave está no índice.

## Próxima etapa

Produzir rascunhos com as fontes aprovadas, explicando tipo de evidência e limites.
Empresas sem cobertura suficiente recebem uma indicação clara da lacuna, sem
inventar um motivo para o preço. Não é necessário preencher todos os dias.

Antes de qualquer associação diária, conferir horário de publicação e distinguir
notícia anterior ao fechamento, posterior a ele e horário desconhecido. Os textos
macroeconômicos devem continuar separados dos acontecimentos de cada empresa.
Cobertura de Ibovespa e índices americanos ainda não foi concluída por esta triagem.

Marketaux continua fora do caminho principal: os três exemplos testados não deram
material útil para as respectivas empresas. Esse resultado não prova inutilidade
da API em todos os mercados, mas não justifica depender dela nesta entrega.
