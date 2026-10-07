# Problemas e dúvidas

## Por que a matriz tem células vazias?

Na opção “Dentro da semana”, o primeiro dia tem “—” porque seu fechamento é o preço inicial. Não falta necessariamente um preço, e não é retorno zero. O primeiro retorno aparece na próxima data com comparação válida.

Nas demais datas, um retorno diário precisa do preço da data e do preço da data consecutiva anterior na extração. Se um estiver ausente, inválido ou conflitante, a célula fica vazia. Ela não significa retorno zero.

Exemplo: há preço na sexta, falta na segunda e há preço na terça. Não calculamos segunda; também não apresentamos sexta → terça como um retorno diário de terça. Veja [gráficos diários](metodologia.md#como-interpretar-os-gráficos-diários).

## Por que a alternativa não mostra retorno na segunda-feira?

No case, a alternativa começa no fechamento de segunda, 14/09. Para ter retorno na própria segunda, precisaríamos comparar com a sexta anterior, 11/09, que fica fora dessa janela. Por isso a segunda aparece como “— / preço inicial”. A terça compara 14/09 → 15/09 e é o primeiro retorno da alternativa. Se a primeira data disponível cair em outro dia, a mesma regra se aplica a ela.

As duas opções terminam no mesmo último fechamento da semana anterior. “Dentro da semana” não significa uma semana em andamento até o dia atual.

## Como uma ação com lacunas aparece no top 20?

O retorno semanal depende das duas pontas semanais. Uma ausência no meio pode impedir comparações diárias sem impedir o cálculo semanal. Não há preenchimento das lacunas.

## Meu arquivo foi rejeitado por esquema inesperado

Confira separador, nomes e ordem das nove colunas. O site aceita o formato documentado; uma outra configuração de exportação precisa de adequação explícita antes do processamento. Consulte [Dados e tratamento](dados.md).

## A data é inadequada ou não há cotações suficientes

A referência define a semana-calendário anterior. Confira se o CSV contém dados antes dela e dentro dela. Uma referência futura é rejeitada pelo formulário/API. Uma cobertura muito baixa nas pontas também impede o ranking.

## A semana termina antes da sexta-feira

Pode haver feriado ou extração parcial. O programa exige revisão e não presume a causa. O formulário mostra as três datas encontradas e suas contagens de fechamentos positivos. Após conferir a extração e o calendário, marque a aceitação explícita e execute novamente. Trocar o arquivo ou a referência invalida a confirmação. O comando Python mantém `--allow-nonfriday-end`. Essa decisão fica no relatório e, para envios pela interface, no registro do envio; ela não dispensa cobertura, qualidade dos preços ou evidência B3.

## A B3 está indisponível ou há classificação pendente

Uma consulta pode falhar por indisponibilidade da fonte. Fontes suficientes já guardadas podem permitir a execução; se faltarem evidências necessárias, ela falha com explicação. Também pode haver códigos históricos ou conflitos que precisam de revisão. Não se publica uma ON/PN sem confirmação nas duas pontas.

## Há menos de 20 ações elegíveis

O pipeline exige 20 ações para produzir o top 20. Confira a abrangência da extração, as duas datas e as exclusões. Não reduzimos automaticamente o tamanho do ranking.

## A fila está cheia ou atingi o limite de envios

Há uma execução ativa e até duas esperando; cada origem pode enviar três vezes por hora. Aguarde capacidade ou a liberação do limite, conforme a mensagem. Reenviar repetidamente não acelera o processamento.

## O resultado deixou de estar disponível

Resultados de teste expiram após sete dias. Salve os derivados enquanto estiverem disponíveis. A demonstração original permanece fixa. Guardar só o link não preserva os arquivos após a expiração.

## A média parece diferente da soma da tabela

A média utiliza os retornos calculados antes do arredondamento da apresentação. Refaça a conta com `return_fraction` ou `return_pct` dos CSVs, não apenas com os percentuais de duas casas da tela.

Para conferir decisões e procedência, abra [Auditoria e reprodução](auditoria.md).


## O alerta de preço médio muda o retorno?

Não, por si só. Quando o preço médio fica abaixo do mínimo ou acima do máximo informado no CSV, os valores merecem conferência. O ranking usa o fechamento inicial e o final, não o médio. O sistema não presume a causa nem corrige valores automaticamente. Um alerta no próprio fechamento merece atenção porque esse preço entra no cálculo. O painel explica a diferença para cada ocorrência.

## Os guias antigos mudam quando a documentação é atualizada?

A cópia associada à execução permanece igual. Abra “Documentação desta execução” na auditoria para ler a revisão arquivada. Uma associação realizada depois do processamento é identificada como posterior; se a execução não registrou guias, o site informa isso. A documentação do menu principal mostra os artigos atuais.
