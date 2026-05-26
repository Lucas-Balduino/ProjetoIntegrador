"""Cliente HTTP utilitário para a API SIDRA do IBGE.

Centraliza a montagem de URLs, o cache local em disco e o retry/backoff.
Documentação da API: https://apisidra.ibge.gov.br/home/ajuda

Formato canônico das URLs:
- Valores:    https://apisidra.ibge.gov.br/values/t/{T}/n{N}/{nivel}/p/{P}/v/{V}/c{Ci}/{cats}/f/u
- Descritor:  https://apisidra.ibge.gov.br/DescritoresTabela/t/{T}
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

import requests
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)


LOGGER = logging.getLogger(__name__)

BASE_URL = "https://apisidra.ibge.gov.br"
VALUES_PATH = "/values"
DESCRIPTORS_PATH = "/DescritoresTabela/t"

ROOT_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT_DIR / "data" / "raw"
DESCRIPTORS_DIR = RAW_DIR / "descritores"

NIVEIS = {
    "BR": "1",
    "GR": "2",
    "UF": "3",
    "MU": "6",
    "RM": "7",
    "RD": "8",
}


@dataclass
class SidraQuery:
    """Parâmetros de uma consulta de valores na API SIDRA."""

    tabela: int
    nivel: str = "BR"
    unidades: str = "all"
    periodos: str = "all"
    variaveis: str = "allxp"
    classificacoes: dict[str, str] = field(default_factory=dict)
    formato: str = "u"

    def to_path(self) -> str:
        nivel_codigo = NIVEIS.get(self.nivel.upper(), self.nivel)
        parts: list[str] = [
            f"t/{self.tabela}",
            f"n{nivel_codigo}/{self.unidades}",
            f"p/{self.periodos}",
            f"v/{self.variaveis}",
        ]
        for cid, cats in sorted(self.classificacoes.items()):
            cid_norm = cid.lower().lstrip("c")
            parts.append(f"c{cid_norm}/{cats}")
        parts.append(f"f/{self.formato}")
        return "/".join(parts)

    def to_url(self) -> str:
        return f"{BASE_URL}{VALUES_PATH}/{self.to_path()}"

    def cache_key(self) -> str:
        h = hashlib.sha1(self.to_path().encode("utf-8")).hexdigest()[:12]
        return f"t{self.tabela}_{self.nivel.lower()}_{h}.json"


def _ensure_dirs() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    DESCRIPTORS_DIR.mkdir(parents=True, exist_ok=True)


@retry(
    retry=retry_if_exception_type((requests.RequestException, json.JSONDecodeError)),
    wait=wait_exponential(multiplier=2, min=2, max=30),
    stop=stop_after_attempt(4),
    reraise=True,
)
def _http_get_json(url: str, timeout: int = 60) -> Any:
    LOGGER.info("GET %s", url)
    response = requests.get(
        url,
        timeout=timeout,
        headers={"Accept": "application/json", "User-Agent": "projeto-diaristas-PI1/0.1"},
    )
    response.raise_for_status()
    return response.json()


def fetch_values(query: SidraQuery, *, use_cache: bool = True) -> list[dict[str, Any]]:
    """Retorna o payload de /values, usando cache em disco quando disponível."""
    _ensure_dirs()
    cache_path = RAW_DIR / query.cache_key()
    if use_cache and cache_path.exists():
        try:
            return json.loads(cache_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            LOGGER.warning("Cache corrompido em %s, refazendo download", cache_path)

    payload = _http_get_json(query.to_url())
    cache_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return payload


def fetch_descriptor(tabela: int, *, use_cache: bool = True) -> dict[str, Any]:
    """Retorna o JSON do descritor de uma tabela SIDRA."""
    _ensure_dirs()
    cache_path = DESCRIPTORS_DIR / f"t{tabela}.json"
    if use_cache and cache_path.exists():
        try:
            return json.loads(cache_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            LOGGER.warning("Descritor cacheado corrompido em %s, refazendo", cache_path)

    url = f"{BASE_URL}{DESCRIPTORS_PATH}/{tabela}"
    payload = _http_get_json(url)
    cache_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return payload


def iter_paged_periodos(periodos: Iterable[str], chunk: int = 12) -> Iterable[str]:
    """Quebra uma lista de períodos em pedaços para evitar estourar o limite SIDRA."""
    buffer: list[str] = []
    for p in periodos:
        buffer.append(p)
        if len(buffer) == chunk:
            yield ",".join(buffer)
            buffer = []
    if buffer:
        yield ",".join(buffer)


def polite_sleep(seconds: float = 0.5) -> None:
    """Pequena pausa entre requisições para respeitar a API."""
    time.sleep(seconds)


__all__ = [
    "SidraQuery",
    "NIVEIS",
    "fetch_values",
    "fetch_descriptor",
    "iter_paged_periodos",
    "polite_sleep",
]
