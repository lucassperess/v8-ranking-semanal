Média dos retornos do top 20: 17,78%

# Ações que mais subiram na semana anterior

Referência: 2026-09-22. Semana analisada: 2026-09-14 a 2026-09-20. Variação principal: fechamento ajustado de 2026-09-11 a 2026-09-18.

| Posição | Ação | Espécie | Fechamento inicial | Fechamento final | Retorno |
| ---: | --- | --- | ---: | ---: | ---: |
| 1 | ECOM3 | ON | 1.06 | 1.56 | 47,17% |
| 2 | FASA3 | ON | 0.21 | 0.29 | 38,10% |
| 3 | TASA3 | ON | 6.06 | 8.13 | 34,16% |
| 4 | TASA4 | PN | 6.03 | 8.06 | 33,67% |
| 5 | AMBP3 | ON | 0.14 | 0.18 | 28,57% |
| 6 | TXRX4 | PN | 1.75 | 2.14 | 22,29% |
| 7 | ESTR4 | PN | 1.54 | 1.85 | 20,13% |
| 8 | BIED3 | ON | 5.55 | 6.37 | 14,77% |
| 9 | MGEL4 | PN | 5.24 | 5.95 | 13,55% |
| 10 | ONCO3 | ON | 1.14 | 1.29 | 13,16% |
| 11 | WDCN3 | ON | 2.75 | 3.11 | 13,09% |
| 12 | LUXM4 | PN | 2.72 | 2.99 | 9,93% |
| 13 | ISAE3 | ON | 32.31 | 35.37 | 9,47% |
| 14 | CASH3 | ON | 5.25 | 5.73 | 9,14% |
| 15 | RCSL3 | ON | 0.44 | 0.48 | 9,09% |
| 16 | QUAL3 | ON | 1.52 | 1.65 | 8,55% |
| 17 | DOTZ3 | ON | 10.15 | 11 | 8,37% |
| 18 | MEAL3 | ON | 0.9 | 0.97 | 7,78% |
| 19 | ARML3 | ON | 3.79 | 4.07 | 7,39% |
| 20 | DASA3 | ON | 2.65 | 2.84 | 7,17% |

## Leitura e premissas

A semana-calendário anterior vai de 2026-09-14 a 2026-09-20. O fechamento imediatamente anterior à semana mede também o movimento da segunda-feira. Retorno = fechamento ajustado final da Economatica / fechamento ajustado inicial - 1. Entram ações ON e PN confirmadas pela B3 nas duas pontas; BDRs, units e outros instrumentos ficam fora. Não foi aplicado filtro de liquidez. A ordenação usa retorno sem arredondamento, com ticker como desempate. A média é aritmética e usa os 20 retornos sem arredondamento.

Na interpretação alternativa (2026-09-14 a 2026-09-18), a média é 15,93%; 16 ações aparecem nos dois top 20. Essa alternativa não substitui o resultado principal.

Foram consideradas 308 ações com preços válidos nas duas datas; 12 outros instrumentos com dois preços ficaram fora. Códigos sem os dois fechamentos constam em [candidate_exclusions.csv](candidate_exclusions.csv). Os retornos de todas as ações estão em [all_returns.csv](all_returns.csv); o ranking da janela alternativa está em [top20_alternativo.csv](top20_alternativo.csv).

Alertas de qualidade envolvendo o top 20 (não alteram preços automaticamente): BIED3 em 2026-09-18: average — Valor fora do intervalo mínimo–máximo.

## Reproduzir

Com Python 3.11+ e o CSV original disponível, rode na raiz do projeto:

```powershell
python weekly_ranking.py --input "CAMINHO\economatica.csv" --reference-date 2026-09-22 --output-dir "runs\semana-2026-09-22"
```

O programa obtém cadastros e cotações oficiais da B3 quando não estão em `data/reference/`. Com os arquivos já guardados, acrescente `--offline`. Os CSVs de retornos, classificações, alertas e manifestos ficam na pasta da execução.
