# Code Review PostgreSQL — Anti-patrones, seguridad, PL/pgSQL

## Checklist de revisión rápida

1. ¿Parámetros SIEMPRE ($1) — jamás concatenación de strings? (inyección)
2. ¿SELECT * en producción? → columnas explícitas.
3. ¿Tipos correctos (TIMESTAMPTZ, NUMERIC, CITEXT, JSONB) o reflejos de MySQL?
4. ¿Las reglas de negocio en constraints o solo en la app?
5. ¿Falta índice en FK? (PG no lo crea solo).
6. ¿JSONB consultado con ->> sin GIN? ¿Arrays con ANY() sin GIN?
7. ¿GRANTs granulares o TODO ON ALL TABLES?
8. ¿N+1 en el código de la app? (una query por fila → JOIN o IN).

## Anti-patrones frecuentes

```sql
-- Mal: JSONB sin índice
SELECT * FROM pedidos WHERE data->>'estado' = 'pagado';
-- Bien:
CREATE INDEX idx_pedidos_estado ON pedidos USING gin(data);
SELECT * FROM pedidos WHERE data @> '{"estado":"pagado"}';

-- Mal: array sin índice
SELECT * FROM productos WHERE 'laptop' = ANY(etiquetas);
-- Bien:
CREATE INDEX idx_prod_etiquetas ON productos USING gin(etiquetas);
SELECT * FROM productos WHERE etiquetas @> ARRAY['laptop'];

-- Mal: case-insensitive manual en cada query
SELECT * FROM usuarios WHERE LOWER(email) = LOWER($1);   -- sin índice de expresión = Seq Scan
-- Bien: CITEXT UNIQUE, o CREATE INDEX ON usuarios(lower(email));

-- Mal: ENUM para dominio que crece (roles, tipos de pago) → ALTER TYPE por cada valor
-- Bien: tabla catálogo + FK (patrón del sistema gestion-estudiantes)

-- Mal: OFFSET profundo en paginación
-- Bien: keyset pagination (WHERE id > $last ORDER BY id LIMIT n)

-- Mal: GROUP BY flexible estilo MySQL (PG lo rechaza)
SELECT carrera, COUNT(*) FROM matriculas GROUP BY semestre;   -- ERROR en PG
-- Bien: GROUP BY carrera
```

## PL/pgSQL

```sql
-- Trigger de actualizado idiomático (equivalente de ON UPDATE CURRENT_TIMESTAMP)
CREATE OR REPLACE FUNCTION set_actualizado() RETURNS trigger AS $$
BEGIN
  NEW.actualizado := now();
  RETURN NEW;
END $$ LANGUAGE plpgsql;

CREATE TRIGGER trg_usuarios_actualizado BEFORE UPDATE ON usuarios
FOR EACH ROW WHEN (OLD.* IS DISTINCT FROM NEW.*)   -- solo cuando realmente cambia
EXECUTE FUNCTION set_actualizado();
```

Reglas: funciones pequeñas y con un propósito; `WHEN (OLD.* IS DISTINCT FROM NEW.*)` para no disparar en writes vacíos; evitar lógica de negocio compleja en triggers (pertenece a la capa de dominio o a constraints declarativos).

## Seguridad

```sql
-- RLS cuando múltiples contextos comparten tabla (multi-tenant, multi-rol)
ALTER TABLE pagos ENABLE ROW LEVEL SECURITY;
CREATE POLICY propios_pagos ON pagos FOR SELECT
  TO app_estudiante
  USING (estudiante = current_setting('app.estudiante')::text);

-- GRANULAR, nunca TODO
GRANT SELECT, INSERT, UPDATE ON pagos TO app_rw;
GRANT USAGE ON SEQUENCE pagos_id_seq TO app_rw;
REVOKE ALL ON schema public FROM public;   -- esquema cerrado
```

- Credenciales por variable de entorno o .pgpass — prohibido en el código.
- Conexión TLS si hay red de por medio.
- Auditoría: bitácora de acciones (patrón del sistema gestion-estudiantes) o pgaudit para niveles superiores.
