"""Gravação Parquet/CSV com dtypes seguros para colunas object mistas."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd


LOGGER = logging.getLogger(__name__)


def prepare_for_parquet(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza dtypes para evitar falha do PyArrow em colunas heterogêneas."""
    if df.empty:
        return df

    out = df.copy()
    for col in out.columns:
        s = out[col]
        if pd.api.types.is_datetime64_any_dtype(s):
            continue
        if s.dtype == object:
            non_null = s.dropna()
            if non_null.empty:
                continue
            types = {type(v) for v in non_null.head(200)}
            if types <= {str}:
                out[col] = s.astype("string")
            elif types <= {int, float} or types <= {int} or types <= {float}:
                out[col] = pd.to_numeric(s, errors="coerce")
            else:
                out[col] = s.map(lambda x: pd.NA if pd.isna(x) else str(x)).astype("string")
    return out


def save_dataframe(
    df: pd.DataFrame,
    csv_path: Path,
    pq_path: Path | None = None,
    *,
    stem: str = "",
) -> tuple[Path, Path | None]:
    """Grava CSV e, se pq_path informado, Parquet após prepare_for_parquet."""
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    safe = prepare_for_parquet(df)
    safe.to_csv(csv_path, index=False, encoding="utf-8")
    if pq_path is None:
        return csv_path, None
    try:
        safe.to_parquet(pq_path, index=False)
        return csv_path, pq_path
    except Exception as exc:
        LOGGER.warning("Parquet falhou para %s: %s", stem or csv_path.stem, exc)
        skipped = pq_path.with_suffix(".SKIPPED")
        return csv_path, skipped
