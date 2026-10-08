# Comece aqui

Esta ferramenta transforma uma extração de dados financeiros da plataforma Economatica em um ranking semanal de ações ON e PN. Você pode explorar o resultado do case ou enviar outro arquivo no mesmo formato para testar o processo e obter uma nova análise.

## Fontes dos dados

**Economatica:** fornece os preços utilizados no cálculo dos retornos e as demais informações presentes na extração. A ferramenta utiliza a coluna de fechamento ajustado para proventos já exportada pela Economatica; não aplica novos ajustes aos preços.

**B3:** fornece os registros oficiais usados para confirmar se cada instrumento é uma ação ordinária (ON) ou preferencial (PN) nas datas utilizadas. Os preços usados no cálculo continuam sendo os da Economatica.

## O que a ferramenta entrega

- **Ranking semanal:** as 20 ações ON e PN com os maiores retornos entre aquelas com preços válidos e classificação confirmada nas duas datas do cálculo. Cada linha mostra o retorno individual daquela ação no período.
- **Média do top 20:** um card mostra a média aritmética dos 20 retornos do ranking selecionado. Cada ação tem o mesmo peso nessa média.
- **Volume do top 20:** a tabela do ranking mostra o volume financeiro médio por dia e quantos dias possuem dados válidos. A tabela diária permite consultar os valores de cada data da semana. Volume ausente não vira zero; uma ação não é retirada do ranking por ter volume pequeno.
- **Contexto das empresas e dos mercados:** a aba Contexto reúne acontecimentos datados, informações anteriores e links para as fontes da empresa selecionada. A seção Referências de mercado apresenta Ibovespa, índices americanos e dólar, seguida de acontecimentos confirmados nas fontes consultadas. A cobertura pode ser parcial; essas informações não comprovam a causa de cada retorno.
- **Duas formas de medir a mesma semana:** a principal inclui a mudança de preço até o primeiro fechamento disponível dentro da semana; a alternativa começa no fechamento desse dia e mede a mudança a partir dali. Ambas terminam no mesmo fechamento final. Veja o exemplo abaixo.
- **Gráficos e tabela diária:** preços e retornos diários da ação selecionada; distribuição dos retornos semanais de todas as ações elegíveis; e uma tabela que cruza as ações do top 20 com as datas. Cada célula mostra a variação do fechamento anterior para o fechamento da data indicada, respeitando a janela selecionada.
- **Detalhes das ações:** preços inicial e final, diferença em reais por ação, maior retorno do ranking e faixa de retornos do top 20. Quando há alertas nos dados das duas datas usadas para uma ação, uma marca aparece junto ao ticker. Selecionar a ação atualiza o painel com a explicação.
- **Arquivos para conferir o resultado:** a auditoria reúne as datas do cálculo, os códigos excluídos e seus motivos, os rankings em CSV, as ocorrências nos dados e as evidências oficiais usadas na classificação. Também permite abrir a cópia da documentação associada àquela execução.

### Entenda as duas janelas com preços simples

Imagine uma ação com estes fechamentos: **R$ 10 na sexta anterior**, **R$ 11 na segunda** e **R$ 12 na sexta final**. Estes preços são ilustrativos, não os do case.

| Opção | Preços comparados | Retorno | O que inclui |
| --- | --- | --- | --- |
| Semana completa | R$ 10 → R$ 12 | 20,00% | A mudança da segunda-feira e o restante da semana |
| Dentro da semana — alternativa | R$ 11 → R$ 12 | 9,09% | A mudança depois do fechamento da segunda-feira |

A alternativa não acompanha uma semana em andamento até o dia atual. Ela usa **a mesma semana anterior e a mesma data final da principal**, mas começa por outro preço.

No case, a semana analisada é **14 a 20/09/2026**. A principal compara **11/09 → 18/09**; a alternativa compara **14/09 → 18/09**. Na alternativa, segunda-feira fornece o preço inicial: seu retorno diário aparece como **—**. O primeiro retorno é o de terça, comparando o fechamento de segunda com o de terça. Em outra extração, as datas podem ser diferentes.

## Como funciona uma nova análise

1. Abra [Nova análise](/nova-analise), envie um CSV no [formato documentado](dados.md) e escolha a data de referência. Essa data identifica a semana-calendário anterior que será analisada.
2. A ferramenta executa o mesmo processo usado no case: trata os dados, seleciona as datas, confirma as ações, calcula os retornos e prepara os resultados. Se houver uma pendência que impeça o cálculo, a página explica o motivo.
3. O site abre uma página própria para acompanhar o processamento. Quando os cálculos terminam com sucesso, **o resultado aparece nessa mesma página**, com seus cards, ranking, gráficos, volume e downloads. A coleta opcional de contexto continua depois disso; a aba Contexto informa o andamento e recebe a leitura quando ela fica disponível.
4. **Guarde o endereço web dessa página, a URL exibida no navegador.** Você poderá voltar a ela ou compartilhá-la. Não existe uma lista pública para procurar os envios.
5. Dentro do resultado, **“Auditoria desta execução”** abre as datas, decisões e arquivos daquela análise. Os exemplos desta documentação pertencem ao case; os números do seu envio estão no seu resultado e na sua auditoria.
6. O resultado e seus arquivos ficam disponíveis por **sete dias**. Baixe os arquivos que quiser conservar antes de expirar: guardar a URL não prolonga esse prazo.

Cada envio cria uma análise independente. Ele **não substitui o resultado do case**, que continua disponível permanentemente na [página inicial](/). O logotipo V8 Capital no cabeçalho leva ao resultado de referência. A opção “Ranking” acompanha a execução consultada. A documentação arquivada de uma execução preserva a revisão associada a ela; o menu “Documentação” abre os artigos atuais.

## Explore os guias

Para aprender a usar as abas, consultar o volume e interpretar as fontes, siga para [Como usar o dashboard](como-usar.md). Para conferir os números e saber o que guardar, consulte [Auditoria e reprodução](auditoria.md). Se a coleta de contexto falhar, seus cards, ranking, volume e gráficos continuam disponíveis.

Abra um dos artigos abaixo para consultar as regras, usar o dashboard ou conferir sua análise.
