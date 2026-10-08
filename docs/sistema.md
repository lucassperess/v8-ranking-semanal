# Como o sistema funciona

Você envia um CSV, o servidor executa os scripts Python e o site apresenta os arquivos calculados. A interface utiliza o mesmo processo de análise disponível pelo comando local; os controles do dashboard mudam a visualização dos resultados.

## Caminho de uma análise

1. **Envie o CSV e a referência:** na página Nova análise, escolha o arquivo e confira a semana indicada.
2. **O site verifica a entrada:** confere formato, tamanho, referência, datas disponíveis e limites de envio. Se os dados terminarem antes da sexta-feira, pede revisão. Um envio recusado nesta etapa ainda não entrou na fila.
3. **A análise aguarda sua vez:** após o envio aceito, o site abre uma página própria de acompanhamento. Guarde seu endereço web, a URL.
4. **O servidor executa o Python:** interpreta os dados, escolhe as datas, confirma os instrumentos nas fontes B3, calcula os retornos e produz os arquivos.
5. **O resultado aparece na mesma página:** quando os cálculos concluem, ficam disponíveis cards, ranking, gráficos, volume e auditoria. Uma falha do cálculo apresenta o motivo.
6. **O contexto é preparado:** a etapa opcional consulta fontes e prepara as leituras das empresas e dos mercados. O ranking já pode ser explorado enquanto isso; a aba Contexto informa o andamento e atualiza sem recarregar a página. Se a coleta falhar ou terminar com cobertura parcial, isso é informado na leitura.

## O que significa cada estado?

| Estado | O que está acontecendo | O que fazer |
| --- | --- | --- |
| Aguardando | O envio foi aceito e entrou na fila | Acompanhe pelo mesmo endereço; reenviar cria outro envio |
| Processando | O servidor está executando as etapas | Consulte o andamento na página da análise |
| Concluída | Os resultados foram produzidos | Explore o dashboard, abra a auditoria e baixe os arquivos |
| Falhou | Uma condição impediu a conclusão | Leia o motivo e confira a orientação antes de enviar novamente |

Uma confirmação das datas no formulário permite aceitar que os dados terminem antes da sexta-feira. Ela não libera uma classificação pendente nem corrige um preço. Veja [o que fazer em cada problema](duvidas.md).

O estado “Concluída” indica que os cálculos estão disponíveis. O contexto possui andamento próprio: pode estar em processamento, disponível ou indisponível. “Disponível” não garante notícias para todas as empresas e todos os temas. Consulte as fontes e a cobertura indicada no resultado.

## Por que o resultado é independente do case?

O contexto de cada novo envio também é preparado para a execução: utiliza as empresas presentes nos seus rankings e as datas da semana escolhida. O worker libera o ranking e continua a coleta opcional de contexto. A tela acompanha esse andamento. Essa etapa compartilha o limite total de dez minutos; se não terminar ou não houver credenciais, informa a indisponibilidade sem invalidar o ranking concluído.

A identidade é conferida por ticker e ISIN com a B3 antes de associar notícias a uma empresa. Uma identidade incompatível interrompe apenas a associação de notícias daquele ticker. Fontes, textos, versão do prompt e assinaturas ficam ligados à execução. Os textos do case nunca são copiados para outro envio.

Cada envio recebe uma identificação própria, uma entrada, uma referência e uma pasta de resultados. O case permanece disponível na página inicial; o logotipo V8 Capital leva ao resultado de referência. Os números de outra análise aparecem no endereço e na auditoria dela.

Os arquivos de resultado são calculados em Python. O navegador escolhe quais dados apresentar conforme a ação e a janela selecionadas; não calcula novamente o ranking semanal. As séries diárias também correspondem à janela escolhida. Na alternativa, o primeiro fechamento é o preço inicial e não possui retorno diário dentro dela.

## Prazos e limites

A fila comporta **uma análise em processamento e até duas aguardando**. Cada arquivo pode ter até 10 MB; o processamento tem limite de dez minutos após começar. A mesma origem de acesso pode criar até três análises por hora. Outros limites temporários do servidor também podem recusar novos envios, com mensagem na página.

O CSV original é removido após 24 horas. O resultado de um novo envio, seus derivados e os guias associados ficam disponíveis por sete dias. Guardar a URL não prolonga esse prazo; baixe os arquivos que quiser conservar e mantenha sua própria cópia da entrada. O case é permanente.

Não existe lista pública de envios nem download do CSV original. Quem possui a URL pode consultar os resultados derivados enquanto estiverem disponíveis.

## Guias associados ao resultado

Ao concluir uma análise pela interface, o servidor guarda uma cópia dos artigos disponíveis naquela versão da aplicação. A auditoria oferece a leitura dessa cópia. Alterar os artigos atuais não reescreve os guias arquivados de uma execução.

A cópia possui uma assinatura de conteúdo, que permite conferir sua integridade e ligação com a entrada e o código. Na leitura arquivada, o menu de assuntos navega dentro dessa cópia; a busca dos artigos atuais não é utilizada. Veja [como identificar a revisão](auditoria.md#versão-da-documentação).

## Componentes técnicos e responsabilidades

- **API:** parte da aplicação que recebe o envio e responde às consultas do navegador.
- **Fila:** armazenamento dos trabalhos aceitos que aguardam processamento.
- **Worker:** processo no servidor que retira um trabalho da fila e executa os scripts Python. Isso permite que o site continue atendendo os visitantes durante o cálculo.
- **Pipeline:** sequência de etapas de tratamento, seleção das datas, classificação, cálculo e geração dos arquivos.
- **Apresentação:** reúne os arquivos produzidos e prepara os dados que a interface mostra.

| Arquivo | Responsabilidade |
| --- | --- |
| `webapp/server.py` | Receber envios, responder consultas e servir arquivos públicos permitidos |
| `webapp/store.py` | Guardar execuções e organizar a fila |
| `webapp/worker.py` | Executar análises e remover dados após os prazos |
| `weekly_ranking.py` | Coordenar as etapas do cálculo e gerar relatórios |
| `webapp/presentation.py` | Adaptar resultados e preparar o contexto visual |
| `webapp/volume.py` | Conferir volumes recebidos, calcular médias e cobertura e recuperar o derivado salvo |
| `context_pipeline/` | Coletar fontes, gerar e conferir o contexto opcional e registrar sua reprodução |
| Navegador | Navegação, seleção e apresentação dos dados recebidos |

## Hospedagem e fontes

A aplicação web e o worker funcionam em dois contêineres na VPS, o servidor onde o site está hospedado. As execuções e as fontes B3 guardadas persistem fora desses contêineres. O serviço Traefik encaminha o endereço do site para a aplicação usando HTTPS.

A rotina de cálculo e a apresentação de volume não dependem de IA. O contexto opcional utiliza busca e leitura de fontes externas e um modelo por API; sua disponibilidade depende das credenciais, das fontes, do orçamento e do tempo restante. A obtenção de fontes B3 necessárias à classificação, por sua vez, pode interromper o cálculo. Consulte [as instruções de operação](../deploy/README.md) e [Auditoria e reprodução](auditoria.md#reproduza-pelo-python).

## Séries diárias e resultados anteriores

Resultados antigos que guardaram uma única série diária são adaptados durante a consulta: o servidor seleciona as observações de cada janela e remove a comparação anterior ao início da alternativa. Utiliza os dados diários já guardados, mesmo após a remoção do CSV original.

Essa adaptação não regrava o resultado histórico, os manifestos ou a documentação arquivada. O retorno semanal continua vindo dos arquivos da execução; os gráficos apresentam a janela selecionada.
