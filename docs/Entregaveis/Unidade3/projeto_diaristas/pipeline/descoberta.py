"""Descoberta de tabelas SIDRA relevantes para o tema "diaristas / informalidade".

Estratégia:
1. Fazer scraping HTML das listagens da PNAD Contínua (Trimestral e Mensal),
   coletando: número, nome, período, territórios.
2. Aplicar palavras-chave para classificar cada tabela em blocos temáticos
   (diaristas / informalidade / mercado geral / recortes / rendimento / horas).
3. Mesclar com o catálogo curado em `pipeline/catalogo.yaml`, preservando a
   marcação manual de prioridade quando ela já existir.

Saída: atualiza/cria `pipeline/catalogo.yaml`.
"""

from __future__ import annotations

import argparse
import logging
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable

import requests
import yaml
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential


LOGGER = logging.getLogger(__name__)

PNADCT_URL = "https://sidra.ibge.gov.br/pesquisa/pnadct/tabelas"
PNADCM_URL = "https://sidra.ibge.gov.br/pesquisa/pnadcm"

ROOT_DIR = Path(__file__).resolve().parent.parent
CATALOGO_PATH = ROOT_DIR / "pipeline" / "catalogo.yaml"

KEYWORDS = {
    "diaristas": [
        r"trabalhador.*dom[eé]stic",
        r"servi[çc]os dom[eé]sticos",
        r"n[uú]mero de domic[ií]lios em que trabalhav",
        r"posi[çc][aã]o na ocupa[çc][aã]o.*categoria do emprego",
    ],
    "informalidade": [
        r"informalidade",
        r"sem carteira",
        r"contribui[çc][aã]o.*previd[eê]ncia",
        r"contribuinte.*previd[eê]ncia",
    ],
    "rendimento": [
        r"rendimento m[eé]dio",
        r"massa de rendimento",
    ],
    "horas": [
        r"horas habitualmente",
        r"horas.*efetivamente",
        r"suboc.*hora",
    ],
    "mercado_geral": [
        r"for[çc]a de trabalho",
        r"ocupa[çc][aã]o",
        r"desocupa",
        r"subutiliza",
        r"participa[çc][aã]o",
        r"desalent",
        r"pessoas de 14 anos",
    ],
    "recortes_equidade": [
        r"por sexo",
        r"por cor ou ra[çc]a",
        r"por grupo de idade",
        r"por n[ií]vel de instru[çc][aã]o",
    ],
}


@dataclass
class TabelaSidra:
    numero: int
    nome: str
    periodo: str
    territorios: str
    pesquisa: str  # PNADC/T ou PNADC/M
    blocos_tematicos: list[str]
    prioridade: str = "media"  # alta | media | baixa
    palavras_chave: list[str] | None = None


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=15),
    reraise=True,
)
def _fetch_html(url: str) -> str:
    LOGGER.info("GET %s", url)
    response = requests.get(
        url,
        timeout=60,
        headers={"User-Agent": "projeto-diaristas-PI1/0.1"},
    )
    response.raise_for_status()
    return response.text


def _classify(nome: str) -> list[str]:
    """Retorna a lista de blocos temáticos que casam com o nome da tabela."""
    blocos: list[str] = []
    lower = nome.lower()
    for bloco, patterns in KEYWORDS.items():
        if any(re.search(pat, lower) for pat in patterns):
            blocos.append(bloco)
    if not blocos:
        blocos.append("outros")
    return blocos


def _parse_tabelas(html: str, pesquisa: str) -> list[TabelaSidra]:
    """Extrai todas as linhas de tabela do HTML da listagem SIDRA."""
    soup = BeautifulSoup(html, "lxml")
    tabelas: list[TabelaSidra] = []
    seen: set[int] = set()

    # As listagens do SIDRA usam <table> com linhas no padrão:
    # | Número | Nome | Período | Território |
    for tr in soup.find_all("tr"):
        cells = [c.get_text(" ", strip=True) for c in tr.find_all(["td", "th"])]
        if len(cells) < 4:
            continue
        numero_raw = cells[0]
        if not numero_raw.isdigit():
            continue
        numero = int(numero_raw)
        if numero in seen:
            continue
        seen.add(numero)
        nome = cells[1]
        periodo = cells[2]
        territorios = cells[3]
        blocos = _classify(nome)
        tabelas.append(
            TabelaSidra(
                numero=numero,
                nome=nome,
                periodo=periodo,
                territorios=territorios,
                pesquisa=pesquisa,
                blocos_tematicos=blocos,
            )
        )
    return tabelas


def discover() -> list[TabelaSidra]:
    """Faz scraping das duas listagens (trimestral e mensal) e devolve a união."""
    tabelas: list[TabelaSidra] = []
    for url, pesquisa in [(PNADCT_URL, "PNADC/T"), (PNADCM_URL, "PNADC/M")]:
        try:
            html = _fetch_html(url)
            tabelas.extend(_parse_tabelas(html, pesquisa))
        except requests.RequestException as exc:
            LOGGER.error("Falha ao buscar %s: %s", url, exc)
    return tabelas


def _load_existing_catalog() -> dict:
    if not CATALOGO_PATH.exists():
        return {}
    return yaml.safe_load(CATALOGO_PATH.read_text(encoding="utf-8")) or {}


def _merge_with_curado(descobertas: Iterable[TabelaSidra], curado: dict) -> dict:
    """Combina descoberta automática + marcação manual do catálogo curado."""
    catalogo_existente = {t["numero"]: t for t in curado.get("tabelas", [])}
    out: list[dict] = []
    for desc in descobertas:
        registro = asdict(desc)
        existente = catalogo_existente.pop(desc.numero, None)
        if existente:
            # Preserva prioridade e palavras-chave curadas manualmente.
            registro["prioridade"] = existente.get("prioridade", desc.prioridade)
            if existente.get("palavras_chave"):
                registro["palavras_chave"] = existente["palavras_chave"]
            blocos_curados = existente.get("blocos_tematicos") or []
            registro["blocos_tematicos"] = sorted(
                set(registro["blocos_tematicos"]) | set(blocos_curados)
            )
        out.append(registro)
    # Mantém eventuais entradas curadas que não foram redescobertas (ex.: rede caiu).
    for restante in catalogo_existente.values():
        out.append(restante)
    out.sort(key=lambda r: r["numero"])
    return {
        "fonte": {
            "trimestral": PNADCT_URL,
            "mensal": PNADCM_URL,
            "api_descritor": "https://apisidra.ibge.gov.br/DescritoresTabela/t/{T}",
            "api_valores": "https://apisidra.ibge.gov.br/values/t/{T}/n{N}/all/p/{P}/v/{V}/c{Ci}/{cats}/f/u",
        },
        "blocos_tematicos": list(KEYWORDS.keys()) + ["outros"],
        "tabelas": out,
    }


def save_catalog(catalog: dict) -> Path:
    CATALOGO_PATH.parent.mkdir(parents=True, exist_ok=True)
    CATALOGO_PATH.write_text(
        yaml.safe_dump(catalog, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    return CATALOGO_PATH


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    parser = argparse.ArgumentParser(description="Descobre tabelas SIDRA relevantes")
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Não acessa a rede; apenas reescreve catalogo.yaml a partir do estado atual",
    )
    args = parser.parse_args()

    curado = _load_existing_catalog()
    if args.offline:
        catalog = curado or {"tabelas": []}
    else:
        descobertas = discover()
        if not descobertas:
            LOGGER.warning("Nenhuma tabela descoberta on-line; mantendo catálogo atual")
            catalog = curado or {"tabelas": []}
        else:
            catalog = _merge_with_curado(descobertas, curado)
    out_path = save_catalog(catalog)
    LOGGER.info("Catálogo salvo em %s (%d tabelas)", out_path, len(catalog.get("tabelas", [])))


if __name__ == "__main__":
    main()
