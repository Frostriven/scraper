from __future__ import annotations

import os
from supabase import create_client, Client

from utils.logger import log


def get_client() -> Client:
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    return create_client(url, key)


def upsert_batch(client: Client, records: list[dict], batch_size: int = 500) -> int:
    """Inserta o actualiza registros en lotes. Devuelve el total guardado."""
    total = 0
    for i in range(0, len(records), batch_size):
        batch = records[i : i + batch_size]
        client.table("cedulas_profesionales").upsert(
            batch, on_conflict="cedula_id"
        ).execute()
        total += len(batch)
        log(f"  Guardados {total}/{len(records)} registros…")
    return total
