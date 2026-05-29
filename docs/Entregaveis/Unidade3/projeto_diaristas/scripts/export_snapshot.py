"""Copia marts locais para snapshot versionado (Streamlit Cloud)."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "data" / "marts"
TARGET = ROOT / "dashboard" / "assets" / "marts"

MART_FILES = [
    "dim_tempo",
    "dim_territorio",
    "dim_indicador",
    "dim_recorte",
    "fato_mercado_trabalho",
    "fato_diaristas",
    "dim_pergunta",
    "dim_respondente",
    "fato_pesquisa_primaria",
    "fato_pesquisa_agregada",
]


def export_snapshot(*, force: bool = False) -> int:
    if not SOURCE.exists():
        print(f"ERRO: {SOURCE} não existe. Rode o pipeline ETL primeiro.")
        return 1

    TARGET.mkdir(parents=True, exist_ok=True)
    copied = 0
    for name in MART_FILES:
        for ext in (".parquet", ".csv"):
            src = SOURCE / f"{name}{ext}"
            if not src.exists() or src.name.endswith(".SKIPPED"):
                continue
            dst = TARGET / src.name
            if dst.exists() and not force:
                pass
            shutil.copy2(src, dst)
            copied += 1
            print(f"  {src.name} -> {dst}")

    if copied == 0:
        print("Nenhum arquivo copiado. Verifique data/marts/.")
        return 1

    print(f"\nSnapshot exportado: {copied} arquivo(s) em {TARGET}")
    print("Commit dashboard/assets/marts/ para deploy no Streamlit Cloud.")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Exporta marts para snapshot do dashboard")
    parser.add_argument("--force", action="store_true", help="Sobrescreve arquivos existentes")
    args = parser.parse_args()
    raise SystemExit(export_snapshot(force=args.force))


if __name__ == "__main__":
    main()
