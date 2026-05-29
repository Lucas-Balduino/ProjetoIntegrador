"""ETL da pesquisa primária (Google Forms exportados em Excel).

Lê:
  ProjetoIntegrador/PesquisaFormularios/pesquisa-contratante.xlsx
  ProjetoIntegrador/PesquisaFormularios/pesquisa-diaristas.xlsx

Grava em data/staging/:
  pesquisa_contratante_wide.{csv,parquet}   — uma linha por respondente
  pesquisa_diaristas_wide.{csv,parquet}
  pesquisa_primaria_long.{csv,parquet}      — formato longo (dashboard)
  pesquisa_primaria_agregada.{csv,parquet}  — contagens por pergunta/resposta
"""

from __future__ import annotations

import argparse
import logging
import re
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from pipeline.parquet_io import save_dataframe


LOGGER = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT_DIR / "pipeline" / "formularios.yaml"
STAGING_DIR = ROOT_DIR / "data" / "staging"

QUESTION_NUM_RE = re.compile(r"^\s*(\d+)\.")
TIMESTAMP_COL = "carimbo de data/hora"

# Slugs estáveis por número da pergunta (contratante / diarista compartilham só onde faz sentido)
SLUGS_CONTRATANTE: dict[int, str] = {
    1: "faixa_etaria",
    2: "arranjo_moradia",
    3: "tamanho_residencia",
    4: "frequencia_contratacao",
    5: "canal_contratacao",
    6: "valor_diaria_pago",
    7: "maior_frustracao_aberta",
    8: "dificuldade_ultima_hora_1a5",
    9: "profissional_desmarcou",
    10: "fatores_contratacao_novo",
    11: "varinha_magica_aberta",
}

SLUGS_DIARISTA: dict[int, str] = {
    1: "faixa_etaria",
    2: "tempo_experiencia",
    3: "unica_fonte_renda",
    4: "canal_consegue_diarias",
    5: "dias_faxina_semana",
    6: "dias_livres_sem_cliente",
    7: "dificuldade_cliente_novo_aberta",
    8: "frequencia_desmarque_cliente",
    9: "consequencia_desmarque",
    10: "como_define_preco",
    11: "maior_medo_app",
    12: "confianca_cliente_desconhecido_aberta",
    13: "mei_ativo",
    14: "motivo_nao_mei",
}

BLOCO_MAP_CONTRATANTE: dict[int, str] = {
    **{i: "perfil" for i in range(1, 4)},
    **{i: "habitos" for i in range(4, 7)},
    **{i: "dores" for i in range(7, 10)},
    **{i: "decisao" for i in range(10, 12)},
}

BLOCO_MAP_DIARISTA: dict[int, str] = {
    **{i: "perfil" for i in range(1, 4)},
    **{i: "realidade_trabalho" for i in range(4, 7)},
    **{i: "dores" for i in range(7, 11)},
    **{i: "tecnologia" for i in range(11, 13)},
    **{i: "formalizacao" for i in range(13, 15)},
}


def _repo_root() -> Path:
    cfg = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {}
    rel = cfg.get("repo_root", "../../../../..")
    return (ROOT_DIR / rel).resolve()


def _resolve_path(rel_path: str) -> Path:
    return (_repo_root() / rel_path).resolve()


def _question_number(col: str) -> int | None:
    m = QUESTION_NUM_RE.match(col.strip())
    return int(m.group(1)) if m else None


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Renomeia colunas do Forms para slugs estáveis."""
    rename: dict[str, str] = {}
    for col in df.columns:
        low = col.strip().lower()
        if low == TIMESTAMP_COL or low.startswith("carimbo"):
            rename[col] = "carimbo"
            continue
        num = _question_number(col)
        if num is not None:
            rename[col] = f"q{num:02d}"
        else:
            slug = re.sub(r"[^a-z0-9]+", "_", low).strip("_")[:60]
            rename[col] = slug or col
    out = df.rename(columns=rename)
    if "carimbo" in out.columns:
        out["carimbo"] = pd.to_datetime(out["carimbo"], errors="coerce")
    for col in out.columns:
        if re.match(r"^q\d+$", col):
            out[col] = out[col].map(lambda x: pd.NA if pd.isna(x) else str(x)).astype("string")
    return out


def _slug_for(publico: str, qnum: int) -> str:
    if publico == "contratante":
        return SLUGS_CONTRATANTE.get(qnum, f"q{qnum:02d}")
    return SLUGS_DIARISTA.get(qnum, f"q{qnum:02d}")


def _bloco_for(publico: str, qnum: int) -> str:
    if publico == "contratante":
        return BLOCO_MAP_CONTRATANTE.get(qnum, "outros")
    return BLOCO_MAP_DIARISTA.get(qnum, "outros")


def _to_numeric(series: pd.Series) -> pd.Series:
    """Tenta extrair número (ex.: valor da diária, escala 1-5)."""
    s = series.astype(str).str.strip()
    s = s.replace({"nan": None, "None": None, "": None})
    extracted = s.str.extract(r"(\d+(?:[.,]\d+)?)", expand=False)
    return pd.to_numeric(extracted.str.replace(",", ".", regex=False), errors="coerce")


def load_wide(path: Path, publico: str) -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name=0)
    df = _normalize_columns(df)
    df.insert(0, "publico", publico)
    df.insert(0, "respondente_id", range(1, len(df) + 1))
    df["fonte_arquivo"] = path.name
    return df


def wide_to_long(wide: pd.DataFrame, publico: str) -> pd.DataFrame:
    """Converte respostas wide → long para gráficos do dashboard."""
    id_cols = ["respondente_id", "publico", "carimbo", "fonte_arquivo"]
    id_cols = [c for c in id_cols if c in wide.columns]
    q_cols = [c for c in wide.columns if re.match(r"^q\d+$", c)]
    if not q_cols:
        return pd.DataFrame()

    long = wide.melt(
        id_vars=id_cols,
        value_vars=q_cols,
        var_name="pergunta_col",
        value_name="valor_texto",
    )
    long["pergunta_num"] = long["pergunta_col"].str.extract(r"q(\d+)").astype(int)
    long["pergunta_slug"] = long["pergunta_num"].apply(lambda n: _slug_for(publico, int(n)))
    long["bloco"] = long["pergunta_num"].apply(lambda n: _bloco_for(publico, int(n)))
    long["valor_texto"] = long["valor_texto"].map(
        lambda x: pd.NA if pd.isna(x) else str(x)
    ).astype("string")
    long["valor_numerico"] = _to_numeric(long["valor_texto"])
    long["fonte"] = "pesquisa_primaria"
    return long


def aggregate_responses(long: pd.DataFrame) -> pd.DataFrame:
    """Contagens e percentuais por público / pergunta / resposta."""
    if long.empty:
        return pd.DataFrame()
    grp = (
        long.groupby(["publico", "bloco", "pergunta_slug", "pergunta_num", "valor_texto"], dropna=False)
        .size()
        .reset_index(name="contagem")
    )
    totals = grp.groupby(["publico", "pergunta_slug"])["contagem"].transform("sum")
    grp["percentual"] = (grp["contagem"] / totals * 100).round(2)
    grp["fonte"] = "pesquisa_primaria"
    return grp.sort_values(["publico", "pergunta_num", "contagem"], ascending=[True, True, False])


def _save(df: pd.DataFrame, stem: str) -> tuple[Path, Path]:
    STAGING_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = STAGING_DIR / f"{stem}.csv"
    pq_path = STAGING_DIR / f"{stem}.parquet"
    _, pq_out = save_dataframe(df, csv_path, pq_path, stem=stem)
    return csv_path, pq_out or pq_path.with_suffix(".SKIPPED")


def run(
    *,
    contratante_path: Path | None = None,
    diaristas_path: Path | None = None,
) -> dict[str, pd.DataFrame]:
    cfg = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {}
    fontes = cfg.get("fontes", {})

    c_path = contratante_path or _resolve_path(fontes["contratante"]["arquivo"])
    d_path = diaristas_path or _resolve_path(fontes["diaristas"]["arquivo"])

    if not c_path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {c_path}")
    if not d_path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {d_path}")

    wide_c = load_wide(c_path, "contratante")
    wide_d = load_wide(d_path, "diarista")

    _save(wide_c, "pesquisa_contratante_wide")
    _save(wide_d, "pesquisa_diaristas_wide")
    LOGGER.info("Contratantes: %d respostas", len(wide_c))
    LOGGER.info("Diaristas: %d respostas", len(wide_d))

    long_c = wide_to_long(wide_c, "contratante")
    long_d = wide_to_long(wide_d, "diarista")
    long_all = pd.concat([long_c, long_d], ignore_index=True)
    _save(long_all, "pesquisa_primaria_long")

    agregada = aggregate_responses(long_all)
    _save(agregada, "pesquisa_primaria_agregada")

    return {
        "contratante_wide": wide_c,
        "diaristas_wide": wide_d,
        "long": long_all,
        "agregada": agregada,
    }


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    parser = argparse.ArgumentParser(description="ETL pesquisa primária (Excel Forms)")
    parser.add_argument(
        "--contratante",
        type=Path,
        default=None,
        help="Caminho alternativo para pesquisa-contratante.xlsx",
    )
    parser.add_argument(
        "--diaristas",
        type=Path,
        default=None,
        help="Caminho alternativo para pesquisa-diaristas.xlsx",
    )
    args = parser.parse_args()
    run(contratante_path=args.contratante, diaristas_path=args.diaristas)
    LOGGER.info("Formulários processados em %s", STAGING_DIR)


if __name__ == "__main__":
    main()
