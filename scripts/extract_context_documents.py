"""Download and extract official PDFs from an existing context collection snapshot."""

import argparse
import concurrent.futures
import hashlib
import io
import urllib.error
from pathlib import Path

from scripts.collect_case_context import request_bytes, write_json


def extract_document(task, destination):
    from pypdf import PdfReader
    from pypdf.errors import PyPdfError

    issuer, row = task
    result = {'cvm_code': issuer['cvm_code'], 'tickers': issuer['tickers'], 'metadata': row}
    try:
        body = request_bytes(row['Link_Download'])
        result['sha256'] = hashlib.sha256(body).hexdigest()
        if not body.startswith(b'%PDF'):
            result['status'] = 'non_pdf_response_pending_review'
            return result
        stem = (issuer['cvm_code'] + '-' + row['Protocolo_Entrega'].replace('/', '_')
                + '-v' + row['Versao'])
        path = destination / (stem + '.pdf')
        path.write_bytes(body)
        reader = PdfReader(io.BytesIO(body))
        text = '\n'.join(page.extract_text() or '' for page in reader.pages)
        (destination / (stem + '.txt')).write_text(text, encoding='utf-8')
        result.update(status='pdf_text_extracted_pending_review', file=path.as_posix(),
                      page_count=len(reader.pages), text=text)
    except urllib.error.HTTPError as error:
        result.update(status='source_failed', http_status=error.code)
    except (OSError, ValueError, PyPdfError) as error:
        result.update(status='source_failed', error_type=type(error).__name__)
    return result


def main():
    import json

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--collection', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() and any(args.output.iterdir()):
        parser.error('Use a new output directory to preserve existing documents')
    dossier = json.loads(args.collection.read_text(encoding='utf-8'))
    tasks = [(issuer, row) for issuer in dossier['issuers']
             for row in issuer['documents_delivered_in_week']]
    args.output.mkdir(parents=True, exist_ok=True)
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for result in pool.map(lambda task: extract_document(task, args.output), tasks):
            results.append(result)
            write_json(args.output / 'official-document-texts.json', results)
            print(result['cvm_code'], result['status'], flush=True)


if __name__ == '__main__':
    main()
