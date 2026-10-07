"""Build dated financial and price evidence without changing ranking artifacts."""

import csv
import hashlib
import io
import json
import zipfile
from decimal import Decimal
from pathlib import Path

from scripts.collect_case_context import ROOT, write_json


def select_filing(rows, code, cutoff):
    eligible = [row for row in rows if int(row['CD_CVM']) == int(code)
                and row['DT_RECEB'][:10] <= cutoff and row['DT_REFER'] <= cutoff]
    return max(eligible, key=lambda row: (row['DT_REFER'], int(row['VERSAO'])),
               default=None)


def account_record(rows, filing, account, period_start=None, previous=False):
    candidates = [row for row in rows if int(row['CD_CVM']) == int(filing['CD_CVM'])
                  and row['DT_REFER'] == filing['DT_REFER']
                  and row['VERSAO'] == filing['VERSAO']
                  and row['CD_CONTA'] == account
                  and row['ORDEM_EXERC'] == ('PENÚLTIMO' if previous else 'ÚLTIMO')
                  and (period_start is None or row.get('DT_INI_EXERC') == period_start)]
    if len(candidates) > 1:
        raise ValueError('Ambiguous financial period or duplicate account')
    if not candidates:
        return None
    row = candidates[0]
    if row['MOEDA'] != 'REAL' or row['ESCALA_MOEDA'] not in {'MIL', 'UNIDADE'}:
        raise ValueError('Unsupported financial currency or scale')
    factor = Decimal(1000) if row['ESCALA_MOEDA'] == 'MIL' else Decimal(1)
    return {'account_code': account, 'label': row['DS_CONTA'],
            'value_brl': str(Decimal(row['VL_CONTA']) * factor),
            'period_start': row.get('DT_INI_EXERC'), 'period_end': row['DT_FIM_EXERC'],
            'reported_value': row['VL_CONTA'], 'reported_scale': row['ESCALA_MOEDA']}


def price_observation(series):
    """Missing adjacent prices remain missing; never bridge a graph gap."""
    comparisons = []
    for previous, current in zip(series, series[1:]):
        a, b = previous.get('close'), current.get('close')
        value = None
        if a is not None and b is not None and Decimal(a) > 0 and Decimal(b) > 0:
            value = (Decimal(b) / Decimal(a) - 1) * 100
        comparisons.append({'start_date': previous['date'], 'end_date': current['date'],
                            'return_pct': None if value is None else str(value)})
    valid = [row for row in comparisons if row['return_pct'] is not None]
    return {'daily_comparisons': comparisons,
            'strongest_up_day': max([r for r in valid if Decimal(r['return_pct']) > 0],
                                    key=lambda r: Decimal(r['return_pct']),
                                    default=None),
            'weakest_day': min(valid, key=lambda r: Decimal(r['return_pct']), default=None),
            'positive_days': sum(Decimal(r['return_pct']) > 0 for r in valid),
            'negative_days': sum(Decimal(r['return_pct']) < 0 for r in valid),
            'flat_days': sum(Decimal(r['return_pct']) == 0 for r in valid),
            'missing_comparisons': len(comparisons) - len(valid)}


def build(archive_path, output):
    config = json.loads((ROOT / 'context/case-2026-09-22/issuers.json')
                        .read_text(encoding='utf-8'))
    if output.exists():
        raise ValueError('Use a new output file to preserve prior evidence')
    cutoff = '2026-09-18'
    with zipfile.ZipFile(archive_path) as archive:
        def read(name):
            with archive.open(name) as handle:
                return list(csv.DictReader(io.TextIOWrapper(handle, encoding='cp1252'),
                                           delimiter=';'))
        filings = read('itr_cia_aberta_2026.csv')
        statements = {scope: {kind: read(f'itr_cia_aberta_{kind}_{scope}_2026.csv')
                             for kind in ('DRE', 'BPP')}
                      for scope in ('con', 'ind')}
    financial = []
    for issuer in config['issuers']:
        filing = select_filing(filings, issuer['cvm_code'], cutoff)
        row = {'cvm_code': issuer['cvm_code'], 'tickers': issuer['tickers'],
               'status': 'no_eligible_2026_filing_in_retrieved_catalog', 'filing': filing}
        if filing:
            scope = 'con' if any(int(r['CD_CVM']) == int(issuer['cvm_code'])
                                and r['DT_REFER'] == filing['DT_REFER']
                                and r['VERSAO'] == filing['VERSAO']
                                for r in statements['con']['DRE']) else 'ind'
            dre, bpp = statements[scope]['DRE'], statements[scope]['BPP']
            start = filing['DT_REFER'][:4] + '-04-01'
            if filing['DT_REFER'][5:] != '06-30':
                row['status'] = 'other_period_requires_review'
            else:
                accounts = {label: account_record(dre, filing, code, start)
                            for label, code in [('revenue', '3.01'),
                                                ('operating_result', '3.05'),
                                                ('financial_result', '3.06'),
                                                ('net_result', '3.11')]}
                prior_start = str(int(start[:4]) - 1) + start[4:]
                accounts['prior_year_revenue'] = account_record(dre, filing, '3.01',
                                                               prior_start, True)
                accounts['prior_year_net_result'] = account_record(dre, filing, '3.11',
                                                                  prior_start, True)
                accounts['equity'] = account_record(bpp, filing, '2.03')
                row.update(status='quarter_accounts_selected_pending_interpretation',
                           scope=scope, quarter_start=start, quarter_end=filing['DT_REFER'],
                           accounts=accounts, available_before_price_week=True)
        financial.append(row)
    featured = ROOT / 'resultados/2026-09-22'
    daily = json.loads((featured / 'daily_context.json').read_text(encoding='utf-8'))
    returns = {}
    for key, name in [('main', 'all_returns.csv'), ('alternative', 'all_returns_alternativo.csv')]:
        with (featured / name).open(encoding='utf-8-sig', newline='') as handle:
            returns[key] = {r['ticker']: r for r in csv.DictReader(handle)}
    prices = []
    for issuer in config['issuers']:
        for ticker in issuer['tickers']:
            main, alternative = returns['main'].get(ticker), returns['alternative'].get(ticker)
            prices.append({'ticker': ticker, 'cvm_code': issuer['cvm_code'],
                           'main': main, 'alternative': alternative,
                           'price_change_brl': str(Decimal(main['end_close']) -
                                                   Decimal(main['start_close'])) if main else None,
                           'window_difference_pp': str(Decimal(alternative['return_pct']) -
                                                        Decimal(main['return_pct']))
                               if main and alternative else None,
                           'observations': price_observation(daily['series'][ticker])})
    manifest = {name: hashlib.sha256((featured / name).read_bytes()).hexdigest()
                for name in ['daily_context.json', 'all_returns.csv', 'all_returns_alternativo.csv']}
    result = {'reference_date': config['reference_date'], 'information_cutoff': cutoff,
              'status': 'evidence_for_context_redesign_not_published_analysis',
              'financial_source': 'https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/ITR/DADOS/itr_cia_aberta_2026.zip',
              'financial_archive_sha256': hashlib.sha256(archive_path.read_bytes()).hexdigest(),
              'historical_input_sha256': manifest, 'financial': financial, 'prices': prices,
              'limits': ['Dated antecedents are not new weekly announcements.',
                         'No causal price effect, liquidity or traded volume is inferred.',
                         'Absence from this catalog is not proof of absence of all filings.',
                         'Quarter account definitions may include non-recurring items; no automatic EBITDA or debt ratio.',
                         'No chart-gap filling; observation of price patterns is not an explanation of investor motives.']}
    write_json(output, result)
    return result


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    data = build(args.archive, args.output)
    print(json.dumps({'financial_filings': sum(r['filing'] is not None for r in data['financial']),
                      'ticker_price_dossiers': len(data['prices'])}))
