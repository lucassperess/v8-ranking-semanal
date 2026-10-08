"""Volume recebido: contexto determinístico, separado do ranking e dos preços."""

import csv
import hashlib
import json
from collections import defaultdict
from decimal import Decimal, InvalidOperation


def number(value):
    try:
        result = Decimal(value)
        return result if result.is_finite() and result >= 0 else None
    except (InvalidOperation, TypeError, ValueError):
        return None


def signature(payload):
    data = {key: value for key, value in payload.items() if key != 'content_sha256'}
    return hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def collect(normalized, tickers, week, input_hash, normalized_hash):
    if hashlib.sha256(normalized.read_bytes()).hexdigest() != normalized_hash:
        raise ValueError('Hash divergente: normalized.csv para volume')
    records, dates = defaultdict(list), set()
    with normalized.open(encoding='utf-8', newline='') as stream:
        for row in csv.DictReader(stream):
            day = row.get('trade_date', '')
            if not week['week_start'] <= day <= week['last_week_close']:
                continue
            close = number(row.get('close'))
            if row.get('parse_status') == 'ok' and close is not None and close > 0:
                dates.add(day)
            if row.get('ticker') in tickers:
                records[row['ticker'], day].append(row)
    series = {}
    for ticker in sorted(tickers):
        series[ticker] = []
        for day in sorted(dates):
            rows = records[ticker, day]
            reason, value = 'missing_volume', None
            if len(rows) > 1:
                reason = 'duplicate_record'
            elif rows:
                row = rows[0]
                if row.get('parse_status') != 'ok':
                    reason = 'invalid_record'
                else:
                    value = number(row.get('raw_volume'))
                    reason = None if value is not None else 'invalid_volume' if row.get('raw_volume') else 'missing_volume'
            series[ticker].append({'date': day, 'volume': str(value) if value is not None else None, 'reason': reason})
    payload = {'version': '1.0', 'source': 'Economatica: Volume$|Em moeda orig',
               'input_sha256': input_hash, 'normalized_sha256': normalized_hash,
               'week_start': week['week_start'], 'end_date': week['last_week_close'],
               'dates': sorted(dates), 'series': series,
               'definition': 'Soma dos volumes válidos dividida pelo número de dias com volume válido. Zero explícito entra; ausências e duplicatas não entram. Datas com fechamento positivo na extração definem a cobertura.'}
    payload['content_sha256'] = signature(payload)
    return payload


def attach(payload, root, normalized=None):
    """Novas análises usam a base conferida; versões antigas podem usar um derivado."""
    report_hash = payload['provenance']['input_sha256']
    manifest_path = root / ('etl_manifest.json' if payload['kind'] == 'featured' else 'etl/manifest.json')
    if not manifest_path.exists():
        return payload
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    expected = manifest['outputs']['normalized.csv']
    if normalized is not None and normalized.exists():
        tickers = {r['ticker'] for w in payload['windows'].values() for r in w['top20']}
        volume = collect(normalized, tickers, payload['week'], report_hash, expected)
    elif payload.get('volume'):
        volume = payload['volume']
    elif (root / 'volume_context.json').exists():
        volume = json.loads((root / 'volume_context.json').read_text(encoding='utf-8'))
    else:
        return payload
    if (volume.get('content_sha256') != signature(volume) or volume.get('input_sha256') != report_hash
            or volume.get('normalized_sha256') != expected or manifest['input_sha256'] != report_hash
            or volume.get('week_start') != payload['week']['week_start']
            or volume.get('end_date') != payload['week']['last_week_close']):
        raise ValueError('Derivado de volume não corresponde à execução')
    payload['volume'] = volume
    return payload


def enrich(payload):
    volume = payload.get('volume', {})
    dates = volume.get('dates', [])
    for window in payload['windows'].values():
        stats = []
        for row in window['top20']:
            points = volume.get('series', {}).get(row['ticker'], [])
            values = [number(p.get('volume')) for p in points]
            values = [v for v in values if v is not None]
            total = sum(values, Decimal(0)) if values else None
            mean = total / len(values) if values else None
            row['volume'] = {'mean_daily': str(mean) if mean is not None else None,
                             'total_observed': str(total) if total is not None else None,
                             'valid_days': len(values), 'expected_days': len(dates),
                             'positive_days': sum(v > 0 for v in values),
                             'complete': bool(dates) and len(values) == len(dates)}
            if mean is not None:
                stats.append({'ticker': row['ticker'], **row['volume']})
        ordered = sorted(stats, key=lambda s: (Decimal(s['mean_daily']), s['ticker']))
        moves = []
        for row in window['top20']:
            volumes = {p['date']: p['volume'] for p in volume.get('series', {}).get(row['ticker'], [])}
            for point in window.get('daily', {}).get('heatmap', {}).get(row['ticker'], []):
                raw = point.get('return_pct')
                if raw is not None:
                    moves.append({'ticker': row['ticker'], 'date': point['date'], 'return_pct': raw,
                                  'volume': volumes.get(point['date'])})
        window['volume'] = {'dates': dates, 'series': {row['ticker']: volume.get('series', {}).get(row['ticker'], []) for row in window['top20']},
                            'lowest': ordered[0] if ordered else None, 'highest': ordered[-1] if ordered else None,
                            'incomplete_tickers': [r['ticker'] for r in window['top20'] if not r['volume']['complete']],
                            'available': bool(stats),
                            'largest_move': max(moves, key=lambda p: abs(Decimal(p['return_pct']))) if moves else None}
    return payload
