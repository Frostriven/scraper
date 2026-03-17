from __future__ import annotations

import abc


class BaseScraper(abc.ABC):
    """Interfaz común para todos los scrapers de cédulas."""

    nombre: str = "base"

    @abc.abstractmethod
    async def scrape_all(self) -> list[dict]:
        """Devuelve una lista de registros normalizados."""
        ...
