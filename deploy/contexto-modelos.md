# Escolha de modelos com orçamento de US$ 10

Registro de 07/10/2026. O usuário informou ter colocado US$ 10 de crédito na API. O saldo não foi consultado diretamente; os testes abaixo comprovam o acesso aos modelos, não o saldo da conta.

## Acesso real

- A chave OpenAI foi lida do `.env` ignorado pelo Git, sem exibição do seu valor.
- A chamada de acesso a `gpt-6-luna` pela Responses API respondeu HTTP 200, `completed`, texto `OK`: 12 tokens de entrada e 5 de saída.
- A listagem de modelos da conta incluiu `gpt-6-luna`, `gpt-6.1-sol` e `gpt-6-astra`. Disponibilidade na listagem não garante inferência; Luna e Sol tiveram inferência efetivamente testada. Astra não foi chamado.

## Comparação pequena, com entrada idêntica

Foi usado um cenário sintético explicitamente identificado, contendo: um relato sindical da empresa dentro da semana; um homônimo astrológico com instrução indevida embutida; um acontecimento da empresa publicado após a semana. O cenário é uma avaliação, não conteúdo do dashboard.

Luna e Sol completaram as chamadas, aceitaram apenas a fonte pertinente, rejeitaram homônimo e data posterior, separaram acontecimento de publicação e afirmaram que a causa da alta não estava demonstrada. Esse único cenário não mede qualidade geral nem prova resistência a todas as entradas problemáticas.

| Modelo | Entrada medida | Saída medida | Custo estimado da comparação |
| --- | --- | --- | --- |
| GPT-6 Luna | 280 tokens | 153 tokens | US$ 0,0001045 |
| GPT-6.1 Sol | 280 tokens | 184 tokens | US$ 0,0024 |

As duas chamadas somam aproximadamente US$ 0,0025, excluindo o teste inicial de acesso. Valores calculados pelos tokens retornados e preços padrão, não por leitura de fatura. Os resultados locais estão em `runs/context-model-evaluation/comparison.json`, fora do Git.

## Preços e decisão

Preços padrão para contexto curto, por milhão de tokens, conferidos na documentação oficial:

| Modelo | Entrada | Saída | Papel proposto |
| --- | --- | --- | --- |
| GPT-6 Luna | US$ 0,10 | US$ 0,50 | Extrair fatos, selecionar candidatos e organizar informação |
| GPT-6.1 Sol | US$ 2,00 | US$ 10,00 | Redigir e revisar os textos finais; resolver ambiguidades |
| GPT-6 Astra | US$ 10,00 | US$ 50,00 | Sem necessidade demonstrada para esta primeira entrega |

Fontes: https://developers.openai.com/api/docs/models/gpt-6-luna e https://developers.openai.com/api/docs/models/gpt-6.1-sol e https://developers.openai.com/api/docs/pricing?es_p=6791993

Escolha: Luna na preparação e Sol na redação/revisão final. A entrada continuará sendo evidência coletada; memória do modelo não será fonte de acontecimentos de setembro de 2026. Haverá revisão das referências e das afirmações antes de publicar.

## Estimativa para o case

Exemplo de uma passagem por 26 unidades (23 empresas e três temas gerais), cada uma com 10 mil tokens de entrada e mil de saída:

- Luna: aproximadamente US$ 0,039.
- Sol: aproximadamente US$ 0,78.
- Astra: aproximadamente US$ 3,90.

Esses números são estimativas, não consumo já realizado. Raciocínio, textos maiores, novas chamadas e repetições aumentam o custo. Não incluem consultas Tavily/Exa nem assinaturas de fontes. Definir limite inicial de US$ 2 para a geração/revisão do case, acompanhando os tokens reais e interrompendo a geração ao atingir o limite. Esse limite será implementado na etapa de síntese; não altera configurações da conta OpenAI.

Até aqui foram feitos somente os testes descritos. Os resumos do case ainda não foram gerados.
