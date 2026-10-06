# Como o sistema funciona

O site utiliza o mesmo pipeline Python executável pelo comando local. A interface organiza o envio, acompanha o processamento e apresenta as saídas.

## Caminho de uma análise

1. **Envio:** o navegador envia CSV e referência à API, a porta de entrada do servidor.
2. **Validação:** a API verifica formato, tamanho, data e limites; atribui um identificador imprevisível à execução.
3. **Fila:** a execução aguarda sua vez em armazenamento persistente.
4. **Worker:** um processo separado retira um trabalho da fila e executa o Python. Ele evita bloquear a aplicação que atende os visitantes.
5. **Pipeline:** trata dados, seleciona datas, resolve classificações B3, calcula retornos e produz arquivos.
6. **Apresentação:** um adaptador reúne os resultados e prepara as séries diárias, preservando lacunas.
7. **Resultado:** o navegador consulta a API e apresenta ranking, gráficos, alertas e downloads permitidos.

Os estados públicos são aguardando, processando, concluída e falhou. Uma falha tem motivo legível; não vira uma tabela incompleta com aparência de sucesso.

## Responsabilidades

| Parte | Responsabilidade |
| --- | --- |
| `webapp/server.py` | Rotas, validação do envio e arquivos públicos permitidos |
| `webapp/store.py` | Persistência das execuções e fila |
| `webapp/worker.py` | Processamento e limpeza periódica |
| `weekly_ranking.py` | Orquestração do cálculo e relatórios |
| `webapp/presentation.py` | Adaptação dos resultados e contexto visual |
| Navegador | Navegação, seleção e apresentação |

## Limites públicos

Uma análise ativa e até duas aguardando. Cada arquivo pode ter até 10 MB, cada processamento até dez minutos e cada origem até três envios por hora.

O bruto é removido após 24 horas; resultados de teste ficam disponíveis por sete dias. A referência do case é permanente. Não há lista pública de envios ou download do CSV original. Quem possui o link de uma análise pode consultar o resultado derivado enquanto existir; o link não é autenticação.

## Hospedagem e fontes

A VPS usa dois contêineres: aplicação web/API e worker. O armazenamento de execuções e o cache de fontes B3 persistem fora dos contêineres. Traefik encaminha o subdomínio com HTTPS.

A rotina não depende de IA. A disponibilidade das fontes oficiais pode afetar uma nova análise se as evidências necessárias ainda não estiverem no cache.

Para operar ou manter a implantação, consulte [as instruções de deploy](../deploy/README.md). Para reproduzir o cálculo sem a interface, veja [Auditoria e reprodução](auditoria.md).
