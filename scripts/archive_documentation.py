"""Associa guias a uma execução já conferida, sem reescrever resultados."""
import argparse
from pathlib import Path
from webapp.doc_revision import archive


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir', type=Path, required=True)
    parser.add_argument('--reviewed', action='store_true', required=True,
                        help='Confirma revisão da compatibilidade dos guias com as regras da execução')
    args = parser.parse_args()
    print(archive(args.run_dir, mode='reviewed_after_execution'))


if __name__ == '__main__':
    main()
