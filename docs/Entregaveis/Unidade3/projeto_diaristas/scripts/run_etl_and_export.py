"""Executa pipeline ETL completo + exportação de snapshot para o dashboard."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

TARGETS = ["4097", "6383", "8529", "5440", "6374"]


def run(cmd: list[str]) -> None:
    print("$", " ".join(cmd))
    subprocess.run(cmd, cwd=ROOT, check=True)


def main() -> int:
    py = sys.executable
    for table in TARGETS:
        spec = ROOT / "specs" / f"t{table}.yaml"
        if not spec.exists():
            run([py, "-m", "pipeline.ai_mapper", "--tabela", table])

    run(
        [py, "-m", "pipeline.etl"]
        + [arg for t in TARGETS for arg in ("--target", t)]
        + ["--nivel", "BR", "--periodos", "last"]
    )

    repo_root = ROOT.parent.parent.parent.parent
    contratante = repo_root / "PesquisaFormularios" / "pesquisa-contratante.xlsx"
    diaristas = repo_root / "PesquisaFormularios" / "pesquisa-diaristas.xlsx"
    if contratante.exists() and diaristas.exists():
        run([py, "-m", "pipeline.etl", "--formularios"])
    else:
        print("AVISO: Excel de formulários não encontrados — pulando --formularios")

    run([py, "-m", "pipeline.modelo"])
    run([py, "scripts/export_snapshot.py", "--force"])
    print("\nPipeline concluído. Rode: streamlit run app.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
