# Entrega v1.0.0

Verificação concluída em 06/10/2026. Esta versão identifica a entrega do pipeline, da interface pública e dos guias; a demonstração mantém seus arquivos e sua procedência históricos.

## Acessos

- [Dashboard](https://ranking.lucaspsm.com/)
- [Auditoria da demonstração](https://ranking.lucaspsm.com/metodologia)
- [Nova análise](https://ranking.lucaspsm.com/nova-analise)
- [Documentação](https://ranking.lucaspsm.com/documentacao)
- [Código desta entrega](https://github.com/lucassperess/v8-ranking-semanal/tree/v1.0.0)

## Resultado de referência

| Verificação | Resultado |
| --- | --- |
| Referência | 22/09/2026 |
| Janela principal | 11/09/2026 → 18/09/2026 |
| Top | 20 ações, mesma ordem da entrega histórica |
| Média principal | 17,78% |
| Janela alternativa | 14/09/2026 → 18/09/2026; média 15,93% |
| Universo | 308 ações elegíveis, 320 códigos com duas pontas válidas |
| Exclusões | 12 instrumentos com preços válidos; 158 códigos sem duas pontas válidas |
| Arquivos públicos | 29 downloads conferidos byte a byte contra o Git |

O comando Python foi executado novamente sobre o CSV original, com referência 22/09/2026 e fontes oficiais já armazenadas (`--offline`). Os CSVs dos dois top 20 reproduzidos foram comparados integralmente aos versionados e à ordem apresentada pela API. A verificação dos derivados conferiu assinaturas, retornos decimais, ordenação e médias.

## Replicabilidade pelo site

Dois envios foram executados pelo formulário público e concluídos na VPS. As médias abaixo pertencem a bases de teste e não substituem a demonstração.

| Cenário | Execução | Principal | Alternativa |
| --- | --- | --- | --- |
| Outra extração, sem ECOM3 | `2281aef1ba374ea98879eb9bea75eb59` | 15,77% | 14,97% |
| Extração encerrada em 17/09 | `0a3cf9ba9b974014a4b5f1264845cf76` | 15,59% | 12,72% |

A primeira usou referência 21/09/2026, que seleciona a mesma semana do case. A segunda usou 22/09/2026 e exigiu revisão das datas e aceite explícito, inicialmente desmarcado, antes de entrar na fila. O aceite foi conferido em `analysis_request.json`.

Cada execução expôs 30 arquivos derivados. Todos foram baixados e submetidos à verificação de assinaturas e aritmética. Ambas arquivaram os guias na conclusão (`at_completion`). A tentativa de baixar o bruto retornou 404. Os links de teste expiram após sete dias; a demonstração é permanente.

## Controles e interface

- CSV incompatível, data futura e período sem cobertura retornaram 422 com orientação, pela API pública.
- A suíte local passou nos 57 testes, incluindo a regressão com o CSV original. Os casos artificiais cobrem falhas de fontes/classificação, revisão vinculada ao arquivo e à referência, fila, limite por origem com liberação após uma hora e retenção com resultado expirado após sete dias.
- Ruff, verificação dos artefatos, Prettier e verificações da interface passaram. A execução [37536911915 do CI](https://github.com/lucassperess/v8-ranking-semanal/actions/runs/37536911915) aprovou Python 3.11/3.12 no Linux, Python 3.11 no Windows e a interface.
- Revisão no navegador em 1280 px e larguras móveis de 320, 390 e 430 px: cabeçalho, menu, índices da documentação, auditoria e ranking. As páginas conferidas não apresentaram transbordamento horizontal global; tabelas extensas têm sua própria rolagem.
- Seleção de ativo por teclado e alternância entre preços em R$ e retornos diários em % foram verificadas.
- Foi corrigida a leitura assíncrona do CSV para preservar uma referência editada pelo usuário. Um teste com leitura adiada reproduz a condição de corrida e integra a verificação da interface no CI.

## Publicação e limites da verificação

A aplicação está publicada com HTTPS na VPS, atrás do Traefik. Os contêineres de aplicação e worker usam armazenamento persistente. A atualização preserva esse armazenamento e os demais serviços. Nenhum resultado de teste substitui o case.

Os testes móveis usam tamanhos de viewport de navegador; não substituem testes em aparelhos físicos Android/iOS. A indisponibilidade da B3 foi simulada nos testes locais, sem interromper fontes de produção. Os dois envios completos verificaram o fluxo real de processamento na VPS.

Os testes de retenção usam relógio controlado; não foi necessário aguardar 24 horas ou sete dias. A disponibilidade futura de fontes oficiais continua sendo uma dependência externa. O sistema explica a falha e não publica um ranking incompleto como concluído.

Para comandos, arquitetura e reprodução, consulte [referência técnica](referencia-tecnica.md), [desenvolvimento](desenvolvimento.md) e [decisões](decisoes.md).
