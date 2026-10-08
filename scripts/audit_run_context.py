"""Independently reconcile context prices and financial accounts with saved inputs."""

import argparse
import csv
import io
import json
import zipfile
from decimal import Decimal
from pathlib import Path

from webapp.context import load_run_context
from webapp.presentation import output_path


def audit(root):
    context = load_run_context(root)
    if context['status'] != 'available':
        raise ValueError('Signed context is unavailable')
    presentation = json.loads((root / 'presentation.json').read_text(encoding='utf-8'))
    company = context['company']
    returns, weekly, daily, accounts = {}, 0, 0, 0
    for key, name in [('main', 'all_returns.csv'), ('alternative', 'all_returns_alternativo.csv')]:
        with output_path(root, name).open(encoding='utf-8-sig', newline='') as stream:
            returns[key] = {r['ticker']: r for r in csv.DictReader(stream)}
    for asset in company['assets']:
        for key in ('main', 'alternative'):
            window = asset[key]
            if window['status'] != 'available':
                assert asset['ticker'] not in returns[key]
                continue
            original = returns[key][asset['ticker']]
            expected = (Decimal(original['end_close']) / Decimal(original['start_close']) - 1) * 100
            assert abs(expected - Decimal(window['return_pct'])) < Decimal('1e-20')
            weekly += 1
            points = {r['date']: r['close'] for r in presentation['daily']['series'][asset['ticker']]}
            for row in window['daily_comparisons']:
                a, b = points[row['start_date']], points[row['end_date']]
                if a is None or b is None:
                    assert row['return_pct'] is None
                else:
                    expected = (Decimal(b) / Decimal(a) - 1) * 100
                    assert abs(expected - Decimal(row['return_pct'])) < Decimal('1e-20')
                daily += 1
    tables = {}
    for issuer in company['issuers']:
        financial = issuer['financial_context']
        if not financial:
            continue
        filing = financial['filing']
        year = int(filing['DT_REFER'][:4])
        scope = financial['scope']
        key = year, scope
        if key not in tables:
            with zipfile.ZipFile(root / 'context/private' / f'itr-{year}.bin') as archive:
                tables[key] = list(csv.DictReader(io.StringIO(archive.read(f'itr_cia_aberta_DRE_{scope}_{year}.csv')
                                                                  .decode('cp1252')), delimiter=';'))
        assert filing['DT_RECEB'][:10] <= company['price_end']
        for label, value in financial['accounts'].items():
            if value is None:
                continue
            matches = [r for r in tables[key] if int(r['CD_CVM']) == int(issuer['cvm_code'])
                       and r['DT_REFER'] == filing['DT_REFER'] and r['VERSAO'] == filing['VERSAO']
                       and r['CD_CONTA'] == value['account_code'] and r['DT_INI_EXERC'] == value['period_start']
                       and r['DT_FIM_EXERC'] == value['period_end']
                       and r['ORDEM_EXERC'] == ('PENÚLTIMO' if label.startswith('prior_') else 'ÚLTIMO')]
            assert len(matches) == 1
            original = matches[0]
            assert original['MOEDA'] == 'REAL'
            assert original['ESCALA_MOEDA'] in ('MIL', 'UNIDADE')
            factor = 1000 if original['ESCALA_MOEDA'] == 'MIL' else 1
            assert Decimal(original['VL_CONTA']) * factor == Decimal(value['value_brl'])
            accounts += 1
    market = 0
    for item in context['market']['indicators']:
        for key in ('primary', 'alternative'):
            values = item[key]
            if not values:
                continue
            expected = (Decimal(values['end_value']) / Decimal(values['start_value']) - 1) * 100
            assert expected == Decimal(values['change_pct'])
            market += 1
    return {'assets': len(company['assets']), 'companies': len(company['issuers']),
            'weekly_returns': weekly, 'daily_comparisons': daily, 'financial_accounts': accounts,
            'market_comparisons': market, 'result': 'no_discrepancies'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir', type=Path, required=True)
    print(json.dumps(audit(parser.parse_args().run_dir)))
