"""Collect a reviewable case dossier; never generate summaries or change rankings."""

import argparse
import concurrent.futures
import csv
import hashlib
import io
import json
import os
import re
import subprocess
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CVM_BASE = 'https://dados.cvm.gov.br/dados/CIA_ABERTA/'


def read_keys(path):
    keys = {}
    if path.exists():
        for line in path.read_text(encoding='utf-8-sig').splitlines():
            if '=' in line and not line.lstrip().startswith('#'):
                name, value = line.split('=', 1)
                keys[name.strip()] = value.strip()
    keys.update({name: value for name, value in os.environ.items()
                 if name in {'TAVILY_API_KEY', 'OPENAI_API_KEY'}})
    return keys


def request_bytes(url, payload=None, key=None):
    headers = {'User-Agent': 'v8-ranking-context-collection'}
    if payload is not None:
        headers['Content-Type'] = 'application/json'
    if key:
        headers['Authorization'] = 'Bearer ' + key
    req = urllib.request.Request(url, data=None if payload is None else
                                 json.dumps(payload).encode(), headers=headers)
    with urllib.request.urlopen(req, timeout=40) as response:
        return response.read()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def ranked_tickers(featured):
    tickers = set()
    for name in ('top20.csv', 'top20_alternativo.csv'):
        with (featured / name).open(encoding='utf-8-sig', newline='') as handle:
            tickers.update(row['ticker'] for row in csv.DictReader(handle))
    return tickers


def safe_search(task, keys, start, end):
    label, query = task
    if not keys.get('TAVILY_API_KEY'):
        return {'label': label, 'status': 'missing_credential', 'results': []}
    payload = {'query': query, 'topic': 'general', 'search_depth': 'advanced',
               'start_date': start, 'end_date': end, 'max_results': 5,
               'include_answer': False, 'include_raw_content': False}
    try:
        data = json.loads(request_bytes('https://api.tavily.com/search', payload,
                                        keys['TAVILY_API_KEY']))
        return {'label': label, 'query': query, 'status': 'retrieved_pending_review',
                'results': [{name: item.get(name) for name in
                             ('title', 'url', 'content', 'published_date', 'score')}
                            for item in data.get('results', [])]}
    except urllib.error.HTTPError as error:
        return {'label': label, 'status': 'source_failed', 'http_status': error.code,
                'results': []}
    except (OSError, ValueError) as error:
        return {'label': label, 'status': 'source_failed',
                'error_type': type(error).__name__, 'results': []}


def parse_exa(text):
    items = []
    for block in re.split(r'(?m)^Title: ', text)[1:]:
        title, _, rest = block.partition('\n')
        url = re.search(r'(?m)^URL: (https?://[^\s]+)', rest)
        date = re.search(r'(?m)^Published: (.+)', rest)
        if url:
            items.append({'title': title.strip(), 'url': url.group(1),
                          'published_date': date.group(1).strip() if date else None,
                          'retrieval_status': 'indexed_only_pending_page_review'})
    return items


def exa_search(task, directory):
    label, query = task
    try:
        result = subprocess.run(['mcporter.cmd', 'call', 'exa.web_search_exa',
                                 'query=' + query, 'numResults=5'], capture_output=True,
                                text=True, encoding='utf-8', errors='replace', timeout=70)
        if result.returncode:
            return {'label': label, 'query': query, 'status': 'source_failed', 'results': []}
        (directory / (label + '.txt')).write_text(result.stdout, encoding='utf-8')
        items = parse_exa(result.stdout)
        return {'label': label, 'query': query,
                'status': 'retrieved_pending_review' if items else 'no_parseable_results',
                'results': items}
    except (OSError, subprocess.TimeoutExpired) as error:
        return {'label': label, 'status': 'source_failed',
                'error_type': type(error).__name__, 'results': []}


def collect(config, output, use_exa=False):
    output.mkdir(parents=True, exist_ok=True)
    config_bytes = config.read_bytes()
    cfg = json.loads(config_bytes)
    start, end = cfg['week_start'], cfg['week_end']
    if (cfg['reference_date'], start, end) != ('2026-09-22', '2026-09-14', '2026-09-20'):
        raise ValueError('This collector is limited to the preserved September 2026 case')
    expected = ranked_tickers(ROOT / 'resultados' / cfg['reference_date'])
    configured = [ticker for issuer in cfg['issuers'] for ticker in issuer['tickers']]
    if set(configured) != expected or len(configured) != len(set(configured)):
        raise ValueError('Issuer configuration must cover each ranked ticker exactly once')
    keys = read_keys(ROOT / '.env')
    cad_url = CVM_BASE + 'CAD/DADOS/cad_cia_aberta.csv'
    cad_bytes = request_bytes(cad_url)
    cad_rows = list(csv.DictReader(io.StringIO(cad_bytes.decode('cp1252')), delimiter=';'))
    ipe_url = CVM_BASE + 'DOC/IPE/DADOS/ipe_cia_aberta_2026.zip'
    ipe_bytes = request_bytes(ipe_url)
    with zipfile.ZipFile(io.BytesIO(ipe_bytes)) as archive:
        rows = list(csv.DictReader(io.StringIO(archive.read(archive.namelist()[0])
                                              .decode('cp1252')), delimiter=';'))
    issuers = []
    for item in cfg['issuers']:
        code = item['cvm_code']
        matches = [row for row in cad_rows if row['CD_CVM'].lstrip('0') == code]
        identities = {(row['CNPJ_CIA'], row['DENOM_SOCIAL']) for row in matches}
        if len(identities) != 1:
            raise ValueError('Ambiguous or missing CVM identity for code ' + code)
        cnpj, name = next(iter(identities))
        documents = [row for row in rows if row['Codigo_CVM'].lstrip('0') == code
                     and start <= row['Data_Entrega'][:10] <= end]
        references = [row for row in rows if row['Codigo_CVM'].lstrip('0') == code
                      and start <= row['Data_Referencia'][:10] <= end
                      and row['Data_Entrega'][:10] > end]
        issuers.append({**item, 'legal_name': name, 'cnpj': cnpj,
                        'identity_source': cad_url,
                        'documents_delivered_in_week': documents,
                        'later_documents_referencing_week': references,
                        'review_status': 'pending_review'})
    tasks = [(item['cvm_code'], item['search_name'] + ' ' + ' '.join(item['tickers'])
              + ' notícias comunicado setembro 2026 14 18') for item in issuers]
    tasks += [('macro_brazil', 'Copom decisão 16 setembro 2026 Banco Central'),
              ('macro_us', 'site:federalreserve.gov FOMC September 16 2026 statement'),
              ('macro_fiscal', 'site:senado.leg.br IFI orçamento 17 setembro 2026')]
    searches = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for result in pool.map(lambda task: safe_search(task, keys, start, end), tasks):
            searches.append(result)
            write_json(output / 'tavily-searches.json', searches)
            print('Tavily:', result['label'], result['status'], len(result['results']), flush=True)
    exa = []
    if use_exa:
        directory = output / 'exa'
        directory.mkdir(exist_ok=True)
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
            for result in pool.map(lambda task: exa_search(task, directory), tasks):
                exa.append(result)
                write_json(output / 'exa-searches.json', exa)
                print('Exa:', result['label'], result['status'], len(result['results']), flush=True)
    ptax_url = ("https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/"
                "CotacaoDolarPeriodo(dataInicial=@dataInicial,dataFinalCotacao=@dataFinalCotacao)"
                "?@dataInicial='09-11-2026'&@dataFinalCotacao='09-18-2026'&$format=json")
    try:
        ptax = {'status': 'retrieved', 'url': ptax_url,
                'data': json.loads(request_bytes(ptax_url))['value']}
    except (OSError, ValueError, KeyError) as error:
        ptax = {'status': 'source_failed', 'error_type': type(error).__name__}
    dossier = {'schema_version': 1, 'stage': 'evidence_collection_pending_review',
               'reference_date': cfg['reference_date'], 'week_start': start, 'week_end': end,
               'collected_at': datetime.now(timezone.utc).isoformat(),
               'config_sha256': hashlib.sha256(config_bytes).hexdigest(),
               'official_sources': [{'url': cad_url, 'sha256': hashlib.sha256(cad_bytes).hexdigest()},
                                    {'url': ipe_url, 'sha256': hashlib.sha256(ipe_bytes).hexdigest(),
                                     'row_count': len(rows)}],
               'issuers': issuers, 'tavily_searches': searches, 'exa_searches': exa, 'ptax': ptax,
               'warning': 'Search snippets are candidates, not verified events or causal explanations.'}
    write_json(output / 'collection.json', dossier)
    print('Saved dossier:', output / 'collection.json')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path,
                        default=ROOT / 'context/case-2026-09-22/issuers.json')
    parser.add_argument('--output', type=Path,
                        default=ROOT / 'runs/context-case-2026-09-22')
    parser.add_argument('--exa', action='store_true', help='Also query the available Exa MCP CLI')
    args = parser.parse_args()
    if args.output.exists() and any(args.output.iterdir()):
        parser.error('Use a new output directory to preserve earlier collection snapshots')
    collect(args.config, args.output, args.exa)


if __name__ == '__main__':
    main()
