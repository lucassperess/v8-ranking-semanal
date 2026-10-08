"""Arquiva apenas o novo derivado de volume, sem alterar arquivos históricos."""

import argparse
import json
from pathlib import Path

from webapp.presentation import build_presentation


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir', required=True, type=Path)
    parser.add_argument('--normalized', required=True, type=Path)
    parser.add_argument('--featured', action='store_true')
    args = parser.parse_args()
    target = args.run_dir / 'volume_context.json'
    if target.exists():
        raise ValueError('Derivado já existe; preserve a versão anterior')
    payload = build_presentation(args.run_dir, featured=args.featured, normalized_path=args.normalized)
    target.write_text(json.dumps(payload['volume'], ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    print('Derivado de volume conferido e arquivado:', target)


if __name__ == '__main__':
    main()
