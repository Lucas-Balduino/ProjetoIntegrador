"""Carregamento dos marts com cache e fallback para snapshot versionado."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent.parent
MARTS_LOCAL = ROOT_DIR / "data" / "marts"
MARTS_SNAPSHOT = ROOT_DIR / "dashboard" / "assets" / "marts"

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


def _read_mart(base_dir: Path, name: str) -> pd.DataFrame:
    pq = base_dir / f"{name}.parquet"
    csv = base_dir / f"{name}.csv"
    if pq.exists() and pq.suffix != ".SKIPPED":
        try:
            return pd.read_parquet(pq)
        except Exception:
            pass
    if csv.exists():
        return pd.read_csv(csv)
    return pd.DataFrame()


def _resolve_marts_dir() -> tuple[Path, str]:
    if MARTS_LOCAL.exists() and (
        any(MARTS_LOCAL.glob("*.csv")) or any(MARTS_LOCAL.glob("*.parquet"))
    ):
        return MARTS_LOCAL, "local"
    if MARTS_SNAPSHOT.exists():
        return MARTS_SNAPSHOT, "snapshot"
    return MARTS_SNAPSHOT, "missing"


@st.cache_data(ttl=3600, show_spinner=False)
def load_marts() -> dict[str, Any]:
    """Carrega todos os marts disponíveis."""
    base_dir, source = _resolve_marts_dir()
    marts: dict[str, pd.DataFrame] = {}
    for name in MART_FILES:
        frame = _read_mart(base_dir, name)
        if not frame.empty:
            marts[name] = frame
    return {"source": source, "base_dir": str(base_dir), "marts": marts}


def marts_available(marts_payload: dict[str, Any]) -> bool:
    marts = marts_payload.get("marts", {})
    return bool(marts.get("fato_mercado_trabalho") is not None and not marts["fato_mercado_trabalho"].empty)


def show_data_missing_help() -> None:
    st.error("Dados do dashboard não encontrados.")
    st.markdown(
        """
        Execute o pipeline ETL e exporte o snapshot:

        ```powershell
        cd docs/Entregaveis/Unidade3/projeto_diaristas
        python -m pip install -r requirements.txt
        python -m pipeline.etl --target 4097 --target 6383 --target 8529 --target 5440 --target 6374 --nivel BR --periodos last
        python -m pipeline.etl --formularios
        python -m pipeline.modelo
        python scripts/export_snapshot.py
        ```
        """
    )
