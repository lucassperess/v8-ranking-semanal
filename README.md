Média dos retornos do top 20: 17,78%

# Ranking semanal de ações

[![Verificações do projeto](https://github.com/lucassperess/v8-ranking-semanal/actions/workflows/checks.yml/badge.svg)](https://github.com/lucassperess/v8-ranking-semanal/actions/workflows/checks.yml)

Case em Python 3.11+ que recebe um CSV da Economatica, confirma ações ON/PN com fontes datadas da B3 e calcula o top 20 da semana anterior. A interface usa o mesmo pipeline para novas extrações, com resultados independentes.

## Explore a entrega

| Quero… | Acesso |
| --- | --- |
| Ver o ranking e os gráficos | [Dashboard público](https://ranking.lucaspsm.com/) |
| Conferir números, exclusões e arquivos | [Auditoria do case](https://ranking.lucaspsm.com/metodologia) |
| Testar outra extração | [Nova análise](https://ranking.lucaspsm.com/nova-analise) |
| Entender as regras e o processo | [Documentação](https://ranking.lucaspsm.com/documentacao) |
| Ler o resultado sem usar o site | [Entrega de referência](resultados/2026-09-22/README.md) |
| Conferir a versão e as verificações da entrega | [Entrega v1.0.0](docs/entrega-v1.0.0.md) |

**Referência: 22/09/2026.** Pontas principais: 11/09 → 18/09; 308 ações elegíveis, 20 selecionadas, média **17,78%**. A janela alternativa usa 14/09 → 18/09 e tem média **15,93%**. São dados históricos da extração, sem atualização em tempo real.

## Regras essenciais

- Semana-calendário anterior à referência; fechamento anterior à semana até o último fechamento nela.
- Retorno = fechamento ajustado final ÷ inicial − 1. Preços vêm da Economatica; a B3 confirma a espécie nas duas datas.
- Universo ON/PN, sem filtro de liquidez. Os 20 maiores retornos usam precisão decimal, desempate pelo ticker e média aritmética; arredondamento apenas na apresentação.
- Ausências permanecem ausências. Pendências de cobertura, duplicatas ou classificação impedem um resultado anunciado como completo.
- Semana terminada antes de sexta exige revisão e aceitação explícita. A confirmação não dispensa os demais controles.

## Gerar um novo ranking

Com Python 3.11+ disponível, na raiz do repositório:

```powershell
python weekly_ranking.py --input "CAMINHO/economatica.csv" --reference-date 2026-09-22 --output-dir "runs/reproducao-2026-09-22"
```

Troque arquivo, referência e pasta para outra análise. O pipeline completo usa a biblioteca padrão. Ele busca as fontes B3 necessárias ausentes em `data/reference/`; com todas as fontes guardadas, acrescente `--offline`. Para escolher outro cache, use `--reference-dir`. `--allow-nonfriday-end` registra aceitação de semana encurtada após sua conferência.

O comando gera relatório, rankings das duas janelas, evidências de classificação, qualidade e README com a média da própria execução. Para reproduzir integralmente, são necessários o CSV original, as fontes B3 e a versão do código: os derivados públicos não substituem essas entradas. O bruto fica fora do Git.

## Usar e conferir

A interface mostra preços e retornos diários, variação em R$ por ação, distribuição e matriz diária. O resumo e os alertas acompanham a janela escolhida. [Guia com exemplos visuais](docs/como-usar.md).

O site aceita o [formato documentado de nove colunas](docs/dados.md), até **10 MB**: uma análise ativa, duas aguardando, dez minutos por processamento e três envios por hora por origem. Sem login; quem possui o link pode consultar os derivados. Brutos são removidos após 24 horas e testes após sete dias. Não há lista pública nem download do CSV bruto.

A auditoria associa cada nova análise a uma cópia dos guias registrada na conclusão. A referência recebeu uma associação após revisão; isso é identificado no site. Execuções antigas sem registro mostram essa limitação. Veja [Auditoria e reprodução](docs/auditoria.md).

## Desenvolver ou avaliar o código

| Assunto | Documento |
| --- | --- |
| Instalação, API/worker local, testes e mapa dos módulos | [Desenvolvimento](docs/desenvolvimento.md) |
| Comandos por etapa, dicionário e achados do case | [Referência técnica](docs/referencia-tecnica.md) |
| Regras e justificativas | [Decisões](docs/decisoes.md) |
| Arquitetura, fila e retenção | [Sistema](docs/sistema.md) |
| Docker, Traefik e operação da VPS | [Deploy](deploy/README.md) |
| Orientações para agentes | [AGENTS.md](AGENTS.md) e [CLAUDE.md](CLAUDE.md) |

```powershell
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements-dev.txt
.venv/Scripts/python -m unittest discover -s tests -v
```

No Linux/macOS, use `.venv/bin/python`. O CI confere testes sem rede, Python, formatação/sintaxe do frontend e integridade dos resultados. A regressão com o bruto original é opcional via `ECONOMATICA_CASE_CSV`. Testes sintéticos não comprovam disponibilidade B3 nem comportamento em dispositivos físicos.
