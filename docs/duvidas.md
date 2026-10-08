# Problemas e dúvidas

Localize a situação que aparece na sua análise. Cada resposta explica o efeito e indica onde conferir antes de tentar novamente. Os exemplos com datas de setembro pertencem ao case; os dados do seu envio aparecem na sua página de resultado.

## Por que a matriz tem células vazias?

No modo **Retornos (%)**, uma célula com **—** não representa retorno zero. O significado depende da posição:

- **Primeiro dia da alternativa:** o fechamento é o preço inicial; ainda não existe comparação dentro da janela.
- **Demais datas:** faltam dois fechamentos consecutivos utilizáveis, por ausência, valor inválido ou conflito.

Exemplo: há preço na sexta, falta na segunda e há preço na terça. Não calculamos a segunda; também não apresentamos sexta → terça como um retorno diário de terça. Consulte a descrição da célula ou da observação no gráfico para identificar o motivo e [as datas comparadas](metodologia.md#como-interpretar-os-gráficos-diários).

No modo **Volume (R$)**, “—” indica volume ausente, inválido ou duplicado. Um zero informado aparece como **0,00** e participa da média. Falta de volume e falta de fechamento são problemas de campos diferentes.

## O que significa “4 de 5 dias” no volume?

A média usou quatro valores válidos, entre cinco datas observadas da semana. A data sem volume não foi preenchida com zero. Compare a cobertura antes de comparar médias: uma ação com um dia disponível pode ter uma média pouco representativa daquela semana. O ranking continua sendo ordenado pelo retorno, sem filtro de volume.

## Por que há volume no primeiro dia da alternativa, mas não retorno?

O volume é um valor informado para aquele dia. O retorno precisa comparar dois fechamentos: na alternativa, o primeiro fechamento é o início, e ainda não há comparação dentro da janela. Por isso, o dia pode ter volume e mostrar “—” no retorno. Volume igual a zero também é possível.

## O contexto está em processamento ou indisponível

Os cálculos são liberados antes da coleta opcional de contexto. Acompanhe a aba **Contexto** na mesma URL; ela atualiza quando a leitura fica pronta. Não é necessário reenviar o CSV para consultar o andamento.

Uma fonte inacessível, credencial ausente, limite de orçamento ou fim do prazo de processamento pode impedir a geração. A mensagem informa a indisponibilidade; o ranking, o volume e os gráficos calculados continuam disponíveis. Um novo envio cria outra análise e pode consumir novamente os serviços externos.

## Há contexto disponível, mas faltam notícias de algumas empresas ou temas

“Disponível” indica que existe uma leitura concluída, não uma notícia confirmada para cada empresa em cada dia. A empresa pode ter apenas antecedentes, como um resultado trimestral anterior. Um tema de mercado também pode ficar sem acontecimento confirmado mesmo com o índice disponível.

Confira as datas, os grupos de fontes e a limitação indicada. Ausência de notícia confirmada não significa ausência de negociação ou de acontecimentos. Volume pequeno descreve os dados de negociação recebidos; sozinho, não explica a causa da alta ou queda.

## Posso guardar e reproduzir o contexto?

Baixe os JSONs de **Contexto e fontes** durante os sete dias para conservar os textos e registros apresentados. Uma nova consulta às APIs pode produzir outra seleção de fontes e outra redação.

A reprodução sem novas APIs exige as evidências e respostas internas salvas pelo responsável pela ferramenta, que não fazem parte dos downloads públicos. Veja [a diferença entre conferir, recalcular e reproduzir](auditoria.md#conferir-recalcular-e-reproduzir-o-contexto).

## Por que a alternativa não mostra retorno na segunda-feira?

No case, a alternativa começa no fechamento de segunda, 14/09. Um retorno na própria segunda exigiria comparação com 11/09, fora dessa janela. A segunda fornece o preço inicial; a terça compara 14/09 com 15/09 e é o primeiro retorno da alternativa.

A regra vale para o primeiro dia disponível, mesmo que não seja segunda-feira. As duas opções terminam no mesmo fechamento da semana anterior. “Dentro da semana” não acompanha uma semana em andamento até o dia atual.

## Como uma ação com lacunas aparece no top 20?

O retorno semanal depende dos fechamentos inicial e final. Uma ausência entre essas datas pode impedir uma comparação diária sem impedir o cálculo semanal. Confira os preços inicial e final no painel e a data da lacuna no gráfico. Nenhum preço ausente é preenchido.

## Uma ação foi excluída, mas a análise terminou. Isso é esperado?

Sim. Um código sem os dois preços utilizáveis ou um instrumento fora do universo ON/PN pode ficar de fora, com motivo registrado. A análise pode concluir se houver pelo menos 20 ações elegíveis em cada opção e as demais verificações forem atendidas.

Abra a auditoria: “Exclusões das pontas” explica a ausência de preços; “Decisões do universo” explica exclusões pelo tipo. Uma decisão de revisão pendente, por sua vez, impede o ranking. Veja [como conferir uma exclusão](auditoria.md#entender-uma-exclusão).

## Meu arquivo foi rejeitado por esquema inesperado

A ferramenta não conseguiu interpretar o formato esperado. Confira nomes e ordem das nove colunas, vírgulas como separadores, ponto decimal e datas AAAA-MM-DD. Trocar apenas a extensão para `.csv` não basta.

Exporte novamente a base no [formato aceito](dados.md#formato-aceito) e confira as primeiras linhas como texto antes de reenviar. Linhas com estrutura irregular também podem impedir o processamento; confira a linha indicada na mensagem, quando disponível.

## A data é inadequada ou não há cotações suficientes

A referência seleciona a semana anterior à semana em que essa data está. Uma referência futura é rejeitada pela interface. O CSV precisa conter fechamento anterior à semana e ao menos duas datas com fechamentos positivos dentro dela.

Confira a referência, o período exportado e a mensagem apresentada. Uma data inicial muito antiga ou uma redução acentuada nas contagens de fechamentos também pode bloquear a análise. Reexporte o período necessário sem preencher preços manualmente. Veja [as verificações das datas](metodologia.md#verificações-antes-de-calcular-o-ranking).

## A semana termina antes da sexta-feira

O último dia com fechamento positivo no arquivo é anterior à sexta-feira esperada. Pode ter havido feriado, exportação parcial ou outro problema; o site não presume a causa.

Na página Nova análise, confira as três datas mostradas e suas contagens no CSV original. Se aceitar a comparação até a última data disponível, marque a confirmação e execute novamente. Trocar o arquivo ou a referência exige nova revisão. Pelo comando, a aceitação utiliza `--allow-nonfriday-end`.

A confirmação fica registrada e não dispensa cobertura suficiente, qualidade dos preços ou classificação oficial. Não aceite apenas para fazer uma mensagem desaparecer; primeiro confira se o período recebido é o que pretende analisar.

## A B3 está indisponível ou há classificação pendente

A análise precisa de registros oficiais suficientes para confirmar ON/PN nas duas datas. Arquivos já guardados podem permitir a execução; quando falta uma fonte necessária, o processamento informa a falha. Uma divergência de espécie ou identificação também pode exigir revisão.

Se a mensagem indicar indisponibilidade de acesso, tente novamente mais tarde. Se indicar conflito ou falta de confirmação de um instrumento, confira o código e os registros apresentados; repetir o mesmo envio não resolve automaticamente a divergência. Veja [as decisões da classificação](classificacao.md#três-decisões-possíveis).

## Há menos de 20 ações elegíveis

Após verificar preços e classificação, uma das opções ficou com menos de 20 ações. A ferramenta interrompe a análise inteira; não publica um top menor com o mesmo nome.

Confira qual janela falhou e os motivos informados. Reexporte os dados necessários mantendo o universo ON/PN e as datas previstas. A alternativa pode ter menos elegíveis porque utiliza outro fechamento inicial. Apenas alterar preços ou preencher ausências para atingir 20 não é uma correção válida.

## A fila está cheia ou atingi o limite de envios

A fila aceita uma análise em processamento e até duas aguardando. A mesma origem de acesso pode criar até três análises por hora; outros limites temporários do servidor também podem recusar um envio.

Leia a mensagem para distinguir fila cheia de limite por hora. Aguarde a liberação de capacidade ou do prazo. Reenviar repetidamente não acelera o cálculo. Uma análise já aceita continua acessível por sua URL de acompanhamento.

## Qual a diferença entre envio recusado e análise que falhou?

**Envio recusado:** a página Nova análise apresenta o problema antes de criar um trabalho na fila. Corrija o formato, as datas ou a condição indicada e envie novamente. Um pedido de revisão das datas também acontece antes da criação da análise.

**Análise que falhou:** o envio foi aceito, ganhou uma página própria e uma etapa posterior impediu a conclusão. Leia o motivo nessa página. Um novo envio cria outra análise; não retoma automaticamente o processamento anterior.

## O resultado deixou de estar disponível

Novas análises expiram após sete dias. Guardar o endereço web não preserva o resultado depois desse prazo. Baixe os arquivos durante a disponibilidade; a ausência de uma lista pública de envios também exige guardar a URL.

O case continua permanentemente na página inicial, acessível pelo logotipo V8 Capital no cabeçalho. Para conservar uma nova análise, veja [o que guardar](auditoria.md#o-que-guardar-para-reproduzir).

## A média que refiz com os percentuais da tela é diferente

Os percentuais da tela são arredondados para duas casas. A média do card utiliza os retornos calculados antes desse arredondamento.

Some os 20 retornos e divida por 20 usando `return_pct` do CSV da janela correspondente. Se utilizar `return_fraction`, multiplique a média por 100 para expressá-la em porcentagem. Somar os retornos sem dividir por 20 não produz a média. Confira também se o card e o CSV pertencem à mesma opção.

## Um alerta aparece, mas o ranking foi calculado. Qual foi o efeito?

Nem toda ocorrência impede o cálculo. Selecione a ação e leia a data, o campo e o motivo. Na auditoria, “Contexto de qualidade” e “Ocorrências por linha” oferecem a conferência mais ampla.

**Preço médio fora do mínimo–máximo:** o campo merece conferência, mas não entra na fórmula do retorno. **Fechamento fora desse intervalo:** atualmente recebe aviso e pode entrar no cálculo; como o fechamento é utilizado, essa inconsistência pode afetar o resultado. O aviso sozinho não bloqueia a execução.

A ferramenta preserva os números e não conclui a causa da inconsistência. Veja [os efeitos atuais dos controles](dados.md#controles-de-qualidade) antes de interpretar uma análise concluída como garantia de ausência de problemas.

## O alerta de preço médio muda o retorno?

O preço médio não entra na fórmula, que utiliza fechamento final dividido pelo inicial, menos um. Portanto, esse alerta sozinho não muda o cálculo.

Exemplo fictício: mínimo R$ 10,00, máximo R$ 12,00 e preço médio R$ 13,00. O médio está fora do intervalo recebido e exige conferência. Isso não prova que o fechamento esteja errado. Confira o campo específico na extração; não altere o fechamento por causa desse aviso sem verificar a fonte.

## Uma nova exportação produziu outra média. O que comparar?

Confira, nesta ordem: referência e datas dos preços; opção principal ou alternativa; preços recebidos; ações elegíveis e exclusões; fontes de classificação; versão do código. Preços ajustados podem ser revistos pela Economatica, e a composição do top 20 pode mudar.

Compare os CSVs e relatórios das duas análises, mantendo cada entrada identificada. Mesma semana no calendário não garante mesmos preços, mesma classificação ou mesmo ranking. Veja [como reproduzir](auditoria.md#reproduza-pelo-python).

## O que guardar para reproduzir depois dos sete dias?

Mantenha sua própria cópia do CSV original, a referência e os arquivos derivados baixados. Para repetir o cálculo com as mesmas condições, preserve também a versão do código, os parâmetros e as fontes B3 utilizadas. Os downloads públicos não incluem o bruto Economatica nem os arquivos originais B3.

Guardar só um print, o ranking ou a URL permite conservar parte do resultado, mas não todos os insumos necessários para repetir o processamento. Veja [a lista de reprodução](auditoria.md#o-que-guardar-para-reproduzir).

## Os guias antigos mudam quando a documentação é atualizada?

A cópia associada à execução permanece igual. Na auditoria, “Documentação desta execução” e “Ler os guias associados” permitem abrir a revisão arquivada. O menu principal “Documentação” abre os artigos atuais.

Uma associação realizada depois do processamento é identificada como posterior. Se a execução não possui guias associados, o site informa essa ausência. A cópia de uma nova análise tem o mesmo prazo de disponibilidade do resultado.
