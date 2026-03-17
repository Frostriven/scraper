from __future__ import annotations

import asyncio
import string

import httpx
from bs4 import BeautifulSoup

from scrapers.base_scraper import BaseScraper
from utils.normalizer import es_medicina, limpiar_texto
from utils.logger import log

BASE_URL = "https://cedulasonora.sec.gob.mx/"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

MAX_RETRIES = 3


class SonoraScraper(BaseScraper):
    nombre = "Sonora"

    async def scrape_all(self) -> list[dict]:
        seen_ids: set[str] = set()
        all_records: list[dict] = []

        for letra in string.ascii_uppercase:
            log(f"  [Sonora] buscando apellido '{letra}' …")
            records = await self._search_letter(letra, seen_ids)
            all_records.extend(records)
            log(f"  [Sonora] '{letra}' → {len(records)} nuevos")
            await asyncio.sleep(1)

        return all_records

    async def _search_letter(self, letra: str, seen_ids: set[str]) -> list[dict]:
        results: list[dict] = []

        async with httpx.AsyncClient(timeout=30, headers=HEADERS, follow_redirects=True) as client:
            for attempt in range(MAX_RETRIES):
                try:
                    resp = await client.get(BASE_URL, params={"buscar": letra})
                    resp.raise_for_status()
                    break
                except Exception as exc:
                    if attempt == MAX_RETRIES - 1:
                        log(f"  [Sonora] error letra '{letra}': {exc}", level="error")
                        return results
                    await asyncio.sleep(2 * (attempt + 1))
            else:
                return results

            soup = BeautifulSoup(resp.text, "lxml")
            rows = soup.select("table tr")

            for row in rows[1:]:  # saltar cabecera
                cols = row.find_all("td")
                if len(cols) < 4:
                    continue

                cedula_id = cols[0].get_text(strip=True)
                if not cedula_id or cedula_id in seen_ids:
                    continue

                nombre_raw = cols[1].get_text(strip=True)
                titulo_raw = cols[2].get_text(strip=True)
                institucion_raw = cols[3].get_text(strip=True) if len(cols) > 3 else ""

                if not es_medicina(titulo_raw):
                    continue

                seen_ids.add(cedula_id)
                parts = nombre_raw.split()
                nombre = " ".join(parts[:-2]) if len(parts) > 2 else parts[0] if parts else ""
                ap_paterno = parts[-2] if len(parts) >= 2 else ""
                ap_materno = parts[-1] if len(parts) >= 3 else ""

                results.append({
                    "cedula_id": cedula_id,
                    "nombre": limpiar_texto(nombre),
                    "apellido_paterno": limpiar_texto(ap_paterno),
                    "apellido_materno": limpiar_texto(ap_materno),
                    "titulo": limpiar_texto(titulo_raw),
                    "institucion": institucion_raw.strip(),
                    "anio_registro": None,
                    "fuente": "SONORA",
                    "estado": "SONORA",
                    "es_medicina": True,
                })

        return results
