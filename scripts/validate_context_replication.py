"""Local validation with fictitious prices and explicitly artificial B3 fixtures.

Company identities/news are fetched live by the separate context generator.
These fixtures must never be published as a real market analysis.
"""

import argparse
import csv
import json
import subprocess
import sys
import zipfile
from datetime import date
from decimal import Decimal
from pathlib import Path

import etl
from context_pipeline.sources import write
from scripts.collect_case_context import ROOT
from webapp.doc_revision import archive
from webapp.presentation import build_presentation


def fixture(directory, scenario='standard'):
    if scenario not in {'standard', 'volume'}:
        raise ValueError('Unknown validation scenario')
    directory.mkdir(parents=True, exist_ok=False)
    wanted = ['PETR4', 'VALE3', 'ITUB4', 'BBDC4', 'ABEV3', 'WEGE3', 'BBAS3', 'RENT3',
              'SUZB3', 'PRIO3', 'GGBR4', 'CSNA3', 'BRAP4', 'LREN3', 'RADL3', 'VIVT3',
              'TIMS3', 'EQTL3', 'CMIG4', 'SBSP3']
    with (ROOT / 'resultados/2026-09-22/period_classification.csv').open(encoding='utf-8') as stream:
        selected = {r['ticker']: r for r in csv.DictReader(stream) if r['ticker'] in wanted}
    if set(selected) != set(wanted):
        raise ValueError('Validation identities are absent from the saved classification')
    days = ['2026-09-25', '2026-09-28', '2026-09-29', '2026-09-30', '2026-10-01', '2026-10-02']
    with (directory / 'fictitious.csv').open('w', encoding='utf-8', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(etl.SOURCE_COLUMNS)
        for step, day in enumerate(days):
            for number, ticker in enumerate(wanted):
                value = Decimal(10) + Decimal(number + 1) / 20 * step
                quantity, volume, close = Decimal(1), value, value
                if scenario == 'volume':
                    value = Decimal(10) + Decimal(number) / 2 + Decimal(number % 7 - 2) / 20 * step
                    close = value
                    quantity = Decimal(100 * (number + 1) * (step + 1))
                    volume = quantity * value
                    if number == 0 and step == 1:
                        quantity, volume = Decimal(0), Decimal(0)
                    if number == 1 and step == 3:
                        volume = '-'
                    if number == 2 and step == 4:
                        volume = '-10'
                    if number == 5 and step == 2:
                        close = '-'
                writer.writerow([ticker + '<XBSP>', day, close, quantity, value, value, value, value, volume])
    refs = directory / 'artificial-reference'
    refs.mkdir()
    for day in (days[0], days[1], days[-1]):
        records = []
        for ticker in wanted:
            line = list(' ' * 245)
            kind = 'ON' if selected[ticker]['instrument_type'] == 'acao_on' else 'PN'
            for begin, end, value in ((0, 2, '01'), (2, 10, day.replace('-', '')),
                                     (12, 24, ticker.ljust(12)), (24, 27, '010'),
                                     (39, 49, kind.ljust(10)), (230, 242, selected[ticker]['isin'])):
                line[begin:end] = value
            records.append(''.join(line))
        with zipfile.ZipFile(refs / f'COTAHIST_D{date.fromisoformat(day):%d%m%Y}.ZIP', 'w') as archive_zip:
            archive_zip.writestr('ARTIFICIAL_TEST_COTAHIST.TXT', '\n'.join(records))
    output = directory / 'analysis'
    subprocess.run([sys.executable, str(ROOT / 'weekly_ranking.py'), '--input', str(directory / 'fictitious.csv'),
                    '--reference-date', '2026-10-07', '--output-dir', str(output),
                    '--reference-dir', str(refs), '--offline'], cwd=ROOT, check=True)
    archive(output)
    payload = build_presentation(output, normalized_path=output / 'etl/normalized.csv')
    write(output / 'volume_context.json', payload['volume'])
    payload['validation_notice'] = 'VALIDAÇÃO LOCAL: preços fictícios e fontes de classificação artificiais. Não representa uma análise de mercado real.'
    write(output / 'presentation.json', payload)
    write(directory / 'fixture-notice.json', {'purpose': 'local replication validation', 'scenario': scenario,
          'prices': 'fictitious', 'classification_files': 'artificial', 'news_collection': 'live',
          'reference_date': '2026-10-07', 'tickers': wanted})
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--scenario', choices=['standard', 'volume'], default='standard')
    args = parser.parse_args()
    print(json.dumps({'run_directory': str(fixture(args.output, args.scenario))}))
