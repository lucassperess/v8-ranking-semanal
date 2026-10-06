"""Exportar somente derivados permitidos para uma demonstração conferida.

python -m scripts.export_audit --run-dir runs/semana --destination resultados/AAAA-MM-DD
O destino deve conter o relatório e os retornos da mesma execução.
"""
import argparse
import shutil
from pathlib import Path

from b3_registry import digest
from webapp.presentation import DOWNLOADS, audit_details, output_path


def export(run_dir: Path, destination: Path) -> None:
    if not audit_details(run_dir)["available"]:
        raise ValueError("Execução sem os derivados de auditoria necessários")
    if digest(run_dir / "ranking_report.json") != digest(destination / "ranking_report.json"):
        raise ValueError("O destino não representa a mesma execução; nenhum arquivo copiado")
    # Valide todos os arquivos existentes antes de qualquer cópia.
    files = [(output_path(run_dir, name), output_path(destination, name, featured=True))
             for name, (group, _) in DOWNLOADS.items()
             if group in {"etl", "classification", "classification_alternative"}
             or name == "quality_context_alternativo.json"]
    for source, target in files:
        if not source.is_file():
            raise ValueError(f"Derivado ausente: {source.name}")
        if target.exists() and digest(source) != digest(target):
            raise ValueError(f"Destino já contém outra versão de {target.name}")
    for source, target in files:
        if not target.exists():
            shutil.copyfile(source, target)
    audit_details(destination, featured=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--destination", required=True, type=Path)
    args = parser.parse_args()
    export(args.run_dir, args.destination)
