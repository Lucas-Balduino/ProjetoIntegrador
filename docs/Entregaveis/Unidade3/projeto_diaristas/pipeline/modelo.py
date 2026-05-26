"""Constrói o modelo dimensional PED-like a partir do staging.

Lê todos os arquivos `data/staging/t*.parquet` (ou CSV de fallback) e gera:

- `data/marts/dim_tempo.{parquet,csv}`
- `data/marts/dim_territorio.{parquet,csv}`
- `data/marts/dim_indicador.{parquet,csv}`
- `data/marts/dim_recorte.{parquet,csv}`
- `data/marts/fato_mercado_trabalho.{parquet,csv}`
- `data/marts/fato_diaristas.{parquet,csv}`

A view `fato_diaristas` é um filtro de `fato_mercado_trabalho`
restrito a registros cuja dim_recorte aponte para "Trabalhador doméstico"
ou ao indicador originado da tabela 6383 (nº de domicílios em que trabalhavam).
"""

from __future__ import annotations

import argparse
import logging
import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import yaml


LOGGER = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parent.parent
STAGING_DIR = ROOT_DIR / "data" / "staging"
MARTS_DIR = ROOT_DIR / "data" / "marts"
CATALOGO_PATH = ROOT_DIR / "pipeline" / "catalogo.yaml"


DIARISTA_PATTERNS = [
    re.compile(r"trabalhador.*dom[eé]stic", re.IGNORECASE),
    re.compile(r"diarist", re.IGNORECASE),
    re.compile(r"servi[çc]os dom[eé]sticos", re.IGNORECASE),
]


@dataclass
class Catalogo:
    tabelas: dict[int, dict]
    categorias_ped: dict[str, str]

    @classmethod
    def load(cls) -> "Catalogo":
        data = yaml.safe_load(CATALOGO_PATH.read_text(encoding="utf-8")) or {}
        tabs = {int(t["numero"]): t for t in data.get("tabelas", [])}
        cats = data.get("categorias_ped", {})
        return cls(tabelas=tabs, categorias_ped=cats)


def _read_staging() -> pd.DataFrame:
    parts: list[pd.DataFrame] = []
    if not STAGING_DIR.exists():
        return pd.DataFrame()
    for pq in STAGING_DIR.glob("t*.parquet"):
        try:
            parts.append(pd.read_parquet(pq))
        except Exception as exc:  # pragma: no cover
            LOGGER.warning("Falha lendo %s: %s", pq, exc)
    if not parts:
        for csv in STAGING_DIR.glob("t*.csv"):
            try:
                parts.append(pd.read_csv(csv))
            except Exception as exc:
                LOGGER.warning("Falha lendo %s: %s", csv, exc)
    if not parts:
        return pd.DataFrame()
    df = pd.concat(parts, ignore_index=True)
    return df


def _build_dim_tempo(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "periodo_codigo" not in df.columns:
        return pd.DataFrame(
            columns=["sk_tempo", "periodo_codigo", "periodo_nome", "ano", "periodicidade"]
        )
    cols = ["periodo_codigo"] + (["periodo_nome"] if "periodo_nome" in df.columns else [])
    base = df[cols].drop_duplicates().dropna(subset=["periodo_codigo"])
    if "periodo_nome" not in base.columns:
        base["periodo_nome"] = base["periodo_codigo"]
    base["periodo_codigo"] = base["periodo_codigo"].astype(str)

    def _ano(code: str, nome: str) -> str:
        if code[:4].isdigit():
            return code[:4]
        # Procura um ano de 4 dígitos no nome (ex.: "1º trimestre 2026").
        m = re.search(r"(19|20)\d{2}", nome or code)
        return m.group(0) if m else ""

    def _periodicidade(code: str, nome: str) -> str:
        if code[:4].isdigit() and len(code) >= 6 and code[4:6].isdigit():
            q = int(code[4:6])
            if 1 <= q <= 4 and len(code) == 6:
                return "trimestral"
            if 1 <= q <= 12:
                return "mensal/movel"
        low = (nome or "").lower()
        if "trimestre" in low:
            return "trimestral"
        if "-" in low and "20" in low:
            return "mensal/movel"
        return "outro"

    base["ano"] = base.apply(lambda r: _ano(r["periodo_codigo"], r["periodo_nome"]), axis=1)
    base["periodicidade"] = base.apply(
        lambda r: _periodicidade(r["periodo_codigo"], r["periodo_nome"]), axis=1
    )
    base["sk_tempo"] = range(1, len(base) + 1)
    return base[["sk_tempo", "periodo_codigo", "periodo_nome", "ano", "periodicidade"]]


def _build_dim_territorio(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "territorio_codigo" not in df.columns:
        return pd.DataFrame(columns=[
            "sk_territorio", "nivel", "territorio_codigo", "territorio_nome"
        ])
    cols = ["nivel_territorial_codigo", "nivel_territorial_nome", "territorio_codigo", "territorio_nome"]
    use = [c for c in cols if c in df.columns]
    base = df[use].drop_duplicates().dropna(subset=["territorio_codigo"])
    base = base.rename(columns={
        "nivel_territorial_codigo": "nivel_codigo",
        "nivel_territorial_nome": "nivel",
    })
    base["sk_territorio"] = range(1, len(base) + 1)
    return base[["sk_territorio", "nivel_codigo", "nivel", "territorio_codigo", "territorio_nome"]]


def _categoria_ped_for(row: dict, catalogo: Catalogo) -> str:
    tabela = int(row.get("tabela", 0))
    info = catalogo.tabelas.get(tabela, {})
    cats = info.get("categorias_ped") or []
    return ",".join(cats) if cats else "Outro"


def _build_dim_indicador(df: pd.DataFrame, catalogo: Catalogo) -> pd.DataFrame:
    if df.empty or "variavel_id" not in df.columns:
        return pd.DataFrame(columns=["sk_indicador", "tabela", "variavel_id", "variavel_nome", "unidade", "categoria_ped"])
    base = df[["tabela", "variavel_id", "variavel_nome", "unidade_medida_nome"]].drop_duplicates()
    base = base.dropna(subset=["variavel_id"])
    base = base.rename(columns={"unidade_medida_nome": "unidade"})
    base["categoria_ped"] = base.apply(lambda r: _categoria_ped_for(r.to_dict(), catalogo), axis=1)
    base["sk_indicador"] = range(1, len(base) + 1)
    return base[["sk_indicador", "tabela", "variavel_id", "variavel_nome", "unidade", "categoria_ped"]]


def _classif_columns(df: pd.DataFrame) -> list[tuple[str | None, str]]:
    """Detecta pares (id_col | None, nome_col) das classificações dinâmicas.

    Quando o SIDRA não devolve o código (D{i}C ausente) cai-se em apenas
    `_nome`, e o id_col fica como `None` — o nome é então usado como chave.
    """
    pairs: list[tuple[str | None, str]] = []
    seen: set[str] = set()
    for col in df.columns:
        m = re.match(r"classif(\d+)_(.+)_nome$", col)
        if not m:
            continue
        prefix = f"classif{m.group(1)}_{m.group(2)}"
        if prefix in seen:
            continue
        seen.add(prefix)
        id_col = f"{prefix}_id"
        if id_col in df.columns:
            pairs.append((id_col, col))
        else:
            pairs.append((None, col))
    return pairs


def _build_dim_recorte(df: pd.DataFrame) -> pd.DataFrame:
    """Empilha todas as classificações dinâmicas em uma única dim_recorte."""
    pairs = _classif_columns(df)
    if df.empty or not pairs:
        return pd.DataFrame(columns=["sk_recorte", "eixo", "valor_id", "valor_nome"])

    blocks: list[pd.DataFrame] = []
    for id_col, nome_col in pairs:
        # Extrai o nome do eixo (ex.: "classif1_sexo_nome" -> "sexo").
        base_col = id_col or nome_col
        eixo = re.sub(r"^classif\d+_", "", base_col)
        eixo = re.sub(r"_(id|nome)$", "", eixo)
        cols = [c for c in [id_col, nome_col] if c]
        b = df[cols].drop_duplicates().dropna(subset=[nome_col])
        if id_col:
            b = b.rename(columns={id_col: "valor_id", nome_col: "valor_nome"})
        else:
            b = b.rename(columns={nome_col: "valor_nome"})
            b["valor_id"] = b["valor_nome"]
        b["eixo"] = eixo
        blocks.append(b[["eixo", "valor_id", "valor_nome"]])

    out = pd.concat(blocks, ignore_index=True).drop_duplicates()
    total = pd.DataFrame([{"eixo": "total", "valor_id": None, "valor_nome": "Total"}])
    out = pd.concat([total, out], ignore_index=True).drop_duplicates(
        subset=["eixo", "valor_id"], keep="first"
    )
    out["sk_recorte"] = range(1, len(out) + 1)
    return out[["sk_recorte", "eixo", "valor_id", "valor_nome"]]


def _build_fato(
    df: pd.DataFrame,
    dim_tempo: pd.DataFrame,
    dim_territorio: pd.DataFrame,
    dim_indicador: pd.DataFrame,
    dim_recorte: pd.DataFrame,
) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    df = df.copy()
    if "periodo_codigo" in df.columns:
        df["periodo_codigo"] = df["periodo_codigo"].astype(str)
        df = df.merge(
            dim_tempo[["sk_tempo", "periodo_codigo"]], on="periodo_codigo", how="left"
        )
    else:
        df["sk_tempo"] = None
    if "territorio_codigo" in df.columns:
        df = df.merge(
            dim_territorio[["sk_territorio", "territorio_codigo"]],
            on="territorio_codigo",
            how="left",
        )
    else:
        df["sk_territorio"] = None
    if "variavel_id" in df.columns:
        df = df.merge(
            dim_indicador[["sk_indicador", "tabela", "variavel_id"]],
            on=["tabela", "variavel_id"],
            how="left",
        )
    else:
        df["sk_indicador"] = None

    # Coalesce de todas as classificações: para cada linha, usamos a 1ª
    # classificação que tem valor preenchido (cada tabela traz uma diferente
    # após o concat).
    pairs = _classif_columns(df)
    if pairs:
        df["_recorte_valor"] = None
        df["_recorte_eixo"] = None
        for id_col, nome_col in pairs:
            key_col = id_col if id_col else nome_col
            base_col = id_col or nome_col
            eixo = re.sub(r"^classif\d+_", "", base_col)
            eixo = re.sub(r"_(id|nome)$", "", eixo)
            mask = df["_recorte_valor"].isna() & df[key_col].notna()
            df.loc[mask, "_recorte_valor"] = df.loc[mask, key_col]
            df.loc[mask, "_recorte_eixo"] = eixo
        df["_recorte_eixo"] = df["_recorte_eixo"].fillna("total")
        df["_recorte_valor"] = df["_recorte_valor"].where(
            df["_recorte_valor"].notna(), other=None
        )
        df = df.merge(
            dim_recorte,
            left_on=["_recorte_eixo", "_recorte_valor"],
            right_on=["eixo", "valor_id"],
            how="left",
        )
    else:
        total_sk = dim_recorte.loc[dim_recorte["eixo"] == "total", "sk_recorte"]
        df["sk_recorte"] = int(total_sk.iloc[0]) if len(total_sk) else None

    cols = [c for c in [
        "sk_tempo", "sk_territorio", "sk_indicador", "sk_recorte",
        "tabela", "valor", "valor_raw", "unidade_medida_nome",
    ] if c in df.columns]
    return df[cols].copy()


def _is_diarista_row(row: pd.Series, catalogo: Catalogo) -> bool:
    if int(row.get("tabela", 0)) == 6383:
        return True
    info = catalogo.tabelas.get(int(row.get("tabela", 0)), {})
    if "diaristas" in (info.get("blocos_tematicos") or []):
        return True
    for col in row.index:
        if col.startswith("classif") and col.endswith("_nome"):
            val = row.get(col)
            if isinstance(val, str) and any(p.search(val) for p in DIARISTA_PATTERNS):
                return True
    return False


def _build_fato_diaristas(
    raw_staging: pd.DataFrame, fato: pd.DataFrame, catalogo: Catalogo
) -> pd.DataFrame:
    if raw_staging.empty or fato.empty:
        return pd.DataFrame()
    raw = raw_staging.copy()
    raw["is_diarista"] = raw.apply(lambda r: _is_diarista_row(r, catalogo), axis=1)
    # Mantém apenas linhas do fato cuja tabela contém ao menos uma linha
    # "diarista" no staging (filtragem mais simples e robusta que tentar
    # propagar flags célula a célula através do agregado).
    mask = fato["tabela"].isin(
        raw.loc[raw["is_diarista"], "tabela"].unique().tolist()
    )
    return fato.loc[mask].copy()


def _save(df: pd.DataFrame, name: str) -> tuple[Path, Path]:
    MARTS_DIR.mkdir(parents=True, exist_ok=True)
    pq = MARTS_DIR / f"{name}.parquet"
    csv = MARTS_DIR / f"{name}.csv"
    try:
        df.to_parquet(pq, index=False)
    except Exception as exc:  # pragma: no cover
        LOGGER.warning("Parquet falhou para %s (%s); só CSV", name, exc)
        pq = pq.with_suffix(".SKIPPED")
    df.to_csv(csv, index=False, encoding="utf-8")
    return pq, csv


def build() -> dict[str, pd.DataFrame]:
    catalogo = Catalogo.load()
    staging = _read_staging()
    if staging.empty:
        LOGGER.error("data/staging está vazio — rode pipeline.etl antes")
        return {}

    dim_tempo = _build_dim_tempo(staging)
    dim_territorio = _build_dim_territorio(staging)
    dim_indicador = _build_dim_indicador(staging, catalogo)
    dim_recorte = _build_dim_recorte(staging)
    fato = _build_fato(staging, dim_tempo, dim_territorio, dim_indicador, dim_recorte)
    fato_diaristas = _build_fato_diaristas(staging, fato, catalogo)

    artifacts = {
        "dim_tempo": dim_tempo,
        "dim_territorio": dim_territorio,
        "dim_indicador": dim_indicador,
        "dim_recorte": dim_recorte,
        "fato_mercado_trabalho": fato,
        "fato_diaristas": fato_diaristas,
    }
    for name, frame in artifacts.items():
        pq, csv = _save(frame, name)
        LOGGER.info("Mart %s: %d linhas (%s)", name, len(frame), csv.name)
    return artifacts


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    parser = argparse.ArgumentParser(description="Constrói o modelo dimensional PED-like")
    parser.parse_args()
    build()


if __name__ == "__main__":
    main()
