"""Prepare a dated case market comparison from saved provider responses."""

import argparse
import hashlib
import json
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from scripts.collect_case_context import ROOT, write_json


def pair(points, start, end):
    if start not in points or end not in points:
        raise ValueError('Market comparison requires exact endpoint observations')
    a, b = Decimal(points[start]), Decimal(points[end])
    if a <= 0 or b <= 0:
        raise ValueError('Market comparison requires positive observations')
    return {'start_date': start, 'end_date': end, 'start_value': str(a), 'end_value': str(b),
            'change_pct': str((b / a - 1) * 100)}


def build(directory, output):
    if output.exists():
        raise ValueError('Preserve prior market context; choose a new output')
    indicators = []
    signatures = {}
    for symbol, label in [('BVSP', 'Ibovespa'), ('GSPC', 'S&P 500'), ('IXIC', 'Nasdaq Composite')]:
        path = directory / (symbol + '.json')
        raw = json.loads(path.read_text(encoding='utf-8'))
        response = raw['response']['chart']['result'][0]
        if response['meta']['symbol'] != '^' + symbol:
            raise ValueError('Provider returned a different market instrument')
        closes = response['indicators']['quote'][0]['close']
        points = {}
        for timestamp, close in zip(response['timestamp'], closes, strict=True):
            day = datetime.fromtimestamp(timestamp, timezone.utc).date().isoformat()
            if close is not None:
                if day in points:
                    raise ValueError('Duplicate market date')
                points[day] = str(close)
        indicators.append({'id': symbol, 'label': label, 'unit': 'pontos',
                           'definition': 'Fechamento diário do índice, segundo o histórico da fonte.',
                           'source_label': 'Yahoo Finance · histórico diário', 'source_url': raw['url'],
                           'timezone': response['meta']['exchangeTimezoneName'],
                           'primary': pair(points, '2026-09-11', '2026-09-18'),
                           'alternative': pair(points, '2026-09-14', '2026-09-18')})
        signatures[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    collected = ROOT / 'runs/context-case-2026-09-22-v1/collection.json'
    ptax = json.loads(collected.read_text(encoding='utf-8'))['ptax']
    if ptax['status'] != 'retrieved':
        raise ValueError('PTAX retrieval is not available')
    points = {row['dataHoraCotacao'][:10]: str(row['cotacaoVenda']) for row in ptax['data']}
    if len(points) != len(ptax['data']):
        raise ValueError('Duplicate PTAX date')
    indicators.append({'id': 'PTAX', 'label': 'Dólar · PTAX venda', 'unit': 'R$ por US$',
                       'definition': 'Taxa diária de referência do Banco Central. Não é cotação '
                                     'de fechamento nem preço de compra de moeda pelo consumidor.',
                       'source_label': 'Banco Central · PTAX', 'source_url': ptax['url'],
                       'timezone': 'America/Sao_Paulo',
                       'primary': pair(points, '2026-09-11', '2026-09-18'),
                       'alternative': pair(points, '2026-09-14', '2026-09-18')})
    signatures['case_collection.json'] = hashlib.sha256(collected.read_bytes()).hexdigest()
    selic_path = directory / 'selic-target.json'
    selic = json.loads(selic_path.read_text(encoding='utf-8'))
    targets = {datetime.strptime(r['data'], '%d/%m/%Y').date().isoformat(): Decimal(r['valor'])
               for r in selic['data']}
    if targets.get('2026-09-16') != Decimal('14') or targets.get('2026-09-17') != Decimal('13.75'):
        raise ValueError('Selic narrative disagrees with official target series')
    signatures[selic_path.name] = hashlib.sha256(selic_path.read_bytes()).hexdigest()
    events = [
        {'id': 'selic', 'title': 'Brasil: a meta da Selic passou de 14,00% para 13,75% ao ano',
         'date': '2026-09-17', 'date_label': '17/09 · início da vigência',
         'text': 'A série oficial do Banco Central registra a nova meta a partir de 17/09. '
                 'Juros menores podem reduzir custos de crédito ao longo do tempo, mas o efeito '
                 'depende da dívida e dos contratos de cada empresa; não é automático no preço da ação.',
         'source_label': 'Banco Central · série da meta Selic', 'source_url': selic['url']},
        {'id': 'fed', 'title': 'Estados Unidos: o Fed elevou sua faixa de juros',
         'date': '2026-09-16', 'date_label': '16/09 · 14h00 em Nova York',
         'text': 'O Federal Reserve anunciou aumento de 0,25 ponto percentual, para a faixa '
                 'de 3,75% a 4,00% ao ano, citando inflação ainda elevada. A decisão é contexto '
                 'para juros e condições financeiras globais; não prova o motivo do retorno de um papel brasileiro.',
         'source_label': 'Federal Reserve · comunicado de 16/09',
         'source_url': 'https://www.federalreserve.gov/newsevents/pressreleases/monetary20260916a.htm'},
        {'id': 'fiscal', 'title': 'Brasil: a IFI apontou dificuldades para o Orçamento de 2027',
         'date': '2026-09-17', 'date_label': '17/09 · 17h27 em Brasília',
         'text': 'A Agência Senado publicou a avaliação da Instituição Fiscal Independente: '
                 'projeção de déficit primário de R$ 86,10 bilhões, diante de uma meta de superávit '
                 'de R$ 18,60 bilhões para 2027. São projeções sobre o orçamento futuro, não resultados '
                 'já realizados. O tema ajuda a acompanhar as discussões sobre dívida e juros.',
         'source_label': 'Agência Senado · avaliação da IFI',
         'source_url': 'https://www12.senado.leg.br/noticias/materias/2026/09/17/governo-tera-que-cortar-despesas-para-fechar-as-contas-em-2027-diz-ifi'},
        {'id': 'politics', 'title': 'Política: pesquisa Datafolha mostrou disputa presidencial apertada',
         'date': '2026-09-17', 'date_label': '17/09 · publicação às 19h05',
         'text': 'A Folha publicou pesquisa realizada de 15 a 17/09: na simulação de segundo turno, '
                 'Lula tinha 46% e Flávio Bolsonaro, 44%, com margem de erro de dois pontos percentuais. '
                 'A pesquisa descreve intenções de voto daquele período, não prevê o resultado da eleição '
                 'nem demonstra efeito sobre as ações do ranking.',
         'source_label': 'Folha · levantamento Datafolha',
         'source_url': 'https://www1.folha.uol.com.br/poder/2026/09/datafolha-lula-e-flavio-bolsonaro-empatam-em-1o-e-2o-turnos.shtml'},
    ]
    result = {'reference_date': '2026-09-22', 'status': 'reviewed_case_market_context',
              'calendar_week': {'start': '2026-09-14', 'end': '2026-09-20'},
              'indicators': indicators, 'events': sorted(events, key=lambda r: (r['date'], r['id'])),
              'method': 'Variação = valor final / inicial − 1, calculada em Python com a precisão '
                        'da fonte. Os índices usam fechamento; o dólar usa PTAX de venda. '
                        'Arredondamento apenas na exibição. São referências distintas, não um índice '
                        'comum nem preços substitutos para a Economatica.',
              'input_sha256': signatures,
              'review_notes': ['Valores conflitantes de reportagem não foram usados nos indicadores.',
                               'Séries dos índices identificam o provedor, não são apresentadas como dados oficiais da B3.',
                               'Ata do Copom publicada depois da semana não foi usada como novidade conhecida na semana.',
                               'Contexto geral não é prova de causa dos retornos individuais.']}
    write_json(output, result)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-dir', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = build(args.input_dir, args.output)
    print(json.dumps({'indicators': len(result['indicators']), 'events': len(result['events'])}))
