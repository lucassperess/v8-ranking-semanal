# Escopo da primeira versão com contexto

Etapa 2 do plano, registrada em 07/10/2026 na branch `codex/contexto`.
Este documento define a entrega futura; a camada de contexto ainda não está implementada. A base preservada e sua recuperação estão em [standby-pre-contexto.md](standby-pre-contexto.md).

## Objetivo

Permitir que quem explora o case veja acontecimentos documentados das empresas e do mercado durante a semana analisada, junto dos gráficos e com links para conferir as fontes. A aplicação é pessoal, temporária e não comercial, destinada à avaliação da entrega.

O contexto será preparado e revisado previamente. Selecionar uma ação exibirá informações já guardadas, sem iniciar uma pesquisa ou geração de texto a cada clique.

## Período e universo

- Case: referência em 22/09/2026, semana-calendário de 14 a 20/09/2026; fechamentos da semana de 14 a 18/09.
- Janela principal: 11/09 → 18/09; alternativa: 14/09 → 18/09.
- Pesquisar acontecimentos da semana-calendário, indicando quando a publicação ocorreu após o último fechamento ou no fim de semana. Esses acontecimentos não explicam retroativamente o retorno encerrado em 18/09.
- Antecedentes anteriores a 14/09 também entram para explicar a situação da empresa conhecida antes da semana: resultados trimestrais, dificuldades financeiras, mudanças estratégicas e condições de negociação. Devem trazer período, data de divulgação e identificação explícita como antecedentes. Não são apresentados como novidades da semana nem como causas comprovadas da variação.
- Atender aos ativos da união de `top20.csv` e `top20_alternativo.csv`, associados às respectivas empresas. Isso permite trocar a janela sem deixar as ações exclusivas da alternativa sem tratamento.
- Pesquisar por empresa, reutilizando acontecimentos corporativos para ON e PN da mesma companhia. A seleção de um ticker continua exibindo os preços e retornos específicos daquele papel.
- A cobertura poderá variar por empresa e por dia. Não exigir um acontecimento para cada data nem preencher ausências com especulação.

## Entrega no dashboard

### Contexto da empresa e leitura do movimento

Revisão de 07/10/2026: a triagem restrita a notícias semanais não atende à entrega. Cada ativo precisa de uma leitura específica do movimento dos preços e de contexto verificável da empresa. A quantidade de empresas com notícias não mede a proporção do retorno explicada.

A apresentação deve reunir três partes: o que ocorreu com o preço, qual situação da empresa era conhecida naquele período e quais acontecimentos ou relações foram documentados. Resultados trimestrais são identificados como antecedentes. Uma notícia encontrada não dispensa avaliar sua relevância. Sem vínculo sustentado por evidência, não atribuir uma causa.

Seção abaixo do gráfico da ação selecionada, contendo acontecimentos ordenados por data. Cada item terá título literal, explicação curta do fato e de sua possível relevância, data do acontecimento quando conhecida, data da publicação e fontes clicáveis.

Se as datas de publicação e acontecimento forem diferentes, explicitar a diferença. Identificar publicações após o fechamento quando o horário puder ser conferido; não presumir um horário desconhecido.

Estados de apresentação distintos:

1. Contexto encontrado e revisado.
2. Nenhum acontecimento específico encontrado nas fontes consultadas durante o período.
3. Pesquisa incompleta por falha ou indisponibilidade de fonte.
4. Contexto ainda não preparado para aquela empresa.

Trocar entre as janelas preserva os acontecimentos do período e atualiza normalmente o ranking e os gráficos. Explicação sugerida: "As duas opções comparam fechamentos diferentes. Os acontecimentos apresentados são os da mesma semana."

### Contexto geral da semana

Uma seção própria, exibida uma vez no dashboard, com resumo curto dos acontecimentos econômicos e políticos relevantes no Brasil e no exterior. Cada afirmação factual deverá ter fonte. Informações gerais não serão repetidas como se fossem notícias específicas de cada empresa.

### Indicadores de mercado

Complemento condicionado à disponibilidade de séries verificáveis: dólar de referência, Ibovespa e índices americanos selecionados. Definir fonte, unidade, datas inicial e final e interpretação antes de exibir uma variação. PTAX deve ser identificada como taxa de referência, sem apresentá-la como cotação intradiária.

Usar datas comparáveis e explicar eventuais diferenças de calendário entre mercados. Se uma série não puder ser conferida no prazo, omitir o indicador e registrar essa limitação, sem impedir a entrega das notícias.

### Transparência e leitura

Identificar o uso de IA na preparação dos resumos, o período pesquisado e a data da coleta. Oferecer acesso às fontes e às limitações da pesquisa. Usar linguagem literal e didática, definindo termos necessários.

No mobile, leitura vertical, sem dependência de hover, com fontes acessíveis e sem sobreposição com o gráfico. Reutilizar os padrões visuais da plataforma.

## Relação entre acontecimentos e preços

As fontes sustentam os acontecimentos, mas uma coincidência de datas não comprova a causa de uma alta ou queda. Distinguir:

- Fato confirmado pela fonte.
- Relação atribuída por uma fonte identificada.
- Possível relevância, apresentada como hipótese e com seu limite explícito.

Não escolher notícias apenas porque seu tom combina com o sinal do retorno. Não usar sentimento automático como prova de impacto no preço. Quando não houver base para uma relação, dizer que as informações disponíveis não permitem afirmar quanto o acontecimento explica a variação.

## Fontes e IA: candidatas, não decisões concluídas

A etapa 3 avaliará Marketaux como fonte financeira; CVM e relações com investidores como evidência oficial; Tavily como complemento; Banco Central para câmbio. Séries de índices dependerão de verificação adicional. GPT-6 Luna é o candidato inicial para síntese, sujeito à avaliação dos textos.

O teste seguinte verificará identidade da empresa, datas, links acessíveis e utilidade da informação. Não haverá contratação automática de vários provedores para preencher lacunas. O resultado do teste determinará a combinação usada.

## Limites desta primeira versão

- Contexto preparado para o case. Novos CSVs seguem o fluxo atual e não recebem automaticamente notícias; a interface deverá esclarecer isso quando pertinente.
- Não inclui atualização contínua, chat, previsões ou geração em tempo real ao selecionar uma ação.
- Notícias e indicadores não alteram preços Economatica, classificação B3, elegibilidade, cálculo, ordenação, média ou lacunas das séries.
- Falhas da camada de contexto não interrompem ranking, gráficos, downloads ou processamento de novos arquivos.
- Credenciais permanecem no servidor e fora do Git e do navegador.
- A demonstração histórica e seus arquivos assinados não serão sobrescritos para armazenar o contexto. A extensão terá registro separado, associado explicitamente ao case.
- A produção atual permanece disponível. A publicação da nova versão será decidida depois da revisão da prévia.

## Critérios de conclusão

- Todos os tickers das duas listas do top 20 têm associação de empresa conferida, leitura específica dos preços e contexto da empresa sustentado por fontes. Um estado explícito de ausência de notícias não basta para aprovar a utilidade da entrega. Lacunas relevantes precisam de nova pesquisa ou ficam registradas como pendência da revisão.
- Eventos e resumo geral apresentam fontes válidas e datas verificadas, sem afirmações causais indevidas.
- Ausência de notícias é distinguida de pesquisa incompleta.
- Troca de ticker e janela funciona; leitura desktop e mobile é conferida.
- A falta do contexto não impede as funcionalidades existentes.
- Séries numéricas exibidas têm origem, unidade e período definidos.
- Dados da coleta, fontes e modelo utilizado ficam registrados para revisão.
- A prévia é apresentada ao usuário antes da decisão de publicar.

## Sequência restante

3. Testar e escolher fontes.
4. Coletar e organizar evidências por empresa e semana.
5. Preparar e revisar explicações com IA.
6. Integrar a apresentação no dashboard.
7. Guardar contexto e rastreabilidade.
8. Revisar conteúdo, interface e funcionamento.
9. Decidir qual versão entregar.

Concluir este documento não executa essas etapas posteriores.
