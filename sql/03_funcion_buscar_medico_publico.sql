-- Función pública para directorio médico (accesible sin autenticación)
CREATE OR REPLACE FUNCTION buscar_medico_publico(
  p_nombre text
)
RETURNS TABLE (
  cedula_id text,
  nombre text,
  apellido_paterno text,
  apellido_materno text,
  titulo text,
  institucion text,
  anio_registro int,
  fuente text
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
    c.anio_registro,
    c.fuente
  FROM cedulas_profesionales c
  WHERE
    c.es_medicina = true
    AND to_tsvector('spanish', c.nombre_completo) @@
        plainto_tsquery('spanish', p_nombre)
  ORDER BY
    ts_rank(
      to_tsvector('spanish', c.nombre_completo),
      plainto_tsquery('spanish', p_nombre)
    ) DESC
  LIMIT 20;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Permitir acceso anónimo a la función
GRANT EXECUTE ON FUNCTION buscar_medico_publico(text) TO anon;
