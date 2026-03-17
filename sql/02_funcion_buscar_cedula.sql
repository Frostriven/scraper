-- Función de búsqueda privada (requiere autenticación)
CREATE OR REPLACE FUNCTION buscar_cedula(
  p_nombre text,
  p_apellido_paterno text,
  p_cedula_id text DEFAULT NULL
)
RETURNS TABLE (
  cedula_id text,
  nombre text,
  apellido_paterno text,
  apellido_materno text,
  titulo text,
  institucion text,
  fuente text,
  es_medicina boolean,
  score real
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    c.cedula_id,
    c.nombre,
    c.apellido_paterno,
    c.apellido_materno,
    c.titulo,
    c.institucion,
    c.fuente,
    c.es_medicina,
    ts_rank(
      to_tsvector('spanish', c.nombre_completo),
      plainto_tsquery('spanish', p_nombre || ' ' || p_apellido_paterno)
    ) AS score
  FROM cedulas_profesionales c
  WHERE
    c.es_medicina = true
    AND (
      (p_cedula_id IS NOT NULL AND c.cedula_id = p_cedula_id)
      OR
      to_tsvector('spanish', c.nombre_completo) @@
      plainto_tsquery('spanish', p_nombre || ' ' || p_apellido_paterno)
    )
  ORDER BY score DESC
  LIMIT 5;
END;
$$ LANGUAGE plpgsql;
