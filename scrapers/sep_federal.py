from __future__ import annotations

import asyncio
import httpx

from scrapers.base_scraper import BaseScraper
from utils.normalizer import es_medicina, limpiar_texto
from utils.logger import log

BASE_URL = "http://search.sep.gob.mx/solr/cedulasCore/select"

MEDICINA_QUERIES = [
    "médico",
    "medico",
    "cirujano",
    "medicina general",
    "ginecolog",
    "pediatr",
    "cardiol",
    "neurolog",
    "psiquiat",
    "urgencias médicas",
    "medicina familiar",
    "dermatol",
    "oftalmol",
    "urolog",
    "oncolog",
    "ortoped",
    "anestesiol",
    "gastroenterol",
    "neumol",
    "endocrinol",
    "reumatol",
    "infectolog",
    "radiolog",
    "patolog",
    "traumatol",
    "nefrol",
    "hepatol",
    "hematolg",
    "medicina interna",
]

FIELDS = "idCedula,nombre,paterno,materno,titulo,institucion,anioRegistro"
MAX_RETRIES = 3
ROWS_PER_PAGE = 1000


class SepFederalScraper(BaseScraper):
    nombre = "SEP Federal"

    async def scrape_all(self) -> list[dict]:
        seen_ids: set[str] = set()
        all_records: list[dict] = []

        for query in MEDICINA_QUERIES:
            log(f"  [SEP] query='{query}' …")
            records = await self._scrape_query(query, seen_ids)
            all_records.extend(records)
            log(f"  [SEP] query='{query}' → {len(records)} nuevos")
            await asyncio.sleep(1)

        return all_records

    async def _scrape_query(self, query: str, seen_ids: set[str]) -> list[dict]:
        results: list[dict] = []
        start = 0

        async with httpx.AsyncClient(timeout=30) as client:
            while True:
                params = {
                    "q": query,
                    "wt": "json",
                    "rows": ROWS_PER_PAGE,
                    "start": start,
                    "fl": FIELDS,
                }

                data = await self._get_with_retries(client, params)
                docs = data.get("response", {}).get("docs", [])
                if not docs:
                    break

                for doc in docs:
                    cedula_id = str(doc.get("idCedula", "")).strip()
                    if cedula_id and cedula_id not in seen_ids:
                        seen_ids.add(cedula_id)
                        results.append(self._normalize(doc))

                start += ROWS_PER_PAGE
                await asyncio.sleep(0.5)

        return results

    async def _get_with_retries(self, client: httpx.AsyncClient, params: dict) -> dict:
        for attempt in range(MAX_RETRIES):
            try:
                resp = await client.get(BASE_URL, params=params)
                resp.raise_for_status()
                return resp.json()
            except Exception as exc:
                if attempt == MAX_RETRIES - 1:
                    raise
                log(f"  [SEP] reintento {attempt + 1}: {exc}", level="warning")
                await asyncio.sleep(2 * (attempt + 1))
        return {}  # nunca llega aquí

    @staticmethod
    def _normalize(doc: dict) -> dict:
        titulo = limpiar_texto(doc.get("titulo"))
        return {
            "cedula_id": str(doc.get("idCedula", "")).strip(),
            "nombre": limpiar_texto(doc.get("nombre")),
            "apellido_paterno": limpiar_texto(doc.get("paterno")),
            "apellido_materno": limpiar_texto(doc.get("materno")),
            "titulo": titulo,
            "institucion": (doc.get("institucion") or "").strip(),
            "anio_registro": doc.get("anioRegistro"),
            "fuente": "SEP_FEDERAL",
            "estado": "FEDERAL",
            "es_medicina": es_medicina(titulo),
        }
