# Releva Scraper

Sistema de scraping de cédulas profesionales médicas en México para la app **Releva**.

## Fuentes

| Scraper | Cobertura | Tipo |
|---------|-----------|------|
| SEP Federal | 25 estados (~78% de médicos) | API Solr pública |
| Sonora | Estado de Sonora | Portal web HTML |
| Guanajuato | Estado de Guanajuato | Portal ASP.NET |

## Setup

```bash
pip install -r requirements.txt
```

### Variables de entorno requeridas

```
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJ...
```

## Uso

```bash
python main.py
```

## SQL

Ejecutar en orden en el SQL Editor de Supabase:

1. `sql/01_tabla_cedulas.sql` — Crea la tabla e índices
2. `sql/02_funcion_buscar_cedula.sql` — Función de búsqueda privada
3. `sql/03_funcion_buscar_medico_publico.sql` — Función de directorio público

## GitHub Actions

El workflow se ejecuta automáticamente el día 1 de cada mes a las 4am UTC.
Para correrlo manualmente: Actions → "Actualizar base de cédulas médicas" → Run workflow.

### Secrets necesarios

- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
