-- Tabla principal de cédulas profesionales
CREATE TABLE IF NOT EXISTS cedulas_profesionales (
  id                uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  cedula_id         text UNIQUE NOT NULL,
  nombre            text NOT NULL,
  apellido_paterno  text NOT NULL,
  apellido_materno  text DEFAULT '',
  nombre_completo   text GENERATED ALWAYS AS (
                      nombre || ' ' || apellido_paterno || ' ' || COALESCE(apellido_materno, '')
                    ) STORED,
  titulo            text,
  institucion       text,
  anio_registro     int,
  estado            text DEFAULT 'FEDERAL',
  fuente            text NOT NULL,
  es_medicina       boolean DEFAULT false,
  creado_at         timestamptz DEFAULT now(),
  actualizado_at    timestamptz DEFAULT now()
);

-- Índice de texto completo para búsqueda por nombre
CREATE INDEX IF NOT EXISTS idx_cedulas_nombre_fts
  ON cedulas_profesionales
  USING gin(to_tsvector('spanish', nombre_completo));

-- Índice por número de cédula
CREATE INDEX IF NOT EXISTS idx_cedulas_cedula_id
  ON cedulas_profesionales(cedula_id);

-- Índice por es_medicina para filtrar rápido
CREATE INDEX IF NOT EXISTS idx_cedulas_medicina
  ON cedulas_profesionales(es_medicina);
