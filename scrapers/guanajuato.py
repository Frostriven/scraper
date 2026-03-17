from __future__ import annotations

import asyncio
import string
import re

import httpx
from bs4 import BeautifulSoup

from scrapers.base_scraper import BaseScraper
from utils.normalizer import es_medicina, limpiar_texto
from utils.logger import log

BASE_URL = "http://www.seg.guanajuato.gob.mx/Ceducativa/Profesionistas/Cedulas/Cedulas.aspx"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

MAX_RETRIES = 3


class GuanajuatoScraper(BaseScraper):
    nombre = "Guanajuato"

    async def scrape_all(self) -> list[dict]:
        seen_ids: set[str] = set()
        all_records: list[dict] = []

        for letra in string.ascii_uppercase:
            log(f"  [Guanajuato] buscando '{letra}' …")
            records = await self._search_letter(letra, seen_ids)
            all_records.extend(records)
            log(f"  [Guanajuato] '{letra}' → {len(records)} nuevos")
            await asyncio.sleep(1.5)

        return all_records

    async def _search_letter(self, letra: str, seen_ids: set[str]) -> list[dict]:
        results: list[dict] = []

        async with httpx.AsyncClient(timeout=30, headers=HEADERS, follow_redirects=True) as client:
            # 1. GET inicial para obtener ViewState
            viewstate_data = await self._get_viewstate(client)
            if not viewstate_data:
                return results

            # 2. POST con búsqueda
            form_data = {
                "__VIEWSTATE": viewstate_data["viewstate"],
                "__VIEWSTATEGENERATOR": viewstate_data.get("viewstate_generator", ""),
                "__EVENTVALIDATION": viewstate_data["event_validation"],
                "txtBuscar": letra,
                "btnBuscar": "Buscar",
            }

            for attempt in range(MAX_RETRIES):
                try:
                    resp = await client.post(BASE_URL, data=form_data)
                    resp.raise_for_status()
                    break
                except Exception as exc:
                    if attempt == MAX_RETRIES - 1:
                        log(f"  [Guanajuato] error POST '{letra}': {exc}", level="error")
                        return results
                    await asyncio.sleep(2 * (attempt + 1))
            else:
                return results

            # 3. Parsear resultados
            soup = BeautifulSoup(resp.text, "lxml")
            table = soup.find("table", {"id": re.compile(r"GridView|grd|tbl", re.I)})
            if not table:
                return results

            rows = table.find_all("tr")
            for row in rows[1:]:
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
                    "fuente": "GUANAJUATO",
                    "estado": "GUANAJUATO",
                    "es_medicina": True,
                })

        return results

    async def _get_viewstate(self, client: httpx.AsyncClient) -> dict | None:
        for attempt in range(MAX_RETRIES):
            try:
                resp = await client.get(BASE_URL)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "lxml")

                vs = soup.find("input", {"name": "__VIEWSTATE"})
                ev = soup.find("input", {"name": "__EVENTVALIDATION"})
                vsg = soup.find("input", {"name": "__VIEWSTATEGENERATOR"})

                if not vs or not ev:
                    log("  [Guanajuato] no se encontró ViewState", level="warning")
                    return None

                return {
                    "viewstate": vs.get("value", ""),
                    "event_validation": ev.get("value", ""),
                    "viewstate_generator": vsg.get("value", "") if vsg else "",
                }
            except Exception as exc:
                if attempt == MAX_RETRIES - 1:
                    log(f"  [Guanajuato] error GET ViewState: {exc}", level="error")
                    return None
                await asyncio.sleep(2 * (attempt + 1))
        return None
