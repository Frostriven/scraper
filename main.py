import asyncio

from scrapers.sep_federal import SepFederalScraper
from scrapers.sonora import SonoraScraper
from scrapers.guanajuato import GuanajuatoScraper
from utils.supabase_client import get_client, upsert_batch
from utils.logger import log


async def main() -> None:
    client = get_client()

    scrapers = [
        ("SEP Federal", SepFederalScraper()),
        ("Sonora", SonoraScraper()),
        ("Guanajuato", GuanajuatoScraper()),
    ]

    total = 0
    for nombre, scraper in scrapers:
        log(f"Iniciando scraper: {nombre}")
        try:
            records = await scraper.scrape_all()
            medicos = [r for r in records if r["es_medicina"]]
            guardados = upsert_batch(client, medicos)
            log(f"{nombre}: {guardados} médicos guardados")
            total += guardados
        except Exception as exc:
            log(f"ERROR en {nombre}: {exc}", level="error")

    log(f"TOTAL médicos guardados en esta corrida: {total}")


if __name__ == "__main__":
    asyncio.run(main())
