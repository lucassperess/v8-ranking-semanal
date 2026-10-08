# Registro de decisões do projeto

Consolidado em 06/10/2026 a partir da implementação existente. Estas decisões explicam o comportamento atual; não são novas regras introduzidas por esta documentação. O escopo é o ranking semanal da extração recebida.

## D01 — Semana-calendário anterior e duas interpretações

**Decisão:** a referência identifica a semana anterior, de segunda a domingo. O principal compara o fechamento anterior à semana com o último dentro dela. A alternativa compara primeiro e último dentro dela.

**Motivo:** incluir no principal o movimento do primeiro pregão e tornar explícita a sensibilidade à interpretação de “última semana”.

**Consequências:** datas são selecionadas globalmente da extração; não há uma ponta diferente por ticker. Cada janela resolve sua própria elegibilidade. Falta de dados, cobertura insuficiente e encerramento antes da sexta-feira exigem os controles implementados; a aceitação explícita de semana encurtada existe no comando e no formulário. Na interface, exige revisão das datas, fica vinculada à assinatura do arquivo e à referência e é registrada na execução. Os demais controles continuam obrigatórios.

**Implementação:** `weekly_ranking.py`, testes de seleção em `tests/test_weekly_ranking.py`.

## D02 — Preços da Economatica; B3 para evidência de instrumento

**Decisão:** usar somente fechamentos ajustados da entrada no retorno. Usar fontes oficiais B3 datadas para confirmar a espécie nas pontas.

**Motivo:** evitar combinar preços brutos e ajustados ou séries com convenções diferentes.

**Consequências:** o projeto não recalcula todos os ajustes da Economatica. COTAHIST contém negociações da data e não é um catálogo universal de todos os códigos recebidos.

**Implementação:** `etl.py`, `resolve_period.py`, `classify_period.py` e `weekly_ranking.py`.

## D03 — Universo ON/PN com confirmação nas duas datas

**Decisão:** incluir ações ON e PN, inclusive classes PN, com dois fechamentos positivos e confirmação oficial consistente. Não aplicar filtro de liquidez. BDRs, units e outros instrumentos ficam fora do universo definido.

**Motivo:** explicitar uma interpretação de “ações” e separar elegibilidade do ranking de catalogação detalhada de todos os instrumentos.

**Consequências:** código completo fornece hipótese; ON/PN requerem confirmação em ambas as pontas. Espécie detalhada desconhecida de um excluído não é automaticamente bloqueadora; contradição oficial, ação fora do padrão ou conflito relevante exige revisão. A extração limita a abrangência do universo.

**Implementação:** `ranking_universe.py`, `classify_period.py`, testes de universo e classificação.

## D04 — Rastreabilidade e ausência sem preenchimento

**Decisão:** preservar bruto, campos originais e identificação de linha. Registrar ausências, falhas e duplicatas sem descarte ou preenchimento silencioso.

**Motivo:** permitir explicar exclusões e distinguir observação, valor ausente e problema de leitura.

**Consequências:** esquema incompatível impede leitura confiável; linha malformada permanece registrada. Exclusão do ranking não significa apagar a linha do tratamento. Ocorrências não autorizam inventar causas ou corrigir preços.

**Implementação:** `etl.py`, `tests/test_etl.py`.

## D05 — Retorno decimal, top 20 e média aritmética

**Decisão:** retorno = preço final / inicial − 1. Usar cálculo decimal; ordenar pelo valor calculado decrescente e ticker crescente no empate. Tirar a média aritmética dos 20 selecionados. Arredondar para duas casas somente na apresentação da porcentagem.

**Motivo:** preservar a precisão recebida, não mudar posições por arredondamento e atender ao requisito de média do top 20.

**Consequências:** divisões têm a precisão finita do contexto decimal. Menos de 20 elegíveis impede publicar um top 20. A média ex post não é retorno de uma carteira previamente investida, índice ou média de todo o universo.

**Implementação:** `weekly_ranking.py`, `tests/test_weekly_ranking.py`.

## D06 — Fontes datadas, cache e interrupção explícita

**Decisão:** obter fontes por data, guardar identificação do conteúdo e reaproveitar arquivos disponíveis. Não publicar ranking quando faltarem evidências necessárias ou houver conflito relevante.

**Motivo:** tornar a decisão temporalmente consistente e impedir resultados aparentemente completos baseados em suposições.

**Consequências:** disponibilidade de rede/fontes afeta execuções sem cache suficiente. `--offline` não garante conclusão se faltar entrada. As assinaturas SHA-256 identificam conteúdo, não comprovam sua correção. Uma nova extração gera nova versão; não se anexa cegamente à anterior.

**Implementação:** `b3_registry.py`, `resolve_period.py`, `classify_period.py` e manifestos.

## D07 — Cálculo Python e apresentação independente

**Decisão:** produzir retornos, média e séries diárias em Python. O navegador seleciona e apresenta valores. Contexto visual não interfere no ranking.

**Motivo:** compartilhar a lógica entre comando e site e evitar dois cálculos concorrentes.

**Consequências:** retorno diário exige preços das datas consecutivas da extração; lacuna não vira zero nem variação de vários dias rotulada diária. A soma dos percentuais diários não substitui o retorno semanal. Gráficos são históricos, sem cotação em tempo real. Preços, retornos diários e matriz acompanham o recorte da janela selecionada. Na alternativa, o primeiro fechamento é a base inicial e recebe retorno nulo com motivo `window_start`, distinguindo-o de zero e de preço ausente. Apresentações anteriores são adaptadas em memória a partir das séries salvas, sem modificar derivados, manifestos ou guias históricos.

**Implementação:** `webapp/presentation.py`, `webapp/static/app.js`, testes de apresentação.

## D08 — Execuções públicas separadas da demonstração

**Decisão:** novos envios não substituem a referência. Limitar fila, tamanho, tempo e frequência. Bruto não tem download público; derivados são publicados por lista permitida e link próprio.

**Motivo:** permitir avaliar replicabilidade mantendo recursos limitados e procedência por execução.

**Consequências:** 10 MB; dez minutos; uma ativa e duas aguardando; três envios por hora por origem. Bruto removido após 24 horas, testes após sete dias. Link imprevisível não é autenticação. Auditoria pública inclui os manifestos ETL e de classificação, decisões do universo, ocorrências e evidências derivadas B3 das duas janelas. Bruto e base normalizada completa não são públicos. Novas análises pela interface arquivam a revisão dos guias na conclusão; associações posteriores à execução são identificadas explicitamente.

**Implementação:** `webapp/server.py`, `store.py`, `worker.py`, `presentation.py` e `deploy/`.

## Como revisar decisões

Uma alteração deve identificar a decisão afetada, a razão da mudança, seus efeitos nos dados/saídas e os testes aplicáveis. Atualize o artigo correspondente junto com o código. Preserve no Git o histórico e os registros da demonstração; melhorias planejadas não devem ser descritas como implementadas.

Os números de 22/09/2026 pertencem ao exemplo. Nenhuma dessas decisões exige que outra extração tenha os mesmos tickers, contagens ou retornos.

## D12 — Revisão explícita de semana encurtada na interface

**Decisão:** antes de enfileirar um envio cujo último fechamento é anterior à sexta-feira, mostrar as datas e as contagens de fechamentos positivos e exigir nova confirmação. Não inferir feriado. Mudanças na entrada ou na referência exigem nova revisão.

**Registro:** opções e horário de aceitação persistem na fila; o worker escreve `analysis_request.json` sem nome original, IP ou bruto. A auditoria confere esse registro contra a entrada e a semana do relatório. Execuções anteriores continuam legíveis sem afirmar uma confirmação pelo formulário que não existiu.

**Limites:** a revisão inicial usa o tratamento existente em lotes e a mesma regra de seleção de semana. Ela confere datas e cobertura; duplicatas, qualidade e classificação completas continuam no pipeline. Falhas ganham orientação para corrigir a extração, rever datas ou aguardar disponibilidade B3, sem liberar pendências.

**Verificação:** `tests/test_replication.py` cobre revisão, confirmação vinculada, cobertura, migração, duas entradas independentes e execução integral com fontes artificiais locais. Testes artificiais não representam consultas reais à B3.

## D13 — Relevância e período do contexto empresarial

**Decisão:** selecionar fontes por identidade e relevância antes da geração de
contexto, priorizando documentos oficiais da CVM e contemplando até 90 dias de
antecedentes. Notícias precisam de identidade, data e trechos verificáveis;
dados financeiros trimestrais mantêm papel próprio. Um documento posterior ao
fechamento não aumenta a cobertura aproveitável daquele retorno.

**Motivo:** evitar que resultados de busca irrelevantes ocupem as vagas de
leitura e que ausência de notícia na semana seja confundida com ausência de
qualquer antecedente empresarial. A seleção não estabelece causalidade.

**Consequências:** limite de cinco documentos oficiais, seis textos selecionados
e 3.000 caracteres por texto preservado. O trecho escolhido permanece contínuo
e rastreável. Fontes rotineiras e relatórios financeiros não contam como mudança
empresarial. A auditoria separa acontecimentos da semana e anteriores. A mesma
empresa pode estar nos dois grupos; as contagens não devem ser somadas.

**Verificação:** filtros e falhas parciais têm testes locais independentes de
rede. Uma conferência real do case usa uma nova pasta, preserva preços e
evidências anteriores e distingue coleta, aprovação e bloqueio por reserva.
Testes isolados não provam que o orçamento padrão permite revisar todas as
empresas em uma única geração. Publicação e ajuste do orçamento são etapas
posteriores.

## D14 — Reserva protegida para empresas e mercado

**Decisão:** contrato `run-context-1.3`, reserva conservadora padrão de US$ 6
para modelos, 80% para empresas e 20% para mercado. Primeira rodada com parcelas
individuais; recuperação do saldo somente depois de todos participarem.

**Motivo:** impedir que as primeiras empresas consumam o recurso necessário
para gerar e revisar as últimas empresas e os temas de mercado.

**Consequências:** chamadas sem acontecimentos válidos não recebem revisão
adicional. Até quatro lacunas financeiras recebem busca complementar. Falhas
nessa busca preservam o resultado anterior. Reserva e tokens informados não
equivalem a faturamento; créditos de busca não integram o limite em dólares.
Não há promessa de descobrir uma causa para cada retorno.

**Verificação:** testes de concorrência, proteção entre participantes, recuperação,
cache e preservação do conteúdo anterior. A conferência isolada das quatro
lacunas do case não encontrou novos acontecimentos empresariais confirmáveis.
A validação integral do contrato novo permanece uma etapa posterior.

## D15 — Volume recebido como contexto de negociação

**Decisão:** exibir volume médio diário dentro da semana e volume por data
para o top 20 de cada janela. Usar o campo financeiro da Economatica;
quantidade ajustada não representa quantidade de negócios. O volume não
muda os retornos, o universo ou a ordenação, nem cria filtro de liquidez.

**Cálculo:** soma dos volumes válidos dividida pelo número de dias válidos.
Zero explícito participa; ausência, valor negativo, inválido ou chave
duplicada permanece lacuna. A cobertura usa datas da semana com fechamento
positivo observado na extração. As janelas principal e alternativa usam
a mesma semana para volume, com suas próprias ações do top 20.

**Rastreabilidade:** cálculo em Decimal e arredondamento somente na tela.
`volume_context.json` preserva séries, lacunas, definição, assinatura do
conteúdo e vínculo com a entrada e a base normalizada. O worker guarda
esse derivado e a apresentação. Resultados sem evidência mostram ausência,
sem preencher valores. O case recebeu um arquivo adicional conferido,
sem sobrescrever os derivados históricos assinados.

**Limites:** média parcial não equivale a média de todos os dias da semana.
Volume recebido pode diferir dos registros oficiais B3; não se atribui
causalidade ou se classifica liquidez automaticamente. A matriz usa azul
em escala linear comum; os retornos mantêm sua escala e suas cores próprias.
