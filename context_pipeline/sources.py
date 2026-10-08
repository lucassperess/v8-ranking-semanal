"""Bounded source collection. Credentials and full source bodies remain private."""

import base64
import csv
import hashlib
import io
import json
import re
import time
import threading
import unicodedata
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from scripts.collect_case_context import request_bytes

CVM = 'https://dados.cvm.gov.br/dados/CIA_ABERTA/'
B3 = 'https://sistemaswebb3-listados.b3.com.br/listedCompaniesProxy/CompanyCall/'


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n',
                    encoding='utf-8', newline='\n')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalized(value):
    return re.sub(r'\s+', ' ', ''.join(c for c in unicodedata.normalize('NFKD', value)
                                       if not unicodedata.combining(c))).strip().lower()


def entity_name(value):
    text = normalized(value)
    text = re.sub(r'\bbco\b', 'banco', text)
    text = re.sub(r'\bcia\b', 'companhia', text)
    text = re.sub(r'\bsid\b', 'siderurgica', text)
    return ' '.join(word for word in re.findall(r'[a-z0-9]+', text)
                    if word not in {'do', 'da', 'de', 'dos', 'das', 's', 'a', 'sa'})


class Collector:
    def __init__(self, directory, keys, cache=None, replay=False):
        self.directory = Path(directory)
        self.cache = Path(cache) if cache else self.directory / 'cache'
        self.keys = keys
        self.replay = replay
        self.api_attempts = {}
        self.api_lock = threading.Lock()

    def api_snapshot(self):
        with self.api_lock:
            return dict(sorted(self.api_attempts.items()))

    def get(self, label, url, payload=None, key=None, cached=False):
        request_sha = hashlib.sha256(json.dumps({'url': url, 'payload': payload}, sort_keys=True).encode()).hexdigest()
        path = self.directory / (label + '.bin')
        metadata_path = path.with_suffix('.json')
        if path.exists() and metadata_path.exists():
            metadata = json.loads(metadata_path.read_text(encoding='utf-8'))
            changed = (metadata.get('url') != url or
                       metadata.get('request_sha256', request_sha) != request_sha or
                       metadata.get('query') != (payload.get('query') if payload else None))
            if changed:
                path = self.directory / (label + '-' + request_sha[:12] + '.bin')
        if path.exists():
            return path.read_bytes()
        if self.replay:
            raise ValueError('Source is absent from the saved collection: ' + label)
        cache_path = self.cache / (hashlib.sha256(url.encode()).hexdigest() + '.bin')
        if cached and cache_path.exists() and time.time() - cache_path.stat().st_mtime < 86400:
            raw = cache_path.read_bytes()
        else:
            provider = {'https://api.tavily.com/search': 'tavily_search',
                        'https://api.tavily.com/extract': 'tavily_extract',
                        'https://api.openai.com/v1/responses': 'openai'}.get(url)
            if provider:
                with self.api_lock:
                    self.api_attempts[provider] = self.api_attempts.get(provider, 0) + 1
            raw = request_bytes(url, payload, key)
            if cached:
                cache_path.parent.mkdir(parents=True, exist_ok=True)
                cache_path.write_bytes(raw)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        write(path.with_suffix('.json'), {'url': url, 'sha256': sha(path),
                                         'request_sha256': request_sha,
                                         'collected_at': datetime.now(timezone.utc).isoformat(),
                                         'query': payload.get('query') if payload else None})
        return raw

    def json(self, *args, **kwargs):
        return json.loads(self.get(*args, **kwargs))

    def table(self, label, url):
        return list(csv.DictReader(io.StringIO(self.get(label, url, cached=True).decode('cp1252')),
                                   delimiter=';'))

    def archive(self, label, url):
        return zipfile.ZipFile(io.BytesIO(self.get(label, url, cached=True)))

    def b3(self, action, query, label):
        encoded = base64.b64encode(json.dumps(query).encode()).decode()
        url = B3 + action + '/' + encoded
        return self.json(label, url, cached=True), url

    def identify(self, ticker, isins):
        prefix = re.sub(r'\d+$', '', ticker)
        found, url = self.b3('GetInitialCompanies', {'language': 'pt-br', 'pageNumber': 1,
                            'pageSize': 100, 'company': prefix}, 'b3-search-' + prefix)
        matches = [row for row in found.get('results', []) if row['issuingCompany'] == prefix]
        if len(matches) != 1:
            raise ValueError('Missing or ambiguous issuer identity')
        candidate = matches[0]
        detail, detail_url = self.b3('GetDetail', {'language': 'pt-br',
                                    'codeCVM': candidate['codeCVM']}, 'b3-' + prefix)
        instruments = [r for r in detail.get('otherCodes', []) if r['code'] == ticker]
        if (len(instruments) != 1 or not isins or
                isins != {instruments[0]['isin']} or
                detail['cnpj'].zfill(14) != candidate['cnpj'].zfill(14)):
            raise ValueError('Current B3 identity does not match the dated ranking ISIN')
        return {'cvm_code': str(int(detail['codeCVM'])), 'name': detail['companyName'],
                'search_name': detail['tradingName'], 'cnpj': detail['cnpj'].zfill(14),
                'tickers': [ticker], 'identity_url': detail_url, 'identity_search_url': url,
                'identity_basis': 'dated_ranking_isin_matches_current_b3_detail'}

    def search(self, label, query, start, end):
        payload = {'query': query, 'topic': 'general', 'search_depth': 'advanced',
                   'start_date': start, 'end_date': end, 'max_results': 5,
                   'include_answer': False, 'include_raw_content': False}
        return self.json('search-' + label, 'https://api.tavily.com/search', payload,
                         self.keys.get('TAVILY_API_KEY')).get('results', [])

    def extract(self, label, candidates):
        urls = list(dict.fromkeys(r['url'] for r in candidates))[:8]
        if not urls:
            return []
        response = self.json('extract-' + label, 'https://api.tavily.com/extract',
                             {'urls': urls, 'extract_depth': 'advanced', 'format': 'markdown',
                              'timeout': 30}, self.keys.get('TAVILY_API_KEY'))
        return [{'id': label + '-web-' + str(i), 'url': r['url'],
                 'title': next((c['title'] for c in candidates if c['url'] == r['url']), r['url']),
                 'body': r['raw_content'][:14000], 'date_basis': 'body_publication_date'}
                for i, r in enumerate(response.get('results', [])) if r.get('raw_content')]

    def documents(self, year):
        url = CVM + f'DOC/IPE/DADOS/ipe_cia_aberta_{year}.zip'
        with self.archive('ipe-' + str(year), url) as archive:
            member = archive.namelist()[0]
            return list(csv.DictReader(io.StringIO(archive.read(member).decode('cp1252')), delimiter=';'))

    def document_body(self, row, label):
        from pypdf import PdfReader

        raw = self.get(label, row['Link_Download'])
        if not raw.startswith(b'%PDF'):
            return None
        reader = PdfReader(io.BytesIO(raw))
        text = '\n'.join(page.extract_text() or '' for page in reader.pages[:20])
        if not text.strip():
            return None
        return {'id': label, 'url': row['Link_Download'],
                'title': row.get('Assunto') or row.get('Categoria') or 'Documento CVM',
                'body': text[:18000], 'publication_date': row['Data_Entrega'][:10],
                'date_basis': 'cvm_delivery_catalog', 'date_evidence': row['Data_Entrega'],
                'cvm_code': str(int(row['Codigo_CVM']))}

    def market(self, week, windows, trace=None):
        from scripts.build_market_context import pair

        start, end = week['preceding_close'], week['last_week_close']
        indicators, missing = [], []
        for symbol, label in [('BVSP', 'Ibovespa'), ('GSPC', 'S&P 500'), ('IXIC', 'Nasdaq Composite'),
                              ('PTAX', 'Dólar · PTAX venda')]:
            try:
                if symbol == 'PTAX':
                    url = ("https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/"
                           "CotacaoDolarPeriodo(dataInicial=@dataInicial,dataFinalCotacao=@dataFinalCotacao)"
                           f"?@dataInicial='{datetime.fromisoformat(start):%m-%d-%Y}'"
                           f"&@dataFinalCotacao='{datetime.fromisoformat(end):%m-%d-%Y}'&$format=json")
                    raw = self.json('market-' + symbol, url)
                    points = {}
                    for row in raw['value']:
                        day = row['dataHoraCotacao'][:10]
                        if day in points:
                            raise ValueError('Duplicate PTAX date')
                        points[day] = str(row['cotacaoVenda'])
                else:
                    a = int(datetime.fromisoformat(start).replace(tzinfo=timezone.utc).timestamp())
                    b = int((datetime.fromisoformat(end) + timedelta(days=2)).replace(tzinfo=timezone.utc).timestamp())
                    url = f'https://query1.finance.yahoo.com/v8/finance/chart/%5E{symbol}?period1={a}&period2={b}&interval=1d'
                    raw = self.json('market-' + symbol, url)['chart']['result'][0]
                    if raw['meta']['symbol'] != '^' + symbol:
                        raise ValueError('Wrong market instrument')
                    points = {}
                    for stamp, close in zip(raw['timestamp'], raw['indicators']['quote'][0]['close'], strict=True):
                        day = datetime.fromtimestamp(stamp, timezone.utc).date().isoformat()
                        if close is not None:
                            if day in points:
                                raise ValueError('Duplicate market date')
                            points[day] = str(close)
                item = {'id': symbol, 'label': label, 'unit': 'R$ por US$' if symbol == 'PTAX' else 'pontos',
                        'definition': 'Referência diária do Banco Central, não fechamento de mercado.'
                        if symbol == 'PTAX' else 'Fechamento diário do índice segundo o provedor.',
                        'source_url': url, 'source_label': 'Banco Central · PTAX' if symbol == 'PTAX' else 'Yahoo Finance · histórico diário'}
                for key, window in windows.items():
                    try:
                        item[key] = pair(points, window['start_date'], window['end_date'])
                    except ValueError:
                        item[key] = None
                indicators.append(item)
            except (OSError, ValueError, KeyError, TypeError) as exc:
                missing.append(symbol)
                if trace is not None:
                    trace.failure('market_indicator', exc, item=symbol)
        return indicators, missing
