# Conferência da documentação de contexto e volume

Data: 08/10/2026. Alterações locais, sem publicação.

## Escopo entregue

- Guias revisados para explicar volume financeiro diário, média e cobertura, incluindo a diferença entre zero e ausência.
- Contexto explicado como evidências e antecedentes, com limites de cobertura e sem atribuir automaticamente a causa dos retornos.
- Distinção entre conferir arquivos públicos, recalcular resultados financeiros, reproduzir respostas salvas e realizar uma nova coleta.
- Reprodução do contexto exige preservar a pasta privada de evidências e a versão correspondente do código; os arquivos públicos, sozinhos, não bastam.
- Caminho de navegação corrigido: o logotipo retorna ao case; o menu Ranking acompanha a execução consultada.
- Cinco capturas atuais do case: ranking com volume, painel ECOM3, contexto ESTR4, volume diário do top 20 e contexto de mercado.

## Qualidade das imagens

As capturas vieram do dashboard local com os dados do case, sem substituir os números por dados fictícios. Os enquadramentos foram conferidos para preservar os conteúdos, as datas e, nas tabelas, as vinte ações. As imagens foram inspecionadas em sua resolução salva, sem ampliação artificial. A documentação usa o arredondamento existente: 14 px nas imagens do artigo e 12 px na ampliação.

As referências antigas substituídas foram retiradas dos artigos atuais. Os arquivos antigos permanecem disponíveis para não quebrar os guias arquivados de execuções anteriores.

## Verificações

- 20 testes relevantes da aplicação web e dos guias arquivados: aprovados.
- 237 links internos e 21 referências de imagens dos oito artigos: nenhum destino ausente.
- Onze imagens do guia Como usar: carregadas com dimensões naturais válidas.
- Ruff, verificação dos artefatos do case, formatação e checagem do frontend: aprovados.
- `git diff --check`: aprovado.
- Controles de ampliação, zoom e fechamento conferidos no desktop e no mobile; imagens carregadas e ausência de transbordamento horizontal conferidas no mobile.

Limite da conferência visual: a captura do viewport da página longa de documentação retornou uma imagem preta; a captura da página inteira não preservou corretamente a sobreposição do modal. Por isso, a ampliação no mobile foi verificada pelo estado dos controles e pelo carregamento da imagem, sem afirmar uma inspeção visual completa do modal nesse dispositivo.

## Preservação

Nenhuma chamada nova às APIs foi realizada nesta revisão. O ranking, os preços, os artefatos assinados e os guias arquivados não foram alterados. Não houve push, deploy ou alteração da versão standby.
