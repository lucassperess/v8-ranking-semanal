# Classificação dos instrumentos

O objetivo desta etapa é decidir com evidência quais instrumentos podem entrar no universo ON/PN. Isso é diferente de catalogar detalhadamente todo instrumento financeiro recebido.

## Código como hipótese

Para códigos completos no padrão de quatro caracteres alfanuméricos seguido de uma faixa numérica, o projeto aplica:

| Final | Classe indicada pela regra |
| --- | --- |
| 3 | Ação ordinária (ON) |
| 4 a 8 | Ação preferencial (PN), incluindo classes |
| 31 a 40 | BDR |
| Outros formatos | Outro; verificar evidências e possíveis contradições |

Não basta procurar o último dígito isolado: `B1CS34` entra na faixa de BDR, e `B3SA3` tem uma base alfanumérica válida. Um final `11` não permite afirmar sozinho que o instrumento seja uma unit.

## Evidência oficial nas datas

Para incluir uma ON/PN, o sistema exige classificação oficial consistente nas duas datas dos preços utilizados. O resolvedor consulta arquivos B3 datados, incluindo COTAHIST diário e cadastro de instrumentos, e reaproveita arquivos já disponíveis.

**COTAHIST** é um arquivo histórico de negociações da B3. Ele ajuda a identificar instrumentos negociados na data; não contém necessariamente um ativo que ficou sem negociação. O cadastro de instrumentos complementa essa evidência. Os preços desses arquivos não entram no retorno.

![Fontes oficiais usadas na classificação do case: COTAHIST de 11/09 e 18/09/2026 e cadastro B3 de 18/09/2026, com nomes dos arquivos e disponibilidade.](assets/fontes-b3-20261007.png)

*A tabela da auditoria identifica as fontes oficiais consultadas para a janela selecionada. Estas datas pertencem ao case; outra análise usa as fontes necessárias para suas próprias datas. Os preços desses arquivos não substituem os da Economatica.* [Ampliar imagem](assets/fontes-b3-20261007.png).

Os arquivos são guardados por data e identificação do conteúdo. O cache evita baixar e interpretar novamente a mesma fonte. Cache não transforma uma evidência de outra época em confirmação automática para a data solicitada.

## Três decisões possíveis

| Decisão | Consequência |
| --- | --- |
| Incluir | ON/PN com preços e evidência consistentes nas duas pontas |
| Excluir | Instrumento fora da definição ON/PN, com motivo registrado |
| Revisar | Falta de confirmação para candidata, conflito de preço, identificação ou espécie |

Uma decisão pendente relevante impede o ranking. Se uma fonte oficial indicar ação fora do padrão previsto, a regra também exige revisão para evitar uma exclusão incorreta.

BDRs e outros instrumentos podem ser excluídos pela regra de universo sem uma espécie detalhada resolvida. Contradições oficiais continuam bloqueadoras. Assim, ausência de catálogo detalhado de um excluído não é tratada como confirmação de sua espécie.

## Limites e conferência

Uma nova base pode trazer códigos históricos, mudanças de identificação ou conflitos. A automação não promete resolver qualquer instrumento: ela publica o resultado apenas quando os requisitos do universo forem atendidos.

Na pasta da execução, `b3_evidence.csv` registra evidências, `period_classification.csv` registra a classificação por data e `ranking_universe.csv` registra as decisões. Os arquivos e fontes usados têm procedência nos manifestos.

Consulte a [metodologia](metodologia.md) para a elegibilidade e a [auditoria](auditoria.md) para reproduzir. A implementação está em [ranking_universe.py](../ranking_universe.py) e [resolve_period.py](../resolve_period.py).
