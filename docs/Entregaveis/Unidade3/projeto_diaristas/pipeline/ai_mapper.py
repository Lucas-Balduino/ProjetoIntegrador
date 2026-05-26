"""Mapeador "AI" que traduz descritores SIDRA em specs ETL temáticos.

Consome o JSON de `/DescritoresTabela/t/{T}` e, com auxílio de heurísticas
de palavras-chave do tema (diaristas / informalidade / trabalho doméstico),
gera um arquivo `specs/t{T}.yaml` com:

- variáveis úteis (priorizando %, taxa, rendimento, horas)
- classificações com categorias relevantes (`Trabalhador doméstico`,
  `Sem carteira`, `Informal`, etc.)
- query de exemplo já pronta para o ETL consumir

A heurística é determinística (offline); um LLM externo pode ser plugado
via `--llm` (por padrão desligado para não exigir chave de API).
"""

from __future__ import annotations

import argparse
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from pipeline.utils_sidra import fetch_descriptor


LOGGER = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parent.parent
SPECS_DIR = ROOT_DIR / "specs"
CATALOGO_PATH = ROOT_DIR / "pipeline" / "catalogo.yaml"

PRIORITY_CATEGORY_PATTERNS = [
    r"trabalhador.*dom[eé]stic",
    r"diarist",
    r"sem carteira",
    r"com carteira",
    r"informal",
    r"formal",
    r"servi[çc]os dom[eé]sticos",
    r"empreg[ao]\b",
    r"cuidad",
    r"conta pr[oó]pria",
    r"contribu",
]

PRIORITY_VARIABLE_PATTERNS = [
    r"taxa de",
    r"percentual",
    r"rendimento",
    r"hora",
    r"pessoas",
]


@dataclass
class CategoriaSpec:
    id: str
    nome: str
    prioridade: bool = False


@dataclass
class ClassificacaoSpec:
    id: str
    nome: str
    categorias: list[CategoriaSpec]


@dataclass
class VariavelSpec:
    id: str
    nome: str
    unidade: str
    prioridade: bool = False


def _matches_any(text: str, patterns: list[str]) -> bool:
    lower = text.lower()
    return any(re.search(p, lower) for p in patterns)


def _norm_id(raw: Any) -> str:
    """Normaliza o identificador (categoria/classificação/variável) para string."""
    if isinstance(raw, dict):
        for key in ("id", "Id", "ID", "Codigo", "codigo"):
            if key in raw:
                return str(raw[key])
    return str(raw)


def _extract_variables(descritor: dict) -> list[VariavelSpec]:
    raw = descritor.get("Variaveis") or descritor.get("variaveis") or []
    out: list[VariavelSpec] = []
    for v in raw:
        vid = str(v.get("Id") or v.get("id") or v.get("Codigo") or "")
        nome = v.get("Nome") or v.get("nome") or ""
        unidade = v.get("Unidade") or v.get("unidade") or ""
        if not vid:
            continue
        prio = _matches_any(nome, PRIORITY_VARIABLE_PATTERNS)
        out.append(VariavelSpec(id=vid, nome=nome, unidade=unidade, prioridade=prio))
    return out


def _extract_classifications(descritor: dict) -> list[ClassificacaoSpec]:
    raw = descritor.get("Classificacoes") or descritor.get("classificacoes") or []
    out: list[ClassificacaoSpec] = []
    for c in raw:
        cid = str(c.get("Id") or c.get("id") or c.get("Codigo") or "")
        nome = c.get("Nome") or c.get("nome") or ""
        if not cid:
            continue
        categorias_raw = c.get("Categorias") or c.get("categorias") or []
        cats: list[CategoriaSpec] = []
        for cat in categorias_raw:
            cat_id = str(cat.get("Id") or cat.get("id") or cat.get("Codigo") or "")
            cat_nome = cat.get("Nome") or cat.get("nome") or ""
            if not cat_id:
                continue
            prio = _matches_any(cat_nome, PRIORITY_CATEGORY_PATTERNS)
            cats.append(CategoriaSpec(id=cat_id, nome=cat_nome, prioridade=prio))
        out.append(ClassificacaoSpec(id=cid, nome=nome, categorias=cats))
    return out


def _build_example_query(
    tabela: int,
    variaveis: list[VariavelSpec],
    classificacoes: list[ClassificacaoSpec],
) -> dict[str, Any]:
    """Monta um exemplo de query priorizando variáveis e categorias relevantes."""
    variaveis_alvo = [v.id for v in variaveis if v.prioridade]
    if not variaveis_alvo:
        variaveis_alvo = ["allxp"]
    cls: dict[str, str] = {}
    for c in classificacoes:
        cats_prio = [cat.id for cat in c.categorias if cat.prioridade]
        if cats_prio:
            cls[f"c{c.id}"] = ",".join(cats_prio)
        else:
            cls[f"c{c.id}"] = "all"
    return {
        "tabela": tabela,
        "nivel": "BR",
        "periodos": "last 8",
        "variaveis": ",".join(variaveis_alvo),
        "classificacoes": cls,
    }


def build_spec(tabela: int, *, use_cache: bool = True) -> dict[str, Any]:
    LOGGER.info("Lendo descritor da tabela %s", tabela)
    descritor = fetch_descriptor(tabela, use_cache=use_cache)
    nome = descritor.get("Nome") or descritor.get("nome") or ""

    variaveis = _extract_variables(descritor)
    classifs = _extract_classifications(descritor)
    exemplo = _build_example_query(tabela, variaveis, classifs)

    spec = {
        "tabela": tabela,
        "nome": nome,
        "fonte": f"https://apisidra.ibge.gov.br/DescritoresTabela/t/{tabela}",
        "variaveis": [
            {"id": v.id, "nome": v.nome, "unidade": v.unidade, "prioridade": v.prioridade}
            for v in variaveis
        ],
        "classificacoes": [
            {
                "id": c.id,
                "nome": c.nome,
                "categorias_prioritarias": [
                    {"id": cat.id, "nome": cat.nome}
                    for cat in c.categorias
                    if cat.prioridade
                ],
                "total_categorias": len(c.categorias),
            }
            for c in classifs
        ],
        "exemplo_query": exemplo,
        "observacoes": _heuristic_notes(nome, variaveis, classifs),
    }
    return spec


def _heuristic_notes(
    nome: str, variaveis: list[VariavelSpec], classifs: list[ClassificacaoSpec]
) -> list[str]:
    notas: list[str] = []
    lower = nome.lower()
    if "trabalhador" in lower and "domést" in lower:
        notas.append("Tabela diretamente relacionada ao tema diaristas.")
    if any(_matches_any(v.nome, [r"taxa"]) for v in variaveis):
        notas.append("Contém variáveis de taxa — usar diretamente como indicador.")
    if any(c.nome and "informal" in c.nome.lower() for c in classifs):
        notas.append("Classificação de informalidade presente — preservar no ETL.")
    if any(c.nome and "carteira" in c.nome.lower() for c in classifs):
        notas.append("Distinção com/sem carteira disponível — manter categorias.")
    if not notas:
        notas.append("Sem heurísticas específicas — revisar manualmente.")
    return notas


def save_spec(spec: dict[str, Any]) -> Path:
    SPECS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = SPECS_DIR / f"t{spec['tabela']}.yaml"
    out_path.write_text(
        yaml.safe_dump(spec, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    return out_path


def _load_target_tables(only_priority: str | None = None) -> list[int]:
    if not CATALOGO_PATH.exists():
        raise FileNotFoundError(
            f"Catálogo não encontrado: {CATALOGO_PATH}. Rode pipeline.descoberta antes."
        )
    catalogo = yaml.safe_load(CATALOGO_PATH.read_text(encoding="utf-8")) or {}
    tabelas = catalogo.get("tabelas", [])
    if only_priority:
        tabelas = [t for t in tabelas if t.get("prioridade") == only_priority]
    return [int(t["numero"]) for t in tabelas]


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    parser = argparse.ArgumentParser(description="Gera specs ETL a partir dos descritores SIDRA")
    parser.add_argument("--tabela", type=int, help="Número da tabela SIDRA")
    parser.add_argument("--all", action="store_true", help="Roda para todas as tabelas do catálogo")
    parser.add_argument(
        "--prioridade",
        choices=["alta", "media", "baixa"],
        help="Filtra apenas tabelas com a prioridade indicada (combina com --all)",
    )
    parser.add_argument("--no-cache", action="store_true", help="Ignora cache do descritor")
    args = parser.parse_args()

    if not args.tabela and not args.all:
        parser.error("Informe --tabela <N> ou --all")

    if args.all:
        tabelas = _load_target_tables(only_priority=args.prioridade)
    else:
        tabelas = [args.tabela]

    LOGGER.info("Mapeando %d tabela(s)", len(tabelas))
    for t in tabelas:
        try:
            spec = build_spec(t, use_cache=not args.no_cache)
            out = save_spec(spec)
            LOGGER.info("Spec %s -> %s", t, out)
        except Exception as exc:  # pragma: no cover - relata e segue
            LOGGER.error("Falha na tabela %s: %s", t, exc)


if __name__ == "__main__":
    main()
