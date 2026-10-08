"""Reconcile the reviewed context with saved original observations."""

import csv
import hashlib
import io
import json
import zipfile
from decimal import Decimal
from datetime import datetime, timezone
from pathlib import Path

from scripts.build_case_context import validate_context

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def audit():
    directory = ROOT / 'context/case-2026-09-22'
    company = read(directory / 'company_context_v3.json')
    evidence = read(directory / 'expanded_evidence.json')
    featured = ROOT / 'resultados/2026-09-22'
    validate_context(company, [r['ticker'] for r in evidence['prices']])
    archive_path = ROOT / 'runs/context-coverage-revision-v1/itr2026.zip'
    assert hashlib.sha256(archive_path.read_bytes()).hexdigest() == evidence['financial_archive_sha256']
    tables = {}
    with zipfile.ZipFile(archive_path) as archive:
        for scope in ('con', 'ind'):
            for kind in ('DRE', 'BPP'):
                with archive.open(f'itr_cia_aberta_{kind}_{scope}_2026.csv') as handle:
                    tables[scope, kind] = list(csv.DictReader(io.TextIOWrapper(handle, encoding='cp1252'), delimiter=';'))
    checked_accounts = 0
    for record in evidence['financial']:
        if not record.get('accounts'):
            continue
        filing = record['filing']
        assert filing['DT_RECEB'][:10] < '2026-09-14'
        for name, account in record['accounts'].items():
            if not account:
                continue
            candidates = [r for r in tables[record['scope'], 'BPP' if name == 'equity' else 'DRE']
                          if int(r['CD_CVM']) == int(record['cvm_code'])
                          and r['VERSAO'] == filing['VERSAO'] and r['DT_REFER'] == filing['DT_REFER']
                          and r['CD_CONTA'] == account['account_code']
                          and r['DT_FIM_EXERC'] == account['period_end']
                          and r.get('DT_INI_EXERC') == account['period_start']]
            assert len(candidates) == 1, (record['cvm_code'], name)
            row = candidates[0]
            assert row['MOEDA'] == 'REAL'
            factor = 1000 if row['ESCALA_MOEDA'] == 'MIL' else 1
            assert Decimal(row['VL_CONTA']) * factor == Decimal(account['value_brl'])
            checked_accounts += 1
    daily = read(featured / 'daily_context.json')
    checked_returns = checked_daily = 0
    for asset in company['assets']:
        prices = {r['date']: r['close'] for r in daily['series'][asset['ticker']]}
        for name, file in [('main', 'all_returns.csv'), ('alternative', 'all_returns_alternativo.csv')]:
            reading = asset[name]
            with (featured / file).open(encoding='utf-8', newline='') as handle:
                ranked = {r['ticker']: r for r in csv.DictReader(handle)}
            if reading['status'] != 'available':
                assert asset['ticker'] not in ranked
                continue
            row = ranked[asset['ticker']]
            assert reading['start_date'] == row['start_date'] and reading['end_date'] == row['end_date']
            calculated = (Decimal(row['end_close']) / Decimal(row['start_close']) - 1) * 100
            assert abs(calculated - Decimal(reading['return_pct'])) < Decimal('1e-20')
            checked_returns += 1
            for comparison in reading['daily_comparisons']:
                assert reading['start_date'] <= comparison['start_date'] < comparison['end_date'] <= reading['end_date']
                a, b = prices[comparison['start_date']], prices[comparison['end_date']]
                if a is None or b is None:
                    assert comparison['return_pct'] is None
                else:
                    assert abs((Decimal(b) / Decimal(a) - 1) * 100 - Decimal(comparison['return_pct'])) < Decimal('1e-20')
                checked_daily += 1
    market = read(directory / 'market_context.json')
    for indicator in market['indicators']:
        if indicator['id'] == 'PTAX':
            source_path = ROOT / 'runs/context-case-2026-09-22-v1/collection.json'
            raw = read(source_path)['ptax']
            observations = {r['dataHoraCotacao'][:10]: Decimal(str(r['cotacaoVenda'])) for r in raw['data']}
            signature_name = 'case_collection.json'
        else:
            signature_name = indicator['id'] + '.json'
            source_path = ROOT / 'runs/context-market-v1' / signature_name
            raw = read(source_path)['response']['chart']['result'][0]
            assert raw['meta']['symbol'] == '^' + indicator['id']
            observations = {datetime.fromtimestamp(t, timezone.utc).date().isoformat(): Decimal(str(v))
                            for t, v in zip(raw['timestamp'], raw['indicators']['quote'][0]['close'], strict=True)
                            if v is not None}
        assert hashlib.sha256(source_path.read_bytes()).hexdigest() == market['input_sha256'][signature_name]
        for window in ('primary', 'alternative'):
            pair = indicator[window]
            assert observations[pair['start_date']] == Decimal(pair['start_value'])
            assert observations[pair['end_date']] == Decimal(pair['end_value'])
            assert abs((Decimal(pair['end_value']) / Decimal(pair['start_value']) - 1) * 100 - Decimal(pair['change_pct'])) < Decimal('1e-20')
    return {'companies': len(company['issuers']), 'assets': len(company['assets']),
            'sources': len(company['sources']), 'financial_accounts_reconciled': checked_accounts,
            'weekly_returns_recalculated': checked_returns, 'daily_comparisons_checked': checked_daily,
            'market_comparisons_recalculated': len(market['indicators']) * 2,
            'limitations': ['Source bodies reuse the prior editorial review; no live causal effect is established.',
                            'Date of CVM delivery is not necessarily the first public disclosure.']}


if __name__ == '__main__':
    print(json.dumps(audit(), ensure_ascii=True, indent=2))
