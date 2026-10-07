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
