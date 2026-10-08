# Conferência local da seleção de fontes — 08/10/2026

Esta etapa não publicou código, imagens ou resultados na VPS. A versão pública
e o standby permanecem preservados.

## Alterações conferidas

- Filtros de identidade, URLs inválidas, páginas sociais, cotações e duplicatas.
- Prioridade para documentos oficiais e resultados de RI na seleção.
- Catálogo CVM dos 90 dias anteriores, com reserva de vagas para antecedentes.
- Trecho contínuo com até 3.000 caracteres, preservando a evidência original.
- Abreviação `PART` retirada da consulta, sem alterar a identidade oficial.
- Antecedentes, relatórios financeiros e documentos institucionais separados.
- Documento posterior ao fechamento fora da contagem de cobertura aproveitável.
- Reprodução sem criar uma nova solicitação de IA quando a resposta não existe
  no arquivo salvo.

## Método da conferência

Foram copiados, por leitura, os derivados e parte da coleta privada da execução
pública `0d6dc1e1bad04e44a3c9daa5ed036a5b` para uma pasta local independente.
Os catálogos e documentos arquivados foram reaproveitados quando compatíveis;
as novas consultas e suas respostas foram salvas com identificação própria.

O primeiro ensaio coletivo manteve a reserva padrão de US$ 3,00. Ele confirmou
um bloqueio em geração/revisão de quatro empresas. Esses casos foram testados
separadamente com os mesmos textos, sem novas buscas. Outros testes locais
conferiram antecedentes que a IA inicialmente recusou por serem anteriores à
semana e as consultas com o nome abreviado. As regras de verificação não foram
relaxadas. O serviço mantém a reserva padrão; sua distribuição continua sendo
uma etapa posterior.

O resultado final foi montado com as evidências e respostas salvas, impedindo
chamadas de rede e novas despesas. Em seguida, um replay também sem rede
reproduziu exatamente `company.json` e `market.json`. Essa conferência mede a
qualidade e a reprodução do conteúdo obtido nos testes; não demonstra que uma
geração nova, com a reserva padrão, revise tudo em uma única execução.

## Resultado final

| Medida | Resultado |
| --- | --- |
| Empresas das duas janelas conferidas | 23, correspondentes a 24 tickers |
| Empresas com acontecimentos/antecedentes empresariais verificados até o fechamento | 19 |
| Empresas com apenas antecedente financeiro | 4 |
| Empresas com acontecimentos divulgados na semana, até o fechamento | 8 |
| Empresas com acontecimentos anteriores | 15 |
| Preços, retornos e observações das ações | Idênticos aos da execução pública |
| Replay empresarial e de mercado | Correspondência exata, sem APIs |
| Testes automatizados | 123 aprovados e um ignorado; 124 no total |

Ruff, conferência das assinaturas/cálculos dos derivados históricos e
`git diff --check` também passaram. Não houve alteração visual nesta etapa.

Os grupos de oito e quinze empresas se sobrepõem: não devem ser somados.
Cobertura documental não comprova a causa das variações de preço.

**Ainda sem acontecimento empresarial aproveitável:** PLAS3, TASA3/TASA4,
BIED3 e TXRX4. Elas possuem antecedente financeiro confirmado. Relatórios
trimestrais, convites e formulários rotineiros não foram usados para aumentar
artificialmente a contagem de acontecimentos. Para TXRX4, o catálogo arquivado
não tinha documento IPE entregue no intervalo de 90 dias; isso não prova que
não existam informações em outras fontes.

O primeiro ensaio descartou 83 resultados sem identidade explícita, 61
resultados sociais e 21 textos sem identificação da empresa. São contagens de
itens consultados, não de empresas ou de fatos falsos.

A soma das reservas estimadas dos ensaios foi US$ 4,153798. Esse valor inclui
testes separados e não é cobrança efetiva da OpenAI nem preço por análise.
As consultas Tavily têm contabilização própria. O orçamento do serviço não foi
alterado. A cobertura dos temas macroeconômicos não foi ampliada nesta etapa.

## Evidências locais e próxima etapa

Os arquivos privados ficam em `runs/context-step3-2026-10-08/`, fora do Git:
`analysis/` registra o ensaio coletivo; os resumos isolados registram as
conferências complementares; `final-analysis/` guarda a composição final e seu
replay. `validation-summary.json` reúne contagens e a comparação dos preços.

Próxima etapa: organizar a reserva para que uma execução nova possa revisar
todas as empresas e os temas de mercado, conferir as quatro lacunas e repetir
o teste completo antes de publicar.
