# Documentação do ranking semanal

Esta pasta inicia a documentação editorial do projeto. O mapa abaixo descreve a organização proposta para a interface; apenas o artigo de metodologia foi preparado nesta etapa. As páginas e rotas propostas ainda não foram publicadas no site.

## Caminhos de leitura

| O que você quer fazer? | Por onde começar |
| --- | --- |
| Entender a entrega em poucos minutos | Comece aqui → Metodologia do ranking |
| Testar outra extração | Como usar o dashboard → Dados e tratamento → Nova análise |
| Conferir um número ou uma exclusão | Metodologia → Auditoria da execução consultada |
| Entender ou manter o código | Como o sistema funciona → Auditoria e reprodução |
| Resolver um erro ou interpretar uma lacuna | Problemas e dúvidas → Artigo relacionado |

## Mapa de páginas

Navegação principal proposta: **Ranking · Documentação · Nova análise**.

| Página | Conteúdo e exemplos | Estado |
| --- | --- | --- |
| Comece aqui | Objetivo, escopo, fontes, visão do fluxo e caminhos de leitura | Planejada |
| Como usar o dashboard | KPIs, tabela, seleção de ação, preços e retornos, hover, matriz, downloads, envio e acompanhamento | Planejada |
| [Metodologia do ranking](metodologia.md) | Semana, pontas, elegibilidade, fórmula, ordenação, média, alternativa e limitações | Artigo modelo preparado |
| Dados e tratamento | Contrato das nove colunas, codificação, dicionário, precisão, ausências, duplicatas e controles | Planejada |
| Classificação dos instrumentos | Hipótese pelo código, confirmação B3 por data, fontes, cache, conflitos e decisões | Planejada |
| Como o sistema funciona | Upload → API → fila → worker → Python → arquivos → apresentação; limites e retenção | Planejada |
| Auditoria e reprodução | Arquivos, procedência, versões, comando Python, execução sem internet com fontes disponíveis | Planejada |
| Problemas e dúvidas | Erros de formato, fontes indisponíveis, lacunas, semana incompleta, poucas ações e expiração | Planejada |

## Organização da interface

Estrutura proposta para uma página de artigo:

```text
Ranking · Documentação · Nova análise

Documentação / Metodologia do ranking

Menu de assuntos     Artigo                         Nesta página
Comece aqui          Título e resumo                Semana
Como usar            O que você vai entender        Elegibilidade
Metodologia          Explicação                     Cálculo
Dados                Diagrama / exemplo             Limites
Classificação        Como conferir
Sistema              Artigos relacionados
Auditoria
Dúvidas
```

- Menu de assuntos à esquerda e índice de seções em telas amplas; no celular, navegação recolhível e índice acessível antes do artigo.
- Texto de leitura com largura limitada, hierarquia tipográfica consistente, fundo escuro, contornos suaves e seleção cinza, preservando a identidade do dashboard.
- Diagramas com equivalente textual, tabelas legíveis e exemplos com unidades explícitas.
- Explicações essenciais visíveis no artigo. Tooltips servem para lembretes curtos, com acesso por teclado e toque.
- Links permanentes por assunto e seção; identificação da página atual e navegação de retorno.
- Busca por títulos, conteúdo e sinônimos, como “dados faltando”, “sem cotação” e “preço ausente”. Sua implementação fica para a fase da interface.
- Caminhos relacionados ao final de cada artigo, evitando repetir explicações extensas.

## Regras gerais e dados da execução

A documentação explica as regras. A auditoria de uma execução mostra suas próprias datas, preços, contagens, ocorrências e arquivos.

As rotas atuais `/metodologia` e `/analise/{id}/metodologia` já apresentam dados específicos da execução. Na migração, esses acessos devem continuar funcionando. Uma proposta é publicar os artigos em `/documentacao/{assunto}` e manter uma área de auditoria vinculada a cada análise, com links para os artigos aplicáveis.

Não substituir números de uma análise enviada pelos números do case. Não apresentar um exemplo histórico como valor fixo para novas execuções. A revisão da documentação aplicável deve ser identificada junto à versão do código; isso ainda precisa ser implementado para preservar a interpretação de execuções antigas.

## Padrão editorial

Cada artigo deve conter:

1. Título que descreva o assunto e resumo em linguagem simples.
2. O que é e por que a decisão foi tomada.
3. Funcionamento em etapas, acompanhado de exemplo quando útil.
4. Limitações, erros possíveis e o que o sistema faz nesses casos.
5. Como conferir a explicação nos arquivos ou no código.
6. Links para assuntos relacionados e referências externas pertinentes.

Termos como ETL, worker e hash precisam ser explicados na primeira ocorrência. Separar comportamento implementado, decisão metodológica e melhoria planejada. Na manutenção, atualizar o artigo na mesma alteração que modificar a regra correspondente.

O README da raiz continua sendo a entrada para instalação, comandos e manutenção. Os artigos ficam em Markdown no Git. Uma futura publicação no site deve utilizar esse conteúdo para reduzir divergências entre documentação e repositório.

## Ordem proposta de implementação

1. Revisar este mapa e o artigo modelo quanto a profundidade e linguagem.
2. Preparar guia de uso e artigos de dados/classificação, com capturas anotadas e exemplos.
3. Desenvolver a estrutura de documentação, navegação e busca.
4. Integrar auditoria por execução e a identificação da revisão aplicável.
5. Conferir navegação, leitura no celular, teclado, links e correspondência com o código antes de publicar.

## Referências de organização

A estrutura foi inspirada nos seguintes guias oficiais do Notion, adaptada às necessidades deste projeto:

- [Organizar e conectar conhecimento](https://www.notion.com/help/guides/organize-connect-and-scale-your-notion-knowledge-management-system).
- [Documentação e histórico](https://www.notion.com/help/guides/solidifying-documentation-for-your-startup).
- [Especificações técnicas](https://www.notion.com/help/guides/using-notion-for-tech-specs).
- [Links entre páginas](https://www.notion.com/help/guides/creating-links-and-backlinks).
- [Revisão e confiabilidade do conteúdo](https://www.notion.com/help/guides/verify-knowledge-your-teammates-can-trust-with-page-verification).
