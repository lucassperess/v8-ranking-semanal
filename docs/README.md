# Documentação do ranking semanal

Esta pasta contém os oito artigos publicados pela interface em `/documentacao`. O site lê os arquivos Markdown versionados neste repositório e fornece navegação por assunto, índice de seções e busca. Este mapa orienta a leitura dos conteúdos publicados.

## Caminhos de leitura

Para manutenção do código, consulte o [roteiro técnico e comandos](desenvolvimento.md), o [registro de decisões](decisoes.md) e as [orientações para agentes](../AGENTS.md). Esses documentos técnicos ficam no GitHub; os oito artigos de uso continuam no site.

| O que você quer fazer? | Por onde começar |
| --- | --- |
| Entender a entrega em poucos minutos | Comece aqui → Metodologia do ranking |
| Testar outra extração | Como usar o dashboard → Dados e tratamento → Nova análise |
| Conferir um número ou uma exclusão | Metodologia → Auditoria da execução consultada |
| Entender ou manter o código | Como o sistema funciona → Auditoria e reprodução |
| Resolver um erro ou interpretar uma lacuna | Problemas e dúvidas → Artigo relacionado |

## Mapa de páginas

Navegação principal: **Ranking · Documentação · Nova análise**.

| Página | Conteúdo e exemplos | Estado |
| --- | --- | --- |
| Comece aqui | Objetivo, escopo, fontes, visão do fluxo e caminhos de leitura | Publicado |
| Como usar o dashboard | KPIs, tabela, seleção de ação, preços e retornos, hover, matriz, downloads, envio e acompanhamento | Publicado |
| [Metodologia do ranking](metodologia.md) | Semana, pontas, elegibilidade, fórmula, ordenação, média, alternativa e limitações | Publicado |
| Dados e tratamento | Contrato das nove colunas, codificação, dicionário, precisão, ausências, duplicatas e controles | Publicado |
| Classificação dos instrumentos | Hipótese pelo código, confirmação B3 por data, fontes, cache, conflitos e decisões | Publicado |
| Como o sistema funciona | Upload → API → fila → worker → Python → arquivos → apresentação; limites e retenção | Publicado |
| Auditoria e reprodução | Arquivos, procedência, versões, comando Python, execução sem internet com fontes disponíveis | Publicado |
| Problemas e dúvidas | Erros de formato, fontes indisponíveis, lacunas, semana incompleta, poucas ações e expiração | Publicado |

## Organização da interface

Estrutura de uma página de artigo:

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
- Busca por títulos, conteúdo e sinônimos, como “dados faltando”, “sem cotação” e “preço ausente”. A busca consulta títulos, descrições e conteúdo dos artigos.
- Caminhos relacionados ao final de cada artigo, evitando repetir explicações extensas.

## Regras gerais e dados da execução

A documentação explica as regras. A auditoria de uma execução mostra suas próprias datas, preços, contagens, ocorrências e arquivos.

As rotas atuais `/metodologia` e `/analise/{id}/metodologia` já apresentam dados específicos da execução. Esses acessos permanecem funcionando como auditoria. Os artigos são publicados em `/documentacao/{assunto}`. O parâmetro `?analise={id}` preserva o link da execução consultada ao navegar entre os artigos.

Não substituir números de uma análise enviada pelos números do case. Não apresentar um exemplo histórico como valor fixo para novas execuções. A auditoria identifica a revisão arquivada dos guias e permite abrir seus artigos. Novas análises registram essa cópia na conclusão; associações de execuções anteriores são identificadas como posteriores à execução.

## Padrão editorial

Cada artigo deve conter:

1. Título que descreva o assunto e resumo em linguagem simples.
2. O que é e por que a decisão foi tomada.
3. Funcionamento em etapas, acompanhado de exemplo quando útil.
4. Limitações, erros possíveis e o que o sistema faz nesses casos.
5. Como conferir a explicação nos arquivos ou no código.
6. Links para assuntos relacionados e referências externas pertinentes.

Termos como ETL, worker e hash precisam ser explicados na primeira ocorrência. Separar comportamento implementado, decisão metodológica e melhoria planejada. Na manutenção, atualizar o artigo na mesma alteração que modificar a regra correspondente.

O README da raiz continua sendo a entrada para instalação, comandos e manutenção. Os artigos ficam em Markdown no Git. O site utiliza esse conteúdo para reduzir divergências entre documentação e repositório.

## Exemplos e histórico

O [guia de uso](como-usar.md) contém capturas da referência com instruções de leitura. A auditoria oferece a cópia dos artigos associada à execução e o arquivo `documentation_snapshot.json`, com textos e assinaturas. Artigos atuais podem evoluir sem substituir essa cópia. Veja [Auditoria](auditoria.md) para os limites da associação histórica.

## Referências de organização

A estrutura foi inspirada nos seguintes guias oficiais do Notion, adaptada às necessidades deste projeto:

- [Organizar e conectar conhecimento](https://www.notion.com/help/guides/organize-connect-and-scale-your-notion-knowledge-management-system).
- [Documentação e histórico](https://www.notion.com/help/guides/solidifying-documentation-for-your-startup).
- [Especificações técnicas](https://www.notion.com/help/guides/using-notion-for-tech-specs).
- [Links entre páginas](https://www.notion.com/help/guides/creating-links-and-backlinks).
- [Revisão e confiabilidade do conteúdo](https://www.notion.com/help/guides/verify-knowledge-your-teammates-can-trust-with-page-verification).
