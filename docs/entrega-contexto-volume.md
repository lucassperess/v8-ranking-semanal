# Entrega: ranking, volume e contexto

Versão publicada em 08/10/2026. Código da imagem em produção: [`ef0731d`](https://github.com/lucassperess/v8-ranking-semanal/tree/ef0731d). O repositório também contém os registros posteriores de publicação e este resumo.

## Acessos para avaliação

| Para | Link |
| --- | --- |
| Explorar o case | [Dashboard](https://ranking.lucaspsm.com/) |
| Entender os controles e gráficos | [Como usar](https://ranking.lucaspsm.com/documentacao/como-usar) |
| Conferir o método | [Metodologia](https://ranking.lucaspsm.com/documentacao/metodologia) |
| Consultar datas, exclusões e arquivos | [Auditoria do case](https://ranking.lucaspsm.com/metodologia) |
| Enviar outra extração | [Nova análise](https://ranking.lucaspsm.com/nova-analise) |
| Instalar e reproduzir | [Guia técnico](desenvolvimento.md) |

## Objetivo e método

A ferramenta transforma um CSV da Economatica em um ranking da semana-calendário anterior à referência. O Python calcula os retornos usando os fechamentos ajustados recebidos; arquivos datados da B3 confirmam as ações ON/PN elegíveis nas duas pontas. A ordenação usa os valores sem arredondamento e desempate pelo ticker. A média do top 20 é aritmética, com o mesmo peso para cada ação.

No case, a referência é **22/09/2026**. A janela principal compara **11/09 → 18/09** e inclui o movimento do primeiro pregão. A alternativa compara **14/09 → 18/09**, começando no fechamento do primeiro dia dentro da semana.

| Resultado do case | Valor |
| --- | --- |
| Ações elegíveis na janela principal | 308 |
| Média dos 20 maiores retornos — principal | 17,78% |
| Média dos 20 maiores retornos — alternativa | 15,93% |
| Ações com retorno positivo — principal | 119 de 308, ou 38,64% |

## O que foi acrescentado

- **Volume:** média diária do volume financeiro na semana, cobertura de dias válidos e tabela diária do top 20. Zero explícito entra na média; ausência, valor inválido e duplicata ficam identificados. Não foi acrescentado filtro de liquidez.
- **Contexto:** fatos empresariais datados, antecedentes financeiros e fontes, além de Ibovespa, S&P 500, Nasdaq e dólar PTAX. Nos novos envios, a coleta opcional começa depois da liberação do ranking; uma falha do contexto preserva os cálculos.
- **Documentação:** explicações literais de janelas, cards, volume, arquivos e reprodução, com cinco prints atuais e ampliação dentro da plataforma.

O contexto pode ter cobertura parcial. Um antecedente trimestral não é um acontecimento da semana, e uma notícia não comprova a causa da oscilação. O volume descreve a negociação recebida, sem explicar sozinho uma alta ou queda. Os novos textos recebem conferência automática; não têm revisão humana individual.

## Reprodução e disponibilidade

Para recalcular o ranking, preserve o CSV original, as fontes B3 e a versão do código. O [README](../README.md#gerar-um-novo-ranking) apresenta o comando Python. Para conferir o contexto ou reproduzir sua geração sem novas APIs, siga [Auditoria e reprodução](auditoria.md) e [os comandos técnicos](desenvolvimento.md#contexto-opcional-de-cada-envio). O replay exige também a pasta privada de fontes e respostas salvas; os downloads públicos, sozinhos, não bastam. Uma coleta nova pode encontrar outras evidências e produzir outro texto.

O case permanece na página inicial. Cada envio recebe seu próprio endereço web e fica disponível por sete dias; guarde a URL e baixe os derivados que quiser conservar. O CSV bruto não é oferecido para download e é removido após 24 horas. Arquivos aceitos têm até 10 MB, e o cálculo do ranking tem limite de dez minutos, seguido de até quinze minutos adicionais para o contexto.

## Verificações da entrega

Na preparação, **136 testes passaram sem falhas**, com um teste opcional ignorado. A publicação passou por **27 verificações públicas**: os cinco prints e quatro arquivos financeiros do case coincidiram com o repositório; uma análise anterior permaneceu acessível, e downloads privados continuaram bloqueados. Ranking, volume, contexto, troca de janela e ampliação móvel foram conferidos no navegador. Não foi repetida uma coleta paga na publicação.

A validação integrada de outra base usou preços e classificação artificiais, com fontes reais de contexto: verificou cálculos e reprodução, mas não representa uma análise de mercado real nem garante cobertura de notícias para qualquer envio. Veja o [registro dessa validação](../deploy/contexto-volume-validacao.md).

O standby foi preservado. Os [registros de publicação e restauração](../deploy/contexto-volume-publicado.md) identificam a imagem ativa e o caminho de retorno à versão anterior. A [v1.0.0](entrega-v1.0.0.md) permanece como registro histórico.
