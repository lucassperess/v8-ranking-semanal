# Etapa local — distribuição da reserva e aprofundamento das lacunas

Data: 08/10/2026. Contrato novo: `run-context-1.3`.

## Implementado

- Reserva conservadora padrão de US$ 6 para modelos: 80% empresas, 20% mercado.
- Parcelas protegidas na primeira rodada e recuperação do saldo ao final dela.
- Reuso das fontes e respostas salvas; nenhuma revisão adicional sem eventos válidos.
- Busca complementar limitada a quatro empresas e preservação do conteúdo anterior.
- Filtros adicionais para perfis, agendas, tabelas gerais e boletins de preços.
- Registro de reservas, tentativas de API e tokens informados, sem afirmar faturamento.

## Conferência real isolada

PLAS3, TASA3/TASA4, BIED3 e TXRX4 continuam com antecedentes financeiros.
As buscas adicionais não confirmaram um acontecimento empresarial útil.
Um formulário rotineiro encontrado para BIED3 não representa mudança empresarial.
Os filtros foram revistos e conferidos em uma segunda rodada.

Somando essas duas rodadas: seis chamadas novas OpenAI, quatro buscas e quatro
extrações Tavily. Reserva conservadora adicional: US$ 0,426474. Tokens informados:
45.436 de entrada e 1.461 de saída. Esses números não são o custo faturado.
As respostas Tavily utilizadas não informam créditos consumidos.

Evidências privadas preservadas em `runs/context-step4-budget-2026-10-08/`,
fora do Git. Os testes isolados não comprovam que todas as empresas cabem no
orçamento e no prazo em uma execução completa.

## Próxima etapa

Verificação local concluída: 133 testes, um ignorado, nenhuma falha; Ruff e
`git diff --check` aprovados. `scripts.verify_artifacts` confirmou assinaturas,
retornos, ordenação, top 20 e médias da demonstração histórica.

Executar uma geração completa em nova pasta; conferir cobertura, tempo,
consumo informado, igualdade dos rankings e reprodução sem novas APIs.
Nenhuma publicação ou alteração da VPS foi realizada nesta etapa.
A versão publicada e o standby permanecem preservados.
