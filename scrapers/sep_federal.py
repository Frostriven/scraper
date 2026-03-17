from __future__ import annotations

import asyncio

from playwright.async_api import async_playwright, Page

from scrapers.base_scraper import BaseScraper
from utils.normalizer import es_medicina, limpiar_texto
from utils.logger import log

URL = "https://cedulaprofesional.sep.gob.mx/cedula/presidencia/indexAvanzada.action"

TERMINOS_MEDICINA = [
    "medico", "médico", "medicina", "cirujano",
    "cirujana", "pediatra", "ginecolog", "cardiol",
    "neurolog", "psiquiat", "internista", "urgencias",
    "familiar", "dermatol", "oftalmol", "ortoped",
    "urolog", "anestesiol", "radiolog", "oncolog",
]

MAX_RETRIES = 3


class SepFederalScraper(BaseScraper):
    nombre = "SEP Federal"

    async def scrape_all(self) -> list[dict]:
        seen_ids: set[str] = set()
        all_records: list[dict] = []

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                )
            )
            page = await context.new_page()

            for termino in TERMINOS_MEDICINA:
                log(f"  [SEP] buscando '{termino}' …")
                records = await self._buscar_termino(page, termino, seen_ids)
                all_records.extend(records)
                log(f"  [SEP] '{termino}' → {len(records)} nuevos")
                await asyncio.sleep(2)

            await browser.close()

        return all_records

    async def _buscar_termino(
        self, page: Page, termino: str, seen_ids: set[str]
    ) -> list[dict]:
        results: list[dict] = []

        for attempt in range(MAX_RETRIES):
            try:
                await page.goto(URL, wait_until="networkidle", timeout=30_000)
                break
            except Exception as exc:
                if attempt == MAX_RETRIES - 1:
                    log(f"  [SEP] no se pudo cargar la página para '{termino}': {exc}", level="error")
                    return results
                await asyncio.sleep(2 * (attempt + 1))

        # Detectar CAPTCHA antes de continuar
        if await self._tiene_captcha(page):
            log(f"  [SEP] CAPTCHA detectado para '{termino}', saltando", level="warning")
            return results

        try:
            # Llenar formulario — buscar el campo de nombre por varios selectores posibles
            nombre_input = (
                page.locator('input[name="nombre"]')
                .or_(page.locator('input[id*="nombre"]'))
                .or_(page.locator('input[name="nomBusqueda"]'))
                .first
            )
            await nombre_input.fill(termino)

            # Enviar formulario
            submit_btn = (
                page.locator('input[type="submit"]')
                .or_(page.locator('button[type="submit"]'))
                .or_(page.locator('input[value="Buscar"]'))
                .first
            )
            await submit_btn.click()
            await page.wait_for_load_state("networkidle", timeout=30_000)
        except Exception as exc:
            log(f"  [SEP] error llenando formulario para '{termino}': {exc}", level="error")
            return results

        # Detectar CAPTCHA después del submit
        if await self._tiene_captcha(page):
            log(f"  [SEP] CAPTCHA detectado después de buscar '{termino}', saltando", level="warning")
            return results

        # Extraer resultados de la página actual y paginar
        while True:
            page_results = await self._extraer_tabla(page, seen_ids)
            results.extend(page_results)

            # Intentar ir a la siguiente página
            next_link = await self._encontrar_siguiente(page)
            if not next_link:
                break

            try:
                await next_link.click()
                await page.wait_for_load_state("networkidle", timeout=30_000)
                await asyncio.sleep(1)
            except Exception:
                break

            if await self._tiene_captcha(page):
                log(f"  [SEP] CAPTCHA en paginación para '{termino}', deteniendo", level="warning")
                break

        return results

    async def _extraer_tabla(self, page: Page, seen_ids: set[str]) -> list[dict]:
        results: list[dict] = []
        rows = await page.query_selector_all("table tr")

        for row in rows[1:]:  # saltar cabecera
            cols = await row.query_selector_all("td")
            if len(cols) < 5:
                continue

            cedula_id = (await cols[0].inner_text()).strip()
            if not cedula_id or cedula_id in seen_ids:
                continue

            seen_ids.add(cedula_id)

            nombre = (await cols[1].inner_text()).strip()
            ap_paterno = (await cols[2].inner_text()).strip()
            ap_materno = (await cols[3].inner_text()).strip()
            titulo = (await cols[4].inner_text()).strip()
            institucion = (await cols[5].inner_text()).strip() if len(cols) > 5 else ""

            anio_raw = (await cols[6].inner_text()).strip() if len(cols) > 6 else ""
            try:
                anio = int(anio_raw)
            except (ValueError, TypeError):
                anio = None

            results.append({
                "cedula_id": cedula_id,
                "nombre": limpiar_texto(nombre),
                "apellido_paterno": limpiar_texto(ap_paterno),
                "apellido_materno": limpiar_texto(ap_materno),
                "titulo": limpiar_texto(titulo),
                "institucion": institucion,
                "anio_registro": anio,
                "fuente": "SEP_FEDERAL",
                "estado": "FEDERAL",
                "es_medicina": es_medicina(titulo),
            })

        return results

    @staticmethod
    async def _tiene_captcha(page: Page) -> bool:
        captcha_indicators = [
            "captcha", "recaptcha", "g-recaptcha",
            "hcaptcha", "verificación humana", "verify you are human",
        ]
        content = (await page.content()).lower()
        return any(indicator in content for indicator in captcha_indicators)

    @staticmethod
    async def _encontrar_siguiente(page: Page):
        """Busca un enlace de 'siguiente página' en la página actual."""
        for selector in [
            'a:has-text("Siguiente")',
            'a:has-text("siguiente")',
            'a:has-text("Next")',
            'a:has-text("next")',
            'a:has-text(">")',
            'a:has-text("»")',
            'a.next',
            'li.next a',
        ]:
            link = page.locator(selector).first
            if await link.count() > 0 and await link.is_visible():
                return link
        return None
