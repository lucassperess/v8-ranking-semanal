"""Compile reviewed case context separately from immutable ranking artifacts."""

import hashlib
import json
from datetime import date
from decimal import Decimal
from pathlib import Path

from scripts.collect_case_context import ROOT, write_json


def percent(value):
    return f'{Decimal(value):+.2f}%'.replace('.', ',')


def money(value):
    number = abs(Decimal(value))
    if number >= 1000000:
        return 'R$ ' + f'{number / 1000000:.2f}'.replace('.', ',') + ' milhões'
    if number >= 1000:
        return 'R$ ' + f'{number / 1000:.2f}'.replace('.', ',') + ' mil'
    return 'R$ ' + f'{number:.2f}'.replace('.', ',')


def short_date(value):
    return date.fromisoformat(value).strftime('%d/%m/%Y')


def price_reading(record, window):
    """Select adjacent comparisons inside the window, without changing prices."""
    values = record[window]
    if values is None:
        if window == 'alternative' and record['main']:
            first = record['observations']['daily_comparisons'][0]
            if first['return_pct'] is None:
                return {'status': 'unavailable', 'text':
                        f"Falta um fechamento válido em {short_date(first['end_date'])}, "
                        'a data inicial da alternativa. Por isso, o retorno dessa janela '
                        'não pode ser calculado. O retorno da semana completa continua '
                        'disponível, porque seus fechamentos inicial e final são válidos.'}
        return {'status': 'unavailable', 'text': 'Sem comparação válida nesta janela.'}
    start, end = values['start_date'], values['end_date']
    daily = [r for r in record['observations']['daily_comparisons']
             if start <= r['start_date'] and r['end_date'] <= end]
    valid = [r for r in daily if r['return_pct'] is not None]
    missing = len(daily) - len(valid)
    text = (f"Entre {short_date(start)} e {short_date(end)}, {record['ticker']} teve retorno de "
            f"{percent(values['return_pct'])}. O fechamento passou de "
            f"R$ {format(Decimal(values['start_close']), '.2f').replace('.', ',')} para "
            f"R$ {format(Decimal(values['end_close']), '.2f').replace('.', ',')} por ação.")
    if valid:
        strongest = max(valid, key=lambda r: abs(Decimal(r['return_pct'])))
        text += (f" O maior movimento diário entre as comparações com dois preços válidos "
                 f"foi de {percent(strongest['return_pct'])}, "
                 f"entre {short_date(strongest['start_date'])} e "
                 f"{short_date(strongest['end_date'])}.")
        if not missing and all(Decimal(r['return_pct']) > 0 for r in valid):
            text += ' Todas as comparações diárias dessa janela foram positivas.'
    if missing:
        text += (f' Faltam dois preços válidos em {missing} das comparações diárias; '
                 'as lacunas permanecem no gráfico e não viram retorno zero.')
    return {'status': 'available', 'text': text, 'start_date': start, 'end_date': end,
            'daily_comparisons': daily, 'missing_comparisons': missing,
            'return_pct': values['return_pct']}


def window_explanation(record):
    if not record['main'] or not record['alternative']:
        if record['main'] and not record['alternative']:
            return ('A semana completa tem preços válidos em suas duas pontas. '
                    'A alternativa exige um fechamento inicial dentro da semana, '
                    'que não está disponível para este ativo. Por isso, só o retorno '
                    'da semana completa pode ser apresentado.')
        return 'As janelas podem ter elegibilidade diferente; confira as pontas disponíveis.'
    first = record['observations']['daily_comparisons'][0]
    if first['return_pct'] is None:
        return 'A comparação até o primeiro fechamento da semana não tem dois preços válidos.'
    text = (f"A semana completa inclui o movimento de {short_date(first['start_date'])} "
            f"a {short_date(first['end_date'])}: {percent(first['return_pct'])}. "
            'Dentro da semana começa no fechamento de segunda-feira e exclui esse movimento. '
            f"Por isso, os resultados são {percent(record['main']['return_pct'])} e "
            f"{percent(record['alternative']['return_pct'])}, respectivamente. "
            'Os retornos sucessivos se acumulam por multiplicação, não por soma.')
    if record['observations']['missing_comparisons']:
        text += (' Os resultados totais usam os preços das pontas. As comparações diárias '
                 'ausentes não são preenchidas e impedem reconstruir toda a sequência diária.')
    return text


def financial_reading(record):
    if not record.get('accounts'):
        return None
    accounts = record['accounts']
    result = accounts['net_result']
    prior = accounts['prior_year_net_result']
    scope = 'consolidado' if record['scope'] == 'con' else 'individual'
    kind = 'prejuízo' if Decimal(result['value_brl']) < 0 else 'lucro'
    prior_kind = 'prejuízo' if Decimal(prior['value_brl']) < 0 else 'lucro'
    text = (f"No segundo trimestre de 2026 (abril a junho), a receita registrada foi de "
            f"{money(accounts['revenue']['value_brl'])} e o {kind} {scope} foi de "
            f"{money(result['value_brl'])}. No mesmo trimestre de 2025, houve "
            f"{prior_kind} de {money(prior['value_brl'])}. "
            f"Este demonstrativo foi entregue à CVM em {short_date(record['filing']['DT_RECEB'][:10])}, "
            'antes da semana analisada: é um antecedente, não uma notícia nova daquela semana.')
    equity = accounts.get('equity')
    if equity and Decimal(equity['value_brl']) < 0:
        text += (f" Em 30/06/2026, o patrimônio líquido era negativo em "
                 f"{money(equity['value_brl'])}: os passivos superavam os ativos nesse balanço.")
    return {'text': text, 'source_ids': ['itr:' + record['cvm_code']],
            'scope': record['scope'], 'period_start': '2026-04-01',
            'period_end': '2026-06-30'}


def validate_source(source, cutoff='2026-09-18'):
    if not all(source.get(k) for k in ('identity_confirmed', 'body_reviewed', 'date_verified')):
        raise ValueError('Source requires reviewed identity, body and date')
    publication = date.fromisoformat(source['publication_date'])
    if not source.get('date_basis') or not source.get('date_evidence'):
        raise ValueError('Date evidence is missing')
    if publication > date.fromisoformat('2026-09-20'):
        raise ValueError('Source publication is outside case calendar week')
    if bool(source['after_price_end']) != (publication > date.fromisoformat(cutoff)):
        raise ValueError('Post-close date marker disagrees with disclosure date')


def validate_context(context, expected):
    sources = {r['id']: r for r in context['sources']}
    if len(sources) != len(context['sources']):
        raise ValueError('Duplicate source identity')
    for source in sources.values():
        validate_source(source)
    tickers = [r['ticker'] for r in context['assets']]
    if len(tickers) != len(set(tickers)) or set(tickers) != set(expected):
        raise ValueError('Context does not cover the exact union of both rankings')
    for issuer in context['issuers']:
        blocks = issuer['events'] + [issuer['interpretation']]
        if issuer['financial_context']:
            blocks.append(issuer['financial_context'])
        for block in blocks:
            if not block['text'].strip() or not block['source_ids']:
                raise ValueError('Company context requires sourced text')
            for source_id in block['source_ids']:
                source = sources[source_id]
                if source['cvm_code'] != issuer['cvm_code']:
                    raise ValueError('Context source belongs to a different company')
                if source['after_price_end'] and not block.get('after_price_end'):
                    raise ValueError('Later disclosure must be explicitly separated')


def build(output):
    directory = ROOT / 'context/case-2026-09-22'
    if output.exists():
        raise ValueError('Use a new output file to preserve prior context versions')
    config = json.loads((directory / 'issuers.json').read_text(encoding='utf-8'))
    evidence = json.loads((directory / 'expanded_evidence.json').read_text(encoding='utf-8'))
    triage = json.loads((directory / 'triage.json').read_text(encoding='utf-8'))
    editorial = json.loads((directory / 'editorial_notes.json').read_text(encoding='utf-8'))
    financial = {r['cvm_code']: r for r in evidence['financial']}
    notes = {r['cvm_code']: r for r in editorial['issuers']}
    sources = [r for r in triage['sources'] if r['disposition'] == 'approved']
    sources.extend(editorial['additional_sources'])
    for record in financial.values():
        if record.get('accounts'):
            filing = record['filing']
            sources.append({'id': 'itr:' + record['cvm_code'],
                            'cvm_code': record['cvm_code'], 'url': filing['LINK_DOC'],
                            'title': 'Demonstrativo trimestral CVM — abril a junho de 2026',
                            'publication_date': filing['DT_RECEB'][:10],
                            'event_date': '2026-06-30', 'after_price_end': False,
                            'context_type': 'financial_antecedent',
                            'date_basis': 'cvm_itr_delivery_catalog',
                            'date_evidence': filing['DT_RECEB'], 'identity_confirmed': True,
                            'body_reviewed': True, 'date_verified': True,
                            'version': filing['VERSAO'], 'document_id': filing['ID_DOC']})
    issuers = []
    for issuer in config['issuers']:
        note = notes[issuer['cvm_code']]
        issuers.append({'cvm_code': issuer['cvm_code'], 'name': issuer['search_name'],
                        'tickers': issuer['tickers'], 'financial_context':
                        financial_reading(financial[issuer['cvm_code']]),
                        'events': note['events'], 'interpretation': note['interpretation'],
                        'unresolved_question': note['unresolved_question'],
                        'causal_effect_on_return': 'not_established'})
    assets = [{'ticker': record['ticker'], 'cvm_code': record['cvm_code'],
               'main': price_reading(record, 'main'),
               'alternative': price_reading(record, 'alternative'),
               'window_explanation': window_explanation(record)} for record in evidence['prices']]
    result = {'schema_version': 1, 'reference_date': '2026-09-22',
              'price_end': '2026-09-18', 'calendar_week_end': '2026-09-20',
              'status': 'prepared_for_editorial_review_not_published',
              'scope': 'Case apenas; não gera contexto automaticamente para novos envios.',
              'issuer_count': len(issuers), 'asset_count': len(assets),
              'issuers': issuers, 'assets': assets, 'sources': sources,
              'input_sha256': {name: hashlib.sha256((directory / name).read_bytes()).hexdigest()
                               for name in ('issuers.json', 'expanded_evidence.json',
                                            'triage.json', 'editorial_notes.json')},
              'disclosure': 'Contexto preparado com auxílio de IA e revisão editorial. '
                            'A leitura dos preços é calculada diretamente dos arquivos da execução. '
                            'As fontes descrevem fatos e antecedentes; não comprovam a causa de cada retorno.'}
    validate_context(result, [t for r in config['issuers'] for t in r['tickers']])
    write_json(output, result)
    return result


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = build(args.output)
    print(json.dumps({'issuers': result['issuer_count'], 'assets': result['asset_count']}))
