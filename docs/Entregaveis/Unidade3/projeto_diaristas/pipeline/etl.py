"""ETL principal: consome a API SIDRA e normaliza para long format em data/staging.

Saídas (por tabela):
- data/raw/t{T}_{nivel}_{hash}.json   (bruto)
- data/staging/t{T}.parquet           (long format)
- data/staging/t{T}.csv               (mesma coisa, para inspeção rápida)

Cada linha do long format representa uma célula da tabela SIDRA:
  tabela, variavel_id, variavel_nome, unidade,
  periodo, territorio_nivel, territorio_codigo, territorio_nome,
  classif_*_id, classif_*_nome, valor, cv (quando existir)
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Any, Iterable

import pandas as pd
import yaml

from pipeline.parquet_io import save_dataframe
from pipeline.utils_sidra import (
    NIVEIS,
    SidraQuery,
    fetch_values,
    polite_sleep,
)

try:
    from pipeline.etl_formularios import run as run_formularios
except ImportError:  # pragma: no cover
    run_formularios = None


LOGGER = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parent.parent
CATALOGO_PATH = ROOT_DIR / "pipeline" / "catalogo.yaml"
SPECS_DIR = ROOT_DIR / "specs"
STAGING_DIR = ROOT_DIR / "data" / "staging"


def _load_catalogo() -> dict:
    if not CATALOGO_PATH.exists():
        raise FileNotFoundError(f"Catálogo não encontrado em {CATALOGO_PATH}")
    return yaml.safe_load(CATALOGO_PATH.read_text(encoding="utf-8")) or {}


def _load_spec(tabela: int) -> dict | None:
    p = SPECS_DIR / f"t{tabela}.yaml"
    if not p.exists():
        return None
    return yaml.safe_load(p.read_text(encoding="utf-8"))


def _semantic_role(label: str) -> str:
    """Classifica uma coluna da SIDRA em um papel semântico padronizado."""
    if not label:
        return "outro"
    low = label.lower()
    if "variável" in low or "variavel" in low:
        return "variavel"
    if (
        "trimestre" in low
        or "ano" in low
        or "mês" in low
        or "mes" in low
        or "período" in low
        or "periodo" in low
    ):
        return "periodo"
    if (
        "brasil" in low
        or "federação" in low
        or "federacao" in low
        or "região" in low
        or "regiao" in low
        or "município" in low
        or "municipio" in low
        or "territorial" in low
        or "metropolitana" in low
    ):
        return "territorio"
    return "classif:" + label


def _dimension_pairs(header: dict[str, Any]) -> list[tuple[str | None, str, str]]:
    """Lista (cod_key, nome_key, papel) para cada dimensão D{i} do header.

    O SIDRA nem sempre retorna o par C/N: território vem com D1C+D1N,
    mas as demais dimensões (variável, período, classificações) frequentemente
    vêm apenas como D{i}N. Aceitamos `cod_key=None` nesses casos.
    """
    indices: dict[str, dict[str, str]] = {}
    for key, label in header.items():
        if not (key.startswith("D") and key[1:-1].isdigit()):
            continue
        idx, suffix = key[1:-1], key[-1]
        if suffix not in ("C", "N"):
            continue
        indices.setdefault(idx, {})[suffix] = label

    pairs: list[tuple[str | None, str, str]] = []
    for idx in sorted(indices, key=int):
        slot = indices[idx]
        if "N" not in slot:
            continue
        name_key = f"D{idx}N"
        cod_key = f"D{idx}C" if "C" in slot else None
        label = slot.get("N", "") or slot.get("C", "")
        role = _semantic_role(label)
        pairs.append((cod_key, name_key, role))
    return pairs


def normalize_payload(raw: list[dict[str, Any]], tabela: int) -> pd.DataFrame:
    """Converte o JSON bruto da SIDRA em DataFrame long-format pandas.

    A primeira linha do payload SIDRA traz a descrição das colunas (header),
    indicando o que cada `D{i}C/D{i}N` representa (variável, território,
    período ou classificação). Usamos isso para mapear os campos
    para nomes semânticos estáveis.
    """
    if not raw:
        return pd.DataFrame()

    header, data_rows = raw[0], raw[1:]
    pairs = _dimension_pairs(header)

    def _slugify(text: str) -> str:
        s = (
            text.lower()
            .replace(" ", "_")
            .replace("á", "a")
            .replace("ã", "a")
            .replace("â", "a")
            .replace("à", "a")
            .replace("ç", "c")
            .replace("é", "e")
            .replace("ê", "e")
            .replace("í", "i")
            .replace("ó", "o")
            .replace("ô", "o")
            .replace("õ", "o")
            .replace("ú", "u")
            .replace("/", "_")
            .replace("(", "")
            .replace(")", "")
        )
        s = "".join(ch for ch in s if ch.isalnum() or ch == "_")
        return s[:40] or "x"

    classif_counter = 0
    column_map: dict[str, str] = {}
    for code_key, name_key, role in pairs:
        if role == "variavel":
            if code_key:
                column_map[code_key] = "variavel_id"
            column_map[name_key] = "variavel_nome"
        elif role == "periodo":
            if code_key:
                column_map[code_key] = "periodo_codigo"
            column_map[name_key] = "periodo_nome"
        elif role == "territorio":
            if code_key:
                column_map[code_key] = "territorio_codigo"
            column_map[name_key] = "territorio_nome"
        else:
            classif_counter += 1
            slug = _slugify(role.split(":", 1)[1] if ":" in role else role)
            if code_key:
                column_map[code_key] = f"classif{classif_counter}_{slug}_id"
            column_map[name_key] = f"classif{classif_counter}_{slug}_nome"

    records: list[dict[str, Any]] = []
    for row in data_rows:
        rec: dict[str, Any] = {
            "tabela": tabela,
            "nivel_territorial_codigo": row.get("NC"),
            "nivel_territorial_nome": row.get("NN"),
            "unidade_medida_codigo": row.get("MC"),
            "unidade_medida_nome": row.get("MN"),
            "valor_raw": row.get("V"),
            "valor": _to_float(row.get("V")),
        }
        for source_key, target_key in column_map.items():
            rec[target_key] = row.get(source_key)
        records.append(rec)

    df = pd.DataFrame.from_records(records)
    if df.empty:
        return df

    # Garante chaves estáveis mesmo quando o SIDRA só devolve o nome (sem o
    # código): fallback para o próprio nome.
    for code_col, name_col in (
        ("periodo_codigo", "periodo_nome"),
        ("variavel_id", "variavel_nome"),
        ("territorio_codigo", "territorio_nome"),
    ):
        if code_col not in df.columns:
            df[code_col] = df[name_col] if name_col in df.columns else None
        else:
            df[code_col] = df[code_col].where(df[code_col].notna(), df.get(name_col))
    return df


def _to_float(val: Any) -> float | None:
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip()
    if s in {"", "-", "..", "...", "X"}:
        return None
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def _build_query_from_spec(
    tabela: int,
    spec: dict | None,
    nivel: str,
    periodos: str | None,
) -> SidraQuery:
    """Monta a SidraQuery a partir do spec (se houver) com overrides simples."""
    if spec and "exemplo_query" in spec:
        eq = spec["exemplo_query"]
        return SidraQuery(
            tabela=tabela,
            nivel=nivel or eq.get("nivel", "BR"),
            periodos=periodos or eq.get("periodos", "all"),
            variaveis=eq.get("variaveis", "allxp"),
            classificacoes={
                k.lstrip("c"): v for k, v in eq.get("classificacoes", {}).items()
            },
        )
    return SidraQuery(tabela=tabela, nivel=nivel, periodos=periodos or "all")


def extract_table(
    tabela: int,
    *,
    nivel: str = "BR",
    periodos: str | None = None,
    use_cache: bool = True,
) -> pd.DataFrame:
    spec = _load_spec(tabela)
    query = _build_query_from_spec(tabela, spec, nivel=nivel, periodos=periodos)
    LOGGER.info("ETL tabela %s | %s", tabela, query.to_url())
    raw = fetch_values(query, use_cache=use_cache)
    df = normalize_payload(raw, tabela=tabela)
    LOGGER.info("Tabela %s normalizada: %d linhas", tabela, len(df))
    return df


def save_staging(df: pd.DataFrame, tabela: int) -> tuple[Path, Path]:
    STAGING_DIR.mkdir(parents=True, exist_ok=True)
    pq_path = STAGING_DIR / f"t{tabela}.parquet"
    csv_path = STAGING_DIR / f"t{tabela}.csv"
    _, pq_out = save_dataframe(df, csv_path, pq_path, stem=f"t{tabela}")
    return pq_out or pq_path.with_suffix(".SKIPPED"), csv_path


def _iter_target_tables(
    only_priority: str | None = None, restrict: list[int] | None = None
) -> Iterable[dict]:
    catalogo = _load_catalogo()
    for t in catalogo.get("tabelas", []):
        if only_priority and t.get("prioridade") != only_priority:
            continue
        if restrict and int(t["numero"]) not in restrict:
            continue
        yield t


def run(
    targets: list[int] | None = None,
    *,
    nivel: str = "BR",
    periodos: str | None = None,
    only_priority: str | None = None,
    use_cache: bool = True,
) -> list[Path]:
    """Roda o ETL para uma lista de tabelas (ou todas do catálogo)."""
    written: list[Path] = []
    target_rows = list(
        _iter_target_tables(only_priority=only_priority, restrict=targets)
    )
    if not target_rows:
        if targets:
            target_rows = [{"numero": t, "nome": f"(fora do catalogo) t{t}"} for t in targets]
        else:
            LOGGER.warning("Nenhuma tabela alvo encontrada para os critérios")
            return written

    for row in target_rows:
        tabela = int(row["numero"])
        try:
            df = extract_table(tabela, nivel=nivel, periodos=periodos, use_cache=use_cache)
            if df.empty:
                LOGGER.warning("Tabela %s veio vazia, pulando", tabela)
                continue
            pq, csv = save_staging(df, tabela)
            LOGGER.info("Tabela %s gravada: %s / %s", tabela, pq.name, csv.name)
            written.append(pq)
            polite_sleep()
        except Exception as exc:  # pragma: no cover - log e segue
            LOGGER.error("Falha na tabela %s: %s", tabela, exc)
    return written


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    parser = argparse.ArgumentParser(description="ETL SIDRA → data/staging")
    parser.add_argument(
        "--target", type=int, action="append", help="Número da tabela (pode repetir)"
    )
    parser.add_argument("--all", action="store_true", help="Roda todas as tabelas do catálogo")
    parser.add_argument(
        "--prioridade",
        choices=["alta", "media", "baixa"],
        help="Filtra por prioridade (com --all)",
    )
    parser.add_argument(
        "--nivel",
        default="BR",
        choices=list(NIVEIS.keys()),
        help="Nível territorial (default BR)",
    )
    parser.add_argument(
        "--periodos",
        default=None,
        help="Períodos SIDRA (ex.: 'last 8', '202101-202104'). Default: do spec ou 'all'",
    )
    parser.add_argument("--no-cache", action="store_true")
    parser.add_argument(
        "--formularios",
        action="store_true",
        help="Processa pesquisa-contratante.xlsx e pesquisa-diaristas.xlsx",
    )
    parser.add_argument(
        "--somente-formularios",
        action="store_true",
        help="Roda apenas o ETL dos formulários (sem SIDRA)",
    )
    args = parser.parse_args()

    if not args.somente_formularios and not args.target and not args.all:
        if not args.formularios:
            parser.error(
                "Informe --target <N>, --all, --formularios ou --somente-formularios"
            )

    written: list[Path] = []
    if not args.somente_formularios and (args.target or args.all):
        written = run(
            targets=args.target,
            nivel=args.nivel,
            periodos=args.periodos,
            only_priority=args.prioridade if args.all else None,
            use_cache=not args.no_cache,
        )
        LOGGER.info("SIDRA: %d arquivo(s) em data/staging", len(written))

    if args.formularios or args.somente_formularios:
        if run_formularios is None:
            raise ImportError("pipeline.etl_formularios não disponível")
        run_formularios()
        LOGGER.info("Formulários gravados em data/staging (pesquisa_*)")

    LOGGER.info("ETL finalizado.")


if __name__ == "__main__":
    sys.exit(main())
